"""
POC Script Generator

Generates a standalone, self-contained Python setup script from a Vulcan demo module.
The output script:
  - Has zero Vulcan dependencies
  - Reads ES_URL / ES_API_KEY / KIBANA_URL from environment / .env
  - Works with Elastic Cloud Hosted, Cloud Serverless, and self-hosted
  - Creates index templates + ELSER pipeline + bulk-indexes data + Search App + Data Views
  - Optionally creates Agent Builder tools + agent

Usage (from Vulcan):
    gen = POCScriptGenerator()
    script_path = gen.generate(loader, module_name, options)
"""

import json
import logging
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Field types we recognise as "long text" and wire to ELSER
_SEMANTIC_FIELD_HINTS = {
    "description", "text", "content", "body", "summary", "notes",
    "holding", "guidance_text", "clause_text", "matter_description",
    "product_description", "details", "overview", "narrative",
    "incident_description", "alert_body", "log_message",
}


class POCScriptGenerator:
    """Generates a standalone Python POC setup script from a Vulcan demo."""

    # ── public API ────────────────────────────────────────────────────────────

    def generate(
        self,
        loader,
        module_name: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Build the POC script and save it to demos/<module_name>/poc_setup_<slug>.py.

        Returns the Path to the generated file.
        """
        options = options or {}
        cfg = loader.config
        ctx = cfg.get("customer_context") or cfg
        company = ctx.get("company_name") or "Customer"
        dept = ctx.get("department") or "Demo"
        pillar = cfg.get("pillar", cfg.get("demo_type", "search"))
        embedding = cfg.get("embedding_type", "elser")

        slug = module_name.lower().replace(" ", "_")

        # ── load demo artefacts ──────────────────────────────────────────────
        data_profile = self._load_json(loader.module_path / "data_profile.json") or {}
        all_queries = self._load_json(loader.module_path / "all_queries.json") or []
        elastic_assets = self._load_json(loader.module_path / "elastic_assets.json") or {}
        agent_metadata = self._load_json(loader.module_path / "agent_metadata.json") or {}
        query_strategy = self._load_json(loader.module_path / "query_strategy.json") or {}

        # ── materialise datasets ─────────────────────────────────────────────
        datasets_dict = self._materialise_datasets(loader)

        # ── derive semantic fields per dataset ──────────────────────────────
        semantic_map = self._infer_semantic_fields(datasets_dict, data_profile, embedding)

        # ── assemble script sections ─────────────────────────────────────────
        sections = [
            self._section_header(company, dept, slug),
            self._section_imports(),
            self._section_connection(),
            self._section_config(company, dept, pillar, embedding, slug),
            self._section_data(datasets_dict),
            self._section_index_templates(datasets_dict, semantic_map, embedding),
            self._section_pipeline(embedding),
            self._section_indexing(datasets_dict, semantic_map, embedding),
            self._section_search_app(slug, datasets_dict, query_strategy),
            self._section_kibana(datasets_dict),
        ]

        if options.get("include_agent", False) and agent_metadata:
            sections.append(self._section_agent(agent_metadata, all_queries, slug))

        sections.append(self._section_main(datasets_dict, embedding, company))

        script = "\n\n".join(s for s in sections if s)

        # ── write to disk ────────────────────────────────────────────────────
        out_path = loader.module_path / f"poc_setup_{slug}.py"
        out_path.write_text(script, encoding="utf-8")
        logger.info(f"POC script written to {out_path}")
        return out_path

    # ── private helpers ───────────────────────────────────────────────────────

    def _load_json(self, path: Path) -> Optional[Any]:
        try:
            if path.exists():
                return json.loads(path.read_text())
        except Exception as e:
            logger.warning(f"Could not load {path}: {e}")
        return None

    def _materialise_datasets(self, loader) -> Dict[str, List[Dict]]:
        """Run the demo's data_generator and return {index_name: [records]}."""
        try:
            dg = loader.load_data_generator()
            raw = dg.generate_datasets()
            result = {}
            for name, data in raw.items():
                # Handle pandas DataFrames
                try:
                    import pandas as pd
                    if isinstance(data, pd.DataFrame):
                        result[name] = data.where(data.notna(), None).to_dict(orient="records")
                        continue
                except ImportError:
                    pass
                # Handle list of dicts
                if isinstance(data, list):
                    result[name] = data
                elif isinstance(data, dict) and "records" in data:
                    result[name] = data["records"]
            return result
        except Exception as e:
            logger.warning(f"Could not materialise datasets: {e}")
            return {}

    def _infer_semantic_fields(
        self,
        datasets: Dict[str, List[Dict]],
        data_profile: Dict,
        embedding: str,
    ) -> Dict[str, List[str]]:
        """Return {index_name: [field_names_for_semantic_text]}."""
        if embedding not in ("elser", "e5"):
            return {}

        result = {}
        for idx, records in datasets.items():
            if not records:
                continue
            # 1. Check data_profile first
            profile_fields = (
                data_profile.get("datasets", {}).get(idx, {}).get("semantic_fields", [])
            )
            if profile_fields:
                result[idx] = profile_fields
                continue
            # 2. Infer from field names
            sample = records[0]
            semantic = [
                k for k in sample
                if any(hint in k.lower() for hint in _SEMANTIC_FIELD_HINTS)
                and isinstance(sample[k], str)
            ]
            if semantic:
                result[idx] = semantic[:3]  # cap at 3 semantic fields per index
        return result

    # ── script sections ───────────────────────────────────────────────────────

    def _section_header(self, company: str, dept: str, slug: str) -> str:
        now = datetime.utcnow().strftime("%Y-%m-%d")
        return textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """
            POC Setup Script: {company} — {dept}
            Generated by Elastic Demo Builder on {now}

            ┌─────────────────────────────────────────────────────────────────┐
            │  Quick Start                                                    │
            ├─────────────────────────────────────────────────────────────────┤
            │  pip install elasticsearch python-dotenv pandas                 │
            │                                                                 │
            │  # Option A — environment variables                             │
            │  export ES_URL=https://<host>:9243                              │
            │  export ES_API_KEY=<your-api-key>                               │
            │  export KIBANA_URL=https://<host>:5601   # optional             │
            │  python poc_setup_{slug}.py                     │
            │                                                                 │
            │  # Option B — .env file                                         │
            │  echo "ES_URL=..."  > .env                                      │
            │  echo "ES_API_KEY=..." >> .env                                  │
            │  python poc_setup_{slug}.py                     │
            └─────────────────────────────────────────────────────────────────┘

            Supports:
              • Elastic Cloud Hosted   (https://xxx.es.io:9243)
              • Elastic Cloud Serverless (https://xxx.es.io)
              • Self-hosted             (http://localhost:9200)
            """
        ''')

    def _section_imports(self) -> str:
        return textwrap.dedent('''\
            import json
            import logging
            import os
            import sys
            import time
            from datetime import datetime, timezone
            from typing import Any, Dict, List

            try:
                import pandas as pd
            except ImportError:
                pd = None  # pandas optional — data is pre-embedded as dicts

            try:
                from elasticsearch import Elasticsearch, helpers, NotFoundError
            except ImportError:
                sys.exit("❌  Run: pip install elasticsearch")

            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass  # python-dotenv optional

            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s  %(levelname)-7s %(message)s",
                datefmt="%H:%M:%S",
            )
            log = logging.getLogger("poc_setup")
        ''')

    def _section_connection(self) -> str:
        return textwrap.dedent('''\
            # ── Connection ────────────────────────────────────────────────────────────────
            ES_URL      = os.getenv("ES_URL", "").rstrip("/")
            ES_API_KEY  = os.getenv("ES_API_KEY", "")
            ES_USER     = os.getenv("ES_USERNAME", "")
            ES_PASS     = os.getenv("ES_PASSWORD", "")
            KIBANA_URL  = os.getenv("KIBANA_URL", "").rstrip("/")

            if not ES_URL:
                sys.exit("❌  ES_URL not set. Export it or add it to a .env file.")

            def build_es_client() -> Elasticsearch:
                kwargs: Dict[str, Any] = {"request_timeout": 60, "max_retries": 3}
                if ES_API_KEY:
                    kwargs["api_key"] = ES_API_KEY
                elif ES_USER and ES_PASS:
                    kwargs["basic_auth"] = (ES_USER, ES_PASS)
                return Elasticsearch(ES_URL, **kwargs)

            es = build_es_client()

            def check_connection():
                try:
                    info = es.info()
                    log.info(f"✅  Connected to Elasticsearch {info['version']['number']} @ {ES_URL}")
                except Exception as exc:
                    sys.exit(f"❌  Cannot reach Elasticsearch: {exc}")
        ''')

    def _section_config(
        self, company: str, dept: str, pillar: str, embedding: str, slug: str
    ) -> str:
        inference_id = (
            ".elser-2-elasticsearch" if embedding == "elser"
            else "multilingual-e5-small-elasticsearch" if embedding == "e5"
            else embedding
        )
        pipeline_name = f"{slug}-semantic-pipeline"
        search_app_name = f"{slug}-search-app"

        return textwrap.dedent(f'''\
            # ── Demo Configuration ────────────────────────────────────────────────────────
            COMPANY      = {json.dumps(company)}
            DEPARTMENT   = {json.dumps(dept)}
            PILLAR       = {json.dumps(pillar)}
            EMBEDDING    = {json.dumps(embedding)}          # elser | e5 | dense
            INFERENCE_ID = {json.dumps(inference_id)}
            PIPELINE_NAME  = {json.dumps(pipeline_name)}
            SEARCH_APP_NAME = {json.dumps(search_app_name)}
            DEMO_SLUG    = {json.dumps(slug)}
        ''')

    def _section_data(self, datasets: Dict[str, List[Dict]]) -> str:
        if not datasets:
            return "# ── Datasets ── (no data materialised)\nDATASETS: Dict[str, List[Dict]] = {}"

        lines = ["# ── Datasets (pre-embedded) ─────────────────────────────────────────────────"]
        lines.append("# Each dataset is a list of dicts ready for bulk indexing.")
        lines.append("DATASETS: Dict[str, List[Dict]] = {")

        for idx, records in datasets.items():
            # Limit to 300 records in the generated script to keep it reasonable
            sample = records[:300]
            serialised = json.dumps(sample, ensure_ascii=False, default=str)
            lines.append(f"    {json.dumps(idx)}: {serialised},")

        lines.append("}")
        return "\n".join(lines)

    def _section_index_templates(
        self,
        datasets: Dict[str, List[Dict]],
        semantic_map: Dict[str, List[str]],
        embedding: str,
    ) -> str:
        lines = [
            "# ── Index Templates ─────────────────────────────────────────────────────────",
            "",
            "def field_mapping(field_name: str, sample_value: Any) -> Dict[str, Any]:",
            '    """Auto-detect field type from sample value."""',
            "    if isinstance(sample_value, bool):",
            '        return {"type": "boolean"}',
            "    if isinstance(sample_value, int):",
            '        return {"type": "long"}',
            "    if isinstance(sample_value, float):",
            '        return {"type": "float"}',
            "    if isinstance(sample_value, str):",
            "        try:",
            '            datetime.fromisoformat(sample_value.replace("Z", "+00:00"))',
            '            return {"type": "date"}',
            "        except ValueError:",
            "            pass",
            '        if len(sample_value) > 64:',
            '            return {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}}',
            '        return {"type": "keyword"}',
            '    return {"type": "keyword"}',
            "",
            "",
            "def create_index_templates():",
            '    """Create index templates for every dataset."""',
        ]

        for idx, records in datasets.items():
            semantic_fields = semantic_map.get(idx, [])
            lines.append(f"    # {idx}")
            lines.append(f"    sample_{idx} = DATASETS[{json.dumps(idx)}][0] if DATASETS.get({json.dumps(idx)}) else {{}}")

            props_lines = [f"    props_{idx} = {{}}"]
            props_lines.append(f"    for field, val in sample_{idx}.items():")
            props_lines.append(f"        props_{idx}[field] = field_mapping(field, val)")

            # Override semantic fields
            if semantic_fields and embedding in ("elser", "e5"):
                for sf in semantic_fields:
                    props_lines.append(
                        f"    props_{idx}[{json.dumps(sf)}] = "
                        f'{{"type": "semantic_text", "inference_id": INFERENCE_ID}}'
                    )

            lines.extend(props_lines)

            lines.append(f"    template_body_{idx} = {{")
            lines.append(f'        "index_patterns": [{json.dumps(idx + "*")}],')
            lines.append(f'        "template": {{')
            lines.append(f'            "settings": {{"number_of_shards": 1, "number_of_replicas": 0}},')
            lines.append(f'            "mappings": {{"properties": props_{idx}}}')
            lines.append(f'        }}')
            lines.append(f'    }}')
            lines.append(f"    try:")
            lines.append(f"        es.indices.put_index_template(name={json.dumps(idx + '-template')}, body=template_body_{idx})")
            lines.append(f"        log.info(f'✅  Index template {idx}-template created')")
            lines.append(f"    except Exception as exc:")
            lines.append(f"        log.warning(f'⚠️   Template {idx}: {{exc}}')")
            lines.append("")

        return "\n".join(lines)

    def _section_pipeline(self, embedding: str) -> str:
        if embedding not in ("elser", "e5"):
            return (
                "# ── Ingest Pipeline ── (not required for non-semantic embedding)\n"
                "def create_pipeline():\n"
                "    log.info('⏭️   No ELSER/E5 pipeline needed for this embedding type.')\n"
            )

        return textwrap.dedent('''\
            # ── Ingest Pipeline ──────────────────────────────────────────────────────────

            def _wait_for_model(timeout: int = 120):
                """Block until the inference endpoint is ready."""
                deadline = time.time() + timeout
                while time.time() < deadline:
                    try:
                        result = es.perform_request(
                            "GET", f"/_inference/{INFERENCE_ID}", headers={"Accept": "application/json"}
                        )
                        log.info(f"✅  Inference endpoint {INFERENCE_ID} is ready")
                        return True
                    except Exception:
                        log.info(f"⏳  Waiting for {INFERENCE_ID} to be ready…")
                        time.sleep(5)
                log.warning(f"⚠️   Inference endpoint not ready after {timeout}s — continuing anyway")
                return False


            def create_pipeline():
                """Create an ELSER ingest pipeline for semantic fields."""
                # Collect all semantic fields across datasets (deduplicated)
                semantic_fields: List[str] = []
                for idx, records in DATASETS.items():
                    if not records:
                        continue
                    sample = records[0]
                    for k, v in sample.items():
                        if isinstance(v, str) and len(v) > 40 and k not in semantic_fields:
                            semantic_fields.append(k)

                if not semantic_fields:
                    log.info("⏭️   No long-text fields detected — skipping pipeline")
                    return

                _wait_for_model()

                processors = []
                for field in semantic_fields[:6]:  # cap at 6 semantic processors
                    processors.append({
                        "inference": {
                            "model_id": INFERENCE_ID,
                            "input_output": [
                                {"input_field": field, "output_field": f"{field}_sparse"}
                            ],
                            "on_failure": [{"set": {"field": "_index", "value": "_failed"}}],
                        }
                    })

                try:
                    es.ingest.put_pipeline(
                        id=PIPELINE_NAME,
                        body={
                            "description": f"ELSER semantic pipeline for {COMPANY} demo",
                            "processors": processors,
                        },
                    )
                    log.info(f"✅  Ingest pipeline '{PIPELINE_NAME}' created ({len(processors)} processors)")
                except Exception as exc:
                    log.warning(f"⚠️   Pipeline creation failed: {exc}")
        ''')

    def _section_indexing(
        self,
        datasets: Dict[str, List[Dict]],
        semantic_map: Dict[str, List[str]],
        embedding: str,
    ) -> str:
        use_pipeline = embedding in ("elser", "e5")
        has_semantic = any(semantic_map.values())

        return textwrap.dedent(f'''\
            # ── Data Indexing ────────────────────────────────────────────────────────────

            def bulk_index(index_name: str, records: List[Dict], use_pipeline: bool = {use_pipeline and has_semantic}):
                """Bulk-index a list of dicts into Elasticsearch."""
                if not records:
                    log.warning(f"⏭️   No records for {{index_name}} — skipping")
                    return

                # Drop the index if it exists (clean slate for POC)
                try:
                    es.indices.delete(index=index_name, ignore_unavailable=True)
                except Exception:
                    pass

                pipeline_arg = {{"pipeline": PIPELINE_NAME}} if use_pipeline else {{}}

                def _actions():
                    for doc in records:
                        yield {{"_index": index_name, "_source": doc, **pipeline_arg}}

                success, failed = helpers.bulk(
                    es,
                    _actions(),
                    chunk_size=100,
                    raise_on_error=False,
                    request_timeout=120,
                )
                if failed:
                    log.warning(f"⚠️   {{len(failed)}} docs failed for {{index_name}}")
                log.info(f"✅  Indexed {{success}} docs → {{index_name}}")


            def index_all_datasets():
                """Index every dataset in DATASETS."""
                for idx, records in DATASETS.items():
                    bulk_index(idx, records)
        ''')

    def _section_search_app(
        self,
        slug: str,
        datasets: Dict[str, List[Dict]],
        query_strategy: Dict,
    ) -> str:
        indices = list(datasets.keys())
        return textwrap.dedent(f'''\
            # ── Search Application ───────────────────────────────────────────────────────

            INDICES = {json.dumps(indices)}


            def create_search_application():
                """Create an Elastic Search Application over all demo indices."""
                body = {{
                    "indices": INDICES,
                    "template": {{
                        "script": {{
                            "source": {{
                                "query": {{
                                    "multi_match": {{
                                        "query": "{{{{params.query}}}}",
                                        "fields": ["*"],
                                        "type": "best_fields",
                                    }}
                                }}
                            }},
                            "params": {{"query": ""}},
                        }}
                    }},
                }}
                try:
                    es.perform_request(
                        "PUT",
                        f"/_application/search_application/{{SEARCH_APP_NAME}}",
                        body=body,
                        headers={{"Content-Type": "application/json"}},
                    )
                    log.info(f"✅  Search Application '{{SEARCH_APP_NAME}}' created")
                except Exception as exc:
                    log.warning(f"⚠️   Search Application: {{exc}}")
        ''')

    def _section_kibana(self, datasets: Dict[str, List[Dict]]) -> str:
        indices = list(datasets.keys())
        return textwrap.dedent(f'''\
            # ── Kibana Data Views ─────────────────────────────────────────────────────────

            import urllib.request
            import base64

            INDICES_FOR_VIEWS = {json.dumps(indices)}


            def _kibana_headers() -> Dict[str, str]:
                headers = {{"kbn-xsrf": "poc_setup", "Content-Type": "application/json"}}
                if ES_API_KEY:
                    headers["Authorization"] = f"ApiKey {{ES_API_KEY}}"
                elif ES_USER and ES_PASS:
                    creds = base64.b64encode(f"{{ES_USER}}:{{ES_PASS}}".encode()).decode()
                    headers["Authorization"] = f"Basic {{creds}}"
                return headers


            def create_kibana_data_views():
                """Create Kibana Data Views so Discover works immediately."""
                if not KIBANA_URL:
                    log.info("⏭️   KIBANA_URL not set — skipping Data View creation")
                    return

                for idx in INDICES_FOR_VIEWS:
                    payload = json.dumps({{
                        "data_view": {{
                            "title": f"{{idx}}*",
                            "name": idx.replace("_", " ").title(),
                        }}
                    }}).encode()

                    req = urllib.request.Request(
                        f"{{KIBANA_URL}}/api/data_views/data_view",
                        data=payload,
                        headers=_kibana_headers(),
                        method="POST",
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            log.info(f"✅  Data View created: {{idx}}")
                    except urllib.error.HTTPError as exc:
                        if exc.code == 409:
                            log.info(f"ℹ️   Data View already exists: {{idx}}")
                        else:
                            log.warning(f"⚠️   Data View {{idx}}: HTTP {{exc.code}}")
                    except Exception as exc:
                        log.warning(f"⚠️   Data View {{idx}}: {{exc}}")
        ''')

    def _section_agent(
        self, agent_metadata: Dict, all_queries: List[Dict], slug: str
    ) -> str:
        agent_name = agent_metadata.get("name", f"{slug}-agent")
        return textwrap.dedent(f'''\
            # ── Agent Builder (optional) ─────────────────────────────────────────────────

            AGENT_NAME = {json.dumps(agent_name)}


            def create_agent_tools():
                """Register ES|QL queries as Agent Builder tools."""
                tools = []
                for q in ALL_QUERIES[:10]:
                    if not isinstance(q, dict):
                        continue
                    tool = {{
                        "name": q.get("title", "query").lower().replace(" ", "_")[:40],
                        "description": q.get("purpose") or q.get("business_value", ""),
                        "query": q.get("esql") or q.get("query", ""),
                    }}
                    if tool["query"]:
                        tools.append(tool)
                log.info(f"ℹ️   Agent tool registration requires Kibana Agent Builder API — {{len(tools)}} tools ready")
                return tools
        ''')

    def _section_main(
        self, datasets: Dict[str, List[Dict]], embedding: str, company: str
    ) -> str:
        return textwrap.dedent(f'''\
            # ── Main ─────────────────────────────────────────────────────────────────────

            def print_summary():
                kb = KIBANA_URL or "(set KIBANA_URL to get links)"
                print()
                print("=" * 65)
                print(f"  ✅  {company} POC — setup complete")
                print("=" * 65)
                print(f"  Elasticsearch : {{ES_URL}}")
                if KIBANA_URL:
                    print(f"  Kibana        : {{KIBANA_URL}}")
                print(f"  Indices       : {{', '.join(INDICES)}}")
                print(f"  Search App    : {{SEARCH_APP_NAME}}")
                if KIBANA_URL:
                    print(f"  Discover      : {{KIBANA_URL}}/app/discover")
                    print(f"  Dev Tools     : {{KIBANA_URL}}/app/dev_tools")
                print()
                print("  Next steps:")
                print("    1. Open Kibana → Discover → select a data view")
                print("    2. Run ES|QL in Dev Tools to validate queries")
                print("    3. Open the Search Application in Kibana → Search")
                print("=" * 65)


            if __name__ == "__main__":
                start = time.time()
                print(f"\\n🚀  Starting POC setup for {company}…\\n")

                check_connection()
                create_index_templates()
                create_pipeline()
                index_all_datasets()
                create_search_application()
                create_kibana_data_views()

                elapsed = time.time() - start
                log.info(f"⏱️   Total setup time: {{elapsed:.1f}}s")
                print_summary()
        ''')
