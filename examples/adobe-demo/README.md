# Adobe Brand Asset Analytics Demo

## Overview

This demo showcases Elastic Agent Builder's capabilities for Adobe's brand asset management and campaign analytics use case. It demonstrates how AI-powered tools can provide instant insights across multiple interconnected datasets.

## Demo Components

### 📊 Datasets

1. **brand_assets** (289 records)
   - Core inventory of brand assets
   - Fields: Asset ID, Product Name, Asset Type, Status, Region
   - Configured as lookup index for efficient joins

2. **campaign_performance** (~11,000 records)
   - Daily campaign metrics across channels
   - Fields: Performance ID, Campaign Name, Asset ID, Impressions, Clicks, Revenue
   - Time range: Jan 2024 - Jun 2025

3. **asset_usage_events** (~16,000 records)
   - Internal usage and workflow tracking
   - Fields: Event ID, Asset ID, Action Type, Department, User ID
   - Tracks downloads, views, approvals

### 🔍 ES|QL Queries / Agent Tools

The demo includes 8 sophisticated ES|QL queries packaged as Agent Builder tools:

1. **Campaign ROI Analysis** - ROI by campaign and asset type
2. **Channel Performance** - Regional performance with CTR/CVR metrics
3. **Hidden Gems Discovery** - Underutilized high-potential assets
4. **Approval Workflow Efficiency** - Department approval metrics
5. **Monthly Trends** - Time-series performance analysis
6. **Asset Type Rankings** - Performance by creative format
7. **Audience Profitability** - Segment efficiency scoring
8. **Department Usage** - Internal adoption patterns

### 🤖 Agent Configuration

**Agent Name**: Brand Asset Performance Intelligence

**Agent Description**: AI-powered analytics for brand asset management and campaign optimization

**Custom Instructions**: Expert in brand analytics, focusing on ROI, asset utilization, and cross-functional insights

## Key Demo Points

### Business Value
- Reduces analysis time from hours to seconds
- Democratizes data access for non-technical users
- Provides real-time, actionable insights
- Identifies optimization opportunities automatically

### Technical Highlights
- Complex multi-table joins with LOOKUP JOIN
- Advanced aggregations and window functions
- Handling of time-series data
- Automatic type conversion (TO_DOUBLE for percentages)

## Demo Flow

### Part 1: The Magic (5 min)
Start with the AI agent already configured:
```
User: "Show me underutilized assets with high potential"
```
The agent instantly identifies hidden gems using complex 3-way joins.

### Part 2: Under the Hood (10 min)
Build ES|QL queries progressively:
1. Simple aggregation (revenue by campaign)
2. Add calculations (ROI with EVAL)
3. Join datasets (enrich with asset metadata)
4. Complex analytics (hidden gems query)

### Part 3: Configuration (5 min)
Show how to create the agent and tools in Agent Builder UI

### Part 4: Q&A Session (5-10 min)
Let stakeholders ask natural language questions

## Sample Questions for Demo

### Performance & ROI
- "Which campaigns have the best ROI?"
- "What's driving revenue in North America?"
- "Show me underperforming campaigns"

### Optimization
- "Which assets should we retire?"
- "What content types perform best?"
- "Find quick wins for next quarter"

### Operations
- "How efficient are our approval workflows?"
- "Which departments use video assets most?"
- "Show bottlenecks in creative pipeline"

## Success Metrics

- **Query Performance**: All queries execute in <500ms
- **Data Freshness**: Real-time data updates
- **Accuracy**: 100% validated query results
- **User Adoption**: Natural language accessible

## Files in This Demo

```
adobe-demo/
├── README.md                 # This file
├── data/
│   ├── brand-assets.csv     # Core asset inventory
│   ├── campaign-performance.csv  # Campaign metrics
│   └── asset-usage.csv      # Usage events
├── queries/
│   └── esql_queries.json    # All 8 ES|QL queries
├── agent_config.json        # Agent Builder configuration
├── demo_guide.md           # Presenter script
└── validation_report.json  # Query validation results
```

## Setup Instructions

1. **Upload Data**
   ```bash
   # Create indices with proper mappings
   PUT /brand-assets {"settings": {"index.mode": "lookup"}}
   # Upload CSVs via Kibana
   ```

2. **Create Agent**
   - Navigate to Agent Builder UI
   - Import agent_config.json
   - Configure each tool with ES|QL queries

3. **Validate**
   - Run validation suite
   - Confirm all queries return results
   - Test natural language interactions

## Customization Tips

- **Industry Adaptation**: Replace "brand assets" with industry-specific entities
- **Metrics Focus**: Adjust KPIs based on customer priorities
- **Time Range**: Modify date ranges for relevance
- **Data Volume**: Scale up/down based on demo environment

## Troubleshooting

### Common Issues

1. **Integer Division Returns 0**
   - Solution: Use TO_DOUBLE() for decimal results
   ```esql
   EVAL ctr = TO_DOUBLE(Clicks) / Impressions * 100
   ```

2. **JOIN Fails - Column Not Found**
   - Solution: Ensure JOIN happens before aggregation
   ```esql
   FROM campaign-performance
   | LOOKUP JOIN brand-assets ON `Asset ID`  # JOIN FIRST
   | STATS ... BY `Asset Type`               # Then aggregate
   ```

3. **Lookup Index Error**
   - Solution: Set index.mode during creation
   ```json
   {"settings": {"index.mode": "lookup"}}
   ```

## Demo Success Checklist

- [ ] All data uploaded successfully
- [ ] Indices created with correct mappings
- [ ] All 8 queries validated
- [ ] Agent configured and responding
- [ ] Demo guide reviewed
- [ ] Backup plan prepared
- [ ] Customer context incorporated

## Contact

For questions or improvements to this demo:
- Slack: #agent-builder-demos
- Email: sa-tools@elastic.co

---

*This demo was auto-generated by the Elastic Demo Builder platform*