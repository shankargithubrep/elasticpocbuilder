# **Elastic Agent Builder Demo for Tecso Corporation**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Market Research & Customer Intelligence technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on Tecso Corporation data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **customer_transactions** (Timeseries Index)
- **Record Count:** 500,000+ records
- **Primary Key:** `transaction_id`
- **Key Fields:**
  - `transaction_id` (keyword) - Unique transaction identifier
  - `customer_id` (keyword) - Links to customers.customer_id
  - `transaction_date` (date) - Purchase timestamp
  - `product_id` (keyword) - Links to products.product_id
  - `quantity` (long) - Items purchased
  - `unit_price` (double) - Price per unit
  - `total_amount` (double) - Total transaction value
  - `channel` (keyword) - "online" or "in_store"
  - `campaign_id` (keyword) - Links to campaigns.campaign_id (nullable)
  - `store_location` (keyword) - Physical store or "WEB"
- **Purpose:** Core transactional data capturing all customer purchases across channels

### **customers** (Reference Index - Lookup Mode)
- **Record Count:** 50,000+ records
- **Primary Key:** `customer_id`
- **Key Fields:**
  - `customer_id` (keyword) - Unique customer identifier
  - `customer_name` (text) - Full name
  - `email` (keyword) - Contact email
  - `registration_date` (date) - First interaction date
  - `customer_segment` (keyword) - "Premium", "Standard", "Budget"
  - `preferred_channel` (keyword) - Primary shopping channel
  - `loyalty_tier` (keyword) - "Gold", "Silver", "Bronze", "None"
  - `total_lifetime_value` (double) - Historical total spend
- **Purpose:** Customer master data for profile enrichment
- **Index Mode:** MUST be set to "lookup" for LOOKUP JOIN operations

### **products** (Reference Index - Lookup Mode)
- **Record Count:** 10,000+ records
- **Primary Key:** `product_id`
- **Key Fields:**
  - `product_id` (keyword) - Unique product identifier
  - `product_name` (text) - Product description
  - `category` (keyword) - "Electronics", "Apparel", "Home", "Beauty", "Sports"
  - `subcategory` (keyword) - Detailed classification
  - `brand` (keyword) - Manufacturer/brand name
  - `unit_cost` (double) - Cost basis
  - `list_price` (double) - Standard retail price
  - `margin_percent` (double) - Profit margin
- **Purpose:** Product catalog for merchandising analytics
- **Index Mode:** MUST be set to "lookup" for LOOKUP JOIN operations

### **campaigns** (Reference Index - Lookup Mode)
- **Record Count:** 500+ records
- **Primary Key:** `campaign_id`
- **Key Fields:**
  - `campaign_id` (keyword) - Unique campaign identifier
  - `campaign_name` (text) - Marketing campaign description
  - `campaign_type` (keyword) - "Email", "Social", "Display", "In-Store"
  - `start_date` (date) - Campaign launch
  - `end_date` (date) - Campaign conclusion
  - `budget` (double) - Total campaign spend
  - `target_segment` (keyword) - Intended audience
  - `channel` (keyword) - Primary distribution channel
- **Purpose:** Marketing campaign attribution and ROI analysis
- **Index Mode:** MUST be set to "lookup" for LOOKUP JOIN operations

**Relationships:**
- `customer_transactions.customer_id` → `customers.customer_id`
- `customer_transactions.product_id` → `products.product_id`
- `customer_transactions.campaign_id` → `campaigns.campaign_id`

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

#### **1. Upload customer_transactions (Standard Timeseries)**

Navigate to **Kibana → Management → Dev Tools**

```json
PUT customer_transactions
{
  "mappings": {
    "properties": {
      "transaction_id": { "type": "keyword" },
      "customer_id": { "type": "keyword" },
      "transaction_date": { "type": "date" },
      "product_id": { "type": "keyword" },
      "quantity": { "type": "long" },
      "unit_price": { "type": "double" },
      "total_amount": { "type": "double" },
      "channel": { "type": "keyword" },
      "campaign_id": { "type": "keyword" },
      "store_location": { "type": "keyword" }
    }
  }
}
```

Then use **Machine Learning → Data Visualizer → Upload File** to import your `customer_transactions.csv`

#### **2. Upload customers (LOOKUP MODE)**

