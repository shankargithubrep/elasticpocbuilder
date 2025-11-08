# Elastic Agent Builder Demo for Adobe
## Internal Demo Script & Reference Guide

---

## 📋 Demo Overview

**Total Time:** 25-30 minutes
**Audience:** Adobe technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on brand asset data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## 🗂️ Dataset Architecture

### **Dataset 1: brand_assets.csv** (Your existing data)
- **289 records** - Brand asset inventory
- **Primary Key**: `Asset ID` (BA-1001 through BA-1289)
- **Fields**: 
  - Asset ID (Primary Key)
  - Product Name - Product line association
  - Asset Type - Logo, Video, Banner, Font, etc. (17 types)
  - Description - Text description of the asset
  - Deployment Date - When first deployed
  - Status - Active, Archived, In Review, Retired
  - Region - Global, EMEA, APAC, North America, LATAM
  - File Path - Internal storage location
  - Usage Guidelines - Usage restrictions/guidelines
  - Associated Campaign - Original campaign assignment

### **Dataset 2: campaign_performance.csv** (Generated)
- **~11,000 records** - Campaign performance metrics
- **Relationships**: Links to brand_assets via Asset ID and Campaign Name
- **Fields**: Performance ID, Campaign Name, Asset ID, Date, Channel, Region, Audience Segment, Impressions, Clicks, Conversions, Engagement Rate, Conversion Rate, Spend, Revenue
- **Time Range**: Jan 2024 - Jun 2025 (18 months)

### **Dataset 3: asset_usage_events.csv** (Generated)
- **~16,000 records** - Asset usage and workflow tracking
- **Relationships**: Links to brand_assets via Asset ID
- **Fields**: Event ID, Asset ID, Timestamp, Action Type, User ID, Department, Device Type, Duration Seconds, Session ID
- **Time Range**: Jan 2024 - Jun 2025 (18 months)

---

## 🚀 Demo Setup Instructions

### Step 1: Prepare Your Datasets
1. **Use your existing brand_assets.csv** (289 records already created)
2. **Generate the two new datasets** using the interactive app
3. Save all three files in an accessible location

### Step 2: Create Elasticsearch Indices

**CRITICAL: brand_assets must use lookup mode for joins to work**

```bash
# Create brand_assets index with lookup mode
PUT /brand-assets
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "Asset ID": { "type": "keyword" },
      "Product Name": { "type": "keyword" },
      "Asset Type": { "type": "keyword" },
      "Description": { "type": "text" },
      "Deployment Date": { "type": "date" },
      "Status": { "type": "keyword" },
      "Region": { "type": "keyword" },
      "File Path": { "type": "keyword" },
      "Usage Guidelines": { "type": "text" },
      "Associated Campaign": { "type": "keyword" }
    }
  }
}

# Create campaign_performance index
PUT /campaign-performance
{
  "mappings": {
    "properties": {
      "Performance ID": { "type": "keyword" },
      "Campaign Name": { "type": "keyword" },
      "Asset ID": { "type": "keyword" },
      "Date": { "type": "date" },
      "Channel": { "type": "keyword" },
      "Region": { "type": "keyword" },
      "Audience Segment": { "type": "keyword" },
      "Impressions": { "type": "long" },
      "Clicks": { "type": "long" },
      "Conversions": { "type": "long" },
      "Engagement Rate": { "type": "double" },
      "Conversion Rate": { "type": "double" },
      "Spend": { "type": "double" },
      "Revenue": { "type": "double" }
    }
  }
}

# Create asset_usage_events index
PUT /asset-usage
{
  "mappings": {
    "properties": {
      "Event ID": { "type": "keyword" },
      "Asset ID": { "type": "keyword" },
      "Timestamp": { "type": "date" },
      "Action Type": { "type": "keyword" },
      "User ID": { "type": "keyword" },
      "Department": { "type": "keyword" },
      "Device Type": { "type": "keyword" },
      "Duration Seconds": { "type": "long" },
      "Session ID": { "type": "keyword" }
    }
  }
}
```

