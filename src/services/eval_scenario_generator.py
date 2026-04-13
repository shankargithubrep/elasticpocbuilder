"""
Eval Scenario Generator

Generates a customer evaluation query pack (eval_scenarios.json) for any
demo module by:
  1. Extracting the real index schema from the data generator
  2. Reading demo config for context
  3. Calling the LLM to produce structured ES|QL evaluation scenarios
  4. Saving the result to demos/{module}/eval_scenarios.json

The generated scenarios are used by the Eval Workbench tab and are
reusable across sessions.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EvalScenarioGenerator:
    """Generates eval scenarios for a demo module on demand."""

    SCENARIOS_FILENAME = "eval_scenarios.json"

    def __init__(self, module_path: str, llm_client=None):
        self.module_path = Path(module_path)
        self.llm_client = llm_client
        self._scenarios_path = self.module_path / self.SCENARIOS_FILENAME

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def has_scenarios(self) -> bool:
        return self._scenarios_path.exists()

    def load_scenarios(self) -> Optional[Dict[str, Any]]:
        """Load persisted scenarios. Returns None if not generated yet."""
        if not self._scenarios_path.exists():
            return None
        try:
            return json.loads(self._scenarios_path.read_text())
        except Exception as e:
            logger.error(f"Failed to load eval_scenarios.json: {e}")
            return None

    def generate(self, progress_callback=None) -> Dict[str, Any]:
        """
        Full pipeline: extract schema → build prompt → call LLM → parse → save.
        Returns the persisted scenarios dict.
        """
        def _cb(msg):
            if progress_callback:
                progress_callback(msg)
            logger.info(msg)

        _cb("📂 Loading demo config...")
        config = self._load_config()

        _cb("🔍 Extracting index schema from data generator...")
        schema = self._extract_schema()

        if not schema:
            raise RuntimeError(
                "Could not extract schema from data generator. "
                "Make sure data_generator.py exists and is valid."
            )

        def _field_count(info):
            if isinstance(info, dict):
                return len(info.get("fields", []))
            return len(info)

        _cb(f"✅ Schema extracted: {len(schema)} indices, "
            f"{sum(_field_count(v) for v in schema.values())} total fields")

        _cb("🤖 Calling LLM to generate eval scenarios...")
        llm_client = self.llm_client or self._get_default_llm()
        raw = self._call_llm(llm_client, config, schema)

        _cb("🔧 Parsing LLM response...")
        scenarios = self._parse_response(raw)

        _cb(f"💾 Saving {len(scenarios)} scenarios to eval_scenarios.json...")
        result = self._save(config, schema, scenarios)

        _cb(f"✅ Done — {len(scenarios)} scenarios generated.")
        return result

    # ------------------------------------------------------------------
    # Schema extraction
    # ------------------------------------------------------------------

    def _extract_schema(self) -> Dict[str, Any]:
        """
        Load the data generator, call generate_datasets(), and extract:
        - field names per index
        - sample values for categorical fields (for WHERE / MATCH hints)
        - which fields look like free-text (good for MATCH queries)

        Falls back to basic field-name-only dict on failure.
        """
        try:
            from src.framework.module_loader import ModuleLoader
            loader = ModuleLoader(str(self.module_path))
            data_gen = loader.load_data_generator()
            datasets = data_gen.generate_datasets()

            schema: Dict[str, Any] = {}
            for name, df in datasets.items():
                fields = list(df.columns)
                samples: Dict[str, List] = {}
                text_fields: List[str] = []

                for col in fields:
                    if col == "@timestamp":
                        continue
                    try:
                        unique_vals = df[col].dropna().unique()
                        # Categorical: few unique string values → good for WHERE
                        if df[col].dtype == object:
                            n_unique = len(unique_vals)
                            if n_unique <= 30:
                                samples[col] = [
                                    str(v) for v in unique_vals[:8]
                                    if str(v) not in ("NULL", "None", "nan", "")
                                ]
                            # Text: many unique string values with spaces → MATCH candidates
                            elif n_unique > 30:
                                sample_val = str(unique_vals[0]) if len(unique_vals) else ""
                                if " " in sample_val and len(sample_val) > 10:
                                    text_fields.append(col)
                                    samples[col] = [
                                        str(v) for v in unique_vals[:5]
                                        if str(v) not in ("NULL", "None", "")
                                    ]
                    except Exception:
                        pass

                schema[name] = {
                    "fields": fields,
                    "samples": samples,
                    "text_fields": text_fields,
                }

            logger.info(f"Schema extracted: {list(schema.keys())}")
            return schema
        except Exception as e:
            logger.warning(f"Data generator schema extraction failed ({e}), falling back to file parse")
            raw = self._parse_schema_from_file()
            # Wrap in the richer format
            return {k: {"fields": v, "samples": {}, "text_fields": []} for k, v in raw.items()}

    def _parse_schema_from_file(self) -> Dict[str, List[str]]:
        """
        Fallback: parse data_generator.py looking for pd.DataFrame({...})
        constructions to extract field names without executing the code.
        """
        import re
        schema = {}
        dg_path = self.module_path / "data_generator.py"
        if not dg_path.exists():
            return schema

        text = dg_path.read_text()

        # Find all  return pd.DataFrame({...})  blocks
        # and pull the quoted keys out as field names
        blocks = re.findall(r'return pd\.DataFrame\(\{([\s\S]*?)\}\)', text)
        method_names = re.findall(
            r'def (_generate_\w+)\(', text
        )

        for i, block in enumerate(blocks):
            keys = re.findall(r'"([^"]+)"\s*:', block) or re.findall(r"'([^']+)'\s*:", block)
            if not keys:
                continue
            # Map to the dataset name: strip leading _generate_ and trailing ()
            method = method_names[i] if i < len(method_names) else f"dataset_{i}"
            dataset_name = method.replace("_generate_", "")
            schema[dataset_name] = keys

        return schema

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    def _get_default_llm(self):
        from src.services.llm_proxy_service import UnifiedLLMClient
        return UnifiedLLMClient()

    def _build_prompt(self, config: dict, schema: Dict[str, Any]) -> str:
        ctx = config.get("customer_context", {})
        company     = ctx.get("company_name", "Unknown Company")
        department  = ctx.get("department", "")
        industry    = ctx.get("industry", "")
        pain_points = ctx.get("pain_points", [])
        use_cases   = ctx.get("use_cases", [])
        metrics     = ctx.get("metrics", [])
        demo_type   = config.get("demo_type", "search")

        # Build rich schema description with samples and text field callouts
        schema_lines = []
        all_text_fields: Dict[str, List[str]] = {}   # index → text field names
        for idx_name, info in schema.items():
            # Support both old (list) and new (dict) format
            if isinstance(info, list):
                fields = info
                samples: Dict = {}
                text_fields: List[str] = []
            else:
                fields     = info.get("fields", [])
                samples    = info.get("samples", {})
                text_fields = info.get("text_fields", [])

            schema_lines.append(f"\nIndex: {idx_name}")
            schema_lines.append("Fields: " + ", ".join(fields))

            if text_fields:
                all_text_fields[idx_name] = text_fields
                schema_lines.append("  ↳ Text fields (use MATCH for full-text search): " + ", ".join(text_fields))

            if samples:
                for field, vals in samples.items():
                    if vals:
                        schema_lines.append(
                            f"  ↳ Sample values for {field}: "
                            + ", ".join(f'"{v}"' for v in vals[:6])
                        )

        schema_text = "\n".join(schema_lines)
        pain_text   = "\n".join(f"- {p}" for p in pain_points)
        uc_text     = "\n".join(f"- {u}" for u in use_cases)
        metric_text = "\n".join(f"- {m}" for m in metrics)

        # Build LIKE-based document search examples using real field names and sample values
        # (All string fields in demo data are indexed as keyword type; MATCH requires text type)
        like_examples = []
        for idx_name, info in schema.items():
            if isinstance(info, list):
                fields = info
                samples: Dict = {}
            else:
                fields = info.get("fields", [])
                samples = info.get("samples", {})

            # Pick the best "title-like" field from this index
            title_field = next(
                (f for f in fields if any(k in f.lower() for k in ("title", "name", "description", "content", "message", "subject"))),
                None
            )
            # Pick a good categorical filter field with known sample values
            cat_field = next(
                ((f, vals) for f, vals in samples.items() if vals and f in fields),
                (None, [])
            )

            if title_field:
                base = f'FROM {idx_name}\n  | WHERE {title_field} LIKE "*keyword*"'
                if cat_field[0]:
                    base += f'\n  | AND {cat_field[0]} == "{cat_field[1][0]}"'
                base += f'\n  | KEEP {", ".join(fields[:6])}\n  | LIMIT 10'
                like_examples.append(base)

        like_block = "\n\n".join(like_examples[:3]) if like_examples else (
            "FROM index_name\n  | WHERE field_name LIKE \"*keyword*\"\n  | KEEP field1, field2\n  | LIMIT 10"
        )

        # Also collect concrete sample values to anchor search keywords
        sample_hints = []
        for idx_name, info in schema.items():
            if isinstance(info, dict):
                for field, vals in info.get("samples", {}).items():
                    if vals:
                        sample_hints.append(f"  {idx_name}.{field}: {', '.join(repr(v) for v in vals[:4])}")
        sample_hints_text = "\n".join(sample_hints[:12]) if sample_hints else "  (no sample values available)"

        doc_search_instruction = f"""
