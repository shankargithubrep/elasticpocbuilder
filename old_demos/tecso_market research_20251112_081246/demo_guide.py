from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class TecsoDemoGuide(DemoGuideModule):
    """Demo guide for Tecso - Market Research"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        return '''# **Elastic Agent Builder Demo for Tecso**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Market Research technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on Tecso retail customer data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **purchase_transactions** (Timeseries Index)
- **Record Count:** 100,000+ transaction records
- **Primary Key:** `transaction_id`
- **Key Fields:**
  - `transaction_id` (keyword) - Unique transaction identifier
  - `customer_id` (keyword) - Foreign key to customers
  - `product_id` (keyword) - Foreign key to products
  - `@timestamp` (date) - Transaction timestamp
  - `purchase_channel` (keyword) - "online" or "in-store"
  - `transaction_amount` (double) - Total purchase value
  - `quantity` (integer) - Number of items purchased
  - `payment_method` (keyword) - Payment type used
  - `store_location` (keyword) - Physical store or "online"
- **Relationships:** Links to customers and products via IDs
- **Index Mode:** Standard timeseries

### **customers** (Reference/Lookup Index)
- **Record Count:** 10,000+ customer profiles
- **Primary Key:** `customer_id`
- **Key Fields:**
  - `customer_id` (keyword) - Unique customer identifier
  - `customer_name` (text) - Full name
  - `age` (integer) - Customer age
  - `age_group` (keyword) - "18-25", "26-35", "36-45", "46-55", "56+"
  - `customer_segment` (keyword) - "Premium", "Standard", "Budget"
  - `loyalty_tier` (keyword) - "Gold", "Silver", "Bronze"
  - `email` (keyword) - Contact email
  - `registration_date` (date) - Account creation date
  - `lifetime_value` (double) - Total historical spend
- **Relationships:** Referenced by purchase_transactions
- **Index Mode:** **MUST BE "lookup"** for LOOKUP JOIN

### **products** (Reference/Lookup Index)
- **Record Count:** 5,000+ product SKUs
- **Primary Key:** `product_id`
- **Key Fields:**
  - `product_id` (keyword) - Unique product identifier
  - `product_name` (text) - Full product name
  - `category` (keyword) - "Electronics", "Apparel", "Home & Garden", "Sports", "Beauty"
  - `subcategory` (keyword) - Specific product type
  - `brand` (keyword) - Brand name
  - `price` (double) - Current retail price
  - `cost` (double) - Cost basis
  - `description` (text) - Detailed product description (for semantic search)
  - `tags` (keyword array) - Product attributes
- **Relationships:** Referenced by purchase_transactions
- **Index Mode:** **MUST BE "lookup"** for LOOKUP JOIN

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

#### **Upload purchase_transactions (Timeseries)**

1. Navigate to **Kibana → Management → Dev Tools**
2. Create the index with proper mapping:

```json
PUT purchase_transactions
{
  "mappings": {
    "properties": {
      "transaction_id": { "type": "keyword" },
      "customer_id": { "type": "keyword" },
      "product_id": { "type": "keyword" },
      "@timestamp": { "type": "date" },
      "purchase_channel": { "type": "keyword" },
      "transaction_amount": { "type": "double" },
      "quantity": { "type": "integer" },
      "payment_method": { "type": "keyword" },
      "store_location": { "type": "keyword" }
    }
  }
}
```

3. Navigate to **Kibana → Management → Stack Management → Data Views**
4. Create data view for `purchase_transactions` with timestamp field `@timestamp`
5. Go to **Kibana → Management → Integrations → Upload a file**
6. Upload your `purchase_transactions.csv` file
7. Map CSV columns to the fields above
8. Import into the `purchase_transactions` index

#### **Upload customers (Lookup Mode)**

1. In **Dev Tools**, create the lookup index:

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
      "age": { "type": "integer" },
      "age_group": { "type": "keyword" },
      "customer_segment": { "type": "keyword" },
      "loyalty_tier": { "type": "keyword" },
      "email": { "type": "keyword" },
      "registration_date": { "type": "date" },
      "lifetime_value": { "type": "double" }
    }
  }
}
```

2. Upload `customers.csv` using the file upload feature
3. Import into the `customers` index

#### **Upload products (Lookup Mode)**

1. In **Dev Tools**, create the lookup index:

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
      "price": { "type": "double" },
      "cost": { "type": "double" },
      "description": { "type": "text" },
      "tags": { "type": "keyword" }
    }
  }
}
```

2. Upload `products.csv` using the file upload feature
3. Import into the `products` index

### **Step 2: Verify Data Load**

Run these quick checks in Dev Tools:

```esql
FROM purchase_transactions
| STATS transaction_count = COUNT(*)
```

```esql
FROM customers
| STATS customer_count = COUNT(*)
```

```esql
FROM products
| STATS product_count = COUNT(*)
```

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex market research questions that would typically require a data analyst to write SQL queries, join multiple tables, and create visualizations."

**Sample questions to demonstrate:**

1. **Cross-dataset ROI Analysis:**
   - "Which customer segments generate the most revenue per customer, and how does their average transaction value compare between online and in-store purchases?"
   - *Shows: Multi-dataset joins, revenue calculations, channel comparison*

2. **Demographic Product Affinity:**
   - "What are the top 3 product categories purchased by customers in the 26-35 age group, and how does this differ from the 46-55 age group?"
   - *Shows: Customer profiling, demographic segmentation, comparative analysis*

3. **High-Value Customer Detection:**
   - "Identify customers whose individual purchase amounts are at least 50% higher than their segment's average transaction value. Who are our biggest spenders relative to their peer group?"
   - *Shows: Statistical comparison, outlier detection, segment benchmarking*

4. **Seasonal Trend Analysis:**
   - "Show me monthly revenue trends over the last 6 months broken down by purchase channel. Are we seeing growth in online or in-store sales?"
   - *Shows: Time-series analysis, trend detection, channel performance*

5. **Product Performance with Customer Context:**
   - "Which product categories have the highest purchase frequency among Premium segment customers, and what's the average transaction value for each category?"
   - *Shows: Category performance, segment filtering, frequency analysis*

6. **Semantic Customer Discovery:**
   - "Find customers who frequently buy wireless headphones or bluetooth audio devices. How many distinct customers purchased these types of products in the last 3 months?"
   - *Shows: Semantic search on product descriptions, customer identification, natural language query*

7. **Multi-Dimensional Engagement Analysis:**
   - "Give me a comprehensive view of customer engagement: total customers by segment, their preferred purchase channel, average transaction value, and total revenue contribution for the last quarter."
   - *Shows: Multi-metric dashboard, comprehensive analysis, business KPIs*

**Presenter:** "Notice how I'm asking questions in plain English - no SQL, no technical jargon. The agent understands the business context, knows which datasets to query, performs the joins automatically, and returns actionable insights."

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL, Elastic's modern query language."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "Let's start simple. Tecso's market research team wants to know: What are our top-performing purchase channels by total revenue?"

**Copy/paste into console:**

```esql
FROM purchase_transactions
| STATS total_revenue = SUM(transaction_amount), transaction_count = COUNT(*) BY purchase_channel
| SORT total_revenue DESC
```

**Run and narrate results:** "This is basic ES|QL - just 3 lines of code:
- FROM: Source our transaction data
- STATS: Aggregate revenue and count transactions, grouped by channel
- SORT: Show highest revenue first

The syntax is intuitive - it reads like English. We can immediately see whether online or in-store drives more revenue."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add business calculations to get deeper insights. Now we want to calculate average transaction value and understand the revenue per transaction for each channel."

**Copy/paste:**

```esql
FROM purchase_transactions
| STATS 
    total_revenue = SUM(transaction_amount),
    transaction_count = COUNT(*)
  BY purchase_channel
| EVAL avg_transaction_value = TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count)
| EVAL revenue_formatted = CONCAT("$", TO_STRING(ROUND(total_revenue, 2)))
| SORT total_revenue DESC
```

**Run and highlight:** "Key additions here:
- EVAL: Creates calculated fields on-the-fly
- TO_DOUBLE: Critical for decimal division - ensures we get accurate averages
- Multiple calculations: Average transaction value and formatted revenue
- Business-relevant metrics that marketing can act on

We can now see that while in-store might have more transactions, online could have higher average order values - or vice versa. This informs channel investment decisions."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources. We want to analyze revenue by customer segment - this requires joining transaction data with customer profile data using ES|QL's JOIN capability."

**Copy/paste:**

```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_revenue = SUM(transaction_amount),
    customer_count = COUNT_DISTINCT(customer_id),
    transaction_count = COUNT(*)
  BY customer_segment, purchase_channel
| EVAL avg_transaction_value = TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count)
| EVAL revenue_per_customer = TO_DOUBLE(total_revenue) / TO_DOUBLE(customer_count)
| SORT total_revenue DESC
| LIMIT 10
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines transactions with customer profiles using customer_id as the join key
- Now we have access to customer_segment from the customers dataset
- We're calculating both average transaction value AND revenue per customer
- This reveals which segments are most valuable - Premium customers might have fewer transactions but much higher values
- For LOOKUP JOIN to work, the customers index must have 'index.mode: lookup' - which we set during setup

This single query answers: Which customer segments should we prioritize in our marketing campaigns?"

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing product category performance across customer demographics. This joins all three datasets and performs multi-dimensional analysis."

**Copy/paste:**

```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| WHERE @timestamp >= NOW() - 90 days
| STATS 
    total_revenue = SUM(transaction_amount),
    total_quantity = SUM(quantity),
    unique_customers = COUNT_DISTINCT(customer_id),
    transaction_count = COUNT(*),
    avg_customer_age = AVG(age)
  BY category, age_group
| EVAL avg_transaction_value = TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count)
| EVAL revenue_per_customer = TO_DOUBLE(total_revenue) / TO_DOUBLE(unique_customers)
| EVAL items_per_transaction = TO_DOUBLE(total_quantity) / TO_DOUBLE(transaction_count)
| EVAL category_age_segment = CONCAT(category, " | ", age_group)
| WHERE total_revenue > 5000
| SORT total_revenue DESC
| LIMIT 20
```

**Run and break down:** 

"This is a production-grade analytical query that reveals which product categories resonate with specific age demographics:

- **Two LOOKUP JOINs**: We're enriching transactions with both customer demographics AND product details
- **Time filter**: Last 90 days of data for recent trends
- **Multi-dimensional grouping**: By product category AND customer age group
- **Six key metrics**: Revenue, quantity, customer count, transaction count, and average age
- **Four calculated KPIs**: Average transaction value, revenue per customer, items per transaction, and a combined segment label
- **Filtering**: Only show category-age combinations with meaningful revenue (>$5000)
- **Ranked results**: Top 20 combinations by revenue

**Business Impact:** This single query tells Tecso's market research team:
- Electronics might be dominated by 26-35 year-olds
- Home & Garden could be strongest with 46-55 age group
- Beauty products might have highest transaction frequency with 18-25 demographic

This enables precise targeting: 'Run Instagram ads for Beauty products targeting 18-25 females' or 'Send Home & Garden catalogs to 46-55 homeowners.' That's the power of combining data science with business context."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Presenter:** "Now that we've built these queries, let's package them into an AI agent that anyone on the market research team can use - no ES|QL knowledge required."

**Agent Configuration:**

**Agent ID:** `tecso-market-research-agent`

**Display Name:** `Tecso Market Research Analytics Agent`

**Custom Instructions:** 
```
You are an AI assistant specializing in retail market research analytics for Tecso. 
You have access to customer purchase transaction data, customer profiles, and product catalogs.

Your primary goals:
- Analyze customer buying behavior across online and in-store channels
- Identify customer segments and their purchasing patterns
- Provide product category performance insights
- Help understand demographic preferences for targeted marketing
- Calculate key retail metrics: AOV, revenue per customer, purchase frequency

Always provide context with your answers - explain what the numbers mean for business decisions.
When showing revenue figures, format them as currency. When discussing segments, provide actionable recommendations.
If asked about trends, compare time periods and highlight significant changes.
```

---

### **Creating Tools**

**Presenter:** "We create tools that wrap our ES|QL queries. Each tool is like giving the agent a specific analytical capability."

#### **Tool 1: Customer Segment Revenue Analysis**

**Tool Name:** `analyze_segment_revenue_by_channel`

**Description:** 
```
Analyzes revenue performance by customer segment and purchase channel. 
Calculates total revenue, customer count, transaction count, average transaction value, 
and revenue per customer. Use this to identify high-value customer segments and 
understand channel preferences by segment.
```

**ES|QL Query:**
```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_revenue = SUM(transaction_amount),
    customer_count = COUNT_DISTINCT(customer_id),
    transaction_count = COUNT(*)
  BY customer_segment, purchase_channel
| EVAL avg_transaction_value = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count), 2)
| EVAL revenue_per_customer = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(customer_count), 2)
| SORT total_revenue DESC
```

---

#### **Tool 2: Product Category Performance by Age Demographics**

**Tool Name:** `analyze_category_by_age_demographics`

**Description:**
```
Identifies which product categories perform best with specific age demographics.
Shows revenue, customer count, and average transaction metrics grouped by 
product category and customer age group. Use this for targeted marketing campaigns 
and inventory optimization based on demographic preferences.
```

**ES|QL Query:**
```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| WHERE @timestamp >= NOW() - 90 days
| STATS 
    total_revenue = SUM(transaction_amount),
    unique_customers = COUNT_DISTINCT(customer_id),
    transaction_count = COUNT(*)
  BY category, age_group
| EVAL avg_transaction_value = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(transaction_count), 2)
| WHERE total_revenue > 1000
| SORT total_revenue DESC
| LIMIT 25
```

---

#### **Tool 3: High-Value Customer Identification**

**Tool Name:** `identify_high_value_customers`

**Description:**
```
Identifies customers whose individual purchase amounts significantly exceed their 
segment's average, revealing upsell opportunities and VIP customers. Compares each 
customer's spending to their segment benchmark. Use this to identify customers for 
premium programs or personalized engagement.
```

**ES|QL Query:**
```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    customer_total_spend = SUM(transaction_amount),
    customer_transaction_count = COUNT(*)
  BY customer_id, customer_name, customer_segment
| EVAL customer_avg_transaction = TO_DOUBLE(customer_total_spend) / TO_DOUBLE(customer_transaction_count)
| STATS 
    individual_avg = AVG(customer_avg_transaction),
    individual_total = SUM(customer_total_spend)
  BY customer_id, customer_name, customer_segment
| STATS 
    segment_avg_transaction = AVG(individual_avg)
  BY customer_segment
| LOOKUP JOIN (
    FROM purchase_transactions
    | LOOKUP JOIN customers ON customer_id
    | STATS customer_avg = AVG(transaction_amount) BY customer_id, customer_name, customer_segment
  ) ON customer_segment
| WHERE customer_avg > segment_avg_transaction * 1.5
| SORT customer_avg DESC
| LIMIT 50
```

---

#### **Tool 4: Semantic Product Customer Discovery**

**Tool Name:** `find_customers_by_product_type`

**Description:**
```
Uses semantic search to identify customers who frequently purchase specific types of 
products described in natural language (e.g., "wireless headphones", "organic skincare").
Searches product descriptions and names to find matching items, then identifies customers 
who bought them. Use this for precise customer profiling and targeted campaign creation.
Parameters: product_description (text), time_range_days (number, default 90)
```

**ES|QL Query:**
```esql
FROM purchase_transactions
| LOOKUP JOIN products ON product_id
| WHERE @timestamp >= NOW() - {{time_range_days}} days
| WHERE product_name LIKE "*{{product_keyword}}*" OR description LIKE "*{{product_keyword}}*"
| LOOKUP JOIN customers ON customer_id
| STATS 
    purchase_count = COUNT(*),
    total_spent = SUM(transaction_amount),
    first_purchase = MIN(@timestamp),
    last_purchase = MAX(@timestamp)
  BY customer_id, customer_name, customer_segment, age_group
| WHERE purchase_count >= 2
| SORT total_spent DESC
| LIMIT 100
```

**Presenter:** "With these four tools, our agent can answer dozens of different market research questions. The agent automatically selects the right tool based on the user's question - no manual tool selection needed."

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Presenter:** "Now let's see the agent in action. I'll ask a variety of market research questions, and you'll see how it intelligently selects tools and provides insights."

---

#### **Warm-up Questions (Start here to build confidence)**

1. **"What are our top 3 customer segments by total revenue?"**
   - *Expected: Uses segment revenue tool, shows Premium/Standard/Budget ranking*

2. **"How many total transactions do we have in the last 90 days?"**
   - *Expected: Simple count query, establishes data volume*

3. **"Which purchase channel generates more revenue - online or in-store?"**
   - *Expected: Channel comparison, percentage breakdown*

---

#### **Business-Focused Questions (Core use cases)**

4. **"Which customer segments should we prioritize for our holiday marketing campaign based on revenue per customer?"**
   - *Expected: Segment analysis with revenue per customer metric, recommendation for Premium segment*

5. **"What product categories are most popular with customers aged 26-35, and how does this compare to customers aged 46-55?"**
   - *Expected: Demographic category analysis, comparative insights, specific marketing recommendations*

6. **"Identify our top 10 highest-value customers who spend significantly more than others in their segment."**
   - *Expected: High-value customer identification tool, names and spending patterns*

7. **"What's the average transaction value for Premium customers versus Budget customers, and what does this tell us about pricing strategy?"**
   - *Expected: Segment comparison with AOV, strategic pricing insights*

---

#### **Trend Analysis Questions (Time-based insights)**

8. **"Show me revenue trends by purchase channel over the last 6 months. Are we growing online sales?"**
   - *Expected: Time-series analysis, month-over-month comparison, growth percentage*

9. **"Which product categories have seen the biggest revenue growth in the last quarter compared to the previous quarter?"**
   - *Expected: Category performance over time, growth rate calculations*

10. **"How has our customer mix changed over the past year? Are we acquiring more Premium or Budget segment customers?"**
    - *Expected: Segment distribution over time, new customer analysis*

---

#### **Advanced/Optimization Questions (Show sophistication)**

11. **"Find all customers who have purchased Electronics products priced over $500 in the last 3 months. These are candidates for our premium accessory campaign."**
    - *Expected: Semantic product search + price filter + customer list*

12. **"What's the overlap between customers who shop both online and in-store? Do omnichannel customers spend more than single-channel customers?"**
    - *Expected: Channel behavior analysis, customer segmentation by channel usage, spending comparison*

---

**Presenter Tips:**
- Ask 4-6 questions during the demo (don't do all 12)
- Mix categories: Start with warmup, do 2-3 business questions, 1 trend question, 1 advanced
- Pause after each answer to highlight: "Notice how the agent..."
  - Selected the right tool automatically
  - Performed joins across datasets
  - Formatted the answer in business language
  - Provided actionable recommendations
- If an answer is particularly good, say: "This would have taken a data analyst 30 minutes to query and visualize - we got it in 10 seconds"

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "ES|QL is Elastic's modern query language, purpose-built for analytics and data science"
- "The piped syntax is intuitive and readable - even non-technical users can understand what a query does"
- "It operates on blocks of data, not individual rows - this makes it extremely performant even on millions of records"
- "Supports complex operations out of the box: joins, window functions, time-series analysis, statistical functions"
- "Unlike traditional SQL, ES|QL is optimized for the way Elasticsearch stores and retrieves data"

### **On Agent Builder:**
- "Agent Builder bridges the gap between AI and enterprise data - it's not just a chatbot, it's an analytical assistant"
- "No custom development required - you configure, you don't code"
- "Works with your existing Elasticsearch indices - no data migration, no ETL pipelines"
- "The agent automatically selects the right tools based on the user's question - intelligent routing"
- "Built-in security: respects Elasticsearch role-based access control, users only see data they're authorized to see"
- "Version control for agents and tools - track changes, roll back if needed"

### **On Business Value for Tecso:**
- "Democratizes data access - market research analysts, merchandising teams, and executives can all ask questions without waiting for IT"
- "Real-time insights, always up-to-date - no stale reports or outdated dashboards"
- "Reduces dependency on data teams - frees up analysts for strategic work instead of ad-hoc queries"
- "Faster decision-making - answer business questions in seconds, not days"
- "Scales with your data - works the same whether you have 100K or 100M transactions"
- "For Tecso specifically: Better customer segmentation = more targeted campaigns = higher ROI on marketing spend"

### **On Market Research Use Cases:**
- "Customer profiling becomes dynamic - segment customers by any combination of demographics, behavior, and purchase patterns"
- "Product-market fit analysis - understand which products resonate with which customer groups"
- "Campaign effectiveness - measure impact of marketing initiatives on specific segments"
- "Competitive positioning - identify gaps in your product catalog based on customer demand patterns"

---

## **🔧 Troubleshooting**

### **If a query fails:**

**Error: "Unknown index"**
- Check index names match exactly (case-sensitive)
- Verify indices were created: Run `GET _cat/indices?v` in Dev Tools

**Error: "Unknown column"**
- Verify field names are case-sensitive correct
- Check mapping: Run `GET <index_name>/_mapping` to see actual field names

**Error: "LOOKUP JOIN requires lookup index mode"**
- Ensure joined indices (customers, products) were created with `"index.mode": "lookup"`
- Recreate the index with proper settings if needed

**Error: "Cannot divide by zero"**
- Add WHERE clause to filter out zero values: `WHERE transaction_count > 0`
- Use conditional EVAL: `EVAL avg = CASE(transaction_count > 0, revenue / transaction_count, 0)`

---

### **If agent gives wrong answer:**

**Agent selects wrong tool:**
- Check tool descriptions - are they clear and specific about when to use the tool?
- Review custom instructions - does the agent understand the business context?
- Add more specific keywords to tool descriptions

**Agent returns no results:**
- Verify the underlying ES|QL query works in Dev Tools first
- Check date ranges - might be filtering out all data
- Verify join keys match between datasets

**Agent provides incomplete answer:**
- Update custom instructions to be more specific about answer format
- Add examples of good answers in the instructions
- Check if the tool's query has appropriate LIMIT values

---

### **If join returns no results:**

**No data after LOOKUP JOIN:**
- Verify join key format is consistent across datasets (e.g., "CUST001" vs "cust001")
- Check that lookup index has data: `FROM customers | LIMIT 10`
- Ensure join key field names match exactly
- Verify the lookup index is in "lookup" mode: `GET customers/_settings`

**Partial results after join:**
- This is expected with LEFT JOIN - not all records will have matches
- Check data quality: Do all transactions have valid customer_ids?
- Consider adding WHERE clause to filter null values after join

---

### **Performance Issues:**

**Query takes too long:**
- Add time range filters: `WHERE @timestamp >= NOW() - 30 days`
- Reduce LIMIT values for testing
- Check if you're joining on indexed fields (keyword fields are best for joins)
- Consider adding WHERE filters before joins to reduce dataset size

**Agent response is slow:**
- Check if tools have appropriate LIMIT clauses
- Verify indices are properly sharded for your data volume
- Consider creating aggregated summary indices for common queries

---

## **🎬 Closing**

**Presenter:** "Let me summarize what we've shown you today with Tecso's market research data:

✅ **Complex analytics on interconnected datasets** - We joined transactions, customers, and products seamlessly to answer multi-dimensional questions

✅ **Natural language interface for non-technical users** - Market research analysts can ask questions in plain English and get SQL-quality insights

✅ **Real-time insights without custom development** - No Python scripts, no BI tool configurations, no data engineering required

✅ **Queries that would take hours, answered in seconds** - What used to require a data analyst, SQL expertise, and multiple iterations now happens instantly

**For Tecso specifically:**
- Your market research team can segment customers dynamically based on any criteria
- Merchandising can understand product-demographic fit for inventory optimization
- Marketing can identify high-value customers for VIP programs
- Leadership gets real-time dashboards without waiting for monthly reports

**Implementation Timeline:**
Agent Builder can be deployed in days, not months:
- Week 1: Data mapping and index setup
- Week 2: Tool creation and testing
- Week 3: Agent configuration and user training
- Week 4: Production rollout

**Next Steps:**
1. We can set up a POC environment with your actual Tecso data
2. Work with your team to identify the top 10 questions you need answered regularly
3. Build custom tools tailored to your specific KPIs and metrics
4. Train your market research team on asking effective questions

The technology you've seen today is production-ready. Elastic Agent Builder is being used by retailers, financial services, healthcare, and manufacturing companies to democratize data access and accelerate decision-making.

**Questions?"**

---

## **📊 Appendix: Additional Query Examples**

### **Customer Lifetime Value Analysis**

```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_spent = SUM(transaction_amount),
    transaction_count = COUNT(*),
    first_purchase = MIN(@timestamp),
    last_purchase = MAX(@timestamp),
    avg_days_between_purchases = (MAX(@timestamp) - MIN(@timestamp)) / transaction_count
  BY customer_id, customer_name, customer_segment
| EVAL customer_tenure_days = (NOW() - first_purchase) / 86400000
| EVAL purchase_frequency = TO_DOUBLE(transaction_count) / TO_DOUBLE(customer_tenure_days) * 30
| WHERE transaction_count >= 3
| SORT total_spent DESC
| LIMIT 50
```

**Use Case:** Identify most valuable customers based on total spend, purchase frequency, and tenure.

---

### **Product Affinity Analysis**

```esql
FROM purchase_transactions
| LOOKUP JOIN products ON product_id
| WHERE @timestamp >= NOW() - 60 days
| STATS 
    purchase_count = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id),
    total_revenue = SUM(transaction_amount)
  BY category, subcategory
| EVAL revenue_per_customer = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(unique_customers), 2)
| EVAL avg_purchase_value = ROUND(TO_DOUBLE(total_revenue) / TO_DOUBLE(purchase_count), 2)
| WHERE purchase_count >= 10
| SORT total_revenue DESC
```

**Use Case:** Understand which product subcategories drive the most revenue and customer engagement.

---

### **Channel Migration Analysis**

```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| WHERE @timestamp >= NOW() - 180 days
| STATS 
    online_count = COUNT_DISTINCT(CASE(purchase_channel == "online", transaction_id, null)),
    instore_count = COUNT_DISTINCT(CASE(purchase_channel == "in-store", transaction_id, null)),
    total_spent = SUM(transaction_amount)
  BY customer_id, customer_segment
| EVAL channel_preference = CASE(
    online_count > instore_count, "online",
    instore_count > online_count, "in-store",
    "omnichannel"
  )
| STATS 
    customer_count = COUNT(*),
    avg_spend = AVG(total_spent)
  BY customer_segment, channel_preference
| SORT customer_segment, avg_spend DESC
```

**Use Case:** Identify customer channel preferences by segment to optimize channel investment.

---

**End of Demo Guide**'''

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
