# Customer Brand Analytics Demo

A comprehensive Agent Builder demo showcasing multi-dataset analytics for brand asset management, campaign performance tracking, and usage analytics.

## 📊 Demo Overview

**Use Case:** Marketing asset intelligence and campaign analytics  
**Complexity:** Medium-High  
**Duration:** 25-30 minutes  
**Audience:** Marketing teams, analytics teams, creative operations

### Business Problem

Customer manages hundreds of brand assets across multiple products, regions, and campaigns. Teams need to understand:
- Which assets drive the best campaign performance?
- How are internal teams using these assets?
- What's the ROI across different channels and audiences?
- Which high-potential assets are being underutilized?

Traditional approaches require data engineers and custom dashboards. This demo shows how Agent Builder enables natural language analytics across multiple interconnected datasets.

## 🎯 Key Features Demonstrated

1. **Multi-Dataset Joins** - Combining brand assets, campaign performance, and usage data
2. **Complex Aggregations** - Revenue, ROI, engagement metrics
3. **Time-Series Analysis** - Monthly trends and growth calculations
4. **Advanced Filtering** - Status-based filtering, date ranges, thresholds
5. **Calculated Fields** - ROI calculations, rate calculations, efficiency metrics
6. **Business Insights** - "Hidden gems" analysis, workflow optimization

## 📁 Datasets

### 1. Brand Assets (289 records)
Core asset metadata including:
- Asset ID, Name, Type (Image, Video, Document, etc.)
- Product Line, Region, Creative Format
- File Size, Creator, Status
- Creation and Last Modified dates

**Key Fields:**
- `Asset ID`: Unique identifier (joins to other datasets)
- `Asset Type`: Image, Video, Document, Graphic, Template
- `Product Line`: Photoshop, Illustrator, Premiere, XD, etc.
- `Region`: Americas, EMEA, APAC, Global
- `Status`: Active, Archived, In Review

### 2. Campaign Performance (1,157 records)
Campaign metrics and engagement:
- Campaign Name, Channel, Asset ID
- Impressions, Clicks, Conversions, Revenue, Spend
- Engagement Rate, Target Audience, Date

**Key Fields:**
- `Asset ID`: Links to Brand Assets
- `Campaign Name`: Marketing campaign identifier
- `Channel`: Social Media, Email, Display Ads, Video Ads, Search, Landing Page
- `Revenue`: Campaign revenue ($)
- `Spend`: Campaign spend ($)
- `Engagement Rate`: User engagement (%)

### 3. Usage Analytics (2,890 records)
Internal asset usage tracking:
- Asset ID, User, Department
- Action Type (Downloaded, Viewed, Approved, Edited, Shared)
- Timestamp, Duration (for views)

**Key Fields:**
- `Asset ID`: Links to Brand Assets
- `Department`: Marketing, Sales, Product, Creative, Customer Success, Engineering
- `Action Type`: Downloaded, Viewed, Approved, Edited, Shared
- `Timestamp`: When action occurred

### Data Relationships

```
Brand Assets (1) ←→ (Many) Campaign Performance [via Asset ID]
Brand Assets (1) ←→ (Many) Usage Analytics [via Asset ID]
```

## 🤖 Agent Definition

**Name:** `Customer-brand-analytics`  
**Display Name:** Customer Brand Analytics Assistant  
**Emoji:** 📊  
**Labels:** analytics, marketing, Customer, demo

**Capabilities:**
- Campaign ROI analysis
- Asset performance tracking
- Usage pattern analysis
- Channel performance comparison
- Trend identification
- Hidden gems discovery

See [agent-definition.yaml](./agent-definition.yaml) for complete configuration.

## 🛠️ Tools (8 tools)

1. **Campaign ROI Analysis** - Calculate and compare ROI across campaigns
2. **Channel Performance** - Analyze performance by marketing channel
3. **Hidden Gems** - Find underutilized assets with high potential
4. **Approval Workflow Efficiency** - Analyze approval process timing
5. **Monthly Performance Trends** - Track metrics over time
6. **Asset Type Performance** - Compare performance by asset type
7. **Audience Profitability** - Analyze profitability by target audience
8. **Department Usage Patterns** - Track how departments use assets

See [tools/](./tools/) directory for individual tool definitions.

## 📝 Demo Queries

### Simple Queries (Warm-up)