### MANDATORY: Document Search Category
You MUST include a category called "Document Search" with AT LEAST 10 scenarios.
These simulate what a real end-user (agent / analyst / employee) would type into a search box.

⚠️ CRITICAL: All string fields in this demo are indexed as **keyword** type.
Use `LIKE "*keyword*"` with wildcards — NEVER use MATCH (it only works on text/semantic_text fields).

LIKE search syntax (copy this pattern):
{like_block}

Known field values you can embed as LIKE keywords or exact == filters:
{sample_hints_text}

Rules for Document Search scenarios:
- Use `LIKE "*keyword*"` — keyword must be a realistic word relevant to the {industry} industry
- Extract keywords from the sample values above where possible so queries return real results
- Add == filters on categorical fields (publish_status, lifecycle_status, content_category, etc.) to at least 4 scenarios
- Show KEEP with 4-6 of the most useful fields for the end user
- Vary search intent: broad topic, specific procedure, troubleshooting, compliance lookup
- audience: ["product"] for most, ["engineering"] for queries with extra technical filters
- Do NOT use STATS or aggregations — return individual documents
- Do NOT invent field names — only use field names listed in the schema above
"""

        return f"""You are an Elasticsearch solutions architect generating a customer evaluation query pack.

## Demo Context
- Company: {company}
- Department: {department}
- Industry: {industry}
- Demo type: {demo_type}