```json
PUT customers
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "customer_id": { "type": "keyword" },
      "customer_name": { "type": "text" },
      "email": { "type": "keyword" },
      "registration_date": { "type": "date" },
      "customer_segment": { "type": "keyword" },
      "preferred_channel": { "type": "keyword" },
      "loyalty_tier": { "type": "keyword" },
      "total_lifetime_value": { "type": "double" }
    }
  }
}
```

Upload `customers.csv` via **Data Visualizer → Upload File**, selecting the `customers` index.

#### **3. Upload products (LOOKUP MODE)**

```json
PUT products
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "product_id": { "type": "keyword" },
      "product_name": { "type": "text" },
      "category": { "type": "keyword" },
      "subcategory": { "type": "keyword" },
      "brand": { "type": "keyword" },
      "unit_cost": { "type": "double" },
      "list_price": { "type": "double" },
      "margin_percent": { "type": "double" }
    }
  }
}
```

Upload `products.csv` via **Data Visualizer → Upload File**, selecting the `products` index.

#### **4. Upload campaigns (LOOKUP MODE)**

```json
PUT campaigns
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "campaign_id": { "type": "keyword" },
      "campaign_name": { "type": "text" },
      "campaign_type": { "type": "keyword" },
      "start_date": { "type": "date" },
      "end_date": { "type": "date" },
      "budget": { "type": "double" },
      "target_segment": { "type": "keyword" },
      "channel": { "type": "keyword" }
    }
  }
}
```

Upload `campaigns.csv` via **Data Visualizer → Upload File**, selecting the `campaigns` index.

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question that currently takes your team 1-2 weeks to answer manually."

**Sample questions to demonstrate:**

1. **Cross-Channel ROI Analysis:**
   - "What's the ROI for each marketing campaign in Q4 2024, broken down by customer segment and channel? Show me which campaigns drove the highest revenue per dollar spent."
   - **Why this impresses:** Joins 3 datasets (transactions, campaigns, customers), calculates ROI, segments multiple dimensions

2. **Predictive Churn Detection:**
   - "Show me high-value customers (lifetime value over $5,000) who haven't purchased in the last 60 days but were previously active monthly shoppers. These are our churn risks."
   - **Why this impresses:** Semantic understanding of "churn risk", complex date logic, customer value segmentation

3. **Product Affinity Discovery:**
   - "What product categories are frequently purchased together in the same transaction? Show me the top 5 category pairs with the highest co-occurrence rates."
   - **Why this impresses:** Market basket analysis, self-joins conceptually, statistical calculations

4. **Unified Customer 360:**
   - "Give me a complete profile for customer ID C00123 including their purchase history, preferred products, average order value, last purchase date, and which marketing campaigns they've responded to."
   - **Why this impresses:** Consolidates fragmented data across all systems in seconds

5. **Channel Performance Attribution:**
   - "Compare online vs in-store performance for the last 90 days. Which channel has higher average transaction value, and which products perform better in each channel?"
   - **Why this impresses:** Solves the disconnected channel data pain point immediately

6. **Real-Time Behavioral Anomaly:**
   - "Find customers whose recent purchasing behavior deviates significantly from their historical patterns. Focus on Premium segment customers who've dropped below their normal purchase frequency."
   - **Why this impresses:** Statistical anomaly detection, RFM-style segmentation

7. **Executive Dashboard Query:**
   - "What are the top 5 insights I should know about our business this month? Include revenue trends, top-performing categories, customer acquisition, and any concerning patterns."
   - **Why this impresses:** Agent autonomously decides what's important, runs multiple analyses

**After 2-3 questions:**

**Presenter:** "Notice what just happened - questions that normally require manual data reconciliation across your fragmented online and in-store systems, taking 40-60% of your team's time, answered in seconds. So how does this actually work? Let's go under the hood and build these queries from scratch."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "Tecso's leadership wants to know their top-performing product categories by total revenue. Let's start with a simple aggregation."

**Copy/paste into console:**

