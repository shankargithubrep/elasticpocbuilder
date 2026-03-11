
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any


class CreativeQueryGenerator(QueryGeneratorModule):
    """Query generator for Creative - Brand Asset Discovery department.

    Implements multimodal brand asset discovery queries covering fuzzy search,
    hybrid BM25+semantic search, weighted FORK/FUSE, semantic filtering,
    cross-modal visual similarity, and RAG-powered campaign guidance.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate scripted ES|QL queries with hardcoded values.

        Covers fuzzy asset title search, hybrid asset discovery, thematic
        semantic search, holiday campaign assembly, real estate visual search,
        fitness template discovery, spring collection search, and cross-modal
        visual similarity — all with concrete filter values from the indexed
        data profile.
        """
        queries = []

        # ------------------------------------------------------------------
        # 1. Fuzzy asset title search — typo-tolerant BM25
        # ------------------------------------------------------------------
        queries.append({
            'name': 'asset_title_search_fuzzy',
            'description': (
                'Typo-tolerant BM25 fuzzy search on asset_title with AUTO '
                'edit-distance, scoped to a specific business account. '
                'Eliminates zero-result failures caused by minor spelling '
                'errors so asset discovery succeeds on the first attempt '
                'regardless of input quality.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_fuzzy_title_search',
                'description': (
                    'Finds brand assets despite misspelled search terms. '
                    'Use when users report zero results from typos like '
                    '"loggo variatons" or "menue boards". Returns ranked '
                    'assets with fuzzy BM25 matching on asset titles.'
                ),
                'tags': ['fuzzy', 'search', 'brand_assets', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _score
| WHERE MATCH(asset_title, "logo variations menu boards", {"fuzziness": "AUTO"})
  AND is_active == true
| KEEP asset_id, _score, asset_title, asset_description, asset_type, content_category, owner_account_id, reuse_count
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': (
                'Coffee shop managers and small business owners search for '
                'brand assets using misspelled terms like "loggo variatons" '
                'or "menue boards", getting zero results and being forced to '
                'browse their entire library manually.'
            ),
        })

        # ------------------------------------------------------------------
        # 2. Hybrid asset title search — FORK+FUSE RRF (BM25 + semantic)
        # ------------------------------------------------------------------
        queries.append({
            'name': 'asset_title_search_hybrid',
            'description': (
                'True hybrid FORK+FUSE combining BM25 on asset_title (text '
                'field) with semantic search on asset_description '
                '(semantic_text field), merged via RRF. Scoped to Food & '
                'Beverage vertical. Demonstrates that title keyword precision '
                'and description meaning-awareness together outperform either '
                'alone.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_hybrid_title_search',
                'description': (
                    'Combines keyword and semantic search for brand assets. '
                    'Use when users need both exact title matches and '
                    'semantically related assets from their content library. '
                    'Merges BM25 and semantic results via RRF ranking.'
                ),
                'tags': ['hybrid', 'search', 'rrf', 'brand_assets', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _id, _index, _score
| FORK
  (WHERE MATCH(asset_title, "logo variations menu boards", {"fuzziness": "AUTO"})
    AND business_vertical == "Food & Beverage"
    AND is_active == true
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(asset_description, "logo brand identity menu board coffee shop signage")
    AND business_vertical == "Food & Beverage"
    AND is_active == true
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE
| SORT _score DESC
| LIMIT 15
| KEEP asset_id, _score, asset_title, asset_type, content_category, search_type''',
            'query_type': 'scripted',
            'pain_point': (
                'Coffee shop managers need to find logo variations and menu '
                'boards by title across their own content library, combining '
                'exact keyword precision with semantic understanding of what '
                'those assets represent.'
            ),
        })

        # ------------------------------------------------------------------
        # 3. Weighted hybrid asset title search — FORK+FUSE LINEAR (expert)
        # ------------------------------------------------------------------
        queries.append({
            'name': 'asset_title_search_sophisticated',
            'description': (
                'Sophisticated FORK+FUSE LINEAR with explicit weights — 30% '
                'BM25 title matching, 70% semantic description understanding '
                '— using minmax normalization. Demonstrates tunable hybrid '
                'weighting for brand asset discovery where meaning matters '
                'more than exact title text.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_weighted_hybrid_search',
                'description': (
                    'Precision-tuned hybrid asset search with 30/70 '
                    'BM25/semantic weighting. Use for nuanced content library '
                    'exploration where brand identity meaning outweighs exact '
                    'title keywords. Delivers the highest-quality ranking for '
                    'brand asset discovery.'
                ),
                'tags': ['hybrid', 'weighted', 'linear_fuse', 'brand_assets', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _id, _index, _score
| FORK
  (WHERE MATCH(asset_title, "logo menu board", {"fuzziness": "AUTO"})
    AND business_vertical == "Food & Beverage"
    AND is_active == true
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(asset_description, "logo brand identity menu board coffee shop visual collateral")
    AND business_vertical == "Food & Beverage"
    AND is_active == true
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE LINEAR WITH {"weights": {"fork1": 0.3, "fork2": 0.7}, "normalizer": "minmax"}
| SORT _score DESC
| LIMIT 15
| KEEP asset_id, _score, asset_title, asset_type, content_category, search_type''',
            'query_type': 'scripted',
            'pain_point': (
                'Coffee shop managers need the most precise asset discovery '
                'experience — weighting semantic understanding of brand '
                'identity assets more heavily than exact title keyword '
                'matching for nuanced content library exploration.'
            ),
        })

        # ------------------------------------------------------------------
        # 4. Italian food semantic search — semantic_text on asset_description
        # ------------------------------------------------------------------
        queries.append({
            'name': 'italian_food_semantic_search',
            'description': (
                'Semantic search on asset_description (semantic_text field) '
                'for "Italian food" filtered to Food & Beverage business '
                'vertical. Surfaces pasta photos, menu layouts, and '
                'food-themed graphics even when those exact words do not '
                'appear in any metadata field — the core pain point this '
                'platform solves.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_italian_food_semantic',
                'description': (
                    'Discovers Italian food and restaurant assets by meaning, '
                    'not just keywords. Use when restaurant marketing managers '
                    'search for cuisine photography, menu layouts, and food '
                    'templates that may not be literally tagged "Italian food".'
                ),
                'tags': ['semantic', 'food_beverage', 'restaurant', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _score
| WHERE MATCH(asset_description, "Italian food cuisine pasta restaurant dining")
  AND business_vertical == "Food & Beverage"
  AND is_active == true
| KEEP asset_id, _score, asset_title, asset_description, asset_type, content_category
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': (
                'Restaurant marketing managers search for "Italian food" but '
                'the keyword system only returns assets literally tagged with '
                'that phrase, missing pasta photos tagged as "cuisine '
                'photography", menu layouts labeled "restaurant collateral", '
                'and food-themed Instagram story templates.'
            ),
        })

        # ------------------------------------------------------------------
        # 5. Thematic asset discovery — hybrid FORK+FUSE for restaurant vertical
        # ------------------------------------------------------------------
        queries.append({
            'name': 'thematic_asset_discovery_hybrid',
            'description': (
                'True hybrid FORK+FUSE (RRF) combining BM25 on asset_title '
                'with semantic on asset_description, filtered to Food & '
                'Beverage vertical. Demonstrates that hybrid ranking surfaces '
                'assets tagged as "cuisine photography" and "restaurant '
                'collateral" that pure keyword search misses entirely.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_thematic_hybrid_discovery',
                'description': (
                    'Hybrid thematic asset discovery for restaurant and food '
                    'brands. Use when marketing managers need both keyword '
                    'precision and semantic breadth to surface cuisine '
                    'photography, restaurant collateral, and food templates '
                    'from a single search.'
                ),
                'tags': ['hybrid', 'thematic', 'restaurant', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _id, _index, _score
| FORK
  (WHERE MATCH(asset_title, "Italian food restaurant")
    AND business_vertical == "Food & Beverage"
    AND is_active == true
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(asset_description, "Italian food cuisine pasta restaurant dining collateral food and beverage")
    AND business_vertical == "Food & Beverage"
    AND is_active == true
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE
| SORT _score DESC
| LIMIT 15
| KEEP asset_id, _score, asset_title, asset_type, content_category, search_type''',
            'query_type': 'scripted',
            'pain_point': (
                'Restaurant marketing managers need both keyword precision '
                '("Italian food" must be contextually relevant) and semantic '
                'breadth (surface cuisine photography, restaurant collateral, '
                'food and beverage templates) — neither pure search mode '
                'alone achieves the right balance.'
            ),
        })

        # ------------------------------------------------------------------
        # 6. Holiday sale campaign hybrid — multi-dataset asset assembly
        # ------------------------------------------------------------------
        queries.append({
            'name': 'holiday_sale_campaign_hybrid',
            'description': (
                'Hybrid FORK+FUSE (RRF) across the brand asset catalog '
                'combining BM25 on asset_title with semantic on '
                'asset_description, filtered by campaign_theme and is_active. '
                'Demonstrates complete campaign asset assembly — product '
                'images, promotional banners, and seasonal email templates — '
                'from a single hybrid search query.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_holiday_campaign_hybrid',
                'description': (
                    'Assembles complete holiday sale campaign assets in one '
                    'query. Use when e-commerce retailers need product images, '
                    'discount badges, and seasonal email templates for holiday '
                    'campaigns. Balances keyword precision with semantic '
                    'breadth for full campaign coverage.'
                ),
                'tags': ['hybrid', 'holiday', 'ecommerce', 'campaign', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _id, _index, _score
| FORK
  (WHERE MATCH(asset_title, "holiday sale")
    AND campaign_theme == "Winter Warmth"
    AND is_active == true
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(asset_description, "holiday sale seasonal promotion discount festive campaign")
    AND campaign_theme == "Winter Warmth"
    AND is_active == true
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE
| SORT _score DESC
| LIMIT 20
| KEEP asset_id, _score, asset_title, asset_type, campaign_theme, search_type''',
            'query_type': 'scripted',
            'pain_point': (
                'E-commerce retailers searching for "holiday sale" assets '
                'need results that are keyword-precise AND semantically broad '
                'enough to surface product images, discount badges, and '
                'seasonal email campaign templates that use varied '
                'terminology — neither pure keyword nor pure semantic search '
                'alone achieves this.'
            ),
        })

        # ------------------------------------------------------------------
        # 7. Holiday campaign template discovery — semantic on template_library
        # ------------------------------------------------------------------
        queries.append({
            'name': 'holiday_campaign_template_semantic',
            'description': (
                'Semantic search on template_description for broad recall of '
                'holiday sale templates filtered to free templates, sorted by '
                'popularity_score. Surfaces promotional banners and seasonal '
                'email campaign templates even when tagged with varied '
                'terminology like "festive offers" or "winter shopping event".'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_holiday_template_semantic',
                'description': (
                    'Discovers free holiday campaign templates by semantic '
                    'meaning. Use when e-commerce teams need promotional '
                    'banners and seasonal email templates for holiday '
                    'campaigns. Filters to free templates and ranks by '
                    'community popularity.'
                ),
                'tags': ['semantic', 'templates', 'holiday', 'esql'],
            },
            'query': '''FROM template_library METADATA _score
| WHERE MATCH(template_description, "holiday sale seasonal promotion discount festive")
  AND is_premium == false
  AND campaign_type == "Holiday Campaign"
| SORT _score DESC
| LIMIT 50
| KEEP template_id, _score, template_name, template_description, template_category, campaign_type, popularity_score''',
            'query_type': 'scripted',
            'pain_point': (
                'After retrieving holiday sale template candidates, the '
                'ranked list needs further refinement to ensure the most '
                'campaign-ready seasonal email templates and promotional '
                'banners appear at the top — not just assets that happen to '
                'mention "holiday" in their description.'
            ),
        })

        # ------------------------------------------------------------------
        # 8. Modern kitchen faceted semantic — visual_asset_embeddings
        # ------------------------------------------------------------------
        queries.append({
            'name': 'modern_kitchen_faceted_semantic',
            'description': (
                'Semantic search on visual_caption (semantic_text field) for '
                '"modern kitchen" with faceted filtering on modality and '
                'business context. Demonstrates that all top results belong '
                'to the real estate context — no fitness, restaurant, or '
                'retail assets appear — validating the precision requirement '
                'for vertical-specific asset discovery.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_kitchen_visual_semantic',
                'description': (
                    'Finds modern kitchen property visuals by semantic caption '
                    'matching. Use when real estate agents search for interior '
                    'property photos and need results scoped strictly to real '
                    'estate imagery, excluding unrelated verticals like '
                    'fitness or retail.'
                ),
                'tags': ['semantic', 'real_estate', 'visual', 'esql'],
            },
            'query': '''FROM visual_asset_embeddings METADATA _score
| WHERE MATCH(visual_caption, "modern kitchen contemporary interior design property real estate")
  AND modality == "image"
| KEEP embedding_id, _score, asset_ref_title, visual_caption, source_asset_id, modality
| SORT _score DESC
| LIMIT 15''',
            'query_type': 'scripted',
            'pain_point': (
                'Real estate agents searching for "modern kitchen" assets '
                'receive results diluted with fitness, restaurant, and retail '
                'content from other business verticals — without '
                'multi-dimensional faceted filtering, the result set is too '
                'noisy to be actionable.'
            ),
        })

        # ------------------------------------------------------------------
        # 9. Fitness template discovery — weighted FORK+FUSE LINEAR (expert)
        # ------------------------------------------------------------------
        queries.append({
            'name': 'fitness_template_discovery_sophisticated',
            'description': (
                'Sophisticated FORK+FUSE LINEAR with explicit weights — 25% '
                'BM25 on template_name for exact format matching, 75% '
                'semantic on template_description for fitness thematic '
                'relevance — with minmax normalization. Filtered to Fitness & '
                'Wellness industry_tag and free templates.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_fitness_template_weighted',
                'description': (
                    'Precision-weighted fitness template discovery with 25/75 '
                    'BM25/semantic scoring. Use when fitness studio owners '
                    'need class schedule and promotional banner templates that '
                    'match their industry. Filters to free templates and '
                    'surfaces the most relevant fitness content.'
                ),
                'tags': ['hybrid', 'fitness', 'templates', 'weighted', 'esql'],
            },
            'query': '''FROM template_library METADATA _id, _index, _score
| FORK
  (WHERE MATCH(template_name, "class schedule promotional banner fitness")
    AND industry_tag == "Fitness & Wellness"
    AND is_premium == false
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(template_description, "fitness studio class schedule workout promotional banner gym exercise health wellness")
    AND industry_tag == "Fitness & Wellness"
    AND is_premium == false
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE LINEAR WITH {"weights": {"fork1": 0.25, "fork2": 0.75}, "normalizer": "minmax"}
| SORT _score DESC
| LIMIT 15
| KEEP template_id, _score, template_name, template_category, industry_tag, search_type''',
            'query_type': 'scripted',
            'pain_point': (
                'Local fitness studio owners need class schedule templates '
                'and promotional banners that match their industry — but the '
                'platform must balance exact template name matching with '
                'semantic understanding of fitness content to surface the '
                'most professionally relevant and community-proven results.'
            ),
        })

        # ------------------------------------------------------------------
        # 10. Spring collection template search — semantic on template_library
        # ------------------------------------------------------------------
        queries.append({
            'name': 'spring_collection_template_search',
            'description': (
                'Semantic search on template_description for "spring '
                'collection" filtered to free templates and seasonal '
                'campaign type, sorted by popularity_score. Demonstrates '
                'meaning-aware discovery — surfaces fashion photo templates, '
                'color palette guides, and promotional copy even when tagged '
                'as "seasonal lookbook" or "new arrivals campaign".'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_spring_template_semantic',
                'description': (
                    'Discovers spring and seasonal fashion templates by '
                    'thematic meaning. Use when boutique owners search for '
                    'spring collection assets including fashion photos, color '
                    'palettes, and promotional copy. Filters to free templates '
                    'for cost-conscious small businesses.'
                ),
                'tags': ['semantic', 'fashion', 'seasonal', 'templates', 'esql'],
            },
            'query': '''FROM template_library METADATA _score
| WHERE MATCH(template_description, "spring collection seasonal fashion new arrivals fresh colors boutique retail")
  AND is_premium == false
  AND campaign_type == "Spring Collection"
| KEEP template_id, _score, template_name, template_description, template_category, campaign_type, popularity_score
| SORT _score DESC
| LIMIT 12''',
            'query_type': 'scripted',
            'pain_point': (
                'Boutique owners searching for "spring collection" assets '
                'must find fashion photos, color palette guides, and '
                'promotional copy templates based on thematic meaning — not '
                'just templates literally tagged "spring collection" — while '
                'filtering to free templates only for cost-conscious small '
                'businesses.'
            ),
        })

        # ------------------------------------------------------------------
        # 11. Cross-modal visual similarity — fitness video keyframe search
        # ------------------------------------------------------------------
        queries.append({
            'name': 'cross_modal_visual_similarity_search',
            'description': (
                'Text-to-image semantic search on visual_caption '
                '(semantic_text field) using a natural language description '
                'of the uploaded workout video\'s visual content — simulating '
                'keyframe caption matching. Filtered to graphic-design and '
                'video-frame modalities. The source_asset_id enables '
                'downstream join to retrieve full asset metadata for '
                'cross-modal template suggestions.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_crossmodal_visual_search',
                'description': (
                    'Finds visually similar fitness assets via semantic '
                    'caption matching. Use when fitness studio owners upload '
                    'a workout video and need automatic suggestions for '
                    'matching promotional banners and class schedule '
                    'templates. Bridges modalities for cross-content '
                    'recommendations.'
                ),
                'tags': ['semantic', 'visual', 'fitness', 'multimodal', 'esql'],
            },
            'query': '''FROM visual_asset_embeddings METADATA _score
| WHERE MATCH(visual_caption, "workout fitness exercise gym training class energetic athletic movement")
  AND modality IN ("graphic-design", "video-frame")
| KEEP embedding_id, _score, asset_ref_title, visual_caption, source_asset_id, modality, capture_date
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': (
                'Fitness studio owners upload a workout video and expect '
                'automatic suggestions for matching promotional banners and '
                'class schedule templates — but the platform has no mechanism '
                'to bridge modalities, forcing hours of manual curation for '
                'every campaign.'
            ),
        })

        # ------------------------------------------------------------------
        # 12. High-reuse asset analytics — top performing assets by vertical
        # ------------------------------------------------------------------
        queries.append({
            'name': 'top_reuse_assets_by_vertical',
            'description': (
                'Aggregation query identifying the highest-reused brand '
                'assets per business vertical, filtered to active assets '
                'with reuse_count above the top 10% threshold. Provides '
                'campaign teams with data-driven insight into which asset '
                'types and content categories drive the most reuse across '
                'small business accounts.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_top_reuse_analytics',
                'description': (
                    'Identifies top-performing brand assets by reuse count '
                    'across business verticals. Use to discover which asset '
                    'types and content categories drive the most campaign '
                    'reuse. Guides template prioritization and content '
                    'library curation decisions.'
                ),
                'tags': ['analytics', 'performance', 'brand_assets', 'esql'],
            },
            'query': '''FROM brand_asset_catalog
| WHERE is_active == true
  AND reuse_count > 27
| STATS
    total_assets = COUNT(*),
    avg_reuse = AVG(reuse_count),
    max_reuse = MAX(reuse_count),
    top_asset_count = COUNT(*)
  BY business_vertical, asset_type
| SORT avg_reuse DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': (
                'Small businesses need lightweight marketing platform '
                'alternative to complex enterprise tools — understanding '
                'which assets are most reused helps prioritize the content '
                'library and surface proven templates first.'
            ),
        })

        # ------------------------------------------------------------------
        # 13. Template popularity by industry and platform — cost-aware
        # ------------------------------------------------------------------
        queries.append({
            'name': 'free_template_popularity_by_industry',
            'description': (
                'Aggregation query ranking free templates by average '
                'popularity_score across industry tags and platform targets. '
                'Filtered to is_premium == false to surface the most '
                'community-proven free templates for cost-conscious small '
                'business owners who need high-quality starting points '
                'without enterprise pricing.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_free_template_popularity',
                'description': (
                    'Ranks free templates by popularity across industries and '
                    'platforms. Use to surface the most community-proven free '
                    'templates for cost-conscious small businesses. Identifies '
                    'which industries and platforms have the strongest free '
                    'template coverage.'
                ),
                'tags': ['analytics', 'templates', 'cost_effective', 'esql'],
            },
            'query': '''FROM template_library
| WHERE is_premium == false
  AND popularity_score > 8.04
| STATS
    template_count = COUNT(*),
    avg_popularity = AVG(popularity_score),
    max_popularity = MAX(popularity_score)
  BY industry_tag, platform_target
| SORT avg_popularity DESC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': (
                'Small businesses need cost-effective serverless search '
                'solution that scales with usage — surfacing the best free '
                'templates by popularity ensures small business owners get '
                'maximum value without premium costs.'
            ),
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries with ?parameter syntax.

        Covers account-scoped fuzzy asset search, vertical-filtered hybrid
        discovery, campaign theme filtering, tenant-scoped visual caption
        search, and template discovery with user-controlled industry and
        platform filters.
        """
        queries = []

        # ------------------------------------------------------------------
        # 1. Parameterized fuzzy asset title search — account-scoped
        # ------------------------------------------------------------------
        queries.append({
            'name': 'asset_title_fuzzy_search_by_account',
            'description': (
                'Parameterized typo-tolerant BM25 fuzzy search on asset_title '
                'scoped to a specific owner_account_id. Accepts user search '
                'terms and account identifier as required parameters. '
                'Eliminates zero-result failures from spelling errors while '
                'enforcing tenant isolation for multi-account deployments.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_fuzzy_search_account',
                'description': (
                    'Typo-tolerant brand asset search scoped to a specific '
                    'account. Use when users search their content library with '
                    'potentially misspelled terms. Accepts search query and '
                    'account ID to enforce tenant isolation.'
                ),
                'tags': ['fuzzy', 'search', 'parameterized', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _score
| WHERE MATCH(asset_title, ?search_query, {"fuzziness": "AUTO"})
  AND owner_account_id == ?account_id
  AND is_active == true
| KEEP asset_id, _score, asset_title, asset_description, asset_type, content_category, reuse_count
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Search terms for asset title (supports typos via AUTO fuzziness)',
                    'required': True,
                },
                {
                    'name': 'account_id',
                    'type': 'string',
                    'description': 'Owner account identifier for tenant-scoped search (e.g., acct-coffee-001)',
                    'required': True,
                },
            ],
            'pain_point': (
                'Coffee shop managers and small business owners search for '
                'brand assets using misspelled terms, getting zero results '
                'and being forced to browse their entire library manually.'
            ),
        })

        # ------------------------------------------------------------------
        # 2. Parameterized hybrid asset discovery — vertical + account scoped
        # ------------------------------------------------------------------
        queries.append({
            'name': 'hybrid_asset_discovery_by_vertical',
            'description': (
                'Parameterized FORK+FUSE hybrid search combining BM25 on '
                'asset_title with semantic on asset_description, filtered by '
                'business_vertical and owner_account_id. Accepts user query, '
                'vertical, and account as required parameters for flexible '
                'multi-tenant deployment across all business verticals.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_hybrid_vertical_search',
                'description': (
                    'Hybrid brand asset search filtered by business vertical '
                    'and account. Use when marketing teams need both keyword '
                    'precision and semantic breadth for their industry. '
                    'Supports all verticals from food & beverage to real '
                    'estate and fitness.'
                ),
                'tags': ['hybrid', 'parameterized', 'vertical', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _id, _index, _score
| FORK
  (WHERE MATCH(asset_title, ?search_query, {"fuzziness": "AUTO"})
    AND business_vertical == ?business_vertical
    AND owner_account_id == ?account_id
    AND is_active == true
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(asset_description, ?semantic_query)
    AND business_vertical == ?business_vertical
    AND owner_account_id == ?account_id
    AND is_active == true
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE
| SORT _score DESC
| LIMIT 15
| KEEP asset_id, _score, asset_title, asset_type, content_category, business_vertical, search_type''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Keyword search terms for asset title matching',
                    'required': True,
                },
                {
                    'name': 'semantic_query',
                    'type': 'string',
                    'description': 'Semantic search terms for asset description (can be more descriptive than keyword query)',
                    'required': True,
                },
                {
                    'name': 'business_vertical',
                    'type': 'string',
                    'description': 'Business vertical filter (e.g., Food & Beverage, Retail & E-commerce, Fitness & Wellness)',
                    'required': True,
                },
                {
                    'name': 'account_id',
                    'type': 'string',
                    'description': 'Owner account identifier for tenant-scoped search',
                    'required': True,
                },
            ],
            'pain_point': (
                'Small business owners need to search their own content '
                'library with both keyword precision and semantic breadth, '
                'scoped to their account and industry vertical.'
            ),
        })

        # ------------------------------------------------------------------
        # 3. Parameterized campaign theme asset search
        # ------------------------------------------------------------------
        queries.append({
            'name': 'campaign_theme_asset_search',
            'description': (
                'Parameterized semantic search on asset_description filtered '
                'by campaign_theme and asset_type. Accepts user search query, '
                'campaign theme, and optional asset type filter as required '
                'parameters. Enables e-commerce retailers and small businesses '
                'to assemble complete campaign asset sets by theme.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_campaign_theme_search',
                'description': (
                    'Finds brand assets by campaign theme and asset type. '
                    'Use when e-commerce retailers or small businesses need '
                    'to assemble complete campaign asset sets for a specific '
                    'theme like holiday sale, summer promotion, or spring '
                    'collection.'
                ),
                'tags': ['semantic', 'campaign', 'parameterized', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _score
| WHERE MATCH(asset_description, ?search_query)
  AND campaign_theme == ?campaign_theme
  AND asset_type == ?asset_type
  AND is_active == true
| KEEP asset_id, _score, asset_title, asset_description, asset_type, campaign_theme, reuse_count
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Semantic search terms describing the campaign content needed',
                    'required': True,
                },
                {
                    'name': 'campaign_theme',
                    'type': 'string',
                    'description': 'Campaign theme filter (e.g., Winter Warmth, Summer Promotion, Spring Collection)',
                    'required': True,
                },
                {
                    'name': 'asset_type',
                    'type': 'string',
                    'description': 'Asset type filter (e.g., Promotional Banner, Email Template Header, Social Media Graphic)',
                    'required': True,
                },
            ],
            'pain_point': (
                'E-commerce retailers searching for "holiday sale" assets '
                'need results scoped to specific campaign themes and asset '
                'types to assemble complete campaign sets efficiently.'
            ),
        })

        # ------------------------------------------------------------------
        # 4. Parameterized visual caption search — account-scoped multimodal
        # ------------------------------------------------------------------
        queries.append({
            'name': 'visual_caption_search_by_account',
            'description': (
                'Parameterized semantic search on visual_caption '
                '(semantic_text field) filtered by modality and '
                'owner_account_id. Accepts visual description query, '
                'modality type, and account ID as required parameters. '
                'Enables cross-modal asset discovery scoped to individual '
                'tenant accounts for fitness studios, real estate agents, '
                'and boutique owners.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_visual_caption_search',
                'description': (
                    'Semantic visual asset search by caption description '
                    'scoped to a specific account and modality. Use when '
                    'users describe visual content they are looking for and '
                    'need results from their own asset library only. Supports '
                    'cross-modal discovery for fitness, real estate, and '
                    'fashion verticals.'
                ),
                'tags': ['semantic', 'visual', 'parameterized', 'multimodal', 'esql'],
            },
            'query': '''FROM visual_asset_embeddings METADATA _score
| WHERE MATCH(visual_caption, ?visual_description)
  AND modality == ?modality
  AND owner_account_id == ?account_id
| KEEP embedding_id, _score, asset_ref_title, visual_caption, source_asset_id, modality, capture_date
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'visual_description',
                    'type': 'string',
                    'description': 'Natural language description of the visual content to find (e.g., modern kitchen with marble countertops)',
                    'required': True,
                },
                {
                    'name': 'modality',
                    'type': 'string',
                    'description': 'Visual modality filter: graphic-design, image, logo-vector, video-frame, or document-visual',
                    'required': True,
                },
                {
                    'name': 'account_id',
                    'type': 'string',
                    'description': 'Owner account identifier for tenant-scoped visual search',
                    'required': True,
                },
            ],
            'pain_point': (
                'Fitness studio owners and real estate agents need to find '
                'visual assets matching specific content descriptions within '
                'their own account, without results contaminated by other '
                'business verticals.'
            ),
        })

        # ------------------------------------------------------------------
        # 5. Parameterized free template discovery — industry + platform
        # ------------------------------------------------------------------
        queries.append({
            'name': 'free_template_discovery_by_industry',
            'description': (
                'Parameterized semantic search on template_description '
                'filtered by industry_tag and platform_target, restricted '
                'to free templates. Accepts semantic query, industry tag, '
                'and platform target as required parameters. Designed for '
                'cost-conscious small businesses discovering the best free '
                'templates for their specific industry and distribution '
                'channel.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_free_template_industry',
                'description': (
                    'Discovers free templates by industry and platform target '
                    'using semantic search. Use when small business owners '
                    'need industry-specific templates for a specific platform '
                    'like Instagram, Email, or Print without paying for '
                    'premium content.'
                ),
                'tags': ['semantic', 'templates', 'parameterized', 'cost_effective', 'esql'],
            },
            'query': '''FROM template_library METADATA _score
| WHERE MATCH(template_description, ?search_query)
  AND industry_tag == ?industry_tag
  AND platform_target == ?platform_target
  AND is_premium == false
| KEEP template_id, _score, template_name, template_description, template_category, campaign_type, popularity_score, customization_complexity
| SORT popularity_score DESC
| LIMIT 15''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Semantic search terms describing the template type needed (e.g., spring collection seasonal fashion)',
                    'required': True,
                },
                {
                    'name': 'industry_tag',
                    'type': 'string',
                    'description': 'Industry filter (e.g., Fitness & Wellness, Food & Beverage, Fashion & Apparel, Real Estate)',
                    'required': True,
                },
                {
                    'name': 'platform_target',
                    'type': 'string',
                    'description': 'Platform distribution target (e.g., Instagram Feed, Instagram Story, Email Newsletter, Pinterest)',
                    'required': True,
                },
            ],
            'pain_point': (
                'Small businesses need lightweight marketing platform '
                'alternative to complex enterprise tools — discovering free '
                'templates by industry and platform eliminates hours of '
                'manual browsing for cost-conscious owners.'
            ),
        })

        # ------------------------------------------------------------------
        # 6. Parameterized weighted hybrid template search — expert tuning
        # ------------------------------------------------------------------
        queries.append({
            'name': 'weighted_hybrid_template_search',
            'description': (
                'Parameterized FORK+FUSE LINEAR with user-controlled weights '
                'combining BM25 on template_name with semantic on '
                'template_description. Accepts search queries, industry tag, '
                'and is_premium filter as required parameters. Enables '
                'advanced users to tune the balance between exact name '
                'matching and thematic semantic relevance.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_weighted_hybrid_template',
                'description': (
                    'Advanced weighted hybrid template search with tunable '
                    'BM25/semantic balance. Use when marketing teams need '
                    'fine-grained control over template discovery — '
                    'emphasizing either exact name matching or thematic '
                    'semantic relevance depending on their campaign needs.'
                ),
                'tags': ['hybrid', 'weighted', 'templates', 'parameterized', 'esql'],
            },
            'query': '''FROM template_library METADATA _id, _index, _score
| FORK
  (WHERE MATCH(template_name, ?keyword_query, {"fuzziness": "AUTO"})
    AND industry_tag == ?industry_tag
    AND is_premium == ?is_premium
   | EVAL search_type = "bm25"
   | SORT _score DESC
   | LIMIT 50)
  (WHERE MATCH(template_description, ?semantic_query)
    AND industry_tag == ?industry_tag
    AND is_premium == ?is_premium
   | EVAL search_type = "semantic"
   | SORT _score DESC
   | LIMIT 50)
| FUSE LINEAR WITH {"weights": {"fork1": 0.25, "fork2": 0.75}, "normalizer": "minmax"}
| SORT _score DESC
| LIMIT 15
| KEEP template_id, _score, template_name, template_category, industry_tag, popularity_score, search_type''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'keyword_query',
                    'type': 'string',
                    'description': 'Keyword search terms for template name matching',
                    'required': True,
                },
                {
                    'name': 'semantic_query',
                    'type': 'string',
                    'description': 'Semantic search terms for template description (broader thematic terms)',
                    'required': True,
                },
                {
                    'name': 'industry_tag',
                    'type': 'string',
                    'description': 'Industry filter (e.g., Fitness & Wellness, Coffee & Cafe, Fashion & Apparel)',
                    'required': True,
                },
                {
                    'name': 'is_premium',
                    'type': 'boolean',
                    'description': 'Filter to premium (true) or free (false) templates',
                    'required': True,
                },
            ],
            'pain_point': (
                'Local fitness studio owners and boutique owners need class '
                'schedule templates and promotional banners that match their '
                'industry — the platform must balance exact template name '
                'matching with semantic understanding of industry content.'
            ),
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using MATCH, RERANK, and COMPLETION commands.

        Implements the customer testimonial RAG pipeline for SaaS companies,
        holiday campaign template reranking, and a general brand asset
        campaign guidance completion query — all leveraging semantic_text
        fields from the strategy datasets.
        """
        queries = []

        # ------------------------------------------------------------------
        # 1. Customer testimonial RAG — SaaS B2B campaign guidance
        # ------------------------------------------------------------------
        queries.append({
            'name': 'customer_testimonial_rag_completion',
            'description': (
                'Full RAG pipeline: semantic search on asset_description for '
                '"customer testimonial" filtered to SaaS & Technology '
                'business vertical, retrieve top 5 most reused assets, then '
                'use COMPLETION to generate an intelligent campaign-ready '
                'asset summary. Demonstrates how Creative\'s platform moves '
                'beyond search results to AI-generated campaign guidance.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_testimonial_rag_saas',
                'description': (
                    'AI-powered campaign guidance for SaaS customer '
                    'testimonial assets. Use when SaaS marketing teams need '
                    'intelligent recommendations on which video clips, quote '
                    'graphics, and case study templates are most campaign-ready '
                    'for B2B social proof campaigns. Saves hours of manual '
                    'asset review.'
                ),
                'tags': ['rag', 'completion', 'saas', 'testimonial', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _score
| WHERE MATCH(asset_description, "customer testimonial success story social proof B2B case study quote")
  AND business_vertical == "SaaS & Technology"
  AND is_active == true
| SORT reuse_count DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a marketing assistant for a SaaS company. ",
    "Review these brand assets and recommend which are most campaign-ready ",
    "for a B2B customer testimonial campaign. ",
    "Asset: ", asset_title,
    " Type: ", asset_type,
    " Description: ", asset_description,
    " Used in campaigns: ", TO_STRING(reuse_count), " times. ",
    "Provide a concise recommendation.")
| COMPLETION recommendation = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP asset_title, _score, asset_type, recommendation, reuse_count''',
            'query_type': 'rag',
            'pain_point': (
                'A small SaaS company searching for "customer testimonial" '
                'assets needs not just a list of relevant video clips, quote '
                'graphics, and case study templates — but an intelligent '
                'summary of which assets are most campaign-ready for a B2B '
                'marketing context, saving hours of manual review.'
            ),
        })

        # ------------------------------------------------------------------
        # 2. Holiday campaign template rerank + completion — precision refinement
        # ------------------------------------------------------------------
        queries.append({
            'name': 'holiday_campaign_template_rerank',
            'description': (
                'Two-phase retrieval: semantic search on template_description '
                'for broad recall of holiday sale templates, followed by '
                'RERANK to promote the most contextually relevant promotional '
                'banners and seasonal email campaign templates to top '
                'positions, then COMPLETION to generate actionable campaign '
                'deployment guidance. Demonstrates measurable precision '
                'improvement over initial semantic retrieval order.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_holiday_template_rerank',
                'description': (
                    'Two-phase holiday template discovery with ML reranking '
                    'and AI campaign guidance. Use when e-commerce teams need '
                    'the most campaign-ready seasonal templates ranked to the '
                    'top, with actionable deployment recommendations. Combines '
                    'semantic retrieval, reranking, and LLM completion.'
                ),
                'tags': ['rag', 'rerank', 'holiday', 'templates', 'esql'],
            },
            'query': '''FROM template_library METADATA _score
| WHERE MATCH(template_description, "holiday sale seasonal promotion discount festive")
  AND is_premium == false
  AND campaign_type == "Holiday Campaign"
| SORT _score DESC
| LIMIT 50
| RERANK "holiday sale promotional banner and seasonal email campaign template" ON template_description WITH {"inference_id": ".rerank-v1-elasticsearch"}
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a campaign specialist for an e-commerce retailer. ",
    "Review this holiday sale template and provide deployment guidance. ",
    "Template: ", template_name,
    " Category: ", template_category,
    " Campaign type: ", campaign_type,
    " Description: ", template_description,
    " Popularity score: ", TO_STRING(popularity_score), ". ",
    "Recommend how to use this template for maximum holiday campaign impact.")
| COMPLETION deployment_guidance = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP template_id, _score, template_name, template_category, campaign_type, deployment_guidance''',
            'query_type': 'rag',
            'pain_point': (
                'After retrieving holiday sale template candidates, the '
                'ranked list needs further ML-based refinement to ensure the '
                'most campaign-ready seasonal email templates and promotional '
                'banners appear at the top — not just assets that happen to '
                'mention "holiday" in their description.'
            ),
        })

        # ------------------------------------------------------------------
        # 3. Parameterized customer testimonial RAG — user-driven SaaS search
        # ------------------------------------------------------------------
        queries.append({
            'name': 'customer_testimonial_rag_parameterized',
            'description': (
                'Parameterized RAG pipeline accepting user-specified search '
                'query and business vertical. Performs semantic search on '
                'asset_description, retrieves top assets sorted by '
                'reuse_count, and generates AI-powered campaign guidance via '
                'COMPLETION. Enables any business vertical — not just SaaS '
                '— to receive intelligent asset recommendations for '
                'testimonial campaigns.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_testimonial_rag_param',
                'description': (
                    'Parameterized AI campaign guidance for testimonial and '
                    'social proof assets. Use when any small business needs '
                    'intelligent recommendations on their most campaign-ready '
                    'testimonial assets. Accepts search query and business '
                    'vertical as inputs for flexible deployment.'
                ),
                'tags': ['rag', 'completion', 'parameterized', 'testimonial', 'esql'],
            },
            'query': '''FROM brand_asset_catalog METADATA _score
| WHERE MATCH(asset_description, ?search_query)
  AND business_vertical == ?business_vertical
  AND is_active == true
| SORT reuse_count DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a marketing assistant. ",
    "Review these brand assets and recommend which are most campaign-ready. ",
    "Search context: ", ?search_query, ". ",
    "Asset: ", asset_title,
    " Type: ", asset_type,
    " Description: ", asset_description,
    " Campaign reuse count: ", TO_STRING(reuse_count), " times. ",
    "Provide a concise campaign-readiness recommendation.")
| COMPLETION recommendation = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP asset_title, _score, asset_type, business_vertical, recommendation, reuse_count''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Semantic search terms for asset discovery (e.g., customer testimonial success story social proof)',
                    'required': True,
                },
                {
                    'name': 'business_vertical',
                    'type': 'string',
                    'description': 'Business vertical to scope results (e.g., SaaS & Technology, Food & Beverage, Fitness & Wellness)',
                    'required': True,
                },
            ],
            'pain_point': (
                'Small SaaS companies and other small businesses need '
                'intelligent AI-powered asset recommendations that go beyond '
                'a raw search results list — delivering campaign-ready '
                'guidance that saves hours of manual asset review.'
            ),
        })

        # ------------------------------------------------------------------
        # 4. Spring collection campaign brief RAG — boutique owner guidance
        # ------------------------------------------------------------------
        queries.append({
            'name': 'spring_collection_campaign_brief_rag',
            'description': (
                'RAG pipeline for boutique owners: semantic search on '
                'template_description for spring collection templates '
                'filtered to free Fashion & Apparel templates, RERANK for '
                'precision improvement, then COMPLETION to generate a '
                'complete campaign brief. Enables boutique owners to go '
                'from template discovery to campaign strategy in a single '
                'AI-powered query.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_spring_campaign_brief_rag',
                'description': (
                    'Generates AI-powered spring collection campaign briefs '
                    'from template discovery. Use when boutique owners need '
                    'to create a complete social media campaign strategy for '
                    'spring collection launch. Discovers relevant free '
                    'templates and generates actionable campaign guidance.'
                ),
                'tags': ['rag', 'completion', 'fashion', 'seasonal', 'esql'],
            },
            'query': '''FROM template_library METADATA _score
| WHERE MATCH(template_description, "spring collection seasonal fashion new arrivals fresh colors boutique retail")
  AND is_premium == false
  AND industry_tag == "Fashion & Apparel"
| SORT _score DESC
| LIMIT 20
| RERANK "spring collection boutique fashion promotional template" ON template_description WITH {"inference_id": ".rerank-v1-elasticsearch"}
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a creative director for a boutique fashion brand. ",
    "Review this spring collection template and create a campaign brief. ",
    "Template: ", template_name,
    " Category: ", template_category,
    " Platform: ", platform_target,
    " Campaign type: ", campaign_type,
    " Description: ", template_description,
    " Popularity: ", TO_STRING(popularity_score), ". ",
    "Write a 2-sentence campaign brief for a spring collection social media launch.")
| COMPLETION campaign_brief = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP template_id, _score, template_name, template_category, platform_target, campaign_brief''',
            'query_type': 'rag',
            'pain_point': (
                'Boutique owners creating social media campaigns for spring '
                'collection launches need not just template discovery but '
                'AI-generated campaign briefs that translate template options '
                'into actionable marketing strategies — saving hours of '
                'creative planning.'
            ),
        })

        # ------------------------------------------------------------------
        # 5. Modern kitchen listing description RAG — real estate agent
        # ------------------------------------------------------------------
        queries.append({
            'name': 'modern_kitchen_listing_description_rag',
            'description': (
                'RAG pipeline for real estate agents: semantic search on '
                'visual_caption for modern kitchen imagery, then COMPLETION '
                'to generate compelling property listing description copy '
                'based on the discovered visual assets. Bridges visual asset '
                'discovery with AI-generated listing copy for complete '
                'property marketing workflow.'
            ),
            'tool_metadata': {
                'tool_id': 'creative_brand_asse_kitchen_listing_rag',
                'description': (
                    'Generates property listing descriptions from kitchen '
                    'visual assets. Use when real estate agents find modern '
                    'kitchen photos and need AI-written listing copy that '
                    'matches the visual style. Bridges visual asset discovery '
                    'with automated copywriting for property marketing.'
                ),
                'tags': ['rag', 'completion', 'real_estate', 'visual', 'esql'],
            },
            'query': '''FROM visual_asset_embeddings METADATA _score
| WHERE MATCH(visual_caption, "modern kitchen contemporary interior design luxury appliances property")
  AND modality == "image"
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a real estate copywriter. ",
    "Based on this property photo description, write a compelling listing highlight. ",
    "Photo title: ", asset_ref_title,
    " Visual description: ", visual_caption,
    " Modality: ", modality, ". ",
    "Write 1-2 compelling sentences for a property listing that highlights this kitchen feature.")
| COMPLETION listing_copy = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP embedding_id, _score, asset_ref_title, source_asset_id, listing_copy''',
            'query_type': 'rag',
            'pain_point': (
                'Real estate agents searching for "modern kitchen" assets '
                'need not just property photos and virtual tour assets — '
                'they need matching listing description copy that accurately '
                'reflects the visual content, saving hours of manual '
                'copywriting for each property listing.'
            ),
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum narrative impact.

        Builds from foundational fuzzy search through hybrid discovery,
        weighted expert queries, semantic filtering, cross-modal visual
        search, analytics, and culminates with RAG-powered AI guidance
        — demonstrating the full spectrum of Creative's brand asset
        discovery capabilities.
        """
        return [
            # Act 1: Solve the zero-result problem with fuzzy search
            'asset_title_search_fuzzy',
            'asset_title_fuzzy_search_by_account',

            # Act 2: Hybrid search — keyword precision + semantic breadth
            'asset_title_search_hybrid',
            'hybrid_asset_discovery_by_vertical',

            # Act 3: Expert weighted hybrid for maximum relevance tuning
            'asset_title_search_sophisticated',
            'weighted_hybrid_template_search',

            # Act 4: Thematic semantic discovery — Italian food use case
            'italian_food_semantic_search',
            'thematic_asset_discovery_hybrid',

            # Act 5: Campaign assembly — holiday sale e-commerce
            'holiday_sale_campaign_hybrid',
            'campaign_theme_asset_search',
            'holiday_campaign_template_semantic',
            'holiday_campaign_template_rerank',

            # Act 6: Vertical-specific visual search — real estate
            'modern_kitchen_faceted_semantic',
            'visual_caption_search_by_account',

            # Act 7: Cross-modal discovery — fitness studio
            'cross_modal_visual_similarity_search',
            'fitness_template_discovery_sophisticated',

            # Act 8: Seasonal template discovery — boutique fashion
            'spring_collection_template_search',
            'free_template_discovery_by_industry',

            # Act 9: Analytics — understanding asset performance
            'top_reuse_assets_by_vertical',
            'free_template_popularity_by_industry',

            # Act 10: RAG — AI-powered campaign intelligence
            'customer_testimonial_rag_completion',
            'customer_testimonial_rag_parameterized',
            'spring_collection_campaign_brief_rag',
            'modern_kitchen_listing_description_rag',
        ]
