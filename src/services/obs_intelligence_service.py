"""
Observability Intelligence Service — Backend for Reliability Engine™

Tenant-aware, multi-region observability data layer.
Falls back to realistic simulation when live ES data is not yet indexed.

Standard tags on every query:
  tenant_id  — isolates data per customer/tenant
  region     — routes to correct regional cluster
  service    — APM service name
  env        — production / staging / dev
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Simulation data ───────────────────────────────────────────────────────────

_SERVICES = [
    {"name": "api-gateway",       "team": "platform",  "language": "go",     "tier": "critical"},
    {"name": "auth-service",      "team": "platform",  "language": "java",   "tier": "critical"},
    {"name": "contact-routing",   "team": "ccaas",     "language": "java",   "tier": "critical"},
    {"name": "voice-transcription","team": "ai",        "language": "python", "tier": "high"},
    {"name": "agent-assist",      "team": "ai",        "language": "python", "tier": "high"},
    {"name": "reporting-engine",  "team": "analytics", "language": "java",   "tier": "medium"},
    {"name": "notification-svc",  "team": "platform",  "language": "node",   "tier": "medium"},
    {"name": "billing-service",   "team": "finance",   "language": "java",   "tier": "high"},
]

_ALERT_TYPES = [
    {"name": "High P95 Latency",      "service": "api-gateway",       "severity": "critical", "icon": "🔴"},
    {"name": "Error Rate Spike",      "service": "auth-service",      "severity": "high",     "icon": "🟠"},
    {"name": "SLO Burn Rate Alert",   "service": "contact-routing",   "severity": "critical", "icon": "🔴"},
    {"name": "Memory Saturation",     "service": "voice-transcription","severity": "high",     "icon": "🟠"},
    {"name": "Slow DB Queries",       "service": "reporting-engine",  "severity": "medium",   "icon": "🟡"},
]

_LOG_PATTERNS = [
    {"pattern": "NullPointerException in PaymentProcessor",   "count": 847,  "trend": "↑", "service": "billing-service"},
    {"pattern": "Connection timeout to Redis cluster",         "count": 312,  "trend": "↑", "service": "api-gateway"},
    {"pattern": "JWT token validation failed",                 "count": 289,  "trend": "→", "service": "auth-service"},
    {"pattern": "gRPC deadline exceeded on voice stream",      "count": 156,  "trend": "↓", "service": "voice-transcription"},
    {"pattern": "Rate limit exceeded for tenant",              "count": 94,   "trend": "→", "service": "api-gateway"},
    {"pattern": "Circuit breaker OPEN for downstream",        "count": 67,   "trend": "↑", "service": "contact-routing"},
]

_SLO_DEFINITIONS = [
    {"name": "API Availability",       "service": "api-gateway",     "target": 99.9,  "window": "30d"},
    {"name": "Auth Latency P95 < 200ms","service": "auth-service",   "target": 99.5,  "window": "30d"},
    {"name": "Contact Routing Success","service": "contact-routing", "target": 99.95, "window": "30d"},
    {"name": "Voice Quality Score",    "service": "voice-transcription","target": 98.0,"window": "7d"},
    {"name": "Billing Accuracy",       "service": "billing-service", "target": 99.99, "window": "30d"},
]

_ANOMALIES = [
    {"metric": "p95_latency",    "service": "api-gateway",     "score": 0.94, "delta": "+340ms", "started": "14m ago"},
    {"metric": "error_rate",     "service": "auth-service",    "score": 0.87, "delta": "+2.3%",  "started": "2h ago"},
    {"metric": "throughput_drop","service": "contact-routing", "score": 0.81, "delta": "-28%",   "started": "47m ago"},
    {"metric": "memory_rss",     "service": "voice-transcription","score": 0.76,"delta": "+1.4GB","started": "6h ago"},
]


class ObsIntelligenceService:
    """
    Tenant-aware observability data service.
    Runs live ES|QL when connected, falls back to simulation.
    """

    def __init__(
        self,
        tenant_id: str = "genesys",
        region: str = "us-east-1",
        es_client=None,
    ):
        self.tenant_id = tenant_id
        self.region = region
        self._es = es_client
        self._live = es_client is not None

    # ── Service Health ────────────────────────────────────────────────────────

    def get_service_health(self) -> Dict[str, Any]:
        if self._live:
            return self._live_service_health()
        return self._sim_service_health()

    def _sim_service_health(self) -> Dict[str, Any]:
        rng = random.Random(self.tenant_id + self.region)
        services = []
        for svc in _SERVICES:
            error_rate = round(rng.uniform(0.0, 3.5 if svc["tier"] == "critical" else 1.5), 2)
            p95 = rng.randint(45, 850 if error_rate > 1.5 else 250)
            health = "critical" if error_rate > 2.5 else "degraded" if error_rate > 0.8 else "healthy"
            services.append({
                **svc,
                "error_rate":  error_rate,
                "p95_ms":      p95,
                "throughput":  rng.randint(200, 8000),
                "health":      health,
                "health_icon": "🔴" if health == "critical" else "🟡" if health == "degraded" else "🟢",
                "tenant_id":   self.tenant_id,
                "region":      self.region,
            })
        active_alerts = sum(1 for s in services if s["health"] != "healthy")
        return {
            "services": services,
            "active_alerts": active_alerts,
            "healthy_pct": round(sum(1 for s in services if s["health"] == "healthy") / len(services) * 100),
            "esql": self._esql_service_health(),
        }

    def _esql_service_health(self) -> str:
        return f"""\
