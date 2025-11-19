# **Elastic Agent Builder Demo for Verizon FIOS**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Consumer TV Product & Personalization Engineering technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered semantic search and explainable recommendations on Verizon FIOS streaming data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **content_catalog** (200,000 records)
Primary dataset containing all available streaming content in the Verizon FIOS catalog.

**Primary Key:** `content_id` (string)

**Key Fields:**
- `content_id` - Unique identifier for each piece of content
- `title` - Content title
- `content_type` - Type (movie, series, documentary, etc.)
- `genres` - Array of genre classifications
- `themes` - Array of thematic elements (e.g., "redemption", "family-conflict", "coming-of-age")
- `release_year` - Year of release
- `duration_minutes` - Runtime in minutes
- `content_vector` - 768-dimension semantic embedding for thematic similarity
- `description` - Full text description of content
- `cast` - Array of actor names
- `director` - Director name
- `rating` - Content rating (G, PG, PG-13, R, etc.)
- `popularity_score` - Current popularity metric (0-100)

**Relationships:** 
- Referenced by `viewing_history.content_id`
- Referenced by `recommendation_explanations.recommended_content_id`

---

### **user_preferences** (4,200,000 records)
User preference profiles capturing explicit and implicit content preferences.

**Primary Key:** `user_id` (string)

**Key Fields:**
- `user_id` - Unique subscriber identifier
- `subscriber_tenure_days` - Days since subscription started
- `preferred_themes` - Array of liked thematic elements
- `disliked_themes` - Array of actively disliked themes
- `avoided_genres` - Array of genres user consistently skips
- `favorite_genres` - Array of preferred genres
- `preference_vector` - 768-dimension vector representing aggregate preferences
- `viewing_session_count` - Total number of viewing sessions
- `cold_start_flag` - Boolean indicating if user has <5 sessions
- `last_updated` - Timestamp of last preference update
- `trust_score` - User's self-reported trust in recommendations (0-100)
- `avg_watch_completion_rate` - Percentage of content watched to completion

**Relationships:**
- Links to `viewing_history.user_id`

---

### **viewing_history** (850,000,000 records)
Event-level viewing data capturing all user interactions with content.

**Primary Key:** `event_id` (string)

**Key Fields:**
- `event_id` - Unique event identifier
- `user_id` - Subscriber who viewed content
- `content_id` - Content that was viewed
- `event_type` - Type of interaction (play, skip, dismiss, complete, search)
- `event_timestamp` - When the event occurred
- `watch_duration_seconds` - How long content was watched
- `completion_percentage` - Percentage of content completed
- `skip_reason` - If skipped, the reason (not-interested, already-seen, etc.)
- `recommendation_source` - How user found content (recommendation, search, browse)
- `session_id` - Viewing session identifier
- `device_type` - Device used (set-top-box, mobile, web)

**Relationships:**
- References `content_catalog.content_id`
- References `user_preferences.user_id`

---

### **recommendation_explanations** (50,000 records)
Pre-generated explanations for common recommendation patterns to enable transparent AI.

**Primary Key:** `explanation_id` (string)

**Key Fields:**
- `explanation_id` - Unique explanation identifier
- `recommendation_pattern` - Pattern type (theme-match, genre-match, similar-viewers, etc.)
- `recommended_content_id` - Content being recommended
- `explanation_text` - Human-readable explanation
- `reasoning_factors` - Array of factors contributing to recommendation
- `confidence_score` - Confidence in recommendation (0-100)
- `user_feedback_score` - Average user rating of explanation helpfulness
- `theme_overlap` - Array of shared themes driving recommendation

**Relationships:**
- References `content_catalog.content_id` via `recommended_content_id`

---

### **content_themes** (5,000 records)
Reference data defining thematic taxonomy and semantic relationships between themes.

**Primary Key:** `theme_id` (string)