**Query 1: Campaign ROI Overview**
```esql
FROM campaign_performance
| EVAL roi = (Revenue - Spend) / Spend * 100
| STATS 
    total_spend = SUM(Spend),
    total_revenue = SUM(Revenue),
    avg_roi = AVG(roi)
  BY `Campaign Name`
| SORT avg_roi DESC
```

**Query 2: Channel Performance Comparison**
```esql
FROM campaign_performance
| STATS 
    total_revenue = SUM(Revenue),
    total_spend = SUM(Spend),
    avg_engagement = AVG(`Engagement Rate`),
    campaign_count = COUNT_DISTINCT(`Campaign Name`)
  BY Channel
| EVAL roi = (total_revenue - total_spend) / total_spend * 100
| SORT total_revenue DESC
```

### Join Queries (Building Complexity)

**Query 3: Asset Type Performance**
```esql
FROM brand_assets
| LOOKUP JOIN campaign_performance ON `Asset ID`
| EVAL revenue_per_impression = Revenue / Impressions * 1000
| STATS 
    total_revenue = SUM(Revenue),
    avg_engagement = AVG(`Engagement Rate`),
    campaigns = COUNT_DISTINCT(`Campaign Name`)
  BY `Asset Type`, Status
| WHERE Status == "Active"
| SORT total_revenue DESC
```

### Advanced Queries (The "Wow" Moments)

**Query 4: Hidden Gems (Underutilized High Performers)**
```esql
FROM brand_assets
| LOOKUP JOIN campaign_performance ON `Asset ID`
| LOOKUP JOIN usage_analytics ON `Asset ID`
| WHERE Status == "Active"
| STATS 
    avg_roi = AVG((Revenue - Spend) / Spend * 100),
    total_revenue = SUM(Revenue),
    usage_count = COUNT(),
    campaigns = COUNT_DISTINCT(`Campaign Name`)
  BY `Asset ID`, `Asset Name`, `Asset Type`
| WHERE avg_roi > 200 AND usage_count < 10 AND campaigns < 3
| EVAL potential_score = avg_roi * (1 + total_revenue / 10000)
| SORT potential_score DESC
| LIMIT 10
```

**Query 5: Monthly Performance Trends**
```esql
FROM campaign_performance
| EVAL month = DATE_TRUNC(1 month, TO_DATETIME(Date))
| STATS 
    monthly_revenue = SUM(Revenue),
    monthly_spend = SUM(Spend),
    avg_engagement = AVG(`Engagement Rate`)
  BY month, Channel
| SORT month ASC
```

See [queries/](./queries/) directory for all 8 queries with documentation.

## 🚀 Setup Instructions

### Prerequisites

- Elasticsearch cluster with Agent Builder enabled
- Kibana access
- Permissions to create data views and agents

### Step 1: Generate and Index Data

1. Open [datasets/generator.html](./datasets/generator.html) in a web browser
2. Click each "Generate & Download" button to create CSVs:
   - Brand Assets (289 records)
   - Campaign Performance (1,157 records)
   - Usage Analytics (2,890 records)
3. In Kibana, navigate to **Management > Stack Management > Data Views**
4. Upload each CSV file using **Machine Learning > Data Visualizer**
5. Create data views for each dataset:
   - `brand_assets`
   - `campaign_performance`
   - `usage_analytics`

### Step 2: Test Queries

1. Open **Kibana > Discover**
2. Switch to ES|QL mode
3. Test each query from the [queries/](./queries/) directory
4. Verify results match expected outputs
5. Note any required adjustments for your cluster

### Step 3: Create Agent and Tools

1. Navigate to **Elasticsearch > Agent Builder**
2. Click **Create Agent**
3. Use configuration from [agent-definition.yaml](./agent-definition.yaml)
4. Create each tool using definitions from [tools/](./tools/)
5. Assign all tools to the agent
6. Test in Agent Playground

### Step 4: Prepare Presentation

