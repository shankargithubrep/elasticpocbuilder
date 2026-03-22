"""
Prompt History Service

Persists every prompt submitted to the demo generator so you can:
  - Review what prompts produced good demos
  - Re-use or tweak past prompts
  - Track which customer/pillar combinations were generated

Storage: demos/prompt_history.json  (one JSON file, newest-first list)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_HISTORY_FILE = Path("demos/prompt_history.json")
_MAX_ENTRIES = 100  # cap to avoid unbounded growth


class PromptHistoryService:

    def save(
        self,
        prompt: str,
        demo_name: Optional[str] = None,
        company: Optional[str] = None,
        pillar: Optional[str] = None,
        entry_id: Optional[str] = None,
    ) -> str:
        """
        Append (or update) a prompt entry.

        Returns the entry's id so callers can update it later
        (e.g. attach the demo_name after generation completes).
        """
        history = self._load()

        # If entry_id given, update existing entry instead of inserting
        if entry_id:
            for entry in history:
                if entry.get("id") == entry_id:
                    if demo_name:
                        entry["demo_name"] = demo_name
                    if company:
                        entry["company"] = company
                    if pillar:
                        entry["pillar"] = pillar
                    self._save(history)
                    return entry_id

        # New entry
        new_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        entry: Dict[str, Any] = {
            "id": new_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "demo_name": demo_name,
            "company": company,
            "pillar": pillar or "search",
        }
        history.insert(0, entry)          # newest first
        history = history[:_MAX_ENTRIES]  # trim
        self._save(history)
        return new_id

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent `limit` entries (newest first)."""
        return self._load()[:limit]

    def delete(self, entry_id: str) -> bool:
        """Remove a single entry by id. Returns True if found."""
        history = self._load()
        new = [e for e in history if e.get("id") != entry_id]
        if len(new) == len(history):
            return False
        self._save(new)
        return True

    def clear(self):
        """Wipe all history."""
        self._save([])

    # ── internal ──────────────────────────────────────────────────────────────

    def _load(self) -> List[Dict[str, Any]]:
        try:
            if _HISTORY_FILE.exists():
                return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not load prompt history: {e}")
        return []

    def _save(self, history: List[Dict[str, Any]]):
        try:
            _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            _HISTORY_FILE.write_text(
                json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Could not save prompt history: {e}")