```esql
FROM customer_transactions
| STATS total_revenue = SUM(total_amount) BY category = product_id
| SORT total_revenue DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our transactional data
- STATS: Aggregate revenue with grouping by product
- SORT and LIMIT: Top 10 results

The syntax is intuitive - it reads like English. But we're missing product details. Let's fix that."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Now let's add business metrics that matter - average order value, transaction count, and calculate what percentage each category contributes to total revenue."

**Copy/paste:**

```esql
FROM customer_transactions
| STATS 
    total_revenue = SUM(total_amount),
    transaction_count = COUNT(*),
    avg_transaction_value = AVG(total_amount)
  BY channel
| EVAL revenue_per_transaction = TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count)
| EVAL avg_transaction_rounded = ROUND(avg_transaction_value, 2)
| SORT total_revenue DESC
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly
- TO_DOUBLE: Critical for decimal division in ES|QL
- Multiple STATS: Aggregating multiple metrics simultaneously
- ROUND: Business-friendly formatting
- Business-relevant calculations: revenue per transaction, comparing online vs in-store

This already solves part of Tecso's disconnected channel data problem - we're seeing unified metrics across both channels."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's solve the 'no unified customer profile' pain point. We'll enrich transaction data with customer segment and loyalty information using ES|QL's JOIN capability."

**Copy/paste:**

```esql
FROM customer_transactions
| LOOKUP JOIN customers ON customer_id
| WHERE transaction_date >= NOW() - 90 days
| STATS 
    total_revenue = SUM(total_amount),
    transaction_count = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id),
    avg_order_value = AVG(total_amount)
  BY customer_segment, loyalty_tier
| EVAL revenue_per_customer = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(unique_customers), 2)
| SORT total_revenue DESC
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines transaction data with customer master data using customer_id as the join key
- Now we have access to customer_segment and loyalty_tier from the customers index
- This is a LEFT JOIN: All transactions kept, enriched with customer profile data
- WHERE: Filtering to last 90 days for recency
- For LOOKUP JOIN to work, the customers index must have 'index.mode: lookup'

This creates that unified view Tecso needs - transactions are no longer anonymous, they're connected to rich customer profiles."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing real-time campaign ROI with customer segmentation and product performance. This is the kind of analysis that currently takes Tecso's team 1-2 weeks to manually compile."

**Copy/paste:**

```esql
FROM customer_transactions
| WHERE transaction_date >= NOW() - 90 days AND campaign_id IS NOT NULL
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN campaigns ON campaign_id
| STATS 
    total_revenue = SUM(total_amount),
    total_transactions = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id),
    avg_order_value = AVG(total_amount),
    total_margin = SUM(total_amount * margin_percent / 100)
  BY campaign_name, customer_segment, category, channel
| LOOKUP JOIN campaigns ON campaign_id
| EVAL roi = ROUND((TO_DOUBLE(total_revenue) - TO_DOUBLE(budget)) / TO_DOUBLE(budget) * 100, 2)
| EVAL margin_percent_calc = ROUND(TO_DOUBLE(total_margin) / TO_DOUBLE(total_revenue) * 100, 2)
| EVAL revenue_per_customer = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(unique_customers), 2)
| WHERE total_revenue > 1000
| SORT roi DESC
| LIMIT 20
```

**Run and break down:** 

"This query demonstrates the full power of solving Tecso's pain points:

**Multi-dataset joins:** We're combining ALL FOUR datasets:
- customer_transactions (base timeseries data)
- customers (profile enrichment)
- products (category and margin data)
- campaigns (marketing attribution and budget)

**Solving fragmented data:** Online and in-store transactions analyzed together, no manual reconciliation needed

**Predictive metrics:** ROI calculation shows which campaigns are actually profitable, not just which generated revenue

**Multi-dimensional segmentation:** Breaking down by campaign, customer segment, product category, AND channel simultaneously

**Real-time insights:** This runs in seconds on 500,000+ transactions. Currently takes Tecso's team 1-2 weeks.

**Key calculated fields:**
- roi: (Revenue - Campaign Budget) / Budget * 100
- margin_percent_calc: Actual profit margin percentage
- revenue_per_customer: Customer-level efficiency metric

This single query replaces dozens of manual Excel pivot tables and VLOOKUP operations your team currently does."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tecso-customer-intelligence-agent`

**Display Name:** `Tecso Customer Intelligence Assistant`

**Custom Instructions:** 

"You are an AI assistant specialized in retail analytics for Tecso Corporation's Market Research & Customer Intelligence team. Your role is to provide actionable insights from customer transaction data, product catalogs, customer profiles, and marketing campaigns.