## Pain Points
{pain_text}

## Use Cases
{uc_text}

## Success Metrics
{metric_text}

## Available Elasticsearch Indices and Fields
{schema_text}

## Task
Generate 22-28 structured ES|QL evaluation scenarios for this demo.
{doc_search_instruction}

The remaining 12-18 scenarios should cover analytics categories relevant to pain points
(e.g. Tenant Isolation, Compliance & Audit, Data Quality, Performance, Business Analytics).

### Rules (ALL scenarios)
0. BRANDING: Always say "Elasticsearch" or "Elastic" — NEVER "OpenSearch", "Solr", or any competitor name. Use neutral terms ("search engine", "index") if needed.
1. ONLY use index names and field names exactly as listed above. No other names.
2. Write valid ES|QL 9.x syntax (FROM, WHERE, EVAL, STATS, SORT, LIMIT, INLINESTATS, LOOKUP JOIN, MATCH).
3. Use LOOKUP JOIN only when both indices appear in the schema above.
4. Never use COUNT(*) WHERE — use EVAL is_x = CASE(...) then SUM(is_x).
5. Always end with LIMIT (max 50).
6. Each scenario must directly address a pain point, use case, or realistic user need.
7. "proves" must be one concise sentence stating the Elastic capability demonstrated.
8. "note" must be one presenter talking point — what to say when results appear on screen.

### Required JSON format
Return ONLY a JSON array. No markdown fences, no explanation, no preamble.
Each element must be exactly:
{{
  "id": "DS-1",
  "category": "Document Search",
  "category_icon": "🔍",
  "title": "Short title",
  "description": "2-3 sentences explaining what the query does and why it matters.",
  "proves": "One sentence: what Elastic capability does this prove?",
  "audience": ["product"],
  "esql": "FROM index_name\\n| WHERE field_name LIKE \\"*keyword*\\"\\n| KEEP field1, field2\\n| LIMIT 10",
  "indices": ["index_name"],
  "note": "Presenter talking point."
}}

ID scheme: DS-1..DS-10 for Document Search, then RQ-1, AC-1, PF-1, CA-1, CL-1 etc. for analytics.

