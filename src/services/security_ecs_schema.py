"""
Elastic Common Schema (ECS) Field Registry for Security Demos

This module is the ground-truth reference for all ECS field names, types,
and index patterns used in Security, Observability, and SIEM/XDR demo generation.

It feeds:
- SecurityQueryStrategyGenerator (prompt construction)
- ObservabilityStrategyGenerator (APM field requirements)
- SchemaContract validation (ECS field name enforcement)
- detection_rules_tab UI (MITRE ATT&CK badge rendering)
- ElasticsearchIndexer (IP field type mapping, ILM policies)

References:
- https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html
- https://attack.mitre.org/tactics/enterprise/
"""

from typing import Dict, List, Any


# =============================================================================
# ECS Base Event Fields — required in ALL security event datasets
# =============================================================================

ECS_BASE_FIELDS: Dict[str, str] = {
    "@timestamp": "date",
    "event.category": "keyword",      # authentication, network, process, file, registry, dns
    "event.type": "keyword",          # start, end, info, error, allowed, denied, creation, deletion
    "event.outcome": "keyword",       # success, failure, unknown
    "event.severity": "long",
    "event.dataset": "keyword",
    "event.module": "keyword",
    "event.kind": "keyword",          # event, alert, metric, state, pipeline_error, signal
    "event.action": "keyword",
    "event.id": "keyword",
    "event.provider": "keyword",
    "event.ingested": "date",
    "event.created": "date",
    "message": "text",
    "tags": "keyword",
    "labels": "object",
}


# =============================================================================
# ECS Host Fields
# =============================================================================

ECS_HOST_FIELDS: Dict[str, str] = {
    "host.name": "keyword",
    "host.hostname": "keyword",
    "host.id": "keyword",
    "host.ip": "ip",
    "host.mac": "keyword",
    "host.architecture": "keyword",
    "host.os.name": "keyword",
    "host.os.type": "keyword",        # windows, linux, macos, ios, android
    "host.os.version": "keyword",
    "host.os.platform": "keyword",
    "host.os.kernel": "keyword",
    "host.type": "keyword",
    "host.uptime": "long",
    "host.domain": "keyword",
    "host.geo.country_name": "keyword",
    "host.geo.city_name": "keyword",
    "host.geo.region_name": "keyword",
    "host.geo.location": "geo_point",
}


# =============================================================================
# ECS User Fields
# =============================================================================

ECS_USER_FIELDS: Dict[str, str] = {
    "user.name": "keyword",
    "user.id": "keyword",
    "user.email": "keyword",
    "user.full_name": "keyword",
    "user.domain": "keyword",
    "user.hash": "keyword",
    "user.roles": "keyword",
    "user.group.id": "keyword",
    "user.group.name": "keyword",
    "user.target.name": "keyword",    # target user in privilege escalation
    "user.target.id": "keyword",
    "user.effective.name": "keyword", # effective user after sudo/runas
    "user.effective.id": "keyword",
    "user.changes.name": "keyword",
    "user.changes.roles": "keyword",
}


# =============================================================================
# ECS Process Fields — EDR / Endpoint Detection
# =============================================================================

ECS_PROCESS_FIELDS: Dict[str, str] = {
    "process.name": "keyword",
    "process.executable": "keyword",
    "process.command_line": "wildcard",   # wildcard for LIKE queries
    "process.args": "keyword",
    "process.args_count": "long",
    "process.pid": "long",
    "process.ppid": "long",
    "process.parent.name": "keyword",
    "process.parent.executable": "keyword",
    "process.parent.pid": "long",
    "process.parent.command_line": "wildcard",
    "process.hash.md5": "keyword",
    "process.hash.sha1": "keyword",
    "process.hash.sha256": "keyword",
    "process.code_signature.status": "keyword",
    "process.code_signature.subject_name": "keyword",
    "process.code_signature.trusted": "boolean",
    "process.start": "date",
    "process.end": "date",
    "process.uptime": "long",
    "process.working_directory": "keyword",
    "process.entity_id": "keyword",       # unique process identifier
    "process.thread.id": "long",
}


