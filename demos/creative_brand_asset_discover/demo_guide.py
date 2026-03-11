from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class CreativeDemoGuide(DemoGuideModule):
    """Demo guide for Creative - Brand Asset Discovery"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        return '''# **Elastic Agent Builder Demo for Creative**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Brand Asset Discovery — technical and business stakeholders
**Goal:** Show how Agent Builder enables AI-powered search on Creative's brand asset catalog, template library, and visual embedding data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

**The Story We're Telling:**
Creative is building a lightweight marketing platform for small businesses — coffee shops, restaurants, real estate agents, boutiques — who need to discover and reuse their own brand assets without the complexity of enterprise tools. The pain is real: Azure AI Search struggles with multimodal content, keyword search fails when users don't know exact file names, and the MVP needs to ship before Christmas. Elastic solves all three problems today, in this demo.

---

## **🗂️ Dataset Architecture**

### **Dataset 1: `brand_asset_catalog`**
**Record Count:** 500–1,000 documents
**Primary Key:** `asset_id`
**Description:** The core catalog of every brand asset uploaded by small business accounts — logos, menu boards, product photos, social media graphics, email templates, and promotional banners. Each record is scoped to an owning business account, enabling strict multi-tenant isolation so a coffee shop never sees a restaurant's assets.

| Field | Description |
|---|---|
| `asset_id` | Unique identifier for each brand asset |
| `asset_title` | Human-readable asset name (BM25 keyword search target) |
| `asset_description` | Rich descriptive text about the asset's content and use (semantic_text field — vector search target) |
| `asset_type` | Format category: `logo`, `menu_board`, `instagram_story`, `email_template`, `banner`, etc. |
| `content_category` | Thematic grouping: `brand_identity`, `promotional`, `seasonal`, `social_media` |
| `business_vertical` | Industry segment: `coffee_shop`, `restaurant`, `retail`, `real_estate`, `saas`, `fitness` |
| `campaign_theme` | Campaign tag: `holiday_sale`, `summer_promotion`, `grand_opening`, `loyalty_program` |
| `color_palette_tags` | Color metadata for visual filtering |
| `file_format` | `PNG`, `SVG`, `MP4`, `PDF`, etc. |
| `owner_account_id` | Tenant scoping key — every query filters on this for data isolation |
| `upload_date` | ISO timestamp of asset ingestion |
| `reuse_count` | Number of times this asset has been used in campaigns — proxy for popularity |
| `aspect_ratio` | Dimensions ratio: `1:1`, `16:9`, `9:16`, `4:5` |
| `is_active` | Boolean — soft-delete flag; all live queries filter `is_active == true` |

---

### **Dataset 2: `template_library`**
**Record Count:** 500–1,000 documents
**Primary Key:** `template_id`
**Description:** A shared library of ready-to-customize marketing templates spanning all industries and platforms. Templates are tagged by industry, campaign type, and target platform. This dataset powers the "recommended templates" experience — when a user finds a product photo, the platform suggests matching email and social templates.

| Field | Description |
|---|---|
| `template_id` | Unique identifier for each template |
| `template_name` | Short display name (BM25 keyword search target) |
| `template_description` | Detailed description of template purpose, visual style, and use case (semantic_text field) |
| `template_category` | High-level type: `email`, `social_post`, `banner`, `story`, `lookbook` |
| `industry_tag` | Vertical filter: `restaurant`, `retail`, `fitness`, `real_estate`, `coffee_shop` |
| `campaign_type` | Campaign classification: `seasonal_promotion`, `product_launch`, `loyalty`, `event` |
| `platform_target` | Intended channel: `instagram`, `email`, `facebook`, `print`, `website` |
| `customization_complexity` | `low`, `medium`, `high` — indicates editing effort required |
| `popularity_score` | Numeric engagement score based on usage and downloads |
| `last_updated` | ISO timestamp of most recent template revision |
| `is_premium` | Boolean — `false` = free tier, `true` = paid; demo filters to free templates |
| `is_active` | Boolean — soft-delete flag |

---

### **Dataset 3: `visual_asset_embeddings`**
**Record Count:** 500–1,000 documents
**Primary Key:** `embedding_id`
**Description:** Multimodal embedding records generated from visual assets — photos, video keyframes, and graphics. Each record contains a natural language caption describing the visual content of the source asset, enabling text-to-image semantic search. The `source_asset_id` field links back to `brand_asset_catalog` for downstream enrichment and cross-modal template suggestions.

| Field | Description |
|---|---|
| `embedding_id` | Unique identifier for the embedding record |
| `asset_ref_title` | Human-readable title mirrored from the source asset |
| `visual_caption` | AI-generated natural language description of the visual content (semantic_text field — the primary search target) |
| `source_asset_id` | Foreign key linking back to `brand_asset_catalog.asset_id` |
| `embedding_model_version` | Model used to generate the embedding (e.g., `clip-v2`, `e5-large`) |
| `modality` | Asset type: `image`, `video_keyframe`, `graphic` |
| `owner_account_id` | Tenant scoping key — mirrors the owning business account |
| `capture_date` | ISO timestamp of when the embedding was generated |

---

## **🌋 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: The `visual_asset_embeddings` and `template_library` indices that will be used in JOIN operations must have `"index.mode": "lookup"` set at creation time. This cannot be changed after index creation.**

---

#### **Uploading `brand_asset_catalog`**

1. Navigate to **Kibana → Machine Learning → Data Visualizer → File Upload**
2. Upload the `brand_asset_catalog.csv` file
3. On the **Import** screen, set the index name to: `brand_asset_catalog`
4. Expand **Advanced Settings** and add the following mapping override for the semantic field:
   ```json
   {
     "mappings": {
       "properties": {
         "asset_description": {
           "type": "semantic_text",
           "inference_id": ".multilingual-e5-small-elasticsearch"
         }
       }
     }
   }
   ```
5. Click **Import** and wait for confirmation
6. Verify record count: run `FROM brand_asset_catalog | STATS COUNT()` — expect 500–1,000

---

#### **Uploading `template_library`**

1. Navigate to **Kibana → Machine Learning → Data Visualizer → File Upload**
2. Upload the `template_library.csv` file
3. On the **Import** screen, set the index name to: `template_library`
4. Expand **Advanced Settings** and add:
   ```json
   {
     "settings": {
       "index.mode": "lookup"
     },
     "mappings": {
       "properties": {
         "template_description": {
           "type": "semantic_text",
           "inference_id": ".multilingual-e5-small-elasticsearch"
         }
       }
     }
   }
   ```
5. Click **Import** and verify
6. Confirm with: `FROM template_library | STATS COUNT()`

---

#### **Uploading `visual_asset_embeddings`**

1. Navigate to **Kibana → Machine Learning → Data Visualizer → File Upload**
2. Upload the `visual_asset_embeddings.csv` file
3. On the **Import** screen, set the index name to: `visual_asset_embeddings`
4. Expand **Advanced Settings** and add:
   ```json
   {
     "settings": {
       "index.mode": "lookup"
     },
     "mappings": {
       "properties": {
         "visual_caption": {
           "type": "semantic_text",
           "inference_id": ".multilingual-e5-small-elasticsearch"
         }
       }
     }
   }
   ```
5. Click **Import** and verify
6. Confirm with: `FROM visual_asset_embeddings | STATS COUNT()`

---

### **Step 2: Verify Semantic Inference is Running**

Navigate to **Kibana → Stack Management → Machine Learning → Trained Models** and confirm the `.multilingual-e5-small-elasticsearch` model shows status **Started**. If it shows **Not started**, click the start button and wait 60–90 seconds before proceeding.

### **Step 3: Pre-warm the Agent**

Open the Agent Builder interface and confirm the Creative Brand Asset Discovery agent is loaded with all tools active. Run one warm-up question privately before the customer joins to ensure inference endpoints are warm and response times are fast.

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to the AI Agent chat interface
- Have the Creative Brand Asset Discovery agent already configured with all tools visible
- Zoom in on the chat window so the audience can read responses clearly
- Keep Dev Tools closed for now — this section is about the *experience*, not the mechanics

### **Demo Script**

**Presenter:** "Before we go under the hood, let me show you what we're actually building toward. This is the end state — a conversational AI assistant that any small business owner can use to find their brand assets, get template recommendations, and assemble campaign materials, without knowing anything about search technology."

**Presenter:** "I'm going to ask it a few questions, starting simple and getting progressively more interesting."

---

### **Sample Questions to Demonstrate**

**Question 1 — Basic Asset Discovery (Coffee Shop Use Case):**
> *"Find logo variations and menu board graphics for my coffee shop account."*

**What to narrate:** "Notice it returns ranked results from the brand asset catalog, scoped only to the coffee shop account. No other business's assets appear. That's multi-tenant isolation working automatically."

---

**Question 2 — Semantic Understanding (Restaurant Use Case):**
> *"I'm a restaurant manager. Show me Italian food images I can use for an Instagram story."*

**What to narrate:** "The user said 'Italian food' — they didn't say 'pasta' or 'cuisine photography' or 'food and beverage collateral.' Watch how the agent finds assets tagged with those terms anyway. That's semantic search — it understands *meaning*, not just keywords."

---

**Question 3 — Cross-Asset Campaign Assembly (E-Commerce Use Case):**
> *"I'm running a holiday sale. What product images, discount badges, and email templates do I have available?"*

**What to narrate:** "Now it's searching across both the brand asset catalog and the template library in a single turn. The agent is orchestrating multiple tools behind the scenes — the user just asked one question."

---

**Question 4 — Typo-Tolerant Search (Small Business Reality):**
> *"Find me 'loggo variatons' and 'menue boards' for my new location setup."*

**What to narrate:** "Real small business owners don't type perfectly. Watch — despite the typos, the agent returns exactly the right assets. Fuzzy matching with AUTO edit-distance means zero-result failures are essentially eliminated. This is a huge deal for user retention in an MVP."

---

**Question 5 — Visual Similarity via Caption Search (Fitness Use Case):**
> *"I uploaded a workout video. Find me similar fitness content in my library and suggest matching promotional templates."*

**What to narrate:** "This one is multimodal. The agent is searching the visual embeddings index using a natural language description of the video's visual content — matching on AI-generated captions, not file names. Then it cross-references the template library to suggest promotional banners that match the fitness theme."

---

**Question 6 — AI-Generated Campaign Guidance (RAG):**
> *"Which of my customer testimonial assets are most ready for a B2B campaign? Give me a recommendation, not just a list."*

**What to narrate:** "This is the most powerful capability. The agent isn't just retrieving assets — it's reading them and generating a campaign recommendation. That answer is grounded in the actual asset data in Elasticsearch. It's not a generic AI response — it's specific to this business's actual content library."

---

**Question 7 — Faceted Discovery (Real Estate Use Case):**
> *"Show me modern kitchen photos from my property listings that I can use alongside listing description templates."*

**What to narrate:** "Real estate agents need to match property photos with listing copy templates. The agent finds the visual assets by their caption content — 'modern kitchen contemporary interior' — and filters to image modality only. No fitness photos, no restaurant shots. Precision matters."

---

**Transition:** "So that's the experience. Conversational, precise, multimodal, and AI-enhanced. Now let me show you exactly how this works under the hood — because everything you just saw is powered by ES|QL queries running directly inside Elasticsearch."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open **Kibana → Dev Tools Console**
- Have the three indices confirmed populated
- Use a large font size — audience needs to read the query syntax
- Keep a browser tab open to the Elasticsearch ES|QL documentation for credibility if questions arise

---

### **Query 1: Fuzzy BM25 Asset Title Search (2 minutes)**

**Presenter:** "Let's start with the most fundamental problem Creative's users face: they search for assets by name, but they don't always spell them correctly. A coffee shop manager setting up a new location might type 'loggo variatons menue boards' — and with traditional keyword search, they get zero results. That's a terrible first experience for an MVP."

**Presenter:** "Here's how we solve it. This is a fuzzy BM25 search on `asset_title`, scoped to a specific coffee shop account, with AUTO edit-distance tolerance."

**Copy/paste into console:**

```esql
FROM brand_asset_catalog METADATA _score | WHERE MATCH(asset_title, "loggo variatons menue boards", {"fuzziness": "AUTO"}) AND owner_account_id == "acct-coffee-001" AND is_active == true | KEEP asset_id, _score, asset_title, asset_description, asset_type, content_category | SORT _score DESC | LIMIT 20
```

**Run and narrate results:**

"Let's walk through what's happening here:

- **`FROM brand_asset_catalog METADATA _score`** — We're pulling from the core asset catalog and requesting the relevance score so we can rank results
- **`MATCH(asset_title, "loggo variatons menue boards", {"fuzziness": "AUTO"})`** — This is BM25 full-text search with fuzzy matching. AUTO means Elasticsearch calculates the right edit distance based on word length — short words get less tolerance, long words get more
- **`owner_account_id == "acct-coffee-001"`** — Hard tenant filter. This coffee shop only ever sees its own assets. Every single query has this filter
- **`is_active == true`** — Soft-delete filter. Archived assets don't appear
- **`SORT _score DESC | LIMIT 20`** — Best matches first, top 20

Notice the results include assets with correct titles like 'Logo Variations' and 'Menu Board Graphics' — even though the input had three spelling errors. Zero-result failure eliminated on the first attempt. For a Christmas MVP deadline, this is table stakes."

---

### **Query 2: Semantic Search — Finding Italian Food Without Saying 'Pasta' (3 minutes)**

**Presenter:** "Fuzzy search solves typos. But there's a deeper problem — users search by *concept*, not by the metadata tags that were applied when the asset was uploaded. A restaurant manager searches 'Italian food.' Their assets might be tagged 'cuisine photography,' 'food and beverage collateral,' or 'pasta dish editorial.' Traditional keyword search returns nothing. Semantic search returns everything relevant."

**Presenter:** "This query runs against `asset_description`, which is mapped as a `semantic_text` field — meaning Elasticsearch automatically generates and stores vector embeddings for every description at index time. The MATCH function detects the field type and runs vector similarity search automatically."

**Copy/paste:**

```esql
FROM brand_asset_catalog METADATA _score | WHERE MATCH(asset_description, "Italian food cuisine pasta restaurant dining") AND asset_type == "instagram_story" AND business_vertical == "restaurant" AND owner_account_id == "acct-restaurant-001" AND is_active == true | KEEP asset_id, _score, asset_title, asset_description, asset_type, content_category | SORT _score DESC | LIMIT 10
```

**Run and highlight:**

"Key things to point out:

- **Same MATCH syntax, completely different behavior** — because `asset_description` is typed as `semantic_text`, Elasticsearch runs vector similarity instead of BM25. The query author doesn't need to know which type of search is running — the field mapping handles it
- **`asset_type == "instagram_story"`** — We're filtering to a specific format. The restaurant manager wants Instagram story templates, not PDFs
- **`business_vertical == "restaurant"`** — Additional vertical scoping on top of account isolation
- **The results** — Look at the asset titles and descriptions coming back. Assets tagged as 'cuisine photography,' 'pasta dish editorial,' 'food and beverage collateral' are surfacing for the query 'Italian food.' The semantic model understands that these concepts are related

This is exactly the pain point Creative's customers have with Azure AI Search — it struggles with this kind of conceptual, multimodal content discovery. Elasticsearch handles it natively."

---

### **Query 3: True Hybrid Search — BM25 + Semantic via FORK and FUSE (3 minutes)**

**Presenter:** "Here's where it gets really interesting. BM25 is great for exact title matches. Semantic is great for conceptual meaning. But the best results come from combining both — and ES|QL's FORK and FUSE operators make this a single, readable query."

**Presenter:** "This is the query that would power the holiday sale campaign assembly feature — a retailer searches 'holiday sale' and gets product images, promotional banners, and seasonal email templates, all ranked by a unified relevance score that blends keyword precision with semantic understanding."

**Copy/paste:**

```esql
FROM brand_asset_catalog METADATA _id, _index, _score | FORK (WHERE MATCH(asset_title, "holiday sale") AND campaign_theme == "holiday_sale" AND is_active == true | EVAL search_type = "bm25" | SORT _score DESC | LIMIT 50) (WHERE MATCH(asset_description, "holiday sale seasonal promotion discount festive campaign") AND campaign_theme == "holiday_sale" AND is_active == true | EVAL search_type = "semantic" | SORT _score DESC | LIMIT 50) | FUSE | SORT _score DESC | LIMIT 20 | KEEP asset_id, _score, asset_title, asset_type, campaign_theme, search_type
```

**Run and explain:**

"Let me break down this architecture:

- **`FORK`** — Splits the query into two parallel branches that run simultaneously
  - **Branch 1 (BM25):** Keyword search on `asset_title` for 'holiday sale' — catches assets with those exact words in their name, filtered by `campaign_theme`
  - **Branch 2 (Semantic):** Vector search on `asset_description` for the enriched holiday sale concept — catches assets described as 'festive,' 'seasonal discount,' 'promotional campaign' even if the title says something completely different
  - Each branch adds a `search_type` label so we can see which retrieval path surfaced each result
- **`FUSE`** — Merges the two result sets using Reciprocal Rank Fusion (RRF). RRF is a mathematically proven rank fusion algorithm that handles the different score scales of BM25 and vector search without manual normalization
- **`SORT _score DESC | LIMIT 20`** — Final ranking by the fused score

Notice the `search_type` column in the results — some assets were found by BM25 only, some by semantic only, and some by both. The assets found by both tend to rank highest because they scored well on both dimensions. That's the power of hybrid search: better precision AND better recall than either approach alone.

For Creative's serverless deployment, this is also cost-efficient — one query, one round trip, no external re-ranking service."

---

### **Query 4: Sophisticated Weighted Hybrid with ML Reranking — Template Discovery (2 minutes)**

**Presenter:** "For our most demanding use case — a holiday campaign where a retailer needs the absolute best template recommendations — we can go even further. Two-phase retrieval: semantic search for broad recall, followed by ML reranking for precision at the top of the list."

**Presenter:** "This is the `holiday_campaign_template_rerank` query. It searches the template library, gets the top 50 semantically relevant results, then runs a cross-encoder reranking model to re-score them and promote the most contextually appropriate promotional banners and email templates to positions 1 through 10."

**Copy/paste:**

```esql
FROM template_library METADATA _score | WHERE MATCH(template_description, "holiday sale seasonal promotion discount festive") AND is_premium == false AND is_active == true | SORT _score DESC | LIMIT 50 | RERANK "holiday sale promotional banner and seasonal email campaign template" ON template_description, template_name WITH { "inference_id": ".rerank-v1-elasticsearch" } | LIMIT 10 | KEEP template_id, _score, template_name, template_description, template_category, campaign_type
```

**Run and break down:**

"This is a two-phase pipeline in a single ES|QL statement:

- **Phase 1 — Broad Recall:** `MATCH(template_description, ...)` runs semantic vector search and returns the top 50 candidates. We cast a wide net — 50 results gives the reranker plenty to work with
- **`is_premium == false`** — Free templates only. Creative's small business customers are on the free tier for the MVP
- **Phase 2 — Precision Reranking:** `RERANK ... WITH { "inference_id": ".rerank-v1-elasticsearch" }` runs a cross-encoder model that reads the full rerank query string — 'holiday sale promotional banner and seasonal email campaign template' — alongside each document's `template_description` and `template_name` simultaneously, producing a much more nuanced relevance score than vector similarity alone
- **`LIMIT 10`** — After reranking, we take only the top 10. The reranker has done the hard work of promoting the genuinely best matches

Watch the ranking change between the initial semantic scores and the final reranked scores. Templates that were in positions 8–15 after semantic search often move into the top 5 after reranking — because the cross-encoder understands the *relationship* between the query and the document, not just their independent embeddings.

This is the difference between 'good enough' search and 'this is exactly what I needed' search. For a marketing platform where template selection directly affects campaign quality, that precision gap matters."

---

### **Query 5: RAG — AI-Generated Campaign Recommendations from Asset Data (3 minutes)**

**Presenter:** "Now here is the demo climax. Everything we've shown so far returns *data* — lists of assets, ranked results, relevance scores. But what if instead of handing a small business owner a list of ten testimonial assets and saying 'good luck,' the platform could read those assets and generate an actual campaign recommendation? That's RAG — Retrieval Augmented Generation — and ES|QL supports it natively with the COMPLETION operator."

**Presenter:** "This query is designed for a SaaS company using Creative's platform who wants to know which of their customer testimonial assets are most ready for a B2B campaign. Watch what happens."

**Copy/paste:**

```esql
FROM brand_asset_catalog METADATA _score | WHERE MATCH(asset_description, "customer testimonial success story social proof B2B case study quote") AND business_vertical == "saas" AND is_active == true | SORT _score DESC | LIMIT 5 | EVAL prompt = CONCAT("You are a marketing assistant for a SaaS company. Review these brand assets and recommend which are most campaign-ready for a B2B customer testimonial campaign. Asset: ", asset_title, " Type: ", asset_type, " Description: ", asset_description, " Used in campaigns: ", TO_STRING(reuse_count), " times. Provide a concise recommendation.") | COMPLETION recommendation = prompt WITH { "inference_id": "completion-vulcan" } | KEEP asset_title, _score, asset_type, recommendation, reuse_count
```

**Run and explain — walk through each stage deliberately:**

"Let me narrate the full pipeline as it executes:

**Stage 1 — Retrieval:**
`MATCH(asset_description, "customer testimonial success story social proof B2B case study quote")` runs semantic vector search on the `asset_description` field. It surfaces the five most relevant testimonial assets for this SaaS account — even assets tagged as 'client success story' or 'social proof graphic' that don't contain the exact phrase 'customer testimonial.'

**Stage 2 — Data Preparation:**
`EVAL prompt = CONCAT(...)` builds a unique, structured prompt for each of the five retrieved documents. Notice what goes into each prompt: the asset title, the asset type, the full description, and — crucially — the `reuse_count`. The LLM is being told not just what the asset *is*, but how many times it's already been used successfully in campaigns. That's grounding the AI recommendation in real usage data.

**Stage 3 — AI Generation:**
`COMPLETION recommendation = prompt WITH { "inference_id": "completion-vulcan" }` sends each prompt to the configured LLM inference endpoint and writes the generated text back as a new column called `recommendation`. This is one LLM call per row — five assets, five LLM calls, five tailored recommendations.

**Stage 4 — Output:**
`KEEP asset_title, _score, asset_type, recommendation, reuse_count` — We return the asset metadata alongside the AI-generated recommendation. The result set is a ranked list of testimonial assets, each with a specific, data-grounded campaign recommendation written in natural language.

**Why this matters for Creative:**

- **No hallucination risk** — The LLM is only answering questions about assets that actually exist in the database. It can't invent assets that don't exist
- **No external orchestration** — This entire pipeline — retrieval, prompt construction, LLM call, response storage — runs inside a single ES|QL query. No LangChain, no Python middleware, no external API calls from application code
- **Cost control** — `LIMIT 5` before COMPLETION means exactly five LLM calls, every time. Predictable cost at scale
- **Serverless-friendly** — On Elastic Serverless, this scales to zero when not in use and scales up instantly on demand. That's the cost-effective model Creative needs for their small business customers

This is what transforms Elasticsearch from a search engine into an AI-powered marketing intelligence platform."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Navigate to:** Kibana → Agent Builder → Create New Agent

**Agent Configuration:**

| Setting | Value |
|---|---|
| **Agent ID** | `creative-brand-asset-discovery` |
| **Display Name** | `Creative Brand Asset Discovery Assistant` |
| **Model** | `gpt-4o` (or configured enterprise LLM endpoint) |
| **Inference Endpoint** | `completion-vulcan` |

**Custom Instructions:**

```
You are a brand asset discovery assistant for Creative's marketing platform.
You help small business owners — coffee shops, restaurants, retailers, real estate agents,
and fitness studios — find their brand assets, discover relevant templates, and assemble
campaign materials.

Always scope asset searches to the user's owner_account_id. Never return assets from
other accounts. When a user asks for assets, always filter is_active == true.

When a user's query is ambiguous, prefer semantic search over keyword search — they are
describing what they want, not the exact file name. When a user makes spelling errors,
use fuzzy search automatically.

When returning results, summarize what was found in plain language before listing assets.
When the user asks for recommendations or guidance (not just a list), use the RAG
completion tool to generate actionable campaign advice grounded in their actual asset data.

Always suggest relevant templates from the template_library when a user finds brand assets —
completing the 'asset + template' pairing is a core platform value proposition.
```

---

### **Creating Tools**

#### **Tool 1: Fuzzy Asset Title Search**
**Tool Name:** `fuzzy_asset_title_search`
**Description:** "Search brand assets by title with typo tolerance. Use this when the user is searching for specific assets by name and may have spelling errors. Requires owner_account_id parameter."
**Query Template:** Maps to `asset_title_search_fuzzy` — parameterized on the search string and `owner_account_id`
**When the Agent Uses It:** User says "find my logo files," "show me menu boards," or any asset search with a specific name — especially when the input looks like it might have typos

---

#### **Tool 2: Hybrid Brand Asset Search**
**Tool Name:** `hybrid_brand_asset_search`
**Description:** "Hybrid BM25 + semantic search across asset titles and descriptions using FORK and FUSE. Use this when the user is searching by concept or theme rather than exact asset name — e.g., 'Italian food,' 'holiday sale,' 'summer promotion.' Combines keyword precision with semantic understanding for best results."
**Query Template:** Maps to `thematic_asset_discovery_hybrid` and `holiday_sale_campaign_hybrid` — parameterized on search terms, `business_vertical`, `campaign_theme`, and `owner_account_id`
**When the Agent Uses It:** Any conceptual or thematic search — "find assets for my summer campaign," "show me Italian food images," "what do I have for the holiday sale"

---

#### **Tool 3: Template Discovery with Reranking**
**Tool Name:** `template_discovery_rerank`
**Description:** "Two-phase template search: semantic retrieval for broad recall followed by ML reranking for precision. Use this when the user needs template recommendations for a specific campaign type, platform, or industry. Filters to free templates by default. Returns the 10 most contextually relevant templates."
**Query Template:** Maps to `holiday_campaign_template_rerank` and `fitness_template_discovery_sophisticated` — parameterized on campaign description, `industry_tag`, and `campaign_type`
**When the Agent Uses It:** User asks "what templates do I have for X," "recommend a template for my holiday campaign," "find me an Instagram story template for my restaurant"

---

#### **Tool 4: Visual Asset Semantic Search**
**Tool Name:** `visual_asset_caption_search`
**Description:** "Text-to-image semantic search on AI-generated visual captions in the visual_asset_embeddings index. Use this when the user describes visual content — 'modern kitchen,' 'workout video,' 'outdoor dining' — rather than searching by asset name. Filters by modality (image, video_keyframe, graphic) and owner_account_id. Returns source_asset_id for downstream asset catalog lookup."
**Query Template:** Maps to `modern_kitchen_faceted_semantic` and `cross_modal_visual_similarity_search` — parameterized on visual description, `modality`, and `owner_account_id`
**When the Agent Uses It:** User uploads an image and asks "find similar assets," user describes a visual scene, user asks for "photos of" something specific

---

#### **Tool 5: AI Campaign Asset Recommendation (RAG)**
**Tool Name:** `rag_campaign_asset_recommendation`
**Description:** "Full RAG pipeline: semantic retrieval of relevant assets followed by LLM-generated campaign recommendations. Use this when the user asks for advice, recommendations, or guidance — not just a list of assets. Grounds AI recommendations in actual asset data including reuse history. Use sparingly — one call per user request, not per asset."
**Query Template:** Maps to `customer_testimonial_rag_completion` — parameterized on campaign theme, `business_vertical`, and `owner_account_id`
**When the Agent Uses It:** User asks "which assets should I use for my campaign," "recommend the best testimonial content," "what's most campaign-ready for my holiday sale"

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

---

#### **🔥 Warm-Up Questions** *(Get the audience comfortable, show immediate value)*

**Q1:** *"Find logo variations and loyalty program graphics for coffee shop account acct-coffee-001."*
> **What to watch for:** Agent uses `fuzzy_asset_title_search`, returns results scoped strictly to the coffee shop account, no other vertical's assets appear. Point out the `owner_account_id` filter working silently.

**Q2:** *"Show me all holiday sale assets that are currently active."*
> **What to watch for:** Agent uses `hybrid_brand_asset_search` with `campaign_theme == "holiday_sale"`. Both BM25 and semantic branches fire. Results include assets tagged 'festive,' 'seasonal discount,' and 'promotional campaign' — not just ones literally titled 'holiday sale.'

**Q3:** *"What free templates are available for a restaurant's Instagram stories?"*
> **What to watch for:** Agent queries `template_library` with `platform_target == "instagram"` and `industry_tag == "restaurant"` and `is_premium == false`. Reranking promotes the most contextually appropriate story templates to the top.

---

#### **💼 Business-Focused Questions** *(Connect to Creative's actual pain points)*

**Q4:** *"I'm a restaurant marketing manager and I want to find Italian food images for an Instagram campaign. I have account acct-restaurant-001."*
> **What to watch for:** Agent uses semantic search on `asset_description` with `asset_type == "instagram_story"` and `business_vertical == "restaurant"`. Surface the key insight: assets tagged 'cuisine photography' and 'pasta dish editorial' appear for the query 'Italian food.' This is the Azure AI Search gap being closed.

**Q5:** *"I'm setting up a new coffee shop location and I need loggo variatons, menue boards, and loyaltee program graphics."* *(intentional typos)*
> **What to watch for:** Agent detects the search intent despite three spelling errors, uses fuzzy search with `AUTO` fuzziness, returns correct assets. Narrate: "This is the zero-result-failure guarantee. For a small business owner who's not a power user, this is the difference between a tool they trust and one they abandon."

**Q6:** *"I'm an e-commerce retailer running a holiday sale. Assemble my complete campaign kit — product images, discount badges, and email templates."*
> **What to watch for:** Agent fires two tools in sequence — `hybrid_brand_asset_search` for brand assets from `brand_asset_catalog`, then `template_discovery_rerank` for email and banner templates from `template_library`. The response should present a coherent campaign package, not two separate lists.

**Q7:** *"I'm a real estate agent. Find modern kitchen photos from my property listings. My account is acct-realestate-001."*
> **What to watch for:** Agent uses `visual_asset_caption_search` on `visual_asset_embeddings` with `modality == "image"` and `owner_account_id == "acct-realestate-001"`. Results are kitchen and interior property photos — no fitness, restaurant, or retail assets. Point out vertical precision.

---

#### **📈 Trend & Optimization Questions** *(Show analytical depth)*

**Q8:** *"Which of my customer testimonial assets have been used most in campaigns, and which ones would you recommend for an upcoming B2B push?"*
> **What to watch for:** Agent uses the RAG tool — `rag_campaign_asset_recommendation`. The response includes not just a ranked list but AI-generated recommendations for each asset, grounded in `reuse_count` data. Point out: "The LLM is recommending assets based on actual campaign usage history, not generic marketing advice."

**Q9:** *"I'm a fitness studio owner. Find me class schedule templates and promotional banners. I only want free templates."*
> **What to watch for:** Agent uses `fitness_template_discovery_sophisticated` — the weighted LINEAR FUSE with 25% BM25 on `template_name` and 75% semantic on `template_description`. Explain the weighting: "For templates, what the template *does* matters more than what it's *called*, so we weight semantic understanding higher."

**Q10:** *"A small boutique owner wants spring collection templates. What's available that's free and relevant for a seasonal promotion?"*
> **What to watch for:** Agent uses `spring_collection_template_search` — semantic search on `template_description` filtered to `campaign_type == "seasonal_promotion"` and `is_premium == false`. Results include assets tagged 'seasonal lookbook' and 'new arrivals campaign' — not just ones literally labeled 'spring collection.' Demonstrate meaning-aware discovery.

---

#### **🔬 Technical Deep-Dive Questions** *(For technical stakeholders)*

**Q11:** *"How does the platform handle a user who uploads a workout video and wants to find similar content in their library?"*
> **What to watch for:** Agent uses `cross_modal_visual_similarity_search` — text-to-image semantic search on `visual_caption` with `modality == "video_keyframe"`. Explain: "The video's visual content is described in natural language — 'workout fitness exercise gym training class energetic athletic movement' — and matched against AI-generated captions of other assets. The `source_asset_id` field enables the downstream join back to the full asset catalog for metadata enrichment and template suggestions."

**Q12:** *"Can you show me how the hybrid search weighting works? Why would you weight semantic higher than BM25 for brand asset discovery?"*
> **What to watch for:** This is a conversation starter, not an agent query. Pivot to showing the `asset_title_search_sophisticated` query in Dev Tools — the LINEAR FUSE with `"weights": { "fork1": 0.3, "fork2": 0.7 }`. Explain: "For brand assets, the *title* is often a file name like 'IMG_2847_final_v3_FINAL.png' — it tells you almost nothing about the asset's content. The *description* is where the meaning lives. So we weight semantic understanding at 70% and title keyword matching at 30%. The weights are tunable — if your users search by exact file name more often, you'd flip the ratio."

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, purpose-built for analytics and AI-augmented search — not a bolt-on"
- "Piped syntax reads like English: FROM → WHERE → EVAL → SORT → LIMIT. Any developer can read it on day one"
- "Operates on blocks of data, not row-by-row — this is why it performs at scale without tuning"
- "FORK and FUSE make hybrid search a first-class citizen, not a workaround"
- "RERANK and COMPLETION bring the full AI pipeline inside the query layer — no external services required"

### **On Agent Builder:**
- "Bridges conversational AI and enterprise search data without custom middleware"
- "Configure, don't code — tool definitions are natural language descriptions, not API contracts"
- "Works with existing Elasticsearch indices — no data migration, no re-ingestion"
- "The agent automatically selects the right tool based on query intent — fuzzy search for typos, semantic for concepts, RAG for recommendations"
- "Multi-tenant isolation is enforced at the query layer, not the application layer — `owner_account_id` filtering happens inside every ES|QL tool"

### **On RAG & COMPLETION:**
- "Full RAG pipeline runs natively inside Elasticsearch — MATCH → RERANK → COMPLETION in a single ES|QL statement"
- "LLM answers are grounded in actual indexed data — the model can only recommend assets that exist in the database"
- "EVAL + CONCAT builds structured, data-rich prompts from real document fields — `reuse_count`, `asset_type`, `asset_description` all flow into the prompt"
- "Cost is predictable and controllable: LIMIT before COMPLETION means exactly N LLM calls, every time"
- "This transforms Creative's platform from a search tool into a marketing intelligence assistant"

### **On Multimodal Search:**
- "The `visual_asset_embeddings` index enables text-to-image search without a separate vector database"
- "AI-generated captions on `visual_caption` mean users describe what they *see*, not what the file is *named*"
- "`source_asset_id` is the bridge between visual similarity and full asset metadata — enabling cross-modal template suggestions in a single agent turn"
- "This is the specific gap Azure AI Search has with multimodal content — Elasticsearch handles it natively"

### **On Business Value for Creative:**
- "Serverless Elasticsearch scales to zero between searches — perfect for Creative's small business customers who have bursty, unpredictable usage patterns"
- "The MVP can ship before Christmas because these capabilities exist today, tested, in production-ready ES|QL"
- "Small business owners get enterprise-grade semantic search without enterprise complexity — the agent handles all the query sophistication invisibly"
- "Multi-tenant isolation at the query layer means Creative can onboard thousands of small business accounts on a single cluster without data leakage risk"
- "Every query is also an Agent Builder tool — the same ES|QL that powers the demo powers the production agent, with no translation layer"

---

## **🔧 Troubleshooting**

### **If a semantic search query returns zero results:**
- Verify the `asset_description`, `template_description`, or `visual_caption` field is mapped as `semantic_text` — check with `GET brand_asset_catalog/_mapping`
- Confirm the inference endpoint is running: navigate to **Stack Management → Machine Learning → Trained Models** and check model status
- If the model was just started, wait 90 seconds for it to warm up — inference endpoints have a cold start period

### **If FORK/FUSE returns an error:**
- Ensure you are on Elasticsearch 8.16 or later — FORK and FUSE are not available in earlier versions
- Check that both branches of the FORK use the same source index
- Verify METADATA fields `_id`, `_index`, and `_score` are all declared — FUSE requires all three

### **If RERANK returns an error:**
- Confirm the `.rerank-v1-elasticsearch` inference endpoint is deployed and started
- Check that the fields listed in the `ON` clause (`template_description`, `template_name`) exist in the index and contain text data
- RERANK must follow a SORT and LIMIT — ensure the pipeline order is correct

### **If COMPLETION returns an error:**
- Verify the `completion-vulcan` inference endpoint is configured and the underlying LLM is reachable
- Check that the `prompt` field created by EVAL CONCAT is not null — if any concatenated field is null, the entire CONCAT returns null
- Confirm LIMIT before COMPLETION is set — running COMPLETION without LIMIT on a large result set will generate unexpected LLM costs

### **If the agent returns results from the wrong account:**
- Check the tool's query template — every query must include `AND owner_account_id == "{account_id}"` as a hard filter
- Verify the agent's custom instructions specify account scoping
- Review the tool description — if it doesn't mention account scoping, the agent may not pass the parameter

### **If join-related queries fail:**
- Confirm `template_library` and `visual_asset_embeddings` were created with `"index.mode": "lookup"` — this cannot be changed after creation; the index must be recreated if it was missed
- Verify join key formats are consistent — `source_asset_id` in `visual_asset_embeddings` must match `asset_id` format in `brand_asset_catalog` exactly

---

## **🎬 Closing**

"Let me bring this back to where we started. Creative is building a brand asset discovery platform for small businesses — coffee shops, restaurants, real estate agents, boutiques — who need powerful search without enterprise complexity. They have a Christmas deadline, a serverless cost model requirement, and a specific gap with Azure AI Search on multimodal content.

What we've shown today directly addresses all three:

✅ **Fuzzy BM25 search** eliminates zero-result failures for non-technical users who don't type perfectly — zero custom code required

✅ **Semantic search on `semantic_text` fields** surfaces assets by concept and visual content, not just file names — closing the Azure AI Search multimodal gap

✅ **FORK + FUSE hybrid search** combines keyword precision and semantic understanding in a single, readable ES|QL query — better recall AND better precision than either approach alone

✅ **ML Reranking** delivers precision at the top of the list where it matters most — the first three results are the right three results

✅ **Full RAG pipeline with COMPLETION** transforms search results into AI-generated campaign recommendations, grounded in actual asset data and usage history — no hallucination, no external orchestration

✅ **Serverless Elasticsearch** scales with usage and scales to zero between uses — the cost model Creative's small business customers need

✅ **Agent Builder** wraps all of this in a conversational interface that any coffee shop manager or restaurant marketing team can use without training

Agent Builder can be deployed in days, not months. The queries you saw today are tested and running against real indexed data. The path from this demo to a production MVP is a configuration exercise, not a development project.

Questions?"

---

*Internal Reference — Demo Version 1.0 | Creative Brand Asset Discovery | Prepared for Elastic Agent Builder Demonstration*'''

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