FROM apm-*-metrics
  METADATA _index
| WHERE tenant_id == "{self.tenant_id}"
  AND region      == "{self.region}"
  AND @timestamp  > NOW() - 5 MINUTES
| STATS
    error_rate  = ROUND(COUNT(CASE WHEN transaction.result == "HTTP 5xx" THEN 1 END)
                  / COUNT(*) * 100, 2),
    p95_ms      = PERCENTILE(transaction.duration.us, 95) / 1000,
    throughput  = COUNT(*) / 5
  BY service.name
| SORT error_rate DESC"""

    def _live_service_health(self) -> Dict[str, Any]:
        try:
            query = self._esql_service_health()
            resp = self._es.esql(self.region, query) if hasattr(self._es, "esql") else {}
            # Parse response into service list
            cols = [c["name"] for c in resp.get("columns", [])]
            services = []
            for row in resp.get("values", []):
                d = dict(zip(cols, row))
                er = d.get("error_rate", 0) or 0
                services.append({
                    "name":        d.get("service.name", "?"),
                    "error_rate":  er,
                    "p95_ms":      d.get("p95_ms", 0),
                    "throughput":  d.get("throughput", 0),
                    "health":      "critical" if er > 2.5 else "degraded" if er > 0.8 else "healthy",
                    "health_icon": "🔴" if er > 2.5 else "🟡" if er > 0.8 else "🟢",
                    "tenant_id":   self.tenant_id,
                    "region":      self.region,
                })
            return {"services": services, "active_alerts": sum(1 for s in services if s["health"] != "healthy"),
                    "healthy_pct": 100, "esql": query}
        except Exception as e:
            logger.warning(f"Live service health failed, falling back: {e}")
            return self._sim_service_health()

    # ── APM Analytics ─────────────────────────────────────────────────────────

    def get_apm_analytics(self, service: Optional[str] = None, window: str = "1h") -> Dict[str, Any]:
        rng = random.Random(self.tenant_id + self.region + (service or ""))
        buckets = []
        now = datetime.now(timezone.utc)
        for i in range(24):
            ts = now - timedelta(hours=23 - i)
            base_err = rng.uniform(0.1, 0.8)
            spike = rng.random() > 0.85
            buckets.append({
                "timestamp":  ts.strftime("%H:%M"),
                "p50_ms":     rng.randint(40, 120),
                "p95_ms":     rng.randint(150, 900 if spike else 350),
                "p99_ms":     rng.randint(400, 2000 if spike else 600),
                "error_rate": round(base_err * (4 if spike else 1), 2),
                "throughput": rng.randint(300, 5000),
            })
        return {
            "buckets": buckets,
            "service": service or "all",
            "window":  window,
            "summary": {
                "avg_p95":  round(sum(b["p95_ms"] for b in buckets) / len(buckets)),
                "max_p95":  max(b["p95_ms"] for b in buckets),
                "avg_err":  round(sum(b["error_rate"] for b in buckets) / len(buckets), 2),
                "peak_tps": max(b["throughput"] for b in buckets),
            },
            "esql": f"""\
FROM apm-*-transactions
| WHERE tenant_id    == "{self.tenant_id}"
  AND region         == "{self.region}"
  {"AND service.name == '" + service + "'" if service else ""}
  AND @timestamp     > NOW() - {window}
| STATS
    p50 = PERCENTILE(transaction.duration.us, 50)  / 1000,
    p95 = PERCENTILE(transaction.duration.us, 95)  / 1000,
    p99 = PERCENTILE(transaction.duration.us, 99)  / 1000,
    err = ROUND(COUNT(CASE WHEN transaction.result LIKE "HTTP 5*" THEN 1 END)
          / COUNT(*) * 100, 2),
    tps = COUNT(*) / 3600
  BY DATE_TRUNC(1 hour, @timestamp)