**Key Fields:**
- `theme_id` - Unique theme identifier
- `theme_name` - Human-readable theme name
- `theme_category` - High-level category (emotional, narrative, social, etc.)
- `related_themes` - Array of semantically related theme IDs
- `theme_description` - Detailed description of thematic element
- `content_count` - Number of content items tagged with this theme
- `avg_engagement_score` - Average user engagement with this theme

**Relationships:**
- Referenced by `content_catalog.themes`
- Referenced by `user_preferences.preferred_themes` and `disliked_themes`

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

Navigate to **Kibana → Management → Dev Tools**

#### **Create content_catalog index (lookup mode)**

```json
PUT /content_catalog
{
  "settings": {
    "index.mode": "lookup",
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "content_id": { "type": "keyword" },
      "title": { "type": "text", "fields": {"keyword": {"type": "keyword"}} },
      "content_type": { "type": "keyword" },
      "genres": { "type": "keyword" },
      "themes": { "type": "keyword" },
      "release_year": { "type": "integer" },
      "duration_minutes": { "type": "integer" },
      "content_vector": { "type": "dense_vector", "dims": 768 },
      "description": { "type": "text" },
      "cast": { "type": "keyword" },
      "director": { "type": "keyword" },
      "rating": { "type": "keyword" },
      "popularity_score": { "type": "float" }
    }
  }
}
```

**Upload CSV:** Use Kibana's **Data Visualizer → Upload File** feature to upload `content_catalog.csv`

---

#### **Create user_preferences index (lookup mode)**

```json
PUT /user_preferences
{
  "settings": {
    "index.mode": "lookup",
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "user_id": { "type": "keyword" },
      "subscriber_tenure_days": { "type": "integer" },
      "preferred_themes": { "type": "keyword" },
      "disliked_themes": { "type": "keyword" },
      "avoided_genres": { "type": "keyword" },
      "favorite_genres": { "type": "keyword" },
      "preference_vector": { "type": "dense_vector", "dims": 768 },
      "viewing_session_count": { "type": "integer" },
      "cold_start_flag": { "type": "boolean" },
      "last_updated": { "type": "date" },
      "trust_score": { "type": "float" },
      "avg_watch_completion_rate": { "type": "float" }
    }
  }
}
```

**Upload CSV:** `user_preferences.csv`

---

#### **Create viewing_history index (standard mode for events)**

```json
PUT /viewing_history
{
  "settings": {
    "number_of_shards": 3
  },
  "mappings": {
    "properties": {
      "event_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "content_id": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "event_timestamp": { "type": "date" },
      "watch_duration_seconds": { "type": "integer" },
      "completion_percentage": { "type": "float" },
      "skip_reason": { "type": "keyword" },
      "recommendation_source": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "device_type": { "type": "keyword" }
    }
  }
}
```

**Upload CSV:** `viewing_history.csv`

---

#### **Create recommendation_explanations index (lookup mode)**

```json
PUT /recommendation_explanations
{
  "settings": {
    "index.mode": "lookup",
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "explanation_id": { "type": "keyword" },
      "recommendation_pattern": { "type": "keyword" },
      "recommended_content_id": { "type": "keyword" },
      "explanation_text": { "type": "text" },
      "reasoning_factors": { "type": "keyword" },
      "confidence_score": { "type": "float" },
      "user_feedback_score": { "type": "float" },
      "theme_overlap": { "type": "keyword" }
    }
  }
}
```

**Upload CSV:** `recommendation_explanations.csv`

---

#### **Create content_themes index (lookup mode)**

```json
PUT /content_themes
{
  "settings": {
    "index.mode": "lookup",
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "theme_id": { "type": "keyword" },
      "theme_name": { "type": "text", "fields": {"keyword": {"type": "keyword"}} },
      "theme_category": { "type": "keyword" },
      "related_themes": { "type": "keyword" },
      "theme_description": { "type": "text" },
      "content_count": { "type": "integer" },
      "avg_engagement_score": { "type": "float" }
    }
  }
}
```

**Upload CSV:** `content_themes.csv`

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex business questions about Verizon FIOS's recommendation system."