# =============================================================================
# ECS Network Fields — SIEM / NDR / Firewall
# =============================================================================

ECS_NETWORK_FIELDS: Dict[str, str] = {
    "network.protocol": "keyword",        # tcp, udp, dns, http, tls
    "network.transport": "keyword",
    "network.type": "keyword",            # ipv4, ipv6
    "network.direction": "keyword",       # ingress, egress, inbound, outbound, internal, external, unknown
    "network.community_id": "keyword",
    "network.bytes": "long",
    "network.packets": "long",
    "network.application": "keyword",
    "source.ip": "ip",
    "source.port": "long",
    "source.bytes": "long",
    "source.packets": "long",
    "source.geo.country_name": "keyword",
    "source.geo.city_name": "keyword",
    "source.geo.location": "geo_point",
    "source.as.number": "long",
    "source.as.organization.name": "keyword",
    "destination.ip": "ip",
    "destination.port": "long",
    "destination.bytes": "long",
    "destination.packets": "long",
    "destination.geo.country_name": "keyword",
    "destination.geo.city_name": "keyword",
    "destination.geo.location": "geo_point",
    "destination.as.number": "long",
    "destination.as.organization.name": "keyword",
    "related.ip": "ip",
    "related.user": "keyword",
    "related.hosts": "keyword",
    "related.hash": "keyword",
}


# =============================================================================
# ECS File Fields — EDR / Malware Detection
# =============================================================================

ECS_FILE_FIELDS: Dict[str, str] = {
    "file.name": "keyword",
    "file.path": "keyword",
    "file.directory": "keyword",
    "file.extension": "keyword",
    "file.size": "long",
    "file.type": "keyword",              # file, dir, symlink
    "file.hash.md5": "keyword",
    "file.hash.sha1": "keyword",
    "file.hash.sha256": "keyword",
    "file.code_signature.status": "keyword",
    "file.code_signature.trusted": "boolean",
    "file.code_signature.subject_name": "keyword",
    "file.pe.imphash": "keyword",
    "file.pe.original_file_name": "keyword",
    "file.created": "date",
    "file.mtime": "date",
    "file.ctime": "date",
    "file.owner": "keyword",
    "file.uid": "keyword",
}


# =============================================================================
# ECS DNS Fields — SIEM / C2 Detection
# =============================================================================

ECS_DNS_FIELDS: Dict[str, str] = {
    "dns.question.name": "keyword",
    "dns.question.type": "keyword",
    "dns.question.class": "keyword",
    "dns.answers.name": "keyword",
    "dns.answers.type": "keyword",
    "dns.answers.data": "keyword",
    "dns.answers.ttl": "long",
    "dns.response_code": "keyword",
    "dns.resolved_ip": "ip",
    "dns.type": "keyword",               # query, answer
}


# =============================================================================
# ECS HTTP / TLS Fields — Web Security
# =============================================================================

ECS_HTTP_FIELDS: Dict[str, str] = {
    "http.request.method": "keyword",
    "http.request.body.bytes": "long",
    "http.request.referrer": "keyword",
    "http.response.status_code": "long",
    "http.response.body.bytes": "long",
    "http.version": "keyword",
    "url.full": "keyword",
    "url.domain": "keyword",
    "url.path": "keyword",
    "url.scheme": "keyword",
    "url.query": "keyword",
    "url.port": "long",
    "tls.version": "keyword",
    "tls.cipher": "keyword",
    "tls.established": "boolean",
    "tls.resumed": "boolean",
    "tls.server.subject": "keyword",
    "tls.server.issuer": "keyword",
    "tls.server.certificate_chain": "keyword",
    "tls.server.not_after": "date",
    "tls.client.subject": "keyword",
    "user_agent.original": "keyword",
    "user_agent.name": "keyword",
    "user_agent.os.name": "keyword",
}