Then bulk import your CSV data into each index.

---

## Part 1: AI Agent Chat Teaser (5 minutes)

### Setup
- Navigate to your AI Agent chat interface
- Have the agent already configured with all 8 tools

### Demo Script

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question that would normally require a data analyst hours to answer."

**Type in chat:**
```
Show me underutilized assets with high potential
```

**Wait for response, then narrate:**

"Notice what just happened:
1. The agent understood my business intent - 'underutilized' and 'high potential'
2. It selected the right tool from 8 available options
3. It executed a complex ES|QL query joining THREE datasets
4. It returned actionable insights in seconds

This query is:
- Analyzing 16,000 usage events
- Joining with 11,000 campaign performance records
- Enriching with 289 asset metadata records
- Computing composite engagement scores
- All in real-time"

**Ask 2-3 more questions to show versatility:**

```
Which campaigns have the best ROI?
```

```
How efficient are our approval workflows by department?
```

```
What are the monthly revenue trends?
```

**Transition:**
"So how does this actually work? Let's go under the hood and build these queries from scratch."

---

## Part 2: ES|QL Query Building (10 minutes)

### Setup
- Open Kibana Dev Tools Console
- Have the three indices already created and populated
- Clear the console for a fresh start

---

### Query 1: Simple Aggregation (2 minutes)

**Presenter:** "Let's start simple. Adobe wants to know: What's the total revenue by campaign?"

**Copy/paste into console:**
```esql
FROM campaign-performance
| STATS total_revenue = SUM(Revenue) BY `Campaign Name`
| SORT total_revenue DESC
| LIMIT 10
```

**Run and narrate results:**
"This is basic ES|QL:
- FROM: Source our data from the campaign-performance index
- STATS: Aggregate using SUM, group BY campaign name
- SORT and LIMIT: Top 10 campaigns by revenue

The syntax is intuitive - it reads like English. Now let's add some calculations."

---

### Query 2: Add Calculations with EVAL (3 minutes)

**Presenter:** "Revenue is great, but Adobe needs ROI. Let's calculate that."

**Copy/paste:**
```esql
FROM campaign-performance
| EVAL roi = TO_DOUBLE(Revenue - Spend) / Spend * 100
| STATS 
    total_spend = SUM(Spend),
    total_revenue = SUM(Revenue),
    avg_roi = AVG(roi),
    total_conversions = SUM(Conversions)
  BY `Campaign Name`
| EVAL roi_percentage = TO_DOUBLE(total_revenue - total_spend) / total_spend * 100
| SORT roi_percentage DESC
| LIMIT 10
```

**Run and highlight:**
"Key additions:
- EVAL: Creates calculated fields on-the-fly
- TO_DOUBLE: Critical for decimal division - ES|QL does integer division by default
- Multiple STATS: We're aggregating spend, revenue, conversions, AND calculating average ROI
- Second EVAL: Computing overall ROI percentage after aggregation

Look at the results - we can immediately see which campaigns are most efficient with budget."

---

### Query 3: Join Datasets with LOOKUP JOIN (3 minutes)

**Presenter:** "But wait - Adobe wants to know WHICH ASSET TYPES are driving these results. That data lives in a different index. This is where ES|QL's JOIN capability shines."

**Copy/paste:**
```esql
FROM campaign-performance
| LOOKUP JOIN brand-assets ON `Asset ID`
| EVAL roi = TO_DOUBLE(Revenue - Spend) / Spend * 100
| STATS 
    total_spend = SUM(Spend),
    total_revenue = SUM(Revenue),
    avg_roi = AVG(roi),
    total_conversions = SUM(Conversions)
  BY `Campaign Name`, `Asset Type`
| EVAL roi_percentage = TO_DOUBLE(total_revenue - total_spend) / total_spend * 100
| SORT roi_percentage DESC
| LIMIT 15
```