**Sample questions to demonstrate:**

1. **Cross-dataset ROI analysis:**
   *"What's the relationship between cold start users and trust scores? Show me the average trust score for users with less than 5 viewing sessions versus those with more than 40 sessions."*
   
   **What this shows:** Agent joins user_preferences with viewing_history, segments by cold_start_flag, calculates trust score differences. Demonstrates the 18% new subscriber dissatisfaction pain point.

2. **Negative signal detection:**
   *"Which content items are being skipped most frequently by users who have them in their disliked themes? Give me the top 10 content titles with the highest skip rates."*
   
   **What this shows:** Joins viewing_history (skip events) with content_catalog and user_preferences, proving the system can detect when binary recommendation logic fails.

3. **Semantic theme expansion:**
   *"For users flagged as cold start, what are the most common preferred themes, and what related themes should we explore to accelerate their preference model development?"*
   
   **What this shows:** Multi-dataset join across user_preferences and content_themes, using semantic relationships to address cold start reduction from 20-40 sessions to 3-5 sessions.

4. **Explainability gap analysis:**
   *"What percentage of our recommendations have explanations with user feedback scores above 70? Break this down by recommendation pattern type."*
   
   **What this shows:** Analyzes recommendation_explanations to quantify the 42% trust issue, showing which explanation patterns work best.

5. **Search success rate by method:**
   *"Compare completion rates for content discovered through search versus recommendations. Which search terms have the lowest engagement rates?"*
   
   **What this shows:** Joins viewing_history with content_catalog, segments by recommendation_source, addresses the 34% search dismissal rate.

6. **Genre avoidance effectiveness:**
   *"Are we successfully filtering out avoided genres? Show me instances where users with avoided genres still received and skipped content from those genres."*
   
   **What this shows:** Complex join detecting recommendation system failures, proving the need for negative preference learning.

7. **Thematic similarity discovery:**
   *"What are the top 5 theme combinations that drive the highest watch completion rates? Which themes should we prioritize for semantic content discovery?"*
   
   **What this shows:** Multi-dimensional preference understanding beyond genre matching, analyzing theme combinations for engagement.

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "Verizon FIOS wants to understand their cold start problem. Let's find out: What's the distribution of users by viewing session count, and how many are in the cold start zone?"

**Copy/paste into console:**

```esql
FROM user_preferences
| STATS 
    total_users = COUNT(*),
    cold_start_users = COUNT(*) WHERE cold_start_flag == true,
    avg_sessions = AVG(viewing_session_count)
  BY cold_start_flag
| SORT cold_start_flag DESC
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our user preference data
- STATS: Aggregate with conditional counting and grouping
- BY cold_start_flag: Segment users into cold start vs established
- SORT and implicit LIMIT: Show results clearly

The syntax is intuitive - it reads like English. You can immediately see what percentage of your 4.2 million users are struggling with cold start."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to understand the business impact. We need to see trust scores and completion rates for cold start users versus established users."

**Copy/paste:**

```esql
FROM user_preferences
| EVAL 
    session_category = CASE(
      viewing_session_count < 5, "cold_start",
      viewing_session_count < 20, "warming",
      viewing_session_count < 40, "established",
      "power_user"
    )
| STATS 
    user_count = COUNT(*),
    avg_trust = ROUND(AVG(trust_score), 2),
    avg_completion = ROUND(AVG(avg_watch_completion_rate) * 100, 2),
    avg_tenure = ROUND(AVG(subscriber_tenure_days), 0)
  BY session_category
| EVAL 
    trust_gap = avg_trust - 70,
    completion_pct = CONCAT(TO_STRING(avg_completion), "%")
