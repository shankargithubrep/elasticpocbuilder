"""
Persona Dashboard Service

Provides data for three observability personas:

  SRE        — Incident triage, MTTR trend, error budget burn, runbook assistant
  DevOps     — DORA metrics, deployment timeline, change failure rate, pipeline health
  Leadership — SLO scorecard, cost-per-region, business impact, exec summary

Each method returns simulation data with an `esql` key showing the
tenant-filtered query that would run against a live cluster.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

DT = datetime.now(timezone.utc)


def _ts(minutes_ago: int) -> str:
    return (DT - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _day(days_ago: int) -> str:
    return (DT - timedelta(days=days_ago)).strftime("%Y-%m-%d")


_SERVICES = [
    "api-gateway", "auth-service", "contact-routing",
    "voice-transcription", "notification-svc", "billing-engine",
    "analytics-pipeline", "search-service",
]

_RUNBOOKS = {
    "High error rate":    "1. Check upstream DB connections\n2. Review recent deploys (`git log --since=1h`)\n3. Inspect pod restarts: `kubectl get pods -n prod`\n4. Roll back if deploy < 30 min ago",
    "Memory OOM":         "1. Identify pod: `kubectl top pods -n prod --sort-by=memory`\n2. Check heap dumps in Kibana APM\n3. Increase memory limit or trigger HPA\n4. File P1 ticket if recurs > 2× in 24h",
    "Latency spike":      "1. Check p99 by endpoint in APM\n2. Look for DB slow queries (query logs > 1s)\n3. Check Redis hit rate — cache warm?\n4. Review recent infra changes in CloudTrail",
    "Data stream lag":    "1. Check ingest pipeline errors in Kibana\n2. Verify Kafka consumer group lag\n3. Scale up pipeline workers if > 100k backlog\n4. Escalate to data-eng if persists > 15 min",
    "Certificate expiry": "1. Run: `openssl s_client -connect <host>:443 | openssl x509 -noout -dates`\n2. Renew via cert-manager: `kubectl annotate cert <name> cert-manager.io/issue-temporary-certificate=true`\n3. Verify renewal in 5 min\n4. Update secret in vault",
}


class PersonaDashboardService:

    def __init__(self, tenant_id: str = "default", region: str = "us-east-1"):
        self.tenant_id = tenant_id
        self.region    = region

    # ── SRE ──────────────────────────────────────────────────────────────────

    def get_sre_incident_summary(self) -> Dict[str, Any]:
        """Active incidents with severity, age, owning team, and status."""
        severities = ["P1", "P2", "P3"]
        statuses   = ["investigating", "mitigating", "resolved", "monitoring"]
        incidents  = []
        for i, svc in enumerate(random.sample(_SERVICES, 5)):
            sev = random.choice(severities)
            opened_min = random.randint(5, 240)
            incidents.append({
                "id":        f"INC-{1000 + i}",
                "service":   svc,
                "severity":  sev,
                "status":    random.choice(statuses),
                "opened_at": _ts(opened_min),
                "age_min":   opened_min,
                "owner":     random.choice(["sre-oncall", "platform-team", "app-team-alpha"]),
                "title":     f"{sev} — {svc} {'error spike' if sev == 'P1' else 'latency elevated'}",
            })
        return {
            "incidents": incidents,
            "open_p1":   sum(1 for i in incidents if i["severity"] == "P1" and i["status"] != "resolved"),
            "open_p2":   sum(1 for i in incidents if i["severity"] == "P2" and i["status"] != "resolved"),
            "esql": f"""FROM .alerts-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND kibana.alert.status == "active"
| KEEP @timestamp, kibana.alert.rule.name, kibana.alert.severity,
       kibana.alert.status, kibana.alert.reason
| SORT @timestamp DESC
| LIMIT 25""",
        }

    def get_sre_mttr_trend(self) -> Dict[str, Any]:
        """Mean time to resolve over the last 14 days."""
        trend = []
        for d in range(13, -1, -1):
            trend.append({
                "date":    _day(d),
                "mttr_min": round(random.uniform(8, 95), 1),
                "incidents": random.randint(1, 12),
            })
        avg_mttr = round(sum(r["mttr_min"] for r in trend) / len(trend), 1)
        return {
            "trend":    trend,
            "avg_mttr": avg_mttr,
            "target_mttr": 30,
            "esql": f"""FROM traces-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND @timestamp >= NOW() - 14 days