**Run and explain:**
"Magic happening here:
- LOOKUP JOIN: Combines campaign-performance with brand-assets using Asset ID
- Now we have access to ALL fields from brand-assets (Product Name, Asset Type, Status, etc.)
- GROUP BY includes Asset Type: Now we see ROI broken down by both campaign AND creative format
- This is a LEFT JOIN: All campaign records are kept, enriched with asset metadata

Look at the results - we can see that certain asset types (like Video Intro/Outro) perform better than others (like Email Signatures)."

**Important callout:**
"For LOOKUP JOIN to work, the brand-assets index must be created with 'index.mode: lookup' setting. This is Elastic's optimized join mode."

---

### Query 4: Complex Multi-Dataset Analytics - Hidden Gems (2 minutes)

**Presenter:** "Now for the grand finale - the 'Hidden Gems' query. This answers: Which assets are popular with our teams internally but haven't been used much in campaigns? These are quick wins - proven assets ready for broader deployment."

**Copy/paste:**
```esql
FROM campaign-performance
| STATS 
    avg_engagement = AVG(`Engagement Rate`),
    total_conversions = SUM(Conversions),
    total_revenue = SUM(Revenue),
    campaign_count = COUNT_DISTINCT(`Campaign Name`)
  BY `Asset ID`
| LOOKUP JOIN asset-usage ON `Asset ID`
| WHERE `Action Type` IN ("Download", "View", "Share")
| STATS 
    max_avg_engagement = MAX(avg_engagement),
    max_conversions = MAX(total_conversions),
    max_revenue = MAX(total_revenue),
    max_campaigns = MAX(campaign_count),
    internal_usage = COUNT(*)
  BY `Asset ID`
| WHERE internal_usage > 15 AND max_campaigns < 5
| EVAL engagement_score = max_avg_engagement * internal_usage
| LOOKUP JOIN brand-assets ON `Asset ID`
| KEEP `Asset ID`, `Product Name`, `Asset Type`, internal_usage, max_avg_engagement, max_campaigns, engagement_score
| SORT engagement_score DESC
| LIMIT 20
```

**Run and break down:**
"This is a sophisticated analytical query:

**Step 1:** Aggregate campaign performance metrics by Asset ID
- Get average engagement, conversions, revenue, campaign count

**Step 2:** Join with usage events to count internal usage
- Filter to meaningful actions (download, view, share)
- Count how many times teams have used each asset

**Step 3:** Find the sweet spot
- Assets with >15 internal usage events (teams like them)
- But <5 campaign deployments (underutilized externally)

**Step 4:** Create a composite score
- engagement_score = avg_engagement × internal_usage
- Balances campaign performance with internal popularity

**Step 5:** Enrich with brand asset metadata
- Final join to get Product Name and Asset Type for context

The result? A prioritized list of 'hidden gems' - assets that teams already love that could drive great campaign results."

---

## Part 3: Agent & Tool Creation (5 minutes)

### Creating the Agent

**Show Agent Settings screen and walk through:**

**Agent ID:**
```
adobe-brand-analytics-agent
```

**Display Name:**
```
Brand Asset Performance Intelligence
```

**Display Description:**
```
AI-powered analytics agent that provides insights into brand asset performance, campaign ROI, and cross-departmental usage patterns. Query campaign metrics, asset utilization, and workflow efficiency using natural language.
```

**Custom Instructions:**
```
You are an expert brand analytics assistant for Adobe, specializing in brand asset management and campaign performance analysis. You have access to three interconnected datasets:

1. Brand Assets - 289 creative assets across multiple product lines
2. Campaign Performance - Marketing campaign metrics across channels and regions
3. Asset Usage Events - Internal team usage and workflow tracking

Your capabilities:
- Analyze campaign ROI and performance trends
- Identify high-performing assets and asset types
- Find "hidden gems" - assets popular internally but underutilized in campaigns
- Track approval workflows and department usage patterns
- Provide cross-regional and cross-channel insights
- Generate actionable recommendations for asset optimization

Response guidelines:
- Provide clear, actionable insights
- Include specific metrics and data points
- Suggest next steps or recommendations when relevant
- Format responses with clear headers and bullet points for readability
- When showing multiple results, prioritize by business impact

Available data spans: January 2024 - June 2025

Always be precise with data, cite specific metrics, and focus on business value.
```