| SORT avg_trust DESC
```

**Run and highlight:** "Key additions:
- EVAL with CASE: Creates meaningful user segments on-the-fly
- Multiple STATS: Aggregating trust, completion, and tenure metrics simultaneously
- Second EVAL: Calculates trust gap from target threshold of 70
- ROUND and CONCAT: Formatting for business readability
- This directly quantifies the 18% new subscriber dissatisfaction issue

Notice how cold start users likely have significantly lower trust scores - that's your $M problem right there."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine viewing behavior with content data to understand what's being skipped. We'll join viewing_history with content_catalog to see which genres are being dismissed most."

**Copy/paste:**

```esql
FROM viewing_history
| WHERE event_type == "skip" AND event_timestamp > NOW() - 30 days
| STATS skip_count = COUNT(*) BY content_id
| SORT skip_count DESC
| LIMIT 100
| LOOKUP JOIN content_catalog ON content_id
| STATS 
    total_skips = SUM(skip_count),
    unique_content = COUNT(*),
    avg_skips_per_content = ROUND(AVG(skip_count), 1)
  BY genres
| SORT total_skips DESC
| LIMIT 10
```

**Run and explain:** "Magic happening here:
- Start with viewing_history skip events from last 30 days
- Aggregate skips per content item
- LOOKUP JOIN: Enriches with content_catalog data (title, genres, themes)
- Now we can analyze skip patterns by genre
- For LOOKUP JOIN to work, content_catalog must have 'index.mode: lookup'

This reveals which genres are causing the 34% search dismissal rate. If you see genres here that match users' avoided_genres, your filtering isn't working."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated query that detects recommendation system failures. We're finding users who have avoided genres in their preferences but still received and skipped content from those genres. This is the negative preference learning gap."

**Copy/paste:**

```esql
FROM viewing_history
| WHERE event_type == "skip" 
  AND skip_reason == "not-interested"
  AND event_timestamp > NOW() - 14 days
  AND recommendation_source == "recommendation"
| STATS skip_count = COUNT(*) BY user_id, content_id
| LOOKUP JOIN user_preferences ON user_id
| LOOKUP JOIN content_catalog ON content_id
| WHERE avoided_genres IS NOT NULL AND genres IS NOT NULL
| EVAL 
    genre_array = SPLIT(genres, ","),
    avoided_array = avoided_genres
| WHERE MV_MATCH(genre_array, avoided_array)
| STATS 
    failed_recommendations = SUM(skip_count),
    affected_users = COUNT_DISTINCT(user_id),
    problematic_content = COUNT_DISTINCT(content_id)
  BY genres
| EVAL 
    failure_rate_indicator = CASE(
      failed_recommendations > 100, "CRITICAL",
      failed_recommendations > 50, "HIGH",
      failed_recommendations > 20, "MEDIUM",
      "LOW"
    )
| SORT failed_recommendations DESC
| LIMIT 15
```

**Run and break down:** 
"This query is doing heavy lifting:

1. **Filter recent skip events** from recommendations (not search/browse)
2. **Join with user_preferences** to get their avoided_genres list
3. **Join with content_catalog** to get actual content genres
4. **WHERE MV_MATCH**: Multi-value field matching - checks if any content genre appears in user's avoided list
5. **Aggregate failures** by genre, counting distinct users and content
6. **Classify severity** with CASE logic for prioritization

**Business impact:** This query directly identifies the gap where binary recommendation logic fails. Every record here represents a user who explicitly said 'I don't like this genre' but your system recommended it anyway. 

If you see hundreds or thousands of failures, that's why users don't trust your recommendations. This is the data that justifies investing in negative preference learning and the explainability features we're discussing today."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `verizon-fios-recommendation-analyst`

**Display Name:** `Verizon FIOS Recommendation Intelligence Agent`

**Custom Instructions:** 
```
You are an AI assistant specialized in analyzing Verizon FIOS streaming content recommendations and personalization systems. You have access to viewing history, user preferences, content catalog, recommendation explanations, and thematic taxonomy data.

Your primary objectives:
1. Identify cold start problems and quantify their business impact on subscriber satisfaction
2. Detect recommendation system failures, especially where negative preferences are ignored
3. Analyze semantic content discovery patterns and thematic similarity effectiveness
4. Evaluate explainability and trust metrics for recommendations
5. Provide actionable insights for improving personalization accuracy