1. Copy [Google Slides template](https://docs.google.com/presentation/d/1LQxSxOS3tgoRbVO5FD7zdaTn8KoCzeStEwWBUbBLuxA/edit?usp=sharing)
2. Update slides with content from [slides-content.md](./slides-content.md)
3. Add your branding and screenshots
4. Review [demo-script.md](./demo-script.md) for talking points

## 🎬 Demo Flow

**Total Duration:** 25-30 minutes

1. **Introduction** (3-5 min)
   - Business problem and context
   - Dataset overview
   - Agent Builder value proposition

2. **AI Agent Teaser** (5 min)
   - "Show me underutilized assets with high potential"
   - Demonstrate the end result first

3. **ES|QL Query Building** (10 min)
   - Start simple: Basic aggregations
   - Add complexity: EVAL and calculated fields
   - Show joins: Multi-dataset analysis
   - End with hidden gems query

4. **Agent & Tool Creation** (5 min)
   - Show agent configuration
   - Show tool creation
   - Explain how agent selects tools

5. **AI Agent Q&A** (5-7 min)
   - Ask various business questions
   - Show natural language understanding
   - Demonstrate multi-dataset insights

6. **Wrap-up & Q&A** (3-5 min)

## 📋 Demo Questions

### Campaign Performance
- "What's the ROI for each campaign?"
- "Which channel is most profitable?"
- "Show me campaigns with negative ROI"

### Asset Intelligence
- "Which asset types generate the most revenue?"
- "Show me underutilized assets with high potential"
- "What's the performance of video assets vs images?"

### Usage Patterns
- "How efficient are our approval workflows?"
- "Which departments use which asset types?"
- "Show me the most downloaded assets"

### Trends
- "What are the month-over-month revenue trends?"
- "Which audience segments are most profitable?"
- "How has engagement changed over time?"

## 🎓 Key Teaching Points

### ES|QL Capabilities
- **EVAL** for calculated fields (ROI, rates, scores)
- **STATS** for aggregations (SUM, AVG, COUNT)
- **LOOKUP JOIN** for combining datasets
- **WHERE** for filtering
- **DATE_TRUNC** for time bucketing
- **SORT** and **LIMIT** for result control

### Agent Builder Features
- Natural language to ES|QL translation
- Automatic tool selection
- Multi-dataset analysis
- Complex query generation
- Business context understanding

### Business Value
- Self-service analytics (no SQL required)
- Real-time insights
- Data democratization
- Faster decision-making
- Reduced dependency on data teams

## 🐛 Troubleshooting

### Common Issues

**Query fails with "field not found"**
- Verify field names match your data view exactly
- Check for extra spaces or special characters
- ES|QL is case-sensitive

**Join returns no results**
- Verify Asset IDs match across datasets
- Check data types (string vs number)
- Use WHERE to filter after join if needed

**Agent doesn't select the right tool**
- Refine tool descriptions to be more specific
- Improve agent instructions
- Test with different question phrasings

**Data looks unrealistic**
- Regenerate with different parameters
- Adjust distributions in generator.html
- Verify relationships between datasets

See [../../reference/troubleshooting.md](../../reference/troubleshooting.md) for more solutions.

## 📊 Success Metrics

This demo has been delivered successfully to:
- **Customer:** Customer (original)
- **Audience:** Marketing Analytics team
- **Feedback:** Positive, led to follow-up technical discussion
- **Outcome:** PoC engagement

## 🔄 Variations

This demo can be adapted for:
- **E-commerce:** Product analytics, inventory, customer behavior
- **Media:** Content performance, audience engagement, distribution
- **Healthcare:** Patient outcomes, resource utilization, cost analysis
- **Financial Services:** Transaction analysis, risk assessment, customer segments

## 📚 Additional Resources

- [ES|QL Patterns Reference](../../reference/esql-patterns.md)
- [Best Practices Guide](../../reference/best-practices.md)
- [Troubleshooting Guide](../../reference/troubleshooting.md)
- [Google Slides Template](https://docs.google.com/presentation/d/1LQxSxOS3tgoRbVO5FD7zdaTn8KoCzeStEwWBUbBLuxA/edit?usp=sharing)
- [Demo Script Template](https://docs.google.com/document/d/1KQfnZHL6qDJx_-NzyDsUfYKWXg88BKE0-1EDiMt7zYs/edit?usp=sharing)

## 💡 Tips for Success

1. **Practice the queries** - Know them well before the demo
2. **Customize to your audience** - Use their terminology and pain points
3. **Start with the wow** - Lead with the hidden gems query
4. **Tell a story** - Connect insights to business decisions
5. **Leave time for questions** - The best demos spark conversations

---

**Created by:** Elastic Solutions Architecture  
**Last Updated:** October 2025  
**Status:** Production Ready ✅