| STATS
    incidents = COUNT_DISTINCT(trace.id),
    avg_dur_ms = AVG(transaction.duration.us) / 1000
  BY DATE_TRUNC(1 day, @timestamp)
| SORT @timestamp ASC""",
        }

    def get_sre_error_budget(self) -> Dict[str, Any]:
        """Error budget burn rate per service (30-day rolling)."""
        budgets = []
        for svc in _SERVICES:
            availability = round(random.uniform(98.5, 99.99), 3)
            target        = 99.9
            budget_used   = round((100 - availability) / (100 - target) * 100, 1)
            budgets.append({
                "service":      svc,
                "availability": availability,
                "target":       target,
                "budget_used":  budget_used,
                "status": "🔴 BREACHED" if budget_used > 100 else "🟡 AT RISK" if budget_used > 50 else "🟢 OK",
            })
        budgets.sort(key=lambda x: x["budget_used"], reverse=True)
        return {
            "budgets": budgets,
            "esql": f"""FROM traces-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND @timestamp >= NOW() - 30 days
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY service.name
| EVAL availability = ROUND((total - errors) * 100.0 / GREATEST(total, 1), 3)
| EVAL budget_used  = ROUND((100 - availability) / (100 - 99.9) * 100, 1)
| SORT budget_used DESC""",
        }

    def get_sre_runbook(self, alert_name: str) -> Dict[str, Any]:
        """Return a runbook for the given alert type."""
        key   = next((k for k in _RUNBOOKS if k.lower() in alert_name.lower()), None)
        steps = _RUNBOOKS.get(key or list(_RUNBOOKS)[0], "No runbook found. Escalate to on-call lead.")
        return {
            "alert":   alert_name,
            "runbook": steps,
            "esql": f"""FROM logs-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND @timestamp >= NOW() - 1 hour
  AND log.level IN ("ERROR","FATAL")
| STATS count = COUNT(*) BY log.message
| SORT count DESC | LIMIT 10""",
        }

    # ── DevOps ────────────────────────────────────────────────────────────────

    def get_devops_dora(self) -> Dict[str, Any]:
        """DORA four key metrics (simulated 30-day window)."""
        return {
            "deployment_frequency":    {"value": round(random.uniform(2.1, 8.4), 1),  "unit": "deploys/day",   "trend": random.choice(["+", "-"]) + f"{random.randint(1,15)}%", "target": "> 1/day",   "status": "elite"},
            "lead_time_hours":         {"value": round(random.uniform(1.5, 18.0), 1),  "unit": "hours",         "trend": random.choice(["+", "-"]) + f"{random.randint(1,20)}%", "target": "< 24h",     "status": "elite"},
            "change_failure_rate":     {"value": round(random.uniform(1.2, 12.0), 1),  "unit": "%",             "trend": random.choice(["+", "-"]) + f"{random.randint(1,10)}%", "target": "< 15%",     "status": "high"},
            "mttr_hours":              {"value": round(random.uniform(0.5, 4.0), 2),    "unit": "hours",         "trend": random.choice(["+", "-"]) + f"{random.randint(1,25)}%", "target": "< 24h",     "status": "elite"},
            "esql": f"""FROM traces-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND @timestamp >= NOW() - 30 days
| STATS
    deploys = COUNT_DISTINCT(transaction.id),
    errors  = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    total   = COUNT(*)
  BY DATE_TRUNC(1 day, @timestamp)