**Narrate:**
"The custom instructions are critical - they tell the agent:
- What domain it's operating in (brand analytics for Adobe)
- What data it has access to
- How to behave and format responses
- What kind of insights to prioritize"

---

### Creating Tools - All 8 ES|QL Queries

#### Tool 1: Campaign ROI Analysis

**Tool ID:** `adobe.campaign_roi_analysis`

**Description:**
```
Analyzes campaign ROI and performance metrics by campaign name and asset type. Shows total spend, revenue, conversions, and ROI percentage. Use when users ask about campaign profitability, which campaigns are most successful, or ROI comparisons.
```

**Labels:** `campaign, roi, revenue, performance`

**ES|QL Query:**
```esql
FROM campaign-performance
| LOOKUP JOIN brand-assets ON `Asset ID`
| EVAL roi = TO_DOUBLE(Revenue - Spend) / Spend * 100
| STATS 
    total_spend = SUM(Spend),
    total_revenue = SUM(Revenue),
    avg_roi = AVG(roi),
    total_conversions = SUM(Conversions)
  BY `Campaign Name`, `Asset Type`
| EVAL roi_percentage = TO_DOUBLE(total_revenue - total_spend) / total_spend * 100
| SORT roi_percentage DESC
| LIMIT 10
```

---

#### Tool 2: Channel Performance by Region

**Tool ID:** `adobe.channel_performance_regional`

**Description:**
```
Analyzes channel and region performance including CTR, CVR, impressions, and revenue. Use when users ask about which channels work best, regional performance differences, or cross-channel comparisons.
```

**Labels:** `channel, region, ctr, engagement`

**ES|QL Query:**
```esql
FROM campaign-performance
| WHERE Date >= "2024-06-01" AND Date <= "2025-06-30"
| EVAL ctr = TO_DOUBLE(Clicks) / Impressions * 100
| EVAL cvr = TO_DOUBLE(Conversions) / Clicks * 100
| STATS 
    total_impressions = SUM(Impressions),
    avg_ctr = AVG(ctr),
    avg_cvr = AVG(cvr),
    total_revenue = SUM(Revenue)
  BY Region, Channel
| WHERE total_impressions > 100000
| SORT total_revenue DESC
```

---

#### Tool 3: Hidden Gems Analysis

**Tool ID:** `adobe.hidden_gems_analysis`

**Description:**
```
Identifies assets with high internal team usage but low campaign deployment - "hidden gems" ready for broader use. Includes engagement score ranking. Use when users ask about underutilized assets, internal favorites, or optimization opportunities.
```

**Labels:** `optimization, hidden-gems, asset-usage, recommendations`

**ES|QL Query:**
```esql
FROM campaign-performance
| STATS 
    avg_engagement = AVG(`Engagement Rate`),
    total_conversions = SUM(Conversions),
    total_revenue = SUM(Revenue),
    campaign_count = COUNT_DISTINCT(`Campaign Name`)
  BY `Asset ID`
| LOOKUP JOIN asset-usage ON `Asset ID`
| WHERE `Action Type` IN ("Download", "View", "Share")
| STATS 
    max_avg_engagement = MAX(avg_engagement),
    max_conversions = MAX(total_conversions),
    max_revenue = MAX(total_revenue),
    max_campaigns = MAX(campaign_count),
    internal_usage = COUNT(*)
  BY `Asset ID`
| WHERE internal_usage > 15 AND max_campaigns < 5
| EVAL engagement_score = max_avg_engagement * internal_usage
| LOOKUP JOIN brand-assets ON `Asset ID`
| KEEP `Asset ID`, `Product Name`, `Asset Type`, internal_usage, max_avg_engagement, max_campaigns, engagement_score
| SORT engagement_score DESC
| LIMIT 20
```

