"""
Live Replay Engine — re-timestamps and streams demo data into Elasticsearch
in real time so Kibana Alerts, Detection Rules, and Cases fire as designed.

Architecture:
  ReplayEngine          — background thread, reads DataFrame rows, applies
                          ScenarioPlayer overrides, indexes at controlled pace
  Scenario              — dataclass describing an anomaly window
  ScenarioPlayer        — applies field_overrides during active anomaly window
  load_scenarios()      — loads scenarios.json from a demo module directory
"""

import threading
import time
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scenario dataclass
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    name: str
    description: str
    trigger_after_seconds: int
    duration_seconds: int
    anomaly_type: str          # normal | latency_spike | error_surge | slo_breach | attack
    affected_service: str
    severity: str              # low | medium | high | critical
    field_overrides: Dict[str, Any] = field(default_factory=dict)
    expected_alerts: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ScenarioPlayer — applies overrides to individual rows
# ---------------------------------------------------------------------------

class ScenarioPlayer:
    """Applies field overrides from an active scenario to a data row."""

    def __init__(self, scenario: Optional[Scenario]):
        self._scenario = scenario

    def apply(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of row with scenario overrides applied."""
        if not self._scenario or not self._scenario.field_overrides:
            return row
        result = dict(row)
        result.update(self._scenario.field_overrides)
        return result


# ---------------------------------------------------------------------------
# Scenario file loader
# ---------------------------------------------------------------------------

def load_scenarios(path: Path) -> List[Scenario]:
    """Load scenarios from a scenarios.json file. Returns [] if missing."""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
        return [Scenario(**s) for s in raw]
    except Exception as e:
        logger.warning(f"Could not load scenarios from {path}: {e}")
        return []


# ---------------------------------------------------------------------------
# ReplayEngine
# ---------------------------------------------------------------------------

class ReplayEngine:
    """
    Streams demo DataFrame rows into Elasticsearch with current timestamps.

    Usage:
        engine = ReplayEngine(df, index_name, indexer, events_per_second=10)
        engine.set_scenario(scenario)
        engine.start()
        # ... engine runs in background thread ...
        engine.pause()
        engine.resume()
        engine.stop()
        print(engine.stats)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        index_name: str,
        indexer,                          # ElasticsearchIndexer instance
        events_per_second: int = 5,
        window_seconds: int = 30,
        on_event: Optional[Callable[[Dict], None]] = None,
    ):
        self._df = df.copy()
        self._index_name = index_name
        self._indexer = indexer
        self._eps = max(1, events_per_second)
        self._window_seconds = window_seconds
        self._on_event = on_event

        self.state: str = "idle"          # idle | running | paused | stopped
        self.stats: Dict[str, Any] = {
            "total_indexed": 0,
            "total_errors": 0,
            "start_time": None,
            "elapsed_seconds": 0,
            "current_scenario": None,
            "events_per_second": 0,
        }

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()   # not paused initially
        self._lock = threading.Lock()

        self._active_scenario: Optional[Scenario] = None
        self._scenario_start: Optional[float] = None

        # Pre-compute re-timestamped rows
        self._rows = self._prepare_rows()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_scenario(self, scenario: Optional[Scenario]):
        """Set the active scenario. Can be called while running."""
        with self._lock:
            self._active_scenario = scenario
            self._scenario_start = time.monotonic() if scenario else None
            self.stats["current_scenario"] = scenario.name if scenario else None

    def start(self):
        """Start streaming. No-op if already running."""
        if self.state == "running":
            return
        self._stop_event.clear()
        self._pause_event.set()
        self.state = "running"
        self.stats["start_time"] = datetime.utcnow().isoformat()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"ReplayEngine started — {len(self._rows)} rows, {self._eps} eps, index={self._index_name}")

    def pause(self):
        """Pause streaming."""
        if self.state == "running":
            self._pause_event.clear()
            self.state = "paused"
            logger.info("ReplayEngine paused")

    def resume(self):
        """Resume from paused state."""
        if self.state == "paused":
            self._pause_event.set()
            self.state = "running"
            logger.info("ReplayEngine resumed")

    def stop(self):
        """Stop streaming and wait for thread to finish."""
        self._stop_event.set()
        self._pause_event.set()   # unblock if paused
        self.state = "stopped"
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        logger.info(f"ReplayEngine stopped — {self.stats['total_indexed']} total indexed")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _prepare_rows(self) -> List[Dict]:
        """Convert DataFrame to list of dicts with fresh timestamps."""
        if self._df.empty:
            return []
        ts_col = "@timestamp" if "@timestamp" in self._df.columns else None
        rows = self._df.to_dict(orient="records")
        if ts_col:
            new_ts = self._retimestamp(
                [r[ts_col] for r in rows],
                window_seconds=self._window_seconds
            )
            for i, row in enumerate(rows):
                row[ts_col] = new_ts[i]
        return rows

    def _run(self):
        """Background thread — emits events at the configured rate."""
        interval = 1.0 / self._eps
        idx = 0
        total = len(self._rows)
        t_last_stat = time.monotonic()
        count_since_stat = 0

        while not self._stop_event.is_set():
            # Honour pause
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            # Cycle through rows indefinitely
            if total == 0:
                time.sleep(0.5)
                continue

            row = dict(self._rows[idx % total])
            idx += 1

            # Always use current time for @timestamp
            row["@timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            # Apply scenario overrides
            player = ScenarioPlayer(self._active_scenario_if_active())
            row = player.apply(row)

            # Index document
            try:
                self._indexer.client.index(index=self._index_name, document=row)
                with self._lock:
                    self.stats["total_indexed"] += 1
                    count_since_stat += 1
                if self._on_event:
                    self._on_event(row)
            except Exception as e:
                with self._lock:
                    self.stats["total_errors"] += 1
                logger.debug(f"Replay index error: {e}")

            # Update eps stat every second
            now = time.monotonic()
            if now - t_last_stat >= 1.0:
                with self._lock:
                    self.stats["events_per_second"] = count_since_stat
                    self.stats["elapsed_seconds"] = int(now - (
                        time.monotonic() - (now - t_last_stat)
                    ))
                count_since_stat = 0
                t_last_stat = now

            time.sleep(interval)

        self.state = "stopped"

    def _active_scenario_if_active(self) -> Optional[Scenario]:
        """Return scenario only during its active anomaly window."""
        with self._lock:
            sc = self._active_scenario
            t0 = self._scenario_start
        if sc is None or t0 is None:
            return None
        elapsed = time.monotonic() - t0
        if sc.anomaly_type == "normal":
            return None   # normal = no overrides
        if elapsed < sc.trigger_after_seconds:
            return None   # before anomaly window
        if elapsed > sc.trigger_after_seconds + sc.duration_seconds:
            return None   # anomaly window ended
        return sc

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _retimestamp(timestamps: List[str], window_seconds: int = 30) -> List[str]:
        """
        Re-map a list of historical timestamp strings to current time,
        preserving relative ordering and compressing into window_seconds.
        """
        if not timestamps:
            return []

        # Parse originals (handle varying formats)
        parsed = []
        for ts in timestamps:
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
                try:
                    parsed.append(datetime.strptime(ts[:26].rstrip("Z"), fmt.rstrip("Z")))
                    break
                except ValueError:
                    continue
            else:
                parsed.append(datetime.utcnow())

        # Normalise to [0, 1] range based on original span
        t_min = min(parsed)
        t_max = max(parsed)
        span = (t_max - t_min).total_seconds()

        now = datetime.utcnow()
        result = []
        for t in parsed:
            if span > 0:
                ratio = (t - t_min).total_seconds() / span
            else:
                ratio = 0.0
            new_t = now - timedelta(seconds=window_seconds * (1.0 - ratio))
            result.append(new_t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")

        return result