# =============================================================================
# ECS Registry Fields — Windows EDR
# =============================================================================

ECS_REGISTRY_FIELDS: Dict[str, str] = {
    "registry.hive": "keyword",          # HKLM, HKCU, HKU, HKCR
    "registry.key": "keyword",
    "registry.path": "keyword",
    "registry.value": "keyword",
    "registry.data.type": "keyword",     # REG_SZ, REG_DWORD, REG_BINARY
    "registry.data.strings": "keyword",
    "registry.data.bytes": "keyword",
}


# =============================================================================
# ECS Cloud Fields — Cloud Security / CSPM
# =============================================================================

ECS_CLOUD_FIELDS: Dict[str, str] = {
    "cloud.provider": "keyword",         # aws, azure, gcp
    "cloud.account.id": "keyword",
    "cloud.account.name": "keyword",
    "cloud.region": "keyword",
    "cloud.availability_zone": "keyword",
    "cloud.instance.id": "keyword",
    "cloud.instance.name": "keyword",
    "cloud.machine.type": "keyword",
    "cloud.service.name": "keyword",
    "cloud.project.id": "keyword",
    "cloud.project.name": "keyword",
    "orchestrator.cluster.id": "keyword",
    "orchestrator.cluster.name": "keyword",
    "orchestrator.namespace": "keyword",
    "orchestrator.resource.name": "keyword",
    "orchestrator.type": "keyword",      # kubernetes, ecs
    "container.id": "keyword",
    "container.name": "keyword",
    "container.image.name": "keyword",
    "container.image.tag": "keyword",
}


# =============================================================================
# MITRE ATT&CK Threat Fields
# =============================================================================

ECS_THREAT_FIELDS: Dict[str, str] = {
    "threat.framework": "keyword",           # "MITRE ATT&CK"
    "threat.group.id": "keyword",
    "threat.group.name": "keyword",
    "threat.group.alias": "keyword",
    "threat.tactic.id": "keyword",           # TA0001
    "threat.tactic.name": "keyword",         # Initial Access
    "threat.tactic.reference": "keyword",
    "threat.technique.id": "keyword",        # T1078
    "threat.technique.name": "keyword",      # Valid Accounts
    "threat.technique.reference": "keyword",
    "threat.technique.subtechnique.id": "keyword",    # T1078.003
    "threat.technique.subtechnique.name": "keyword",
    "threat.software.id": "keyword",
    "threat.software.name": "keyword",
    "threat.software.type": "keyword",       # Tool, Malware
    "threat.indicator.type": "keyword",      # domain-name, ip-addr, file, email-addr
    "threat.indicator.ip": "ip",
    "threat.indicator.domain": "keyword",
    "threat.indicator.file.hash.sha256": "keyword",
    "threat.indicator.email.address": "keyword",
    "threat.indicator.confidence": "keyword",
    "threat.indicator.first_seen": "date",
    "threat.indicator.last_seen": "date",
    "threat.indicator.marking.tlp": "keyword",  # WHITE, GREEN, AMBER, RED
}


# =============================================================================
# MITRE ATT&CK Tactic Reference (Enterprise)
# =============================================================================