---

#### Tool 4: Approval Workflow Efficiency

**Tool ID:** `adobe.approval_workflow_efficiency`

**Description:**
```
Tracks approval workflow metrics by department including submission counts, approval rates, and rejection rates. Use when users ask about approval processes, workflow efficiency, or department-specific approval patterns.
```

**Labels:** `workflow, approvals, department, efficiency`

**ES|QL Query:**
```esql
FROM asset-usage
| WHERE `Action Type` IN ("Approval Submitted", "Approved", "Rejected")
| EVAL approval_status = CASE(
    `Action Type` == "Approved", "Approved",
    `Action Type` == "Rejected", "Rejected",
    "Pending"
  )
| STATS 
    total_submissions = COUNT(*),
    approved = COUNT(CASE(`Action Type` == "Approved", 1)),
    rejected = COUNT(CASE(`Action Type` == "Rejected", 1))
  BY Department
| EVAL approval_rate = TO_DOUBLE(approved) / total_submissions * 100
| SORT approval_rate DESC
```

---

#### Tool 5: Monthly Performance Trends

**Tool ID:** `adobe.monthly_performance_trends`

**Description:**
```
Shows time-series analysis of monthly spend, revenue, engagement, and conversions with month-over-month growth calculations. Use when users ask about trends, historical performance, or seasonal patterns.
```

**Labels:** `trends, time-series, monthly, growth`

**ES|QL Query:**
```esql
FROM campaign-performance
| EVAL month = DATE_TRUNC(1 month, TO_DATETIME(Date))
| EVAL roi = TO_DOUBLE(Revenue - Spend) / Spend * 100
| STATS 
    monthly_spend = SUM(Spend),
    monthly_revenue = SUM(Revenue),
    avg_engagement = AVG(`Engagement Rate`),
    total_conversions = SUM(Conversions),
    avg_roi = AVG(roi)
  BY month
| SORT month ASC
```

---

#### Tool 6: Asset Type Performance Ranking

**Tool ID:** `adobe.asset_type_performance`

**Description:**
```
Ranks asset types by total revenue, engagement, and campaign usage. Shows which creative formats drive best results. Use when users ask about asset type effectiveness or content format recommendations.
```

**Labels:** `asset-type, ranking, creative, format`

**ES|QL Query:**
```esql
FROM campaign-performance
| LOOKUP JOIN brand-assets ON `Asset ID`
| EVAL revenue_per_impression = TO_DOUBLE(Revenue) / Impressions * 1000
| STATS 
    total_campaigns = COUNT_DISTINCT(`Campaign Name`),
    total_revenue = SUM(Revenue),
    avg_engagement = AVG(`Engagement Rate`),
    avg_revenue_per_1k = AVG(revenue_per_impression)
  BY `Asset Type`, Status
| WHERE Status == "Active"
| SORT total_revenue DESC
| LIMIT 15
```

---

#### Tool 7: Audience Segment Profitability

**Tool ID:** `adobe.audience_segment_profitability`

**Description:**
```
Analyzes profitability metrics by audience segment and channel including cost per conversion, revenue per conversion, and efficiency scores. Use when users ask about audience targeting, segment performance, or optimization strategies.
```

**Labels:** `audience, profitability, targeting, efficiency`