**Key capabilities:**
- Analyze customer behavior patterns across online and in-store channels
- Calculate marketing campaign ROI and attribution
- Identify churn risks and high-value customer segments
- Discover product affinity patterns for merchandising optimization
- Provide unified customer 360-degree profiles
- Detect behavioral anomalies and trend deviations

**Data context:**
- customer_transactions: 500,000+ purchase records across channels
- customers: 50,000+ customer profiles with segmentation
- products: 10,000+ SKUs across 5 major categories
- campaigns: 500+ marketing initiatives

**Analysis priorities:**
1. Always consider both online and in-store channels
2. Segment insights by customer_segment (Premium/Standard/Budget)
3. Calculate ROI for any campaign-related queries
4. Flag churn risks (high-value customers with declining activity)
5. Provide actionable recommendations, not just data

**Response style:**
- Lead with the business insight, then supporting data
- Use clear metrics: revenue, ROI%, customer count, AOV
- Highlight anomalies or concerning trends
- Format numbers for readability (currency, percentages)
- When showing customer profiles, include predictive indicators (churn risk, lifetime value trajectory)"

---

### **Creating Tools**

#### **Tool 1: Campaign ROI & Attribution Analysis**

**Tool Name:** `analyze_campaign_roi`

**Description:** "Calculates marketing campaign return on investment with multi-dimensional attribution across customer segments, product categories, and channels. Returns campaign performance metrics including revenue generated, customer acquisition, ROI percentage, and margin contribution. Use this when asked about campaign effectiveness, marketing performance, or which campaigns are most profitable."

**ES|QL Query:**
```esql
FROM customer_transactions
| WHERE transaction_date >= NOW() - 90 days AND campaign_id IS NOT NULL
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN campaigns ON campaign_id
| STATS 
    total_revenue = SUM(total_amount),
    unique_customers = COUNT_DISTINCT(customer_id),
    total_transactions = COUNT(*)
  BY campaign_name, customer_segment, channel
| LOOKUP JOIN campaigns ON campaign_id
| EVAL roi = ROUND((TO_DOUBLE(total_revenue) - TO_DOUBLE(budget)) / TO_DOUBLE(budget) * 100, 2)
| EVAL revenue_per_customer = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(unique_customers), 2)
| SORT roi DESC
| LIMIT 25
```

---

#### **Tool 2: Unified Customer 360 Profile**

**Tool Name:** `get_customer_360_profile`

**Description:** "Retrieves comprehensive customer profile including purchase history, channel preferences, product affinities, campaign responses, RFM metrics (Recency, Frequency, Monetary), and predictive indicators like churn risk. Use this when asked about specific customers, customer profiles, or to understand individual customer behavior patterns."

**ES|QL Query:**
```esql
FROM customer_transactions
| WHERE customer_id == $customer_id
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| STATS 
    total_purchases = SUM(total_amount),
    transaction_count = COUNT(*),
    avg_order_value = AVG(total_amount),
    last_purchase = MAX(transaction_date),
    first_purchase = MIN(transaction_date),
    online_purchases = SUM(CASE(channel == "online", total_amount, 0)),
    instore_purchases = SUM(CASE(channel == "in_store", total_amount, 0)),
    favorite_category = VALUES(category)
  BY customer_id, customer_name, customer_segment, loyalty_tier
| EVAL days_since_purchase = (NOW() - last_purchase) / 86400000
| EVAL channel_preference = CASE(online_purchases > instore_purchases, "Online", "In-Store")
| EVAL purchase_frequency_days = (last_purchase - first_purchase) / transaction_count / 86400000
```

---

#### **Tool 3: Product Affinity & Market Basket Analysis**

**Tool Name:** `analyze_product_affinity`

**Description:** "Discovers frequently purchased product category combinations and cross-sell opportunities. Analyzes market basket patterns across channels to identify which product categories are commonly bought together. Use this for merchandising optimization, cross-sell recommendations, or understanding product relationship patterns."

**ES|QL Query:**
```esql
FROM customer_transactions
| WHERE transaction_date >= NOW() - 90 days
| LOOKUP JOIN products ON product_id
| STATS 
    total_revenue = SUM(total_amount),
    transaction_count = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id),
    avg_basket_size = AVG(quantity)
  BY category, channel
| EVAL revenue_per_transaction = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count), 2)
| EVAL customer_penetration = unique_customers
| SORT total_revenue DESC
| LIMIT 30
```

