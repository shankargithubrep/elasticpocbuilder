from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class TMobileDemoGuide(DemoGuideModule):
    """Demo guide for T-Mobile - Network Operations & Engineering"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        return '''# T-Mobile Network Operations & Engineering - Demo Guide

## Executive Summary

**Customer:** T-Mobile
**Department:** Network Operations & Engineering
**Industry:** Telecommunications - Mobile Network Operator
**Scale:** 50,000+ cell sites nationwide, 100M+ active subscribers, billions of signaling events daily

## Pain Points Addressed

1. **Fragmented Visibility** - Extended MTTR (2-4 hours) due to manual correlation across vendor-specific systems
2. **Reactive Operations** - 15-30 minute MTTD delays driven by subscriber complaints rather than proactive detection
3. **Batch Processing Delays** - 15-60 minute delays for high-cardinality network analytics
4. **No Unified Framework** - Lack of standardized KPIs preventing enterprise-wide benchmarking

## Demo Flow

### 1. Network Performance Overview
**Query:** Network Performance Metrics by Cell Site
**Purpose:** Establish baseline cell site performance with key KPIs
**Talk Track:** "Let's start with a real-time view of network performance across your cell sites. ES|QL allows us to aggregate billions of signaling events into actionable KPIs in milliseconds."

**Key Metrics:**
- Call success rate & drop rate
- RRC connection success
- Handover success rate
- PRB utilization (uplink/downlink)

### 2. Subscriber Experience Monitoring
**Query:** Subscriber-Centric Network Analysis
**Purpose:** Complete visibility into individual subscriber network experience
**Talk Track:** "When a subscriber calls with an issue, you need instant access to their complete network journey - not manual correlation across 15 different systems."

**Demonstrates:**
- End-to-end subscriber session tracking
- Real-time radio quality metrics (RSRP, RSRQ, SINR)
- Procedure success rates per subscriber

### 3. Anomaly Detection & Root Cause Analysis
**Query:** Network Anomaly Detection
**Purpose:** Proactive identification of performance degradation
**Talk Track:** "Rather than waiting for subscriber complaints, we detect anomalies in real-time - cell ID volatility, IMSI churn, procedure failures - reducing MTTD from 30+ minutes to under 5 minutes."

**Key Capabilities:**
- ML-driven anomaly detection
- Cell ID volatility tracking
- IMSI churn rate analysis
- Automated alerting on degradation patterns

### 4. Multi-Dimensional Performance Analysis
**Query:** Cell Site Performance Benchmarking
**Purpose:** Objective comparison across sites, vendors, regions, technologies
**Talk Track:** "Enable data-driven optimization by comparing performance across your entire network - which vendors perform best? Which cell sites need attention? Which regions are hitting capacity limits?"

**Demonstrates:**
- Cross-site benchmarking
- Vendor performance comparison
- Regional analytics
- Technology performance (4G vs 5G)

### 5. Capacity Planning & Congestion Management
**Query:** Network Capacity Utilization Analysis
**Purpose:** Proactive capacity planning before subscriber impact
**Talk Track:** "Use historical trending and predictive analytics to identify cells approaching capacity limits - preventing congestion before it impacts subscribers."

**Key Metrics:**
- Busy hour PRB utilization (P95)
- Capacity saturation indicators
- Growth trends by site

## Value Proposition

### Time Savings
- **MTTD Reduction:** 30+ minutes → <5 minutes (83% faster)
- **MTTR Reduction:** 2-4 hours → 15-30 minutes (75% faster)
- **Analytics Delay:** 15-60 minutes → Real-time

### Operational Impact
- **Proactive vs Reactive:** Detect issues before subscriber complaints
- **Unified View:** Single pane of glass replacing 15+ vendor systems
- **Standardized KPIs:** Enterprise-wide benchmarking framework

### Business Benefits
- Improved subscriber satisfaction (reduced complaint-driven troubleshooting)
- Faster time to resolution (reduced MTTR/MTTD)
- Data-driven network optimization decisions
- Reduced operational costs through automation

## Objection Handling

**"We already have vendor EMS systems"**
→ ES|QL provides unified analytics across all vendors - no more manual correlation between Nokia, Ericsson, Samsung systems

**"Our team doesn't know SQL"**
→ ES|QL syntax is SQL-like and easier than complex vendor-specific query languages. Most teams productive within days.

**"What about performance with billions of events?"**
→ Queries run on indexed data with millisecond response times. We've demonstrated real-time analytics on high-cardinality network data.

**"How do we handle multi-vendor environments?"**
→ Elastic ingests data from any source - vendor APIs, SNMP, syslog, file-based. Common schema enables cross-vendor analytics.

## Next Steps

1. **Proof of Concept:** 2-week pilot with 3 representative cell sites across vendors
2. **Integration Planning:** Map data sources (EMSs, probe systems, core network)
3. **Training:** 2-day workshop on ES|QL for NOC teams
4. **Production Rollout:** Phased deployment across regional NOCs

## Technical Requirements

- Elasticsearch cluster (self-managed or Elastic Cloud)
- Data ingestion from EMS systems (APIs, file-based, or streaming)
- Kibana for visualization and alerting
- ML nodes for anomaly detection

---

**Demo Duration:** 30-45 minutes
**Audience:** Network Operations leadership, NOC managers, Network Engineers
**Technical Depth:** Medium to High
'''

    def get_talk_track(self) -> Dict[str, str]:
        """Talk track for each query"""
        # Can be customized per demo as needed
        return {}

    def get_objection_handling(self) -> Dict[str, str]:
        """Common objections and responses"""
        return {
            "complexity": "ES|QL syntax is SQL-like and easier than complex aggregations",
            "performance": "Queries run on indexed data with millisecond response times",
            "learning_curve": "Most teams productive within days, not weeks"
        }