MITRE_TACTICS: Dict[str, Dict[str, str]] = {
    "TA0001": {"name": "Initial Access", "description": "Techniques to gain initial foothold"},
    "TA0002": {"name": "Execution", "description": "Techniques to run malicious code"},
    "TA0003": {"name": "Persistence", "description": "Techniques to maintain access"},
    "TA0004": {"name": "Privilege Escalation", "description": "Techniques to gain higher permissions"},
    "TA0005": {"name": "Defense Evasion", "description": "Techniques to avoid detection"},
    "TA0006": {"name": "Credential Access", "description": "Techniques to steal credentials"},
    "TA0007": {"name": "Discovery", "description": "Techniques to learn about the environment"},
    "TA0008": {"name": "Lateral Movement", "description": "Techniques to move through the environment"},
    "TA0009": {"name": "Collection", "description": "Techniques to gather data of interest"},
    "TA0010": {"name": "Exfiltration", "description": "Techniques to steal data"},
    "TA0011": {"name": "Command and Control", "description": "Techniques to communicate with compromised systems"},
    "TA0040": {"name": "Impact", "description": "Techniques to disrupt, destroy, or manipulate"},
    "TA0042": {"name": "Resource Development", "description": "Techniques to establish resources"},
    "TA0043": {"name": "Reconnaissance", "description": "Techniques to gather information"},
}


# =============================================================================
# Top 30 MITRE ATT&CK Techniques (most commonly detected)
# =============================================================================

MITRE_TECHNIQUES: Dict[str, Dict[str, str]] = {
    "T1059": {"name": "Command and Scripting Interpreter", "tactic_id": "TA0002"},
    "T1059.001": {"name": "PowerShell", "tactic_id": "TA0002"},
    "T1059.003": {"name": "Windows Command Shell", "tactic_id": "TA0002"},
    "T1078": {"name": "Valid Accounts", "tactic_id": "TA0001"},
    "T1078.002": {"name": "Domain Accounts", "tactic_id": "TA0003"},
    "T1078.003": {"name": "Local Accounts", "tactic_id": "TA0001"},
    "T1110": {"name": "Brute Force", "tactic_id": "TA0006"},
    "T1110.001": {"name": "Password Guessing", "tactic_id": "TA0006"},
    "T1110.003": {"name": "Password Spraying", "tactic_id": "TA0006"},
    "T1566": {"name": "Phishing", "tactic_id": "TA0001"},
    "T1566.001": {"name": "Spearphishing Attachment", "tactic_id": "TA0001"},
    "T1566.002": {"name": "Spearphishing Link", "tactic_id": "TA0001"},
    "T1055": {"name": "Process Injection", "tactic_id": "TA0004"},
    "T1055.001": {"name": "Dynamic-link Library Injection", "tactic_id": "TA0004"},
    "T1021": {"name": "Remote Services", "tactic_id": "TA0008"},
    "T1021.001": {"name": "Remote Desktop Protocol", "tactic_id": "TA0008"},
    "T1021.002": {"name": "SMB/Windows Admin Shares", "tactic_id": "TA0008"},
    "T1071": {"name": "Application Layer Protocol", "tactic_id": "TA0011"},
    "T1071.001": {"name": "Web Protocols", "tactic_id": "TA0011"},
    "T1071.004": {"name": "DNS", "tactic_id": "TA0011"},
    "T1003": {"name": "OS Credential Dumping", "tactic_id": "TA0006"},
    "T1003.001": {"name": "LSASS Memory", "tactic_id": "TA0006"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic_id": "TA0040"},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic_id": "TA0001"},
    "T1133": {"name": "External Remote Services", "tactic_id": "TA0001"},
    "T1505": {"name": "Server Software Component", "tactic_id": "TA0003"},
    "T1505.003": {"name": "Web Shell", "tactic_id": "TA0003"},
    "T1562": {"name": "Impair Defenses", "tactic_id": "TA0005"},
    "T1562.001": {"name": "Disable or Modify Tools", "tactic_id": "TA0005"},
    "T1140": {"name": "Deobfuscate/Decode Files or Information", "tactic_id": "TA0005"},
}


# =============================================================================
# Kibana Alert / Signal Fields
# =============================================================================