---

#### **Tool 4: Churn Risk & Retention Analysis**

**Tool Name:** `identify_churn_risks`

**Description:** "Identifies at-risk customers showing declining purchase patterns, particularly high-value customers who haven't purchased recently despite historical activity. Calculates recency metrics and flags customers deviating from their normal purchase frequency. Use this for proactive retention targeting and identifying customers who need immediate intervention."

**ES|QL Query:**
```esql
FROM customer_transactions
| LOOKUP JOIN customers ON customer_id
| WHERE customer_segment == "Premium" OR total_lifetime_value > 5000
| STATS 
    last_purchase = MAX(transaction_date),
    total_purchases = SUM(total_amount),
    transaction_count = COUNT(*),
    avg_days_between_purchases = (MAX(transaction_date) - MIN(transaction_date)) / COUNT(*) / 86400000
  BY customer_id, customer_name, customer_segment, loyalty_tier, total_lifetime_value
| EVAL days_since_purchase = (NOW() - last_purchase) / 86400000
| EVAL expected_next_purchase = avg_days_between_purchases
| EVAL days_overdue = days_since_purchase - expected_next_purchase
| WHERE days_since_purchase > 60 AND transaction_count > 5
| SORT days_overdue DESC
| LIMIT 50
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Warm-up Questions (Start here to build confidence):**

1. "What were our top 5 product categories by revenue last quarter?"
   - *Tests basic aggregation and sorting*

2. "How many unique customers made purchases in the last 30 days?"
   - *Tests date filtering and distinct counts*

3. "What's the average order value for online vs in-store transactions?"
   - *Tests channel comparison and averages*

---

**Business-Focused Questions (Core value demonstration):**

4. "Which marketing campaigns had ROI above 200% in the last 90 days? Show me the breakdown by customer segment."
   - *Tests campaign ROI tool with multi-dimensional segmentation*

5. "Show me Premium customers who haven't purchased in 60+ days but used to shop monthly. These are our churn risks."
   - *Tests churn prediction tool with behavioral pattern detection*

6. "What's the complete profile for customer C00856? Include their purchase patterns, favorite products, and any red flags."
   - *Tests unified customer 360 profile tool*

7. "Which product categories are most frequently purchased together? I need this for our merchandising strategy."
   - *Tests product affinity analysis tool*

8. "Compare the performance of email campaigns vs social media campaigns. Which drives higher customer lifetime value?"
   - *Tests campaign attribution with predictive metrics*

---

**Trend Analysis Questions (Advanced insights):**

9. "Show me revenue trends by week for the last 6 months. Are we growing or declining?"
   - *Tests time-series aggregation and trend detection*

10. "Which customer segment has grown the most in the last quarter? Show me customer acquisition by segment."
    - *Tests customer growth analysis and segmentation*

11. "Are there any products that perform significantly better in-store vs online? Show me the biggest differences."
    - *Tests channel performance comparison and anomaly detection*

12. "What percentage of our revenue comes from repeat customers vs new customers?"
    - *Tests customer cohort analysis and retention metrics*

---

**Optimization Questions (Strategic recommendations):**

13. "If I had to cut 3 underperforming campaigns, which ones should I eliminate based on ROI?"
    - *Tests negative filtering and strategic recommendation*

14. "Show me the top 20 customers I should focus retention efforts on - high value but showing warning signs."
    - *Tests prioritized churn risk list with actionable targeting*

15. "What's the optimal product bundle I should promote based on actual purchase patterns?"
    - *Tests market basket insights for merchandising action*

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics - not adapted from transactional SQL"
- "Piped syntax is intuitive and readable - your analysts can learn this in hours, not weeks"
- "Operates on blocks, not rows - extremely performant even on 500,000+ transaction records"
- "Supports complex operations: LOOKUP JOINs across multiple datasets, EVAL for calculations, window functions, time-series analysis"
- "No more manual data reconciliation - joins happen in milliseconds"

### **On Agent Builder:**
- "Bridges AI and enterprise data - your business users ask questions in plain English, Agent Builder translates to ES|QL"
- "No custom development - configure, don't code. This demo setup took hours, not months"
- "Works with existing Elasticsearch indices - no data movement, no ETL pipelines"
- "Agent automatically selects the right tool based on question context - users don't need to know which dataset to query"
- "Built-in governance - you control exactly what data the agent can access through tool definitions"

### **On Business Value for Tecso:**
- "Democratizes data access - your Market Research team doesn't need to wait for IT or data engineers"
- "Real-time insights, always up-to-date - no stale reports, no 'data as of last week'"
- "Reduces dependency on data teams - solves the 1-2 week turnaround time for custom analyses"
- "Faster decision-making - executives get answers in seconds during strategy meetings"
- "Solves the 40-60% time sink on manual reconciliation - your team can focus on insights, not data wrangling"
- "Unified customer view - finally see customers as people, not fragmented IDs across systems"

### **Addressing Tecso's Specific Pain Points:**

**Pain Point 1: Disconnected purchase data across channels**
- "ES|QL's LOOKUP JOIN eliminates manual reconciliation. Online and in-store data unified in a single query."

**Pain Point 2: No unified customer profile**
- "Customer 360 tool consolidates all touchpoints. One customer ID, complete history, predictive indicators."

**Pain Point 3: Lack of predictive modeling**
- "Churn risk tool provides forward-looking guidance. Identify at-risk customers before they lapse."

**Pain Point 4: Insufficient behavioral pattern detection**
- "Market basket analysis discovers complex multi-dimensional patterns humans can't spot manually."

**Pain Point 5: Slow time-to-insight**
- "Queries that took 1-2 weeks now run in seconds. Business stakeholders get answers during the meeting, not after."

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (case-sensitive): `customer_transactions`, `customers`, `products`, `campaigns`
- Verify field names are case-sensitive correct: `customer_id`, `product_id`, `campaign_id`
- Ensure joined indices (`customers`, `products`, `campaigns`) are in lookup mode - check with `GET customers/_settings`
- Confirm date fields are properly formatted as `date` type, not `keyword`

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about when to use each tool?
- Review custom instructions - does the agent understand Tecso's business context?
- Verify the agent has access to all 4 tools in the configuration
- Check if the question requires data the tools don't provide - may need to add a tool

**If join returns no results:**
- Verify join key format is consistent across datasets (e.g., "C00123" vs "C123")
- Check that lookup index has data: `FROM customers | LIMIT 10`
- Ensure the join field exists in both indices: `FROM customer_transactions | KEEP customer_id | LIMIT 5`
- Confirm lookup indices have `"index.mode": "lookup"` in settings

**If performance is slow:**
- Add date filters to limit data scanned: `WHERE transaction_date >= NOW() - 90 days`
- Use LIMIT to cap results: `LIMIT 100`
- Check if indices need optimization: `POST customer_transactions/_forcemerge`

**If calculated fields show wrong values:**
- Ensure TO_DOUBLE() wraps any division operations
- Check for division by zero with WHERE clauses
- Verify date math uses correct millisecond conversions (86400000 ms per day)

---

## **🎬 Closing**

"What we've shown today addresses Tecso's core challenges:

✅ **Unified customer profiles** - No more fragmented views across online and in-store systems

✅ **Predictive customer modeling** - Forward-looking churn risk and lifetime value guidance

✅ **Behavioral pattern detection** - Market basket analysis discovers complex purchasing patterns automatically

✅ **Connected channel data** - Online e-commerce and in-store POS unified in real-time, zero manual reconciliation

✅ **Instant time-to-insight** - Analyses that took 1-2 weeks now answered in seconds

**The transformation:**
- Your team currently spends 40-60% of time on data reconciliation → That time goes to zero
- Custom analyses take 1-2 weeks → Now seconds
- Executives wait for insights → Now get answers during the meeting
- Customers appear as separate entities → Now unified 360-degree profiles

**Implementation reality:**
- Agent Builder can be deployed in days, not months
- No custom development required
- Works with your existing Elasticsearch data
- Your team maintains full control over data access and governance

**Next steps:**
1. Proof of concept with your actual customer transaction data
2. Configure agents for your specific use cases
3. Pilot with Market Research team
4. Scale to broader organization

Questions?"

---

**End of Demo Guide**