| EVAL cfr = ROUND(errors * 100.0 / GREATEST(total, 1), 2)
| SORT @timestamp ASC""",
        }

    def get_devops_deployment_timeline(self) -> Dict[str, Any]:
        """Recent deployments with health outcome."""
        deploys = []
        statuses = ["success", "success", "success", "rollback", "success", "failure"]
        for i in range(12):
            svc      = random.choice(_SERVICES)
            version  = f"v{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 9)}"
            status   = random.choice(statuses)
            deployed = random.randint(15, 2880)
            deploys.append({
                "service":     svc,
                "version":     version,
                "deployed_at": _ts(deployed),
                "deployed_by": random.choice(["ci-pipeline", "jane.doe", "john.smith", "release-bot"]),
                "duration_s":  random.randint(45, 480),
                "status":      status,
                "icon": "✅" if status == "success" else ("⏪" if status == "rollback" else "❌"),
            })
        deploys.sort(key=lambda x: x["deployed_at"], reverse=True)
        return {
            "deployments": deploys,
            "total":    len(deploys),
            "success":  sum(1 for d in deploys if d["status"] == "success"),
            "rollbacks": sum(1 for d in deploys if d["status"] == "rollback"),
            "esql": f"""FROM logs-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND event.action == "deployment"
  AND @timestamp >= NOW() - 7 days
| KEEP @timestamp, service.name, service.version, event.outcome, labels.deployed_by
| SORT @timestamp DESC | LIMIT 25""",
        }

    def get_devops_pipeline_health(self) -> Dict[str, Any]:
        """CI/CD pipeline pass rate and flaky tests by service."""
        pipelines = []
        for svc in _SERVICES:
            runs        = random.randint(20, 120)
            pass_rate   = round(random.uniform(72, 99), 1)
            flaky_tests = random.randint(0, 8)
            pipelines.append({
                "service":     svc,
                "runs_7d":     runs,
                "pass_rate":   pass_rate,
                "flaky_tests": flaky_tests,
                "avg_dur_min": round(random.uniform(3, 22), 1),
                "status": "🔴" if pass_rate < 80 else ("🟡" if pass_rate < 92 else "🟢"),
            })
        pipelines.sort(key=lambda x: x["pass_rate"])
        return {
            "pipelines": pipelines,
            "esql": f"""FROM logs-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND event.category == "pipeline"
  AND @timestamp >= NOW() - 7 days
| STATS
    runs      = COUNT(*),
    passed    = COUNT_CASE(event.outcome == "success"),
    failed    = COUNT_CASE(event.outcome == "failure")
  BY service.name
| EVAL pass_rate = ROUND(passed * 100.0 / GREATEST(runs, 1), 1)
| SORT pass_rate ASC""",
        }

    # ── Leadership ────────────────────────────────────────────────────────────

    def get_leadership_slo_scorecard(self) -> Dict[str, Any]:
        """SLO compliance scorecard for executive review."""
        slos = []
        definitions = [
            ("API Availability",      99.9,  "availability"),
            ("Search Latency P95",    95.0,  "latency"),
            ("Voice Transcription",   99.5,  "availability"),
            ("Contact Routing",       99.0,  "availability"),
            ("Billing Engine",        99.95, "availability"),
            ("Analytics Pipeline",    98.0,  "throughput"),
            ("Auth Service",          99.9,  "availability"),
            ("Notification Delivery", 98.5,  "availability"),
        ]
        for name, target, slo_type in definitions:
            actual      = round(random.uniform(target - 1.5, 100.0), 3)
            actual      = min(actual, 100.0)
            budget_used = round((100 - actual) / max(100 - target, 0.001) * 100, 1)
            slos.append({
                "name":        name,
                "type":        slo_type,
                "target":      target,
                "actual":      actual,
                "budget_used": budget_used,
                "compliant":   actual >= target,
                "status": "🔴 Breached" if actual < target else ("🟡 At Risk" if budget_used > 50 else "🟢 On Track"),
            })
        compliant     = sum(1 for s in slos if s["compliant"])
        at_risk       = sum(1 for s in slos if not s["compliant"] and s["budget_used"] > 50)
        return {
            "slos":        slos,
            "total":       len(slos),
            "compliant":   compliant,
            "at_risk":     at_risk,
            "compliance_pct": round(compliant * 100 / len(slos), 1),
            "esql": f"""FROM traces-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND @timestamp >= NOW() - 30 days
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY service.name
| EVAL availability = ROUND((total - errors) * 100.0 / GREATEST(total, 1), 3)
| SORT availability ASC""",
        }

    def get_leadership_cost_per_region(self) -> Dict[str, Any]:
        """Estimated observability data volume and cost per region."""
        regions_data = [
            ("us-east-1",   "AWS",   "🇺🇸"),
            ("eu-west-1",   "AWS",   "🇪🇺"),
            ("ap-southeast-1", "AWS","🇸🇬"),
            ("us-central1", "GCP",   "🇺🇸"),
            ("eu-west4",    "GCP",   "🇳🇱"),
        ]
        costs = []
        total_gb    = 0
        total_cost  = 0
        for region, cloud, flag in regions_data:
            logs_gb    = round(random.uniform(40, 450), 1)
            metrics_gb = round(random.uniform(10, 80), 1)
            traces_gb  = round(random.uniform(20, 200), 1)
            total      = logs_gb + metrics_gb + traces_gb
            cost_usd   = round(total * random.uniform(0.023, 0.031), 2)
            total_gb   += total
            total_cost += cost_usd
            costs.append({
                "region":     f"{flag} {region}",
                "cloud":      cloud,
                "logs_gb":    logs_gb,
                "metrics_gb": metrics_gb,
                "traces_gb":  traces_gb,
                "total_gb":   round(total, 1),
                "cost_usd":   cost_usd,
            })
        costs.sort(key=lambda x: x["cost_usd"], reverse=True)
        return {
            "regions":    costs,
            "total_gb":   round(total_gb, 1),
            "total_cost": round(total_cost, 2),
            "month":      DT.strftime("%B %Y"),
            "esql": f"""FROM metrics-*