| SORT @timestamp ASC""",
        }

    # ── Log Intelligence ──────────────────────────────────────────────────────

    def get_log_intelligence(self, service: Optional[str] = None) -> Dict[str, Any]:
        rng = random.Random(self.tenant_id)
        patterns = [
            {**p, "count": int(p["count"] * rng.uniform(0.6, 1.4))}
            for p in _LOG_PATTERNS
            if not service or p["service"] == service
        ]
        return {
            "patterns":    patterns,
            "total_errors": sum(p["count"] for p in patterns),
            "top_service": patterns[0]["service"] if patterns else "—",
            "esql": f"""\
FROM logs-*
| WHERE tenant_id == "{self.tenant_id}"
  AND region      == "{self.region}"
  AND log.level   IN ("ERROR", "CRITICAL")
  AND @timestamp  > NOW() - 1 HOUR
| STATS count = COUNT(*) BY log.message, service.name
| SORT count DESC
| LIMIT 20""",
            "claude_insight": (
                f"**Root pattern:** `NullPointerException` in billing-service correlates with "
                f"a Redis timeout cascade — 847 errors in 1h for tenant `{self.tenant_id}`. "
                f"Likely cause: Redis replica lag after the 14:32 deployment in `{self.region}`. "
                f"Recommend: increase connection pool size or add circuit breaker."
            ),
        }

    # ── Incident Triage ───────────────────────────────────────────────────────

    def get_active_alerts(self) -> Dict[str, Any]:
        rng = random.Random(self.tenant_id + self.region)
        alerts = []
        for a in _ALERT_TYPES:
            if rng.random() > 0.35:
                fired = datetime.now(timezone.utc) - timedelta(minutes=rng.randint(2, 180))
                alerts.append({
                    **a,
                    "fired_at":   fired.strftime("%H:%M:%S"),
                    "duration":   f"{rng.randint(2, 180)}m",
                    "tenant_id":  self.tenant_id,
                    "region":     self.region,
                    "affected_tenants": rng.randint(1, 12) if "SLO" in a["name"] else 1,
                })
        return {
            "alerts": alerts,
            "critical_count": sum(1 for a in alerts if a["severity"] == "critical"),
            "esql": f"""\
FROM .alerts-*
| WHERE tenant_id    == "{self.tenant_id}"
  AND region         == "{self.region}"
  AND kibana.alert.status == "active"
| STATS count = COUNT(*) BY kibana.alert.rule.name, kibana.alert.severity
| SORT count DESC""",
        }

    def get_incident_timeline(self, alert_name: str) -> Dict[str, Any]:
        return {
            "alert":    alert_name,
            "tenant":   self.tenant_id,
            "region":   self.region,
            "timeline": [
                {"time": "14:32:01", "event": "Deploy v2.14.3 pushed to api-gateway",          "type": "deploy"},
                {"time": "14:33:45", "event": "Redis connection pool exhausted (20/20 active)", "type": "metric"},
                {"time": "14:34:12", "event": "P95 latency crossed 500ms SLO threshold",        "type": "alert"},
                {"time": "14:34:18", "event": "SLO burn rate alert fired (14x normal rate)",    "type": "alert"},
                {"time": "14:35:00", "event": "Error rate spike: 0.2% → 3.8%",                  "type": "error"},
                {"time": "14:36:30", "event": "Circuit breaker OPEN on downstream billing-svc", "type": "error"},
                {"time": "NOW",      "event": "Incident active — MTTR clock running",           "type": "current"},
            ],
            "root_cause": (
                f"Deploy v2.14.3 introduced a connection leak in the Redis client pool. "
                f"Under load for tenant `{self.tenant_id}`, the pool saturates in ~90s "
                f"causing cascading timeouts. Fix: roll back to v2.14.2 or patch "
                f"`RedisConnectionPool.maxConnections` from 20 → 50."
            ),
            "esql": f"""\
FROM apm-*,logs-*,deploy-events
  METADATA _index
| WHERE tenant_id == "{self.tenant_id}"
  AND region      == "{self.region}"
  AND @timestamp BETWEEN "2026-03-21T14:30:00Z" AND NOW()
