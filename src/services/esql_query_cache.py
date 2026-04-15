"""
ES|QL Query Cache

Stores successful ES|QL queries (those that returned >0 rows) and retrieves
the most similar ones via Jaccard similarity over ES|QL tokens.

Retrieved entries are injected as few-shot examples into the eval scenario
generator prompt, improving generation quality over time as the cache grows.

Cache persists at ~/.elastic-demo-generator/esql_query_cache.json (global across all demos).
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = Path.home() / ".elastic-demo-generator" / "esql_query_cache.json"

# ES|QL keywords that carry no discriminative signal for similarity
_ESQL_STOP_TOKENS = {
    "from", "where", "and", "or", "not", "as", "by", "on", "with",
    "limit", "sort", "asc", "desc", "keep", "drop", "eval", "stats",
    "true", "false", "null", "in", "like", "rlike", "case", "when",
    "then", "else", "end", "is", "to", "the", "of", "for",
}


class EsqlQueryCache:
    """
    Lightweight semantic cache for successful ES|QL queries.

    Similarity is computed via token-level Jaccard overlap over meaningful
    ES|QL identifiers (index names, field names, function names).
    No external ML libraries required — just Python stdlib.
    """

    def __init__(self, cache_path: Optional[Path] = None):
        self._path = Path(cache_path or DEFAULT_CACHE_PATH)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[Dict[str, Any]] = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(
        self,
        query: str,
        category: str,
        title: str,
        demo_module: str,
        row_count: int,
        schema_indices: Optional[List[str]] = None,
    ) -> bool:
        """
        Persist a successful query to the cache.
        Only stores queries that returned at least 1 row.
        Returns True if a new entry was added.
        """
        if not query or row_count <= 0:
            return False

        query = query.strip()

        # Deduplicate by exact query text
        if any(e["query"] == query for e in self._entries):
            return False

        entry = {
            "id": f"{demo_module}::{len(self._entries)}",
            "query": query,
            "category": category,
            "title": title,
            "demo_module": demo_module,
            "schema_indices": schema_indices or [],
            "row_count": row_count,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "tokens": self._tokenize(query),
        }

        self._entries.append(entry)
        self._save()
        logger.info(f"EsqlQueryCache: cached '{title}' ({row_count} rows) — total {len(self._entries)}")
        return True

    def find_similar(
        self,
        reference: str,
        n: int = 5,
        min_score: float = 0.05,
        exclude_module: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return up to n cached entries most similar to reference text.
        Similarity = Jaccard(tokenize(reference), tokenize(entry.query)).
        """
        if not self._entries:
            return []

        ref_tokens = set(self._tokenize(reference))
        if not ref_tokens:
            return []

        scored = []
        for entry in self._entries:
            if exclude_module and entry["demo_module"] == exclude_module:
                continue
            score = self._jaccard(ref_tokens, set(entry["tokens"]))
            if score >= min_score:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:n]]

    def size(self) -> int:
        return len(self._entries)

    def all_entries(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries = []
        self._save()

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        """
        Extract discriminative tokens from an ES|QL query.
        Keeps index names, field names, function names, string literals.
        """
        # Pull identifiers (snake_case field/index names)
        identifiers = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text.lower())
        # Pull quoted string values (sample values, keywords)
        quoted = re.findall(r'"([^"]{2,30})"', text.lower())
        quoted_tokens = [w for q in quoted for w in q.split() if len(w) >= 2]

        all_tokens = [t for t in identifiers if t not in _ESQL_STOP_TOKENS and len(t) >= 2]
        all_tokens += quoted_tokens
        return all_tokens

    def _jaccard(self, a: set, b: set) -> float:
        if not a and not b:
            return 0.0
        return len(a & b) / len(a | b)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> List[Dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text())
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.warning(f"EsqlQueryCache: failed to load cache ({e}), starting fresh")
        return []

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._entries, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"EsqlQueryCache: failed to save cache ({e})")