When analyzing data:
- Always consider the cold start context (users with <5 sessions)
- Highlight instances where avoided genres or disliked themes appear in recommendations
- Calculate trust score impacts and completion rate differences
- Identify semantic search opportunities beyond keyword matching
- Recommend thematic expansions for preference modeling

Be specific with numbers, percentages, and business impact. Focus on the pain points: cold start duration, fragmented data, lack of explainability, ignored negative signals, and semantic search gaps.
```

---

### **Creating Tools**

#### **Tool 1: Cold Start Analysis**

**Tool Name:** `analyze_cold_start_impact`

**Description:** 
```
Analyzes users in cold start phase (fewer than 5 viewing sessions) to quantify business impact. Calculates average trust scores, completion rates, and tenure for cold start users versus established users. Identifies how long users remain in cold start and the satisfaction gap. Use this to measure progress toward reducing cold start from 20-40 sessions to 3-5 sessions.
```

**ES|QL Query:**
```esql
FROM user_preferences
| EVAL session_bucket = CASE(
    viewing_session_count < 5, "cold_start_0_5",
    viewing_session_count < 10, "warming_5_10", 
    viewing_session_count < 20, "developing_10_20",
    viewing_session_count < 40, "established_20_40",
    "mature_40plus"
  )
| STATS 
    user_count = COUNT(*),
    avg_trust_score = ROUND(AVG(trust_score), 2),
    avg_completion_rate = ROUND(AVG(avg_watch_completion_rate) * 100, 2),
    avg_tenure_days = ROUND(AVG(subscriber_tenure_days), 0)
  BY session_bucket
| EVAL trust_gap_from_target = avg_trust_score - 70
| SORT user_count DESC
```

---

#### **Tool 2: Negative Preference Failure Detection**

**Tool Name:** `detect_ignored_negative_preferences`

**Description:**
```
Identifies recommendation system failures where users received content from genres they explicitly avoid or themes they dislike. Joins viewing history (skip events) with user preferences (avoided_genres, disliked_themes) and content catalog. Returns count of failed recommendations, affected users, and problematic content items. Critical for measuring the gap in negative preference learning.
```

**ES|QL Query:**
```esql
FROM viewing_history
| WHERE event_type == "skip" 
  AND event_timestamp > NOW() - 30 days
  AND recommendation_source == "recommendation"
| STATS skip_count = COUNT(*) BY user_id, content_id
| LOOKUP JOIN user_preferences ON user_id  
| LOOKUP JOIN content_catalog ON content_id
| WHERE avoided_genres IS NOT NULL
| STATS 
    total_failed_recs = SUM(skip_count),
    affected_users = COUNT_DISTINCT(user_id),
    problem_content_items = COUNT_DISTINCT(content_id),
    avg_skips_per_user = ROUND(AVG(skip_count), 1)
  BY genres
| SORT total_failed_recs DESC
| LIMIT 20
```

---

#### **Tool 3: Semantic Theme Discovery Performance**

**Tool Name:** `analyze_thematic_similarity_engagement`

**Description:**
```
Evaluates content discovery effectiveness using thematic similarity versus traditional genre matching. Analyzes viewing history completion rates for content discovered through different methods. Identifies which theme combinations drive highest engagement. Use this to optimize semantic content discovery and preference-aware ranking.
```

**ES|QL Query:**
```esql
FROM viewing_history
| WHERE event_type == "complete" 
  AND event_timestamp > NOW() - 60 days
| LOOKUP JOIN content_catalog ON content_id
| WHERE themes IS NOT NULL
| STATS 
    view_count = COUNT(*),
    avg_completion_pct = ROUND(AVG(completion_percentage), 2),
    unique_users = COUNT_DISTINCT(user_id)
  BY themes, recommendation_source