ECS_KIBANA_ALERT_FIELDS: Dict[str, str] = {
    "kibana.alert.rule.name": "keyword",
    "kibana.alert.rule.rule_id": "keyword",
    "kibana.alert.rule.type": "keyword",
    "kibana.alert.rule.category": "keyword",
    "kibana.alert.severity": "keyword",          # low, medium, high, critical
    "kibana.alert.risk_score": "long",
    "kibana.alert.workflow_status": "keyword",   # open, acknowledged, closed
    "kibana.alert.status": "keyword",
    "kibana.alert.start": "date",
    "kibana.alert.end": "date",
    "kibana.alert.duration.us": "long",
    "kibana.alert.uuid": "keyword",
    "kibana.alert.reason": "keyword",
    "kibana.space_ids": "keyword",
}


# =============================================================================
# Kibana Alert Fields (Observability)
# =============================================================================

ECS_KIBANA_ALERT_FIELDS: Dict[str, str] = {
    "kibana.alert.rule.name": "keyword",
    "kibana.alert.rule.rule_id": "keyword",
    "kibana.alert.rule.type": "keyword",
    "kibana.alert.severity": "keyword",
    "kibana.alert.risk_score": "long",
    "kibana.alert.workflow_status": "keyword",
    "kibana.alert.status": "keyword",
    "kibana.alert.start": "date",
    "kibana.alert.end": "date",
    "kibana.alert.uuid": "keyword",
    "kibana.alert.reason": "keyword",
}


# =============================================================================
# APM / OpenTelemetry Fields (Observability Pillar)
# =============================================================================

ECS_APM_FIELDS: Dict[str, str] = {
    "trace.id": "keyword",
    "transaction.id": "keyword",
    "span.id": "keyword",
    "parent.id": "keyword",
    "service.name": "keyword",
    "service.version": "keyword",
    "service.environment": "keyword",    # production, staging, development
    "service.language.name": "keyword",  # python, java, go, nodejs
    "service.language.version": "keyword",
    "service.runtime.name": "keyword",
    "service.runtime.version": "keyword",
    "service.framework.name": "keyword",
    "service.node.name": "keyword",
    "service.target.name": "keyword",
    "service.target.type": "keyword",
    "agent.name": "keyword",             # python, java, go, nodejs, rum-js
    "agent.version": "keyword",
    "event.duration": "long",           # nanoseconds
    "transaction.name": "keyword",
    "transaction.type": "keyword",      # request, scheduled, message, custom
    "transaction.result": "keyword",    # HTTP 2xx, HTTP 4xx, success, failure
    "transaction.sampled": "boolean",
    "span.name": "keyword",
    "span.type": "keyword",             # db, external, cache, messaging
    "span.subtype": "keyword",          # postgresql, mysql, redis, http, grpc
    "span.action": "keyword",           # query, connect, publish, consume
    "span.db.statement": "text",
    "span.db.type": "keyword",
    "labels": "object",
    "numeric_labels": "object",
    "metricset.name": "keyword",
    "metricset.period": "long",
    "processor.event": "keyword",       # transaction, span, metric, error, log
    "processor.name": "keyword",        # transaction, metric, error
}


# =============================================================================
# Compliance Framework Mappings
# =============================================================================