| WHERE tenant_id == "{self.tenant_id}"
  AND @timestamp >= NOW() - 30 days
| STATS
    doc_count = COUNT(*),
    size_bytes = SUM(event.dataset.bytes)
  BY region, data_stream.type
| EVAL size_gb = ROUND(size_bytes / 1073741824, 2)
| SORT size_gb DESC""",
        }

    def get_leadership_business_impact(self) -> Dict[str, Any]:
        """Revenue-at-risk and customer impact from SLO breaches."""
        incidents = []
        services  = ["api-gateway", "billing-engine", "contact-routing", "auth-service"]
        for svc in services:
            duration_min   = random.randint(5, 180)
            affected_users = random.randint(100, 50000)
            revenue_risk   = round(affected_users * random.uniform(0.05, 2.5), 2)
            incidents.append({
                "service":        svc,
                "incident":       f"Availability degradation — {svc}",
                "duration_min":   duration_min,
                "affected_users": affected_users,
                "revenue_risk":   revenue_risk,
                "resolved":       random.choice([True, True, False]),
            })
        total_risk  = round(sum(i["revenue_risk"] for i in incidents), 2)
        total_users = sum(i["affected_users"] for i in incidents)
        return {
            "incidents":    incidents,
            "total_risk":   total_risk,
            "total_users":  total_users,
            "month":        DT.strftime("%B %Y"),
            "esql": f"""FROM traces-*
| WHERE tenant_id == "{self.tenant_id}" AND region == "{self.region}"
  AND transaction.result LIKE "HTTP 5*"
  AND @timestamp >= NOW() - 30 days
| STATS
    error_count = COUNT(*),
    unique_users = COUNT_DISTINCT(user.id)
  BY service.name, DATE_TRUNC(1 day, @timestamp)
| SORT error_count DESC""",
        }

    def get_leadership_exec_summary(self) -> Dict[str, Any]:
        """High-level executive summary: SLO score, incidents, cost, trend."""
        return {
            "slo_compliance_pct":   round(random.uniform(88, 99.2), 1),
            "open_p1_incidents":    random.randint(0, 3),
            "mttr_avg_hours":       round(random.uniform(0.4, 3.5), 1),
            "monthly_cost_usd":     round(random.uniform(4200, 18000), 2),
            "cost_trend_pct":       round(random.uniform(-8, 15), 1),
            "deployments_30d":      random.randint(45, 220),
            "change_failure_rate":  round(random.uniform(1.5, 8.0), 1),
            "data_residency_ok":    True,
            "regions_healthy":      random.randint(3, 5),
            "regions_total":        5,
            "month":                DT.strftime("%B %Y"),
        }