| WHERE view_count > 50
| SORT avg_completion_pct DESC
| LIMIT 30
```

---

#### **Tool 4: Explainability Trust Metrics**

**Tool Name:** `measure_explanation_effectiveness`

**Description:**
```
Analyzes recommendation explanation performance to address the 42% trust gap from black-box collaborative filtering. Joins recommendation explanations with user feedback scores, breaking down by recommendation pattern type. Identifies which explanation approaches build user trust and which need improvement.
```

**ES|QL Query:**
```esql
FROM recommendation_explanations
| STATS 
    explanation_count = COUNT(*),
    avg_confidence = ROUND(AVG(confidence_score), 2),
    avg_user_feedback = ROUND(AVG(user_feedback_score), 2),
    high_trust_count = COUNT(*) WHERE user_feedback_score > 70
  BY recommendation_pattern
| EVAL 
    trust_percentage = ROUND(TO_DOUBLE(high_trust_count) / TO_DOUBLE(explanation_count) * 100, 1),
    trust_status = CASE(
      trust_percentage > 70, "GOOD",
      trust_percentage > 50, "MODERATE", 
      "NEEDS_IMPROVEMENT"
    )
| SORT avg_user_feedback DESC
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

#### **Warm-up Questions (establish baseline understanding):**

1. *"How many total users do we have in our user_preferences dataset, and what percentage are flagged as cold start?"*
   - Tests basic aggregation and percentage calculation

2. *"What are the top 5 most popular content genres in our catalog, and how many titles do we have in each?"*
   - Simple content_catalog analysis

3. *"Show me the distribution of viewing events by event type over the last 7 days."*
   - Time-based filtering and grouping

---

#### **Business-Focused Questions (core pain points):**

4. *"What's the average trust score for cold start users versus users with more than 40 sessions? Quantify the trust gap."*
   - Directly addresses 18% new subscriber dissatisfaction
   - Requires user_preferences segmentation and comparison

5. *"How many recommendations in the past 30 days went to users who had the recommended content's genre in their avoided_genres list? Break this down by genre."*
   - Exposes binary recommendation logic failures
   - Complex multi-dataset join (viewing_history → user_preferences → content_catalog)

6. *"For users who skip content within the first 5 minutes, what are the most common skip reasons, and which content types are skipped most?"*
   - Addresses negative signal learning gap
   - Requires viewing_history filtering and content_catalog enrichment

7. *"What percentage of our recommendation explanations have user feedback scores above 70? Which recommendation patterns perform best?"*
   - Quantifies the 42% trust issue from black-box recommendations
   - Analyzes recommendation_explanations effectiveness

---

#### **Trend Analysis Questions (discover patterns):**

8. *"Which themes appear most frequently in the preferred_themes of users with high trust scores (above 80)? Are there common theme combinations?"*
   - Identifies successful personalization patterns
   - User_preferences analysis with theme aggregation

9. *"Compare watch completion rates for content discovered through search versus recommendations versus browsing. Which method leads to highest engagement?"*
   - Addresses 34% search dismissal rate
   - Viewing_history segmented by recommendation_source

10. *"For cold start users, what's the average number of sessions before their trust score exceeds 60? Has this improved over the past 6 months?"*
    - Measures progress toward 3-5 session cold start goal
    - Time-series analysis on user_preferences

---

#### **Optimization Questions (actionable insights):**

11. *"Which disliked themes appear most frequently across all users? Should we deprioritize content with these themes in our recommendation algorithm?"*
    - Strategic content curation insight
    - User_preferences aggregation with content_catalog correlation

12. *"Identify content items that have high skip rates but are still being recommended frequently. What's causing this recommendation-reality mismatch?"*
    - System performance audit
    - Multi-dataset join: viewing_history → content_catalog with skip analysis

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language designed for analytics, not just search"
- "Piped syntax is intuitive and readable - data analysts pick it up in hours"
- "Operates on columnar blocks, not individual rows - extremely performant even on 850M viewing events"
- "Supports complex operations out of the box: LOOKUP JOINs, CASE logic, multi-value field matching, window functions"
- "No need to pre-define aggregations - ad-hoc analysis in real-time"

