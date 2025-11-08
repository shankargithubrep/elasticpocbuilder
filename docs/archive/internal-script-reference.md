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

### Setup
- Navigate to Agent Builder interface
- Have screenshots ready or share screen

---

### Creating the Agent

**Presenter:** "Now let's package this intelligence into an AI agent that anyone can use. First, we create the agent itself."

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

### Creating a Tool

**Presenter:** "Now we package our ES|QL queries as tools. Let me show you the Hidden Gems tool."

**Show Tool Creation screen and walk through:**

**Tool ID:**
```
adobe.hidden_gems_analysis
```

**Description:**
```
Identifies assets with high internal team usage but low campaign deployment - "hidden gems" ready for broader use. Includes engagement score ranking. Use when users ask about underutilized assets, internal favorites, or optimization opportunities.
```

**Labels:**
```
optimization, hidden-gems, asset-usage, recommendations
```

**ES|QL Query:**
*(Paste the Hidden Gems query from Part 2)*

**Narrate:**
"Key points:
- Tool ID: Namespaced with 'adobe.' prefix for organization
- Description: Tells the agent WHEN to use this tool - critical for selection
- Labels: Help with discovery and filtering
- ES|QL Query: The exact query we just built

The beauty is: We built it once in ES|QL, tested it, and now it's packaged as a reusable tool. We have 8 of these tools, each answering different business questions."

**Show the Tools list:**
"Here are all 8 tools:
1. Campaign ROI Analysis
2. Channel Performance by Region
3. Hidden Gems Analysis
4. Approval Workflow Efficiency
5. Monthly Performance Trends
6. Asset Type Performance Ranking
7. Audience Segment Profitability
8. Department Asset Usage

The agent automatically selects the right tool(s) based on the user's natural language question."

---

## Part 4: AI Agent Q&A Session (5-10 minutes)

### Setup
- Return to AI Agent chat interface
- Have a list of demo questions ready
- Be prepared to improvise based on audience interest

---

### Demo Question Set

**Start with a warm-up:**
```
What campaigns are performing best?
```

**Show cross-tool reasoning:**
```
Which campaigns have the best ROI, and what asset types are they using?
```
*(Should trigger Tools 1 & 6)*

**Business-focused questions:**
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

### Handling Questions

**If the agent gives a great answer:**
- Highlight specific insights
- Point out which tool(s) it used
- Show how it combined data from multiple datasets

**If the agent struggles:**
- Explain why (tool selection, query limitations)
- Show how you'd refine the tool or add a new one
- Turn it into a learning moment about iteration

**Encourage audience questions:**
"What would YOU want to ask? Let's try your question."

---

## 🎯 Key Talking Points Throughout Demo

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

### On the Business Value:
- "Democratizes data access - anyone can ask questions"
- "Real-time insights, always up-to-date"
- "Reduces dependency on data teams"
- "Faster decision-making"

### On Scalability:
- "This pattern works for ANY interconnected datasets"
- "Security ops: threat intel + events"
- "Observability: metrics + logs + traces"
- "Customer analytics: transactions + behaviors"

---

## 🔧 Troubleshooting Tips

**If a query fails:**
- Check index names (hyphens vs underscores)
- Verify field names match exactly (case-sensitive)
- Ensure brand-assets is in lookup mode

**If agent gives wrong answer:**
- Check tool descriptions - are they clear?
- Review custom instructions
- May need to add more examples or context

**If join returns no results:**
- Verify Asset ID format is consistent
- Check that lookup index actually has data
- Run a simple FROM query on each index to confirm

---

## 📊 Optional: Dashboard Walkthrough

**If time permits, show the Kibana dashboard:**

"I've also created a dashboard with these queries for quick reference. This is great for:
- Executive summaries
- Regular reporting
- Spotting trends at a glance

But the AI agent is better for:
- Ad-hoc questions
- Exploratory analysis
- Natural conversation
- Following up on insights

The dashboard and agent complement each other - both powered by the same ES|QL queries."

---

## 🎬 Closing

**Wrap up with impact:**

"What we've shown today:
✅ Complex analytics on interconnected datasets
✅ Natural language interface for non-technical users
✅ Real-time insights without custom development
✅ Queries that would take hours, answered in seconds

**Next Steps for Adobe:**
1. Identify your interconnected datasets
2. Map out key business questions
3. Build ES|QL queries (we can help!)
4. Package as Agent Builder tools
5. Deploy to your teams

**Timeline:** Agent Builder can be deployed in days, not months.

Questions?"

---

## 📝 Post-Demo Follow-Up

**Materials to send:**
- [ ] Demo recording
- [ ] ES|QL query library (all 8 queries)
- [ ] Agent configuration details
- [ ] Setup guide for their environment
- [ ] Links to ES|QL documentation
- [ ] Sample dataset generators (if they want to prototype)

**Offer:**
- [ ] Workshop to build their first agent
- [ ] Review their data architecture
- [ ] Identify additional use cases
- [ ] Support during implementation

---

## 🎓 Presenter Notes

**Energy & Pacing:**
- Start with excitement (AI teaser)
- Slow down for technical details (query building)
- Build momentum through agent creation
- Finish strong with Q&A and possibilities

**What to Emphasize:**
- Business value > Technical features
- "Anyone can ask questions" > "Advanced ES|QL"
- "Minutes to configure" > "Complex implementation"

**What to Avoid:**
- Too much jargon
- Getting stuck on one query too long
- Apologizing for demo limitations
- Overwhelming with too many features

**Remember:**
- The goal is "wow" + "I can do this"
- Show, don't tell
- Let the results speak
- Make it feel achievable

**Good luck! 🚀**
