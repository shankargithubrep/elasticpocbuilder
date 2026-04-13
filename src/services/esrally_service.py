"""
ESRally Service — manages installation, execution, and result parsing
for ESRally benchmarks against the configured Elasticsearch cluster.

Designed for benchmark-only pipeline (no cluster provisioning).
"""

import os
import sys
import csv
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

TRACKS_DIR    = Path(__file__).resolve().parent.parent.parent / "tracks"
RESULTS_DIR   = TRACKS_DIR / "genesys_knowledge" / "results"
TRACK_PATH    = TRACKS_DIR / "genesys_knowledge"

CHALLENGES = {
    "bm25-baseline": {
        "label":       "BM25 Baseline",
        "description": "Pure BM25 text search on genesys_faq_sop — no vector inference. "
                       "Establishes the latency floor for the cluster.",
        "duration":    "~2 min",
        "icon":        "🔤",
        "warmup":      10,
        "iterations":  100,
        "target_qps":  20,
        "operations":  1,
        "index":       "genesys_faq_sop",
    },
    "semantic-benchmark": {
        "label":       "Semantic (Jina v5)",
        "description": "Match on semantic_text field — measures Jina v5 inference latency end-to-end. "
                       "Directly shows the inference overhead vs BM25.",
        "duration":    "~3 min",
        "icon":        "🧠",
        "warmup":      5,
        "iterations":  50,
        "target_qps":  5,
        "operations":  1,
        "index":       "genesys_faq_sop",
    },
    "pdf-benchmark": {
        "label":       "PDF Chunks (BM25)",
        "description": "BM25 search on enterprise_pdf_chunks — structured clause and identifier retrieval.",
        "duration":    "~2 min",
        "icon":        "📄",
        "warmup":      10,
        "iterations":  100,
        "target_qps":  20,
        "operations":  1,
        "index":       "enterprise_pdf_chunks",
    },
    "hybrid-rrf-benchmark": {
        "label":       "Hybrid RRF",
        "description": "BM25 + Jina v5 with RRF fusion on enterprise_pdf_chunks. "
                       "Requires semantic_text mapping on the content field.",
        "duration":    "~4 min",
        "icon":        "⚡",
        "warmup":      5,
        "iterations":  50,
        "target_qps":  5,
        "operations":  1,
        "index":       "enterprise_pdf_chunks",
    },
    "full-stack": {
        "label":       "Full Stack",
        "description": "All operations across both indices in sequence — production-realistic profile.",
        "duration":    "~8 min",
        "icon":        "🏁",
        "warmup":      15,
        "iterations":  150,
        "target_qps":  None,
        "operations":  3,
        "index":       "genesys_faq_sop + enterprise_pdf_chunks",
    },
}

# Metrics we extract from the ESRally JSON report
KEY_METRICS = [
    "50th percentile latency",
    "90th percentile latency",
    "95th percentile latency",
    "99th percentile latency",
    "100th percentile latency",
    "50th percentile service time",
    "95th percentile service time",
    "99th percentile service time",
    "Mean throughput",
    "Median throughput",
    "error rate",
]


# ── Installation ───────────────────────────────────────────────────────────────

def is_installed() -> bool:
    """Check whether the esrally CLI is available on PATH."""
    return shutil.which("esrally") is not None