### **On Agent Builder:**
- "Bridges generative AI with your enterprise data in Elasticsearch"
- "No custom development required - configure tools, don't write code"
- "Works directly with existing Elasticsearch indices - no data duplication"
- "Agent automatically selects the right tool based on natural language questions"
- "Handles complex multi-step reasoning: joins, calculations, filtering, all from a simple question"
- "Built-in security: respects Elasticsearch role-based access controls"

### **On Business Value for Verizon FIOS:**
- "Democratizes data access - product managers can ask questions without waiting on data engineering"
- "Real-time insights on recommendation performance - always up-to-date, never stale"
- "Reduces cold start dissatisfaction by enabling rapid iteration on preference models"
- "Quantifies the trust gap from black-box recommendations - now you can measure explainability ROI"
- "Detects negative preference failures automatically - no more manual analysis of skip patterns"
- "Faster decision-making on content curation and algorithm tuning - hours to minutes"
- "Addresses all 5 core pain points: cold start, fragmented data, explainability, negative signals, semantic search"

### **On Verizon FIOS-Specific Impact:**
- "850 million viewing events analyzed in seconds, not hours"
- "Track progress toward 3-5 session cold start goal with daily metrics"
- "Identify the root causes of 34% search dismissal rate through semantic analysis"
- "Measure trust score improvements as you deploy explainable recommendations"
- "Unified view across 7 fragmented data sources through ES|QL joins"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (`content_catalog`, `user_preferences`, `viewing_history`, `recommendation_explanations`, `content_themes`)
- Verify field names are case-sensitive correct (e.g., `content_id` not `contentId`)
- Ensure joined indices (`content_catalog`, `user_preferences`, `recommendation_explanations`, `content_themes`) are in lookup mode
- Check date filters use correct syntax: `NOW() - 30 days`

**If LOOKUP JOIN returns no results:**
- Verify join key format is consistent (e.g., `content_id` is keyword type in both indices)
- Check that lookup index has data: `FROM content_catalog | LIMIT 1`
- Confirm lookup index has `"index.mode": "lookup"` in settings
- Ensure join key values actually overlap between datasets

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about what data they return?
- Review custom instructions - is the agent's objective well-defined?
- Verify ES|QL queries in tools are syntactically correct
- Test queries manually in Dev Tools first

**If calculations seem off:**
- Remember to use `TO_DOUBLE()` for division to avoid integer rounding
- Check for NULL values that might skew averages
- Verify date ranges are capturing the intended time period

**If multi-value field matching fails:**
- Use `MV_MATCH()` function for array field comparisons
- Ensure fields are mapped as arrays (e.g., `"type": "keyword"` allows multi-value)

---

## **🎬 Closing**

"What we've demonstrated today with Verizon FIOS streaming data:

✅ **Complex analytics across 850M+ viewing events** - queries that complete in seconds

✅ **Natural language interface** for product managers and engineers - no SQL expertise required

✅ **Real-time detection of recommendation failures** - identify when negative preferences are ignored

✅ **Quantified business impact** - measure the 18% cold start dissatisfaction and 42% trust gap

✅ **Multi-dataset joins** - unified view across content catalog, user preferences, viewing history, and explanations

✅ **Semantic theme analysis** - go beyond genre matching to understand narrative and emotional preferences

**The Verizon FIOS personalization team can deploy Agent Builder in days, not months:**
- No custom development required
- Works with existing Elasticsearch data
- Scales to billions of events
- Provides explainable AI that users trust

**Next steps:**
1. Pilot with Consumer TV Product & Personalization Engineering team
2. Connect to production Elasticsearch cluster with real viewing data
3. Iterate on tool queries based on actual use cases
4. Expand to additional use cases: content curation, A/B test analysis, churn prediction

**This isn't just better search - it's intelligent recommendation analytics that directly addresses your 5 core pain points.**

Questions?"