COMPLIANCE_FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "SOC2": {
        "name": "SOC 2 Type II",
        "categories": ["CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7", "CC8", "CC9"],
        "key_controls": [
            "CC6.1 - Logical access controls",
            "CC6.2 - Authentication mechanisms",
            "CC6.3 - Privileged access management",
            "CC6.7 - Data transmission and encryption",
            "CC7.1 - Security monitoring",
            "CC7.2 - Security event detection",
            "CC7.3 - Security incident response",
        ],
        "relevant_event_categories": ["authentication", "network", "file", "process"],
    },
    "PCI-DSS": {
        "name": "PCI DSS v4.0",
        "requirements": ["Req 1", "Req 2", "Req 7", "Req 8", "Req 10", "Req 11", "Req 12"],
        "key_controls": [
            "Req 1 - Network access controls",
            "Req 7 - Restrict access to system components",
            "Req 8 - Identify users and authenticate access",
            "Req 10 - Log and monitor access to system components",
            "Req 11 - Test security of systems and networks regularly",
        ],
        "relevant_event_categories": ["authentication", "network", "web"],
    },
    "HIPAA": {
        "name": "HIPAA Security Rule",
        "safeguards": ["Administrative", "Physical", "Technical"],
        "key_controls": [
            "164.312(a)(1) - Access control",
            "164.312(a)(2)(i) - Unique user identification",
            "164.312(b) - Audit controls",
            "164.312(c)(1) - Integrity controls",
            "164.312(d) - Person or entity authentication",
            "164.312(e)(1) - Transmission security",
        ],
        "relevant_event_categories": ["authentication", "file", "network"],
    },
    "ISO27001": {
        "name": "ISO/IEC 27001:2022",
        "domains": ["A.5", "A.6", "A.7", "A.8", "A.9", "A.10", "A.11", "A.12"],
        "key_controls": [
            "A.5.15 - Access control",
            "A.5.16 - Identity management",
            "A.5.17 - Authentication information",
            "A.8.15 - Logging",
            "A.8.16 - Monitoring activities",
            "A.8.17 - Clock synchronization",
        ],
        "relevant_event_categories": ["authentication", "network", "process", "file"],
    },
    "NIST-CSF": {
        "name": "NIST Cybersecurity Framework 2.0",
        "functions": ["Govern", "Identify", "Protect", "Detect", "Respond", "Recover"],
        "key_controls": [
            "DE.AE - Anomalies and Events",
            "DE.CM - Continuous Monitoring",
            "RS.AN - Incident Analysis",
            "RS.CO - Incident Communication",
        ],
        "relevant_event_categories": ["authentication", "network", "process", "file"],
    },
}


# =============================================================================
# MOTLP (Managed OTLP) — Native OpenTelemetry Field Conventions
# =============================================================================

# Native OTLP span/trace fields as stored by Elastic's MOTLP ingestion layer.
# These differ from ECS-translated APM fields (trace.id → TraceId, etc.)
MOTLP_REQUIRED_FIELDS: Dict[str, str] = {
    # Timing
    "@timestamp":                                   "date",
    "StartTime":                                    "date",
    "EndTime":                                      "date",
    "Duration":                                     "long",       # nanoseconds
    # Trace identifiers (hex strings, not ECS trace.id)
    "TraceId":                                      "keyword",
    "SpanId":                                       "keyword",
    "ParentSpanId":                                 "keyword",
    # Span metadata
    "Name":                                         "keyword",    # span / operation name
    "Kind":                                         "keyword",    # SPAN_KIND_SERVER|CLIENT|INTERNAL|PRODUCER|CONSUMER
    "StatusCode":                                   "keyword",    # STATUS_CODE_OK|ERROR|UNSET
    "StatusMessage":                                "keyword",
    # Resource attributes — preserved as-is by MOTLP
    "resource.attributes.service.name":             "keyword",
    "resource.attributes.service.version":          "keyword",
    "resource.attributes.service.instance.id":      "keyword",
    "resource.attributes.deployment.environment":   "keyword",
    "resource.attributes.telemetry.sdk.name":       "keyword",
    "resource.attributes.telemetry.sdk.version":    "keyword",
    "resource.attributes.telemetry.sdk.language":   "keyword",
    "resource.attributes.host.name":                "keyword",
    "resource.attributes.cloud.provider":           "keyword",
    "resource.attributes.cloud.region":             "keyword",
    # Instrumentation scope
    "scope.name":                                   "keyword",
    "scope.version":                                "keyword",
    # Span attributes — semantic conventions
    "attributes.http.request.method":               "keyword",
    "attributes.http.response.status_code":         "long",
    "attributes.url.path":                          "keyword",
    "attributes.url.full":                          "keyword",
    "attributes.db.system":                         "keyword",
    "attributes.db.statement":                      "keyword",
    "attributes.net.peer.name":                     "keyword",
    "attributes.rpc.service":                       "keyword",
    "attributes.rpc.method":                        "keyword",
    # Dataset routing (OTEL_RESOURCE_ATTRIBUTES=data_stream.dataset=<value>)
    "data_stream.dataset":                          "keyword",
    "data_stream.namespace":                        "keyword",
    "data_stream.type":                             "keyword",
}