**ES|QL Query:**
```esql
FROM campaign-performance
| WHERE Date >= "2024-01-01"
| WHERE Conversions > 0
| EVAL cost_per_conversion = TO_DOUBLE(Spend) / Conversions
| EVAL revenue_per_conversion = TO_DOUBLE(Revenue) / Conversions
| EVAL profit_margin = TO_DOUBLE(Revenue - Spend) / Revenue * 100
| STATS 
    total_conversions = SUM(Conversions),
    avg_cpc = AVG(cost_per_conversion),
    avg_revenue_per_conv = AVG(revenue_per_conversion),
    avg_profit_margin = AVG(profit_margin),
    total_profit = SUM(Revenue - Spend)
  BY `Audience Segment`, Channel
| WHERE total_conversions > 100
| EVAL efficiency_score = (avg_revenue_per_conv / avg_cpc) * avg_profit_margin
| SORT efficiency_score DESC
```

---

#### Tool 8: Department Asset Usage

**Tool ID:** `adobe.department_asset_usage`

**Description:**
```
Shows which asset types are most popular across departments, including total usage, unique users, and cross-departmental adoption. Use when users ask about internal usage patterns or team preferences.
```

**Labels:** `department, usage, internal, adoption`

**ES|QL Query:**
```esql
FROM asset-usage
| STATS 
    usage_count = COUNT(*),
    unique_users = COUNT_DISTINCT(`User ID`)
  BY Department, `Asset ID`
| LOOKUP JOIN brand-assets ON `Asset ID`
| STATS 
    total_usage = SUM(usage_count),
    total_users = SUM(unique_users),
    departments_using = COUNT_DISTINCT(Department)
  BY `Asset Type`
| EVAL avg_usage_per_dept = TO_DOUBLE(total_usage) / departments_using
| SORT total_usage DESC
| LIMIT 15
```

---

## Part 4: AI Agent Q&A Session (5-10 minutes)

### Demo Question Set

**Warm-up:**
```
What campaigns are performing best?
```

**Cross-tool reasoning:**
```
Which campaigns have the best ROI, and what asset types are they using?
```

**Business-focused:**
```
We're planning Q4 campaigns. What insights can help us optimize?
```

```
The creative team wants to know what content to prioritize. Any recommendations?
```

```
Help me identify quick wins - what should we focus on?
```

**Department-specific:**
```
How efficient are our approval workflows? Which departments need improvement?
```

```
Which asset types are most popular across different departments?
```

**Trend analysis:**
```
Show me monthly revenue trends. Are we growing or declining?
```

```
Which audience segments are most profitable? Should we shift our targeting?
```

**Regional insights:**
```
Our North America performance seems low. What's happening there?
```

**Asset optimization:**
```
Which assets should we retire and which should we amplify?
```

---

## 🎯 Key Talking Points

### On ES|QL:
- "Modern query language, built for analytics"
- "Piped syntax is intuitive and readable"
- "Operates on blocks, not rows - extremely performant"
- "Supports complex operations: joins, window functions, time-series"

### On Agent Builder:
- "Bridges AI and enterprise data"
- "No custom development - configure, don't code"
- "Works with existing Elasticsearch indices"
- "Agent automatically selects right tools"

### On Business Value:
- "Democratizes data access - anyone can ask questions"
- "Real-time insights, always up-to-date"
- "Reduces dependency on data teams"
- "Faster decision-making"

---

## 🔧 Troubleshooting

**If a query fails:**
- Check index names (hyphens vs underscores)
- Verify field names match exactly (case-sensitive)
- Ensure brand-assets is in lookup mode

**If agent gives wrong answer:**
- Check tool descriptions - are they clear?
- Review custom instructions
- May need to add more examples

**If join returns no results:**
- Verify Asset ID format is consistent
- Check that lookup index has data
- Run simple FROM query to confirm

---

## 🎬 Closing

"What we've shown today:
✅ Complex analytics on interconnected datasets
✅ Natural language interface for non-technical users
✅ Real-time insights without custom development
✅ Queries that would take hours, answered in seconds

Agent Builder can be deployed in days, not months.

Questions?"

---

## 📝 Post-Demo Materials

- Demo recording
- ES|QL query library
- Agent configuration details
- Setup guide
- ES|QL documentation links
- Sample dataset generators
