#!/usr/bin/env python3
"""
Script to add tool_metadata to T-Mobile demo queries
"""

# Query metadata based on JP Morgan pattern
# tool_id format: tmobile_netops_<purpose>
# description: 1-2 sentence summary focusing on business value
# tags: 5 relevant tags including "esql"

QUERY_METADATA = {
    # SCRIPTED QUERIES
    "Proactive Capacity Saturation Detection with Forecasting Indicators": {
        "tool_id": "tmobile_netops_capacity_saturation",
        "description": "Identifies cells approaching capacity limits using PRB utilization and subscriber concentration analysis. Calculates congestion risk scores against capacity tier baselines for proactive traffic optimization and expansion planning.",
        "tags": ["capacity", "congestion", "planning", "network", "esql"]
    },
    "Multi-Dimensional NOC Performance Benchmarking Dashboard": {
        "tool_id": "tmobile_netops_noc_benchmarking",
        "description": "Provides unified NOC performance dashboard with standardized KPIs across teams, vendors, and regions using FORK for parallel metric calculation. Enables executive benchmarking of NOC efficiency across 15+ regional teams.",
        "tags": ["noc", "performance", "benchmarking", "kpi", "esql"]
    },
    "Vendor Equipment Performance and Known Issues Analysis": {
        "tool_id": "tmobile_netops_vendor_analysis",
        "description": "Analyzes network performance by vendor equipment model to identify patterns and optimization opportunities. Correlates metrics with vendor baselines and equipment characteristics for data-driven vendor management.",
        "tags": ["vendor", "equipment", "performance", "optimization", "esql"]
    },
    "Regional Network Health Overview with Anomaly Detection": {
        "tool_id": "tmobile_netops_regional_health",
        "description": "Provides comprehensive regional network health overview combining cell metrics, incident counts, and ML anomaly detection. Enables regional NOC teams to quickly identify areas requiring attention.",
        "tags": ["regional", "health", "monitoring", "ml", "esql"]
    },
    "Incident Pattern Analysis by Root Cause and Vendor": {
        "tool_id": "tmobile_netops_incident_patterns",
        "description": "Analyzes incident patterns to identify recurring root causes by vendor, region, and type. Identifies systemic issues requiring vendor engagement or process improvements to reduce MTTR.",
        "tags": ["incidents", "root-cause", "patterns", "vendor", "esql"]
    },
    "Subscriber Session Quality and Failure Pattern Analysis": {
        "tool_id": "tmobile_netops_session_quality",
        "description": "Analyzes subscriber session quality patterns including experience scores, procedure failures, and transport performance. Identifies cells and APNs with poor subscriber experience for churn reduction.",
        "tags": ["subscribers", "quality", "experience", "sessions", "esql"]
    },
    "Technology Performance Comparison (LTE vs 5G NR vs LTE-A)": {
        "tool_id": "tmobile_netops_technology_comparison",
        "description": "Compares network performance across radio access technologies (LTE, 5G NR, LTE-A) to inform modernization priorities. Supports data-driven network modernization strategy and technology migration planning.",
        "tags": ["technology", "5g", "lte", "modernization", "esql"]
    },

    # PARAMETERIZED QUERIES
    "Subscriber-Centric IMSI Journey Root Cause Analysis": {
        "tool_id": "tmobile_netops_imsi_journey",
        "description": "Provides end-to-end subscriber network experience visibility by correlating session events across cells, procedures, and transport. Enables rapid troubleshooting reducing MTTD by 15-30 minutes.",
        "tags": ["subscribers", "troubleshooting", "sessions", "imsi", "esql"]
    },
    "Regional Performance Deep Dive with Anomaly Detection": {
        "tool_id": "tmobile_netops_regional_deepdive",
        "description": "Analyzes detailed network performance for specific regions with ML anomaly detection integration. Supports proactive capacity planning and congestion management for regional NOC teams.",
        "tags": ["regional", "performance", "ml", "capacity", "esql"]
    },
    "Subscriber Churn Risk Correlation with Network Experience": {
        "tool_id": "tmobile_netops_churn_risk",
        "description": "Identifies high-value subscribers at churn risk by correlating poor network experience with behavior profiles. Calculates retention priority scores for proactive retention interventions.",
        "tags": ["churn", "retention", "subscribers", "experience", "esql"]
    },
    "Vendor Performance Comparison and Issue Analysis": {
        "tool_id": "tmobile_netops_vendor_comparison",
        "description": "Compares network performance across vendors for specific time periods and technologies. Enables data-driven vendor management and SLA compliance monitoring.",
        "tags": ["vendor", "comparison", "performance", "sla", "esql"]
    },
    "Cell Site Performance Investigation with Incident History": {
        "tool_id": "tmobile_netops_cell_investigation",
        "description": "Deep dive analysis of specific cell sites including historical incidents, ML anomaly patterns, and subscriber impact. Reduces MTTR from 2-4 hours to under 30 minutes with comprehensive context.",
        "tags": ["cell-site", "investigation", "incidents", "troubleshooting", "esql"]
    },

    # RAG QUERIES
    "Cell Site Characteristics and Configuration Search": {
        "tool_id": "tmobile_netops_cell_search",
        "description": "Semantic search across cell site characteristics to find cells matching specific configurations, capacity, or deployment patterns. Enables rapid identification for capacity planning and optimization.",
        "tags": ["semantic-search", "cell-site", "configuration", "rag", "esql"]
    },
    "Network Incident Resolution Knowledge Search": {
        "tool_id": "tmobile_netops_incident_search",
        "description": "Semantic search across historical incident descriptions and resolution actions to find similar problems and proven solutions. Reduces MTTR by 30-90 minutes with instant access to resolution strategies.",
        "tags": ["semantic-search", "incidents", "resolution", "rag", "esql"]
    },
    "Vendor Equipment Known Issues and Optimization Search": {
        "tool_id": "tmobile_netops_vendor_search",
        "description": "Semantic search across vendor equipment known issues and optimization recommendations to identify equipment-specific problems and solutions. Accelerates vendor-specific troubleshooting and optimization.",
        "tags": ["semantic-search", "vendor", "optimization", "rag", "esql"]
    },
    "Subscriber Behavior Pattern and Segmentation Search": {
        "tool_id": "tmobile_netops_subscriber_search",
        "description": "Semantic search across subscriber behavior profiles to identify subscribers with specific usage patterns, device preferences, or risk characteristics. Supports targeted retention and personalized optimization.",
        "tags": ["semantic-search", "subscribers", "behavior", "rag", "esql"]
    },
    "Subscriber Session Quality Issue Investigation": {
        "tool_id": "tmobile_netops_session_search",
        "description": "Semantic search across subscriber session descriptions to find sessions with specific quality issues, procedure failures, or performance patterns. Enables rapid identification of experience problems.",
        "tags": ["semantic-search", "sessions", "quality", "rag", "esql"]
    }
}

print("T-Mobile Query Metadata Definitions")
print("=" * 80)
print(f"\nTotal queries with metadata: {len(QUERY_METADATA)}")
print("\nMetadata format for manual insertion:")
print("-" * 80)

for query_name, metadata in QUERY_METADATA.items():
    print(f'\n# {query_name}')
    print('"tool_metadata": {')
    print(f'    "tool_id": "{metadata["tool_id"]}",')
    print(f'    "description": "{metadata["description"]}",')
    print(f'    "tags": {metadata["tags"]}')
    print('},')