def get_version() -> str:
    """Return the installed ESRally version string."""
    try:
        result = subprocess.run(
            ["esrally", "--version"],
            capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception:
        return "unknown"


def install(on_line: Callable[[str], None] = None) -> tuple[bool, str]:
    """
    Install ESRally via pip into the current Python environment.
    Streams output lines to on_line callback if provided.
    Returns (success, message).
    """
    cmd = [sys.executable, "-m", "pip", "install", "esrally", "--upgrade"]
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            if on_line:
                on_line(line)
        process.wait()
        if process.returncode == 0:
            return True, "ESRally installed successfully."
        return False, "".join(output_lines[-10:])
    except Exception as e:
        return False, str(e)


# ── Command building ───────────────────────────────────────────────────────────

def _build_client_options(api_key: str, use_ssl: bool = True) -> str:
    """Build the --client-options string for the esrally CLI."""
    opts = []
    if use_ssl:
        opts.append("use_ssl:true")
        opts.append("verify_certs:false")   # self-signed / cloud proxy cert
    if api_key:
        # ESRally passes client-options as kwargs to the ES Python client.
        # api_key as a plain string is supported in elasticsearch-py 8.x.
        # Escape colons inside the key by quoting the whole value.
        opts.append(f"api_key:{api_key}")
    return ",".join(opts)


def _normalize_target_host(target_host: str) -> tuple[str, bool]:
    """
    ESRally --target-hosts expects 'host:port' (no scheme).
    Passing 'https://host:443' causes ESRally to double the port → '443:443' error.
    Strip the scheme and return (host:port, use_ssl).
    Works even if the URL already contains '443:443' (cloud_id double-port bug).
    """
    use_ssl = "https" in target_host.lower()

    # Strip scheme
    raw = target_host
    for scheme in ("https://", "http://"):
        if raw.lower().startswith(scheme):
            raw = raw[len(scheme):]
            break

    # raw is now 'host:port' or 'host:port:port' (double-port case)
    # Split from the right to get the last port token
    parts = raw.rsplit(":", 1)
    if len(parts) == 2:
        host, port_str = parts
        # Deduplicate port if host ends with ':443' etc.
        if host.endswith(f":{port_str}"):
            host = host[: -(len(port_str) + 1)]
        try:
            int(port_str)   # validate it's actually a port number
            return f"{host}:{port_str}", use_ssl
        except ValueError:
            pass

    # Fallback: no port — use default
    port = "443" if use_ssl else "9200"
    return f"{raw}:{port}", use_ssl


def build_command(
    challenge: str,
    target_host: str,
    api_key: str,
    race_id: str = "vulcan-bench",
    pipeline: str = "benchmark-only",
) -> list[str]:
    """
    Build the full esrally CLI command for a benchmark race.
    report-file is written to tracks/genesys_knowledge/results/{challenge}_latest.csv
    Note: ESRally supports 'csv' and 'markdown' report formats only (no json).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = RESULTS_DIR / f"{challenge}_latest.csv"

    # Strip scheme — ESRally parses 'https://host:443' as port '443:443' (bug in 2.x)
    normalized_host, use_ssl = _normalize_target_host(target_host)

    cmd = [
        "esrally", "race",
        f"--track-path={TRACK_PATH}",
        f"--challenge={challenge}",
        f"--pipeline={pipeline}",
        f"--target-hosts={normalized_host}",
        f"--client-options={_build_client_options(api_key, use_ssl)}",
        f"--race-id={race_id}",
        "--report-format=csv",
        f"--report-file={report_file}",
        "--kill-running-processes",
        "--on-error=abort",
    ]
    return cmd


# ── Execution ──────────────────────────────────────────────────────────────────

def run_race(
    cmd: list[str],
    on_line: Callable[[str], None] = None,
) -> tuple[int, str]:
    """
    Execute ESRally as a subprocess, streaming stdout+stderr line by line.
    Calls on_line(line) for each output line if provided.
    Returns (returncode, full_output_string).
    """
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        output_lines: list[str] = []
        for line in process.stdout:
            output_lines.append(line)
            if on_line:
                on_line(line)
        process.wait()
        return process.returncode, "".join(output_lines)
    except FileNotFoundError:
        msg = "esrally not found. Install it first (pip install esrally).\n"
        if on_line:
            on_line(msg)
        return -1, msg
    except Exception as e:
        msg = f"Error running ESRally: {e}\n"
        if on_line:
            on_line(msg)
        return -1, msg


# ── Result parsing ─────────────────────────────────────────────────────────────

def load_results(challenge: str) -> list[dict]:
    """
    Load the CSV report written by ESRally for a given challenge.
    ESRally CSV columns: Metric, Task, Value, Unit
    Returns a list of metric dicts: {name, task, value, unit}.
    """
    report_file = RESULTS_DIR / f"{challenge}_latest.csv"
    if not report_file.exists():
        return []
    try:
        rows = []
        with open(report_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalise column names (ESRally uses title-case)
                name  = row.get("Metric", row.get("metric", "")).strip()
                task  = row.get("Task",   row.get("task",   "")).strip()
                value = row.get("Value",  row.get("value",  "")).strip()
                unit  = row.get("Unit",   row.get("unit",   "")).strip()
                if not name or not value:
                    continue
                try:
                    scalar = float(value)
                except ValueError:
                    scalar = None
                rows.append({
                    "name":  name,
                    "task":  task or "overall",
                    "value": {"single": scalar} if scalar is not None else {"single": 0},
                    "unit":  unit,
                })
        return rows
    except Exception as e:
        logger.warning(f"Could not parse ESRally CSV results for {challenge}: {e}")
        return []


def summarise_results(raw: list[dict]) -> dict[str, list[dict]]:
    """
    Group raw metric entries by task name.
    Returns { task_name: [ {metric, value, unit}, ... ] }
    Only includes metrics from KEY_METRICS list.
    """
    by_task: dict[str, list[dict]] = {}
    for entry in raw:
        name  = entry.get("name", "")
        task  = entry.get("task", "") or "overall"
        value = entry.get("value", {})
        unit  = entry.get("unit", "")

        if not any(km.lower() in name.lower() for km in KEY_METRICS):
            continue

        scalar = value.get("single") if isinstance(value, dict) else value
        if scalar is None:
            continue

        by_task.setdefault(task, []).append({
            "metric": name,
            "value":  round(float(scalar), 2),
            "unit":   unit,
        })
    return by_task


def get_target_host_from_env() -> str:
    """
    Derive the Elasticsearch HTTPS endpoint from environment variables.
    Supports ELASTIC_ENDPOINT directly, or decodes from ELASTICSEARCH_CLOUD_ID.
    """
    endpoint = os.getenv("ELASTIC_ENDPOINT", "").strip()
    if endpoint:
        return endpoint

    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID", "").strip()
    if cloud_id and ":" in cloud_id:
        try:
            import base64
            _, encoded = cloud_id.split(":", 1)
            decoded = base64.b64decode(encoded + "==").decode("utf-8")
            parts = decoded.split("$")
            if len(parts) >= 2:
                parent = parts[0]          # e.g. us-central1.gcp.cloud.es.io
                cluster_id = parts[1]      # e.g. abc123
                return f"https://{cluster_id}.{parent}:443"
        except Exception as e:
            logger.warning(f"Could not decode ELASTICSEARCH_CLOUD_ID: {e}")

    return ""


def list_past_results() -> list[dict]:
    """Return metadata for all saved result files."""
    if not RESULTS_DIR.exists():
        return []
    results = []
    for f in sorted(RESULTS_DIR.glob("*_latest.csv"), key=lambda p: p.stat().st_mtime, reverse=True):
        challenge = f.stem.replace("_latest", "")  # e.g. bm25-baseline_latest → bm25-baseline
        raw = load_results(challenge)
        results.append({
            "challenge":  challenge,
            "label":      CHALLENGES.get(challenge, {}).get("label", challenge),
            "file":       str(f),
            "modified":   f.stat().st_mtime,
            "metric_count": len(raw),
        })
    return results