# MOTLP default data streams (Elastic Cloud generic OTLP ingestion)
MOTLP_INDEX_PATTERNS: List[str] = [
    "traces-generic.otel-default",
    "metrics-generic.otel-default",
    "logs-generic.otel-default",
]


# =============================================================================
# Security Index Patterns per Sub-Category
# =============================================================================

SECURITY_INDEX_PATTERNS: Dict[str, List[str]] = {
    "siem": [
        "logs-*",
        "winlogbeat-*",
        "filebeat-*",
        "auditbeat-*",
        "packetbeat-*",
        ".siem-signals-*",
        ".alerts-security.alerts-*",
    ],
    "xdr": [
        "logs-endpoint.events.*",
        "logs-endpoint.alerts-*",
        "logs-network_traffic.*",
        "logs-cloud.*",
        ".alerts-security.alerts-*",
    ],
    "edr": [
        "logs-endpoint.events.process-*",
        "logs-endpoint.events.file-*",
        "logs-endpoint.events.registry-*",
        "logs-endpoint.events.network-*",
        "logs-endpoint.alerts-*",
    ],
    "threat_hunting": [
        "logs-*",
        "logs-endpoint.events.*",
        "filebeat-*",
        "packetbeat-*",
    ],
    "compliance": [
        "logs-*",
        "auditbeat-*",
        "winlogbeat-*",
        ".fleet-actions-*",
    ],
    "observability": [
        "logs-*",
        "metrics-*",
        "traces-apm-*",
        "metrics-apm.*",
        "logs-apm.*",
    ],
    "motlp": [
        "traces-generic.otel-default",
        "metrics-generic.otel-default",
        "logs-generic.otel-default",
    ],
}


# =============================================================================
# ILM Policy Configurations per Use Case
# =============================================================================