{self._few_shot_block(schema)}
Generate the JSON array now:"""

    def _few_shot_block(self, schema: Dict[str, Any]) -> str:
        """
        Retrieve similar successful queries from the cache and format them
        as few-shot examples to guide the LLM toward queries that actually work.
        Returns an empty string if the cache has fewer than 3 entries.
        """
        try:
            from src.services.esql_query_cache import EsqlQueryCache
            cache = EsqlQueryCache()
            if cache.size() < 3:
                return ""

            # Build a reference string from the schema (index + field names)
            reference = " ".join(
                idx + " " + " ".join(
                    (info.get("fields", info) if isinstance(info, dict) else info)[:10]
                )
                for idx, info in list(schema.items())[:4]
            )
            similar = cache.find_similar(reference, n=5)
            if not similar:
                return ""

            lines = [
                "\n## Few-Shot Examples (real queries that returned results — use as style guide)",
                "These queries ran successfully against Elasticsearch. "
                "Model your syntax and field usage on these examples.\n",
            ]
            for ex in similar:
                lines.append(f"### {ex['category']} — {ex['title']} ({ex['row_count']} rows)")
                lines.append("```sql")
                lines.append(ex["query"])
                lines.append("```\n")
            return "\n".join(lines) + "\n"
        except Exception:
            return ""

    def _call_llm(self, llm_client, config: dict, schema: Dict[str, Any]) -> str:
        prompt = self._build_prompt(config, schema)
        messages = [{"role": "user", "content": prompt}]
        # UnifiedLLMClient wraps LLMProxyClient; create_completion returns a str
        return llm_client._proxy_client.create_completion(
            messages=messages,
            max_tokens=16000,
            temperature=0.2,
            task="code_generation",
        )

    # ------------------------------------------------------------------
    # Parse LLM response
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str) -> List[Dict[str, Any]]:
        """
        Extract a JSON array from the LLM response.
        Handles:
        - markdown code fences  (```json ... ```)
        - truncated responses   (response cut off mid-JSON due to token limit)
        """
        import re

        text = raw.strip()

        # Strip markdown code fences if present
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()

        # Find the start of the JSON array
        start = text.find('[')
        if start == -1:
            raise ValueError(
                f"LLM response does not contain a JSON array.\n"
                f"First 200 chars: {text[:200]}"
            )

        # Try the full response first (array may be complete)
        end = text.rfind(']')
        json_text = text[start:end + 1] if end != -1 else text[start:]

        try:
            scenarios = json.loads(json_text)
        except json.JSONDecodeError:
            # Response was truncated — salvage every complete scenario object.
            # Strategy: find the last clean '}' that closes a top-level object,
            # then close the array there.
            salvaged = self._salvage_truncated_array(text[start:])
            if salvaged is None:
                raise ValueError(
                    "LLM response was truncated and could not be salvaged. "
                    "Try regenerating — the model ran out of tokens."
                )
            scenarios = salvaged
            logger.warning(
                f"LLM response was truncated; salvaged {len(scenarios)} complete scenarios."
            )

        if not isinstance(scenarios, list):
            raise ValueError(f"Expected list, got {type(scenarios)}")

        # Validate and normalise each scenario
        validated = []
        for i, s in enumerate(scenarios):
            if not isinstance(s, dict):
                continue
            # Ensure required fields
            s.setdefault("id", f"Q-{i+1}")
            s.setdefault("category", "General")
            s.setdefault("category_icon", "📋")
            s.setdefault("title", f"Scenario {i+1}")
            s.setdefault("description", "")
            s.setdefault("proves", "")
            s.setdefault("audience", ["engineering"])
            s.setdefault("esql", "")
            s.setdefault("indices", [])
            s.setdefault("note", "")
            validated.append(s)

        return validated

    def _salvage_truncated_array(self, partial_json: str) -> Optional[List[Dict]]:
        """
        Try to recover complete scenario objects from a truncated JSON array.
        Walks backwards from the last '}' that closes a top-level object,
        progressively trying shorter substrings until we get valid JSON.
        """
        # Try common indentation patterns: "  }" and "}" at line start
        for close_pattern in ("\n  }", "\n}"):
            pos = len(partial_json)
            while True:
                pos = partial_json.rfind(close_pattern, 0, pos)
                if pos == -1:
                    break
                candidate = partial_json[:pos + len(close_pattern)] + "\n]"
                try:
                    result = json.loads(candidate)
                    if isinstance(result, list) and result:
                        return result
                except json.JSONDecodeError:
                    pass
        return None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_config(self) -> dict:
        config_path = self.module_path / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
        return {}

    def _save(self, config: dict, schema: dict, scenarios: List[dict]) -> dict:
        ctx = config.get("customer_context", {})
        # schema values may be lists or dicts — normalise for summary
        summary = {}
        for k, v in schema.items():
            if isinstance(v, dict):
                summary[k] = len(v.get("fields", []))
            else:
                summary[k] = len(v)
        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "demo_module": self.module_path.name,
            "company": ctx.get("company_name", ""),
            "schema_summary": summary,
            "scenarios": scenarios,
        }
        self._scenarios_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        return result
