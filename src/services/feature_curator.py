"""
Feature Curator

Takes raw feature items from FeatureMonitor and uses Claude to enrich each one with:
  - SA relevance score (1-10)
  - Demo-ability rating (high / medium / low)
  - Customer pain points addressed
  - Target industries / personas
  - 3 customer-facing talking points
  - How to demo it (step-by-step in the app)
  - ES|QL or API example (if applicable)

Output is written to src/data/features/YYYY-MM-DD.json
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"

# Minimum relevance score to include in the output file
MIN_RELEVANCE = 5

SA_PERSONA = """
You are helping Elastic Solutions Architects (SAs) who:
- Run technical proof-of-concept demos for enterprise customers
- Need to show customer business value, not just technical features
- Work across industries: telco, financial services, retail, healthcare, government
- Use tools: Elasticsearch, Kibana, ES|QL, Elastic Agent, ELSER, Inference APIs
- Build demos that address customer pain points around search, observability, security
"""


class FeatureCurator:
    """LLM-powered curator that enriches raw feature items for SA use."""

    def __init__(self, llm_client=None):
        self._llm = llm_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def curate(
        self,
        raw_items: List[Dict[str, Any]],
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Curate a list of raw feature items.
        Returns the full output dict ready to write to disk.
        """
        def _cb(msg: str):
            if progress_callback:
                progress_callback(msg)
            logger.info(msg)

        llm = self._llm or self._default_llm()
        curated = []
        total = len(raw_items)

        for i, item in enumerate(raw_items, 1):
            _cb(f"🔍 Curating {i}/{total}: {item.get('title', '')[:60]}...")
            try:
                enriched = self._enrich(llm, item)
                if enriched.get("sa_relevance_score", 0) >= MIN_RELEVANCE:
                    curated.append(enriched)
            except Exception as e:
                logger.warning(f"Failed to curate item '{item.get('title')}': {e}")

        curated.sort(key=lambda x: x.get("sa_relevance_score", 0), reverse=True)

        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "item_count": len(curated),
            "features": curated,
        }

        _cb(f"✅ Curated {len(curated)}/{total} features (score ≥ {MIN_RELEVANCE})")
        return result

    def save(self, result: Dict[str, Any], date_str: Optional[str] = None) -> Path:
        """Write curated result to src/data/features/YYYY-MM-DD.json."""
        FEATURES_DIR.mkdir(parents=True, exist_ok=True)
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = FEATURES_DIR / f"{date_str}.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        logger.info(f"Saved curated features to {path}")
        return path

    # ------------------------------------------------------------------
    # LLM enrichment
    # ------------------------------------------------------------------

    def _enrich(self, llm, item: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(item)
        messages = [{"role": "user", "content": prompt}]
        raw = llm._proxy_client.create_completion(
            messages=messages,
            max_tokens=2000,
            temperature=0.3,
            task="analysis",
        )
        parsed = self._parse_json(raw)
        # Merge original metadata with enrichment
        return {
            **{k: item[k] for k in ("id", "title", "url", "source", "published", "summary")},
            **parsed,
            "status": "pending_review",
        }

    def _build_prompt(self, item: Dict[str, Any]) -> str:
        return f"""{SA_PERSONA}

## Feature to Evaluate

**Title:** {item.get('title', '')}
**Source:** {item.get('source', '')}
**Published:** {item.get('published', 'unknown')}
**Summary:** {item.get('summary', '')}

## Your Task

Evaluate this Elastic feature/release from an SA perspective and return a JSON object.

Return ONLY valid JSON, no markdown fences, no explanation:

{{
  "sa_relevance_score": <integer 1-10, where 10 = every SA needs this immediately>,
  "demo_ability": "<high|medium|low> — can we actually show this in a live demo today?>",
  "why_it_matters": "<1-2 sentences: the customer business problem this solves>",
  "pain_points": ["<pain point 1>", "<pain point 2>"],
  "target_industries": ["<industry>", ...],
  "target_personas": ["<economic buyer|technical buyer|end user>", ...],
  "talking_points": [
    "<customer-facing talking point 1>",
    "<customer-facing talking point 2>",
    "<customer-facing talking point 3>"
  ],
  "how_to_demo": "<step-by-step: what to click/type in the Elastic Demo Builder app to show this feature>",
  "esql_or_api_example": "<short ES|QL query or REST API snippet showing the feature, or empty string if not applicable>",
  "competitive_angle": "<one sentence: why this beats the competition on this capability, or empty string>",
  "feature_category": "<one of: Search|Observability|Security|Infrastructure|AI/ML|Platform|Analytics>"
}}

Scoring guide for sa_relevance_score:
- 9-10: Major new capability that directly changes how we demo to customers (e.g. ELSER GA, Inference API)
- 7-8:  Significant enhancement to an existing capability SAs frequently demo
- 5-6:  Useful but niche or internal/ops focused
- 1-4:  Bug fix, minor config option, or not relevant to customer demos"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        import re
        text = raw.strip()
        # Strip markdown fences
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        start = text.find('{')
        end   = text.rfind('}')
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response")
        return json.loads(text[start:end + 1])

    def _default_llm(self):
        from src.services.llm_proxy_service import UnifiedLLMClient
        return UnifiedLLMClient()


# ------------------------------------------------------------------
# Feature store reader (used by the UI)
# ------------------------------------------------------------------

def load_latest_features(n_days: int = 30) -> List[Dict[str, Any]]:
    """
    Load the most recent curated feature files (up to n_days back).
    Returns a flat list of feature dicts, newest first, deduped by id.
    """
    if not FEATURES_DIR.exists():
        return []

    files = sorted(FEATURES_DIR.glob("*.json"), reverse=True)
    seen_ids: set = set()
    all_features: List[Dict] = []

    for f in files[:n_days]:
        try:
            data = json.loads(f.read_text())
            for feat in data.get("features", []):
                fid = feat.get("id", feat.get("title", ""))
                if fid not in seen_ids:
                    seen_ids.add(fid)
                    feat["_file_date"] = f.stem  # YYYY-MM-DD from filename
                    all_features.append(feat)
        except Exception as e:
            logger.warning(f"Failed to load {f}: {e}")

    return all_features


def load_feature_stats() -> Dict[str, Any]:
    """Return summary stats for the What's New panel header."""
    features = load_latest_features(7)  # last 7 days
    if not features:
        return {"total": 0, "high_demo": 0, "last_updated": None}

    files = sorted(FEATURES_DIR.glob("*.json"), reverse=True)
    last_updated = files[0].stem if files else None

    return {
        "total": len(features),
        "high_demo": sum(1 for f in features if f.get("demo_ability") == "high"),
        "last_updated": last_updated,
        "by_category": _count_by(features, "feature_category"),
    }


def _count_by(features: List[Dict], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for f in features:
        v = f.get(key, "Other") or "Other"
        counts[v] = counts.get(v, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))