ILM_POLICIES: Dict[str, Dict[str, Any]] = {
    "security_logs": {
        "description": "Long-retention policy for security event logs",
        "hot_phase_days": 7,
        "hot_max_size_gb": 50,
        "warm_phase_days": 30,
        "cold_phase_days": 90,
        "delete_phase_days": 365,
        "frozen_phase_days": None,
    },
    "security_alerts": {
        "description": "Extended retention for security alerts and signals",
        "hot_phase_days": 30,
        "hot_max_size_gb": 20,
        "warm_phase_days": 90,
        "cold_phase_days": 180,
        "delete_phase_days": 730,   # 2 years for compliance
        "frozen_phase_days": None,
    },
    "compliance_audit": {
        "description": "Compliance audit log retention (7 years for PCI-DSS)",
        "hot_phase_days": 30,
        "hot_max_size_gb": 30,
        "warm_phase_days": 180,
        "cold_phase_days": 365,
        "delete_phase_days": 2555,  # 7 years
        "frozen_phase_days": 730,
    },
    "observability_metrics": {
        "description": "Short-retention policy for observability metrics",
        "hot_phase_days": 14,
        "hot_max_size_gb": 30,
        "warm_phase_days": 30,
        "cold_phase_days": 60,
        "delete_phase_days": 90,
        "frozen_phase_days": None,
    },
    "apm_traces": {
        "description": "APM trace data with medium retention",
        "hot_phase_days": 7,
        "hot_max_size_gb": 50,
        "warm_phase_days": 14,
        "cold_phase_days": 30,
        "delete_phase_days": 60,
        "frozen_phase_days": None,
    },
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_fields_for_subcategory(sub_category: str) -> Dict[str, str]:
    """
    Return the canonical ECS field set for a given security sub-category.

    Args:
        sub_category: One of 'siem', 'xdr', 'edr', 'threat_hunting',
                      'compliance', 'observability', 'apm'

    Returns:
        Dict mapping field name to ES field type
    """
    base = {**ECS_BASE_FIELDS, **ECS_HOST_FIELDS, **ECS_USER_FIELDS}

    subcategory_fields = {
        "siem": {
            **base,
            **ECS_NETWORK_FIELDS,
            **ECS_HTTP_FIELDS,
            **ECS_DNS_FIELDS,
            **ECS_THREAT_FIELDS,
            **ECS_KIBANA_ALERT_FIELDS,
        },
        "xdr": {
            **base,
            **ECS_PROCESS_FIELDS,
            **ECS_NETWORK_FIELDS,
            **ECS_FILE_FIELDS,
            **ECS_CLOUD_FIELDS,
            **ECS_THREAT_FIELDS,
            **ECS_KIBANA_ALERT_FIELDS,
        },
        "edr": {
            **base,
            **ECS_PROCESS_FIELDS,
            **ECS_FILE_FIELDS,
            **ECS_REGISTRY_FIELDS,
            **ECS_NETWORK_FIELDS,
            **ECS_THREAT_FIELDS,
        },
        "threat_hunting": {
            **base,
            **ECS_PROCESS_FIELDS,
            **ECS_NETWORK_FIELDS,
            **ECS_FILE_FIELDS,
            **ECS_DNS_FIELDS,
            **ECS_THREAT_FIELDS,
        },
        "compliance": {
            **base,
            **ECS_NETWORK_FIELDS,
            **ECS_FILE_FIELDS,
            **ECS_CLOUD_FIELDS,
            **ECS_KIBANA_ALERT_FIELDS,
        },
        "observability": {
            **ECS_BASE_FIELDS,
            **ECS_HOST_FIELDS,
            **ECS_CLOUD_FIELDS,
            **ECS_HTTP_FIELDS,
        },
        "apm": {
            **ECS_BASE_FIELDS,
            **ECS_HOST_FIELDS,
            **ECS_CLOUD_FIELDS,
            **ECS_APM_FIELDS,
            **ECS_HTTP_FIELDS,
        },
    }

    return subcategory_fields.get(sub_category, base)


def get_index_patterns(sub_category: str) -> List[str]:
    """Return the recommended Elasticsearch index patterns for a sub-category."""
    return SECURITY_INDEX_PATTERNS.get(sub_category, ["logs-*"])


def get_ilm_policy(use_case: str) -> Dict[str, Any]:
    """Return the ILM policy configuration for a given use case."""
    return ILM_POLICIES.get(use_case, ILM_POLICIES["security_logs"])


def get_mitre_tactic(tactic_id: str) -> Dict[str, str]:
    """Return MITRE ATT&CK tactic metadata by ID (e.g., 'TA0001')."""
    return MITRE_TACTICS.get(tactic_id, {})


def get_mitre_technique(technique_id: str) -> Dict[str, str]:
    """Return MITRE ATT&CK technique metadata by ID (e.g., 'T1078')."""
    return MITRE_TECHNIQUES.get(technique_id, {})


def get_compliance_controls(framework: str) -> Dict[str, Any]:
    """Return compliance framework controls for a given framework name."""
    return COMPLIANCE_FRAMEWORKS.get(framework, {})


def list_ip_fields(sub_category: str) -> List[str]:
    """Return all IP-type fields for a given sub-category (for FieldMapper)."""
    all_fields = get_fields_for_subcategory(sub_category)
    return [field for field, ftype in all_fields.items() if ftype == "ip"]


def get_severity_risk_score(severity: str) -> int:
    """Map severity label to Kibana risk score (0-100)."""
    mapping = {
        "low": 21,
        "medium": 47,
        "high": 73,
        "critical": 99,
    }
    return mapping.get(severity.lower(), 47)