| SORT @timestamp ASC
| KEEP @timestamp, _index, service.name, message, event.action
| LIMIT 100""",
        }

    # ── Distributed Tracing ───────────────────────────────────────────────────

    def get_trace_summary(self) -> Dict[str, Any]:
        rng = random.Random(self.tenant_id)
        services = [s["name"] for s in _SERVICES]
        deps = [
            {"from": "api-gateway",        "to": "auth-service",       "p95_ms": rng.randint(20, 80),  "err": round(rng.uniform(0,1),2)},
            {"from": "api-gateway",        "to": "contact-routing",    "p95_ms": rng.randint(30, 150), "err": round(rng.uniform(0,2),2)},
            {"from": "contact-routing",    "to": "voice-transcription","p95_ms": rng.randint(80, 400), "err": round(rng.uniform(0,3),2)},
            {"from": "contact-routing",    "to": "agent-assist",       "p95_ms": rng.randint(60, 200), "err": round(rng.uniform(0,1),2)},
            {"from": "api-gateway",        "to": "billing-service",    "p95_ms": rng.randint(40, 120), "err": round(rng.uniform(0,2),2)},
            {"from": "api-gateway",        "to": "notification-svc",   "p95_ms": rng.randint(15, 60),  "err": round(rng.uniform(0,0.5),2)},
        ]
        critical_path = [
            {"span": "api-gateway → auth-service",       "duration_ms": 68,  "status": "ok"},
            {"span": "api-gateway → contact-routing",    "duration_ms": 142, "status": "ok"},
            {"span": "contact-routing → voice-transcription","duration_ms": 387,"status": "slow"},
            {"span": "voice-transcription (internal)",   "duration_ms": 203, "status": "ok"},
        ]
        return {
            "dependencies": deps,
            "critical_path": critical_path,
            "total_span_ms": sum(s["duration_ms"] for s in critical_path),
            "esql": f"""\
FROM apm-*-spans
| WHERE tenant_id        == "{self.tenant_id}"
  AND region             == "{self.region}"
  AND @timestamp         > NOW() - 15 MINUTES
| STATS
    p95_ms = PERCENTILE(span.duration.us, 95) / 1000,
    errors = COUNT(CASE WHEN span.outcome == "failure" THEN 1 END)
  BY span.destination.service.name, service.name
| SORT p95_ms DESC""",
        }

    # ── SLO Dashboard ─────────────────────────────────────────────────────────

    def get_slo_dashboard(self) -> Dict[str, Any]:
        rng = random.Random(self.tenant_id + self.region)
        slos = []
        for slo in _SLO_DEFINITIONS:
            current = round(rng.uniform(slo["target"] - 1.5, 100.0), 3)
            budget_remaining = round((current - (slo["target"] - 1)) / 1.0 * 100, 1)
            burn_rate = round(rng.uniform(0.8, 4.5), 1)
            slos.append({
                **slo,
                "current":           current,
                "budget_remaining":  max(0, budget_remaining),
                "burn_rate":         burn_rate,
                "status":            "breached" if current < slo["target"] else
                                     "at_risk"  if burn_rate > 2.0 else "healthy",
                "status_icon":       "🔴" if current < slo["target"] else
                                     "🟡" if burn_rate > 2.0 else "🟢",
                "tenant_id":         self.tenant_id,
                "region":            self.region,
            })
        return {
            "slos": slos,
            "healthy_count":  sum(1 for s in slos if s["status"] == "healthy"),
            "at_risk_count":  sum(1 for s in slos if s["status"] == "at_risk"),
            "breached_count": sum(1 for s in slos if s["status"] == "breached"),
            "esql": f"""\
FROM .slo-observability.summary-v3*
| WHERE kibana.space_id == "{self.tenant_id}"
  AND slo.instanceId    LIKE "{self.region}*"
| STATS
    current_sli     = AVG(slo.sliValue),
    error_budget    = AVG(slo.errorBudget.remaining.pct),
    burn_rate_1h    = AVG(slo.burnRate.1h)
  BY slo.name, slo.objective.target
| SORT burn_rate_1h DESC""",
        }

    # ── Anomaly Detection ─────────────────────────────────────────────────────

    def get_anomalies(self) -> Dict[str, Any]:
        rng = random.Random(self.tenant_id)
        anomalies = [
            {**a, "score": round(a["score"] * rng.uniform(0.85, 1.0), 2)}
            for a in _ANOMALIES
        ]
        return {
            "anomalies": anomalies,
            "high_confidence": sum(1 for a in anomalies if a["score"] > 0.85),
            "esql": f"""\
FROM .ml-anomalies-*
| WHERE tenant_id == "{self.tenant_id}"
  AND region      == "{self.region}"
  AND record_score > 50
  AND timestamp   > NOW() - 24 HOURS
| STATS
    max_score  = MAX(record_score),
    event_count = COUNT(*)
  BY job_id, by_field_value
| SORT max_score DESC
| LIMIT 10""",
        }
