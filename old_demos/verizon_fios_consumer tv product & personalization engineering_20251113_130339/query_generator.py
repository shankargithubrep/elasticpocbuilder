
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class VerizonFIOSQueryGenerator(QueryGeneratorModule):
    """Query generator for Verizon FIOS - Consumer TV Product & Personalization Engineering
    
    Addresses pain points:
    - Cold start problems (20-40 sessions to develop preference model)
    - Fragmented data sources across 7 systems
    - No explainability in recommendations (42% lower trust)
    - Binary recommendation logic ignoring negative signals
    - Keyword-based search missing semantic intent (34% dismissal rate)
    - No understanding of content attributes beyond surface metadata
    - Static content taxonomies from 2015 with 3-5 day lag
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ========================================
        # SCRIPTED QUERIES (No Parameters)
        # ========================================

        # Query 1: Semantic Content Discovery - Thematic Similarity
        queries.append({
            "name": "Semantic Content Discovery - Thematic Similarity",
            "description": "Find content with similar thematic elements using semantic understanding beyond surface-level genre matching. Enables users to discover content based on narrative complexity, emotional tone, and thematic resonance. Addresses the 34% search dismissal rate from keyword-based search.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_semantic_discovery",
                "description": "Discovers content using semantic thematic similarity. Finds shows/movies with matching narrative complexity, emotional tone, and themes beyond simple genre matching. Reduces search dismissal from 34% by understanding nuanced preferences.",
                "tags": ["semantic", "discovery", "personalization", "esql"]
            },
            "query": """FROM content_catalog METADATA _score
| WHERE MATCH(description, "complex family dynamics with moral ambiguity and redemption arc")
  AND availability == "On-demand"
| KEEP content_id, _score, title, themes, genre, narrative_complexity, tone
| SORT _score DESC
| LIMIT 15""",
            "query_type": "scripted",
            "pain_point": "Keyword-based search misses semantic intent and nuanced preferences - 34% of search results dismissed without engagement"
        })

        # Query 2: Weighted Hybrid Search - Balancing Semantic and Exact Match
        queries.append({
            "name": "Weighted Hybrid Search - Balancing Semantic and Exact Match",
            "description": "Advanced relevance tuning that balances semantic understanding (75% weight) with exact keyword matching (25% weight) for optimal content discovery. This best practice approach ensures users find both conceptually similar content and exact title matches.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_hybrid_search",
                "description": "Balances semantic similarity (75%) with exact keyword matching (25%) for optimal content discovery. Ensures users find both conceptually similar content and exact title matches, improving search relevance.",
                "tags": ["hybrid", "search", "relevance", "esql"]
            },
            "query": """FROM content_catalog METADATA _score
| WHERE MATCH(description, "psychological thriller mystery", {"boost": 0.75})
   OR MATCH(title, "psychological thriller mystery", {"boost": 0.25})
| KEEP content_id, _score, title, description, tone, narrative_complexity, genre
| SORT _score DESC
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "No understanding of content attributes beyond surface-level metadata - cannot distinguish narrative complexity, tone, or perspective"
        })

        # Query 3: Fuzzy Search for Typo-Tolerant Content Discovery
        queries.append({
            "name": "Fuzzy Search for Typo-Tolerant Content Discovery",
            "description": "Handle user typos and misspellings automatically using fuzzy matching. Critical for improving search success rates when users search by actor names, director names, or show titles with uncertain spelling.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_fuzzy_search",
                "description": "Handles user typos and misspellings automatically using fuzzy matching. Improves search success when users search by actor, director, or title names with uncertain spelling, reducing search abandonment.",
                "tags": ["fuzzy", "search", "typo-tolerance", "esql"]
            },
            "query": """FROM content_catalog METADATA _score
| WHERE MATCH(cast, "Bennedict Cumberbatch", {"fuzziness": "AUTO"})
   OR MATCH(director, "Christofer Nolan", {"fuzziness": "AUTO"})
| KEEP content_id, _score, title, cast, director, genre, release_year
| SORT _score DESC
| LIMIT 25""",
            "query_type": "scripted",
            "pain_point": "Keyword-based search misses semantic intent - users abandon searches due to typos or misspellings"
        })

        # Query 4: Cold Start Content Discovery - Thematic Expansion
        queries.append({
            "name": "Cold Start Content Discovery - Thematic Expansion",
            "description": "For new users with minimal viewing history, discover content by exploring related themes semantically. Helps reduce cold start time from 20-40 sessions to 3-5 sessions by intelligently expanding initial preferences.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_cold_start_discovery",
                "description": "Reduces cold start time from 20-40 sessions to 3-5 sessions for new subscribers. Discovers content by exploring related themes semantically, reducing 18% new subscriber dissatisfaction.",
                "tags": ["cold-start", "personalization", "themes", "esql"]
            },
            "query": """FROM content_themes METADATA _score
| WHERE MATCH(theme_description, "coming of age self discovery identity")
| MV_EXPAND related_themes
| LOOKUP JOIN content_catalog ON related_themes == themes
| KEEP content_id, _score, title, theme_name, related_themes, genre, narrative_complexity
| SORT _score DESC
| LIMIT 12""",
            "query_type": "scripted",
            "pain_point": "Cold start problems - takes 20-40 viewing sessions to develop reasonable preference model, 18% new subscriber dissatisfaction"
        })

        # Query 5: Multi-Term Precision Search with Minimum Match Threshold
        queries.append({
            "name": "Multi-Term Precision Search with Minimum Match Threshold",
            "description": "Advanced precision control requiring at least 3 out of 5 search terms to match, reducing noise in multi-keyword searches. Best practice for complex user queries with multiple optional criteria.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_precision_search",
                "description": "Controls precision by requiring at least 3 out of 5 search terms to match. Reduces noise in multi-keyword searches and improves relevance for complex user queries with multiple optional criteria.",
                "tags": ["precision", "search", "multi-term", "esql"]
            },
            "query": """FROM content_catalog METADATA _score
| WHERE MATCH(description, "female protagonist action adventure strong character development", {
    "operator": "OR",
    "minimum_should_match": 3
  })
| KEEP content_id, _score, title, description, themes, subgenres, cast
| SORT _score DESC
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "Static content taxonomies from 2015 requiring manual updates - search returns too many irrelevant results"
        })

        # Query 6: User Preference Analysis with Theme Affinity
        queries.append({
            "name": "User Preference Analysis with Theme Affinity",
            "description": "Analyze user preference maturity and theme affinity to understand how well the preference model has developed. Identifies cold start users who need accelerated personalization.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_preference_analysis",
                "description": "Analyzes user preference maturity and theme affinity across the subscriber base. Identifies cold start users needing accelerated personalization and tracks preference model development quality.",
                "tags": ["analytics", "preferences", "cold-start", "esql"]
            },
            "query": """FROM user_preferences
| WHERE profile_maturity == "Cold Start"
| MV_EXPAND liked_themes
| STATS 
    user_count = COUNT_DISTINCT(user_id),
    avg_sessions = AVG(session_count),
    theme_popularity = COUNT(*)
  BY liked_themes
| WHERE user_count > 5
| SORT theme_popularity DESC
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "Cold start problems - takes 20-40 viewing sessions to develop reasonable preference model"
        })

        # Query 7: Negative Signal Detection - Skip and Dismissal Patterns
        queries.append({
            "name": "Negative Signal Detection - Skip and Dismissal Patterns",
            "description": "Identify content that users repeatedly skip or dismiss to learn negative preferences. Critical for addressing the problem where users who skip content repeatedly still receive similar recommendations.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_negative_signals",
                "description": "Identifies content repeatedly skipped or dismissed by users to learn negative preferences. Prevents recommending similar content users have explicitly rejected, improving recommendation relevance.",
                "tags": ["analytics", "negative-signals", "personalization", "esql"]
            },
            "query": """FROM viewing_history
| WHERE skipped == true OR dismissed == true
| WHERE completion_percentage < 0.2
| STATS 
    skip_count = COUNT(*),
    avg_watch_duration = AVG(watch_duration_seconds),
    unique_users = COUNT_DISTINCT(user_id)
  BY content_id
| WHERE skip_count > 10
| LOOKUP JOIN content_catalog ON content_id
| KEEP content_id, title, genre, themes, skip_count, avg_watch_duration, unique_users
| SORT skip_count DESC
| LIMIT 25""",
            "query_type": "scripted",
            "pain_point": "Binary recommendation logic ignores negative signals and context - users who skip content repeatedly still receive similar recommendations"
        })

        # Query 8: Content Performance by Narrative Complexity
        queries.append({
            "name": "Content Performance by Narrative Complexity",
            "description": "Analyze how different narrative complexity levels perform with users. Helps understand which complexity levels resonate with different audience segments.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_complexity_performance",
                "description": "Analyzes performance of different narrative complexity levels across user segments. Identifies which complexity levels resonate with audiences to improve content recommendations and acquisition.",
                "tags": ["analytics", "performance", "content", "esql"]
            },
            "query": """FROM viewing_history
| WHERE completion_percentage > 0.7
| LOOKUP JOIN content_catalog ON content_id
| STATS 
    view_count = COUNT(*),
    avg_completion = AVG(completion_percentage),
    avg_rating = AVG(rating_given),
    unique_viewers = COUNT_DISTINCT(user_id)
  BY narrative_complexity, genre
| WHERE view_count > 20
| EVAL engagement_score = TO_DOUBLE(avg_completion) * avg_rating
| SORT engagement_score DESC
| LIMIT 30""",
            "query_type": "scripted",
            "pain_point": "No understanding of content attributes beyond surface-level metadata - cannot distinguish narrative complexity, tone, or perspective"
        })

        # Query 9: Recommendation Explanation Quality Analysis
        queries.append({
            "name": "Recommendation Explanation Quality Analysis",
            "description": "Analyze the quality and effectiveness of recommendation explanations to improve transparency and trust. Addresses the 42% of users reporting lower trust due to black-box collaborative filtering.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_explanation_quality",
                "description": "Analyzes quality and effectiveness of recommendation explanations. Improves transparency to address 42% of users reporting lower trust in black-box recommendations, building user confidence.",
                "tags": ["analytics", "explainability", "trust", "esql"]
            },
            "query": """FROM recommendation_explanations
| STATS 
    explanation_count = COUNT(*),
    avg_similarity = AVG(similarity_score),
    unique_users = COUNT_DISTINCT(user_id)
  BY reasoning_factors
| WHERE explanation_count > 10
| SORT avg_similarity DESC
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "No explainability in recommendations - 42% of users report lower trust due to black-box collaborative filtering"
        })

        # Query 10: Theme Relationship Network Analysis
        queries.append({
            "name": "Theme Relationship Network Analysis",
            "description": "Explore relationships between content themes to understand thematic connections. Helps identify opportunities for cross-theme recommendations and content discovery.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_theme_network",
                "description": "Explores relationships between content themes to identify cross-theme recommendation opportunities. Enables sophisticated content discovery beyond static 2015 taxonomies with 3-5 day update lag.",
                "tags": ["analytics", "themes", "discovery", "esql"]
            },
            "query": """FROM content_themes
| MV_EXPAND related_themes
| STATS 
    relationship_count = COUNT(*),
    unique_parent_themes = COUNT_DISTINCT(parent_theme)
  BY related_themes, emotional_tone
| WHERE relationship_count > 5
| SORT relationship_count DESC
| LIMIT 25""",
            "query_type": "scripted",
            "pain_point": "Static content taxonomies from 2015 requiring manual updates with 3-5 day lag for new content"
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Preference-Aware Content Retrieval with Negative Filtering
        queries.append({
            "name": "Preference-Aware Content Retrieval with Negative Filtering",
            "description": "Retrieve content matching user's preferred themes while actively filtering out disliked themes and avoided genres. Addresses the critical gap where users repeatedly see content they've explicitly rejected.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_preference_aware_retrieval",
                "description": "Retrieves content matching user preferences while actively filtering disliked themes and avoided genres. Prevents recommending content users have explicitly rejected, improving satisfaction.",
                "tags": ["personalization", "filtering", "preferences", "esql"]
            },
            "query": """FROM content_catalog METADATA _score
| WHERE MATCH(description, ?search_query)
| LOOKUP JOIN user_preferences ON user_id
| WHERE user_id == ?user_id
| MV_EXPAND themes
| WHERE themes IN liked_themes
| MV_EXPAND themes
| WHERE themes NOT IN disliked_themes
| WHERE genre NOT IN avoided_genres
| KEEP content_id, _score, title, themes, genre, tone, narrative_complexity
| SORT _score DESC
| LIMIT 10""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "search_query",
                    "type": "text",
                    "description": "Search query describing desired content themes (e.g., 'space exploration with scientific accuracy')",
                    "required": True
                },
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID to retrieve preferences for (e.g., 'user_1234')",
                    "required": True
                }
            ],
            "pain_point": "Binary recommendation logic ignores negative signals and context - users who skip content repeatedly still receive similar recommendations"
        })

        # Query 2: Explainable Recommendation Retrieval
        queries.append({
            "name": "Explainable Recommendation Retrieval",
            "description": "Find recommendation explanations that transparently show why content was suggested. Enables users to understand the reasoning behind recommendations and provide feedback.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_explainable_recommendations",
                "description": "Retrieves transparent recommendation explanations showing why content was suggested. Enables users to understand reasoning and provide feedback, building trust and reducing 42% trust gap.",
                "tags": ["explainability", "recommendations", "trust", "esql"]
            },
            "query": """FROM recommendation_explanations METADATA _score
| WHERE user_id == ?user_id
  AND MATCH(explanation_text, ?explanation_query)
| LOOKUP JOIN content_catalog ON content_id
| KEEP recommendation_id, _score, title, explanation_text, reasoning_factors, similarity_score, genre, themes
| SORT similarity_score DESC
| LIMIT 10""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID to retrieve explanations for (e.g., 'user_1234')",
                    "required": True
                },
                {
                    "name": "explanation_query",
                    "type": "text",
                    "description": "Query to find specific explanation types (e.g., 'similar themes to shows you enjoyed')",
                    "required": True
                }
            ],
            "pain_point": "No explainability in recommendations - 42% of users report lower trust due to black-box collaborative filtering"
        })

        # Query 3: Personalized Content Discovery by Theme and Tone
        queries.append({
            "name": "Personalized Content Discovery by Theme and Tone",
            "description": "Discover content matching user's preferred themes, tone, and complexity preferences. Enables multi-dimensional preference understanding beyond simple genre matching.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_personalized_discovery",
                "description": "Discovers content matching user's preferred themes, tone, and narrative complexity. Enables multi-dimensional preference understanding beyond simple genre matching for better personalization.",
                "tags": ["personalization", "discovery", "multi-dimensional", "esql"]
            },
            "query": """FROM content_catalog METADATA _score
| WHERE MATCH(description, ?theme_query)
| LOOKUP JOIN user_preferences ON user_id
| WHERE user_id == ?user_id
  AND tone == preferred_tone
  AND narrative_complexity == complexity_preference
| MV_EXPAND preferred_genres
| WHERE genre == preferred_genres
| KEEP content_id, _score, title, description, themes, tone, narrative_complexity, genre
| SORT _score DESC
| LIMIT 15""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "theme_query",
                    "type": "text",
                    "description": "Theme-based search query (e.g., 'redemption arc with moral complexity')",
                    "required": True
                },
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID to retrieve preferences for (e.g., 'user_1234')",
                    "required": True
                }
            ],
            "pain_point": "No understanding of content attributes beyond surface-level metadata - cannot distinguish narrative complexity, tone, or perspective"
        })

        # Query 4: User Viewing Pattern Analysis
        queries.append({
            "name": "User Viewing Pattern Analysis",
            "description": "Analyze viewing patterns for a specific user including completion rates, skip behavior, and content preferences. Helps understand user engagement and identify areas for personalization improvement.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_viewing_patterns",
                "description": "Analyzes viewing patterns including completion rates, skip behavior, and content preferences for specific users. Identifies engagement issues and personalization opportunities.",
                "tags": ["analytics", "engagement", "user-behavior", "esql"]
            },
            "query": """FROM viewing_history
| WHERE user_id == ?user_id
| LOOKUP JOIN content_catalog ON content_id
| STATS 
    total_views = COUNT(*),
    avg_completion = AVG(completion_percentage),
    skip_rate = SUM(CASE(skipped == true, 1, 0)) * 100.0 / COUNT(*),
    avg_rating = AVG(rating_given)
  BY genre, interaction_context
| WHERE total_views > 2
| EVAL engagement_score = TO_DOUBLE(avg_completion) * (100.0 - skip_rate) / 100.0
| SORT engagement_score DESC
| LIMIT 20""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID to analyze viewing patterns for (e.g., 'user_1234')",
                    "required": True
                }
            ],
            "pain_point": "Fragmented data sources preventing unified preference modeling across 7 different systems with varying latency"
        })

        # Query 5: Content Recommendation by Similarity Score Threshold
        queries.append({
            "name": "Content Recommendation by Similarity Score Threshold",
            "description": "Retrieve high-quality recommendations above a specific similarity threshold with transparent explanations. Ensures only highly relevant recommendations are shown to users.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_similarity_threshold",
                "description": "Retrieves high-quality recommendations above similarity threshold with transparent explanations. Ensures only highly relevant content is recommended, improving user trust and satisfaction.",
                "tags": ["recommendations", "quality", "threshold", "esql"]
            },
            "query": """FROM recommendation_explanations
| WHERE user_id == ?user_id
  AND similarity_score > ?min_similarity_score
| LOOKUP JOIN content_catalog ON content_id
| KEEP recommendation_id, content_id, title, explanation_text, reasoning_factors, similarity_score, genre, themes, tone
| SORT similarity_score DESC
| LIMIT 15""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID to retrieve recommendations for (e.g., 'user_1234')",
                    "required": True
                },
                {
                    "name": "min_similarity_score",
                    "type": "double",
                    "description": "Minimum similarity score threshold (0.0-1.0, e.g., 0.85 for high-quality recommendations)",
                    "required": True
                }
            ],
            "pain_point": "No explainability in recommendations - 42% of users report lower trust due to black-box collaborative filtering"
        })

        # Query 6: Cold Start User Content Onboarding
        queries.append({
            "name": "Cold Start User Content Onboarding",
            "description": "Discover diverse content across multiple themes and genres for cold start users. Accelerates preference model development by exposing new users to varied content.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_cold_start_onboarding",
                "description": "Discovers diverse content across themes and genres for cold start users. Accelerates preference model development from 20-40 sessions to 3-5 sessions, reducing new subscriber dissatisfaction.",
                "tags": ["cold-start", "onboarding", "personalization", "esql"]
            },
            "query": """FROM user_preferences
| WHERE user_id == ?user_id
  AND profile_maturity == "Cold Start"
| MV_EXPAND liked_themes
| LOOKUP JOIN content_themes ON liked_themes == theme_name
| MV_EXPAND related_themes
| LOOKUP JOIN content_catalog ON related_themes == themes
| KEEP content_id, title, genre, themes, narrative_complexity, tone, theme_name
| SORT content_id ASC
| LIMIT 20""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID for cold start onboarding (e.g., 'user_1234')",
                    "required": True
                }
            ],
            "pain_point": "Cold start problems - takes 20-40 viewing sessions to develop reasonable preference model, 18% new subscriber dissatisfaction"
        })

        # Query 7: Theme-Based Content Search with Preference Matching
        queries.append({
            "name": "Theme-Based Content Search with Preference Matching",
            "description": "Search for content by theme while matching user's tone and complexity preferences. Combines semantic search with personalization for optimal discovery.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_theme_search",
                "description": "Searches content by theme while matching user's tone and complexity preferences. Combines semantic search with personalization for optimal discovery beyond keyword matching.",
                "tags": ["search", "themes", "personalization", "esql"]
            },
            "query": """FROM content_themes METADATA _score
| WHERE MATCH(theme_description, ?theme_search_query)
| LOOKUP JOIN user_preferences ON emotional_tone == preferred_tone
| WHERE user_id == ?user_id
| MV_EXPAND related_themes
| LOOKUP JOIN content_catalog ON related_themes == themes
| WHERE narrative_complexity == complexity_preference
| KEEP content_id, _score, title, theme_name, themes, tone, narrative_complexity, genre
| SORT _score DESC
| LIMIT 15""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "theme_search_query",
                    "type": "text",
                    "description": "Theme search query (e.g., 'family relationships with emotional depth')",
                    "required": True
                },
                {
                    "name": "user_id",
                    "type": "keyword",
                    "description": "User ID to match preferences for (e.g., 'user_1234')",
                    "required": True
                }
            ],
            "pain_point": "Keyword-based search misses semantic intent and nuanced preferences - 34% of search results dismissed without engagement"
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using MATCH and COMPLETION commands
        
        Targets semantic_text fields from strategy:
        - content_catalog.description
        - recommendation_explanations.explanation_text
        - content_themes.theme_description
        """
        queries = []

        # RAG Query 1: Content Discovery Assistant
        queries.append({
            "name": "Content Discovery Assistant - Semantic Q&A",
            "description": "AI-powered content discovery assistant that understands natural language questions about content themes, narratives, and characteristics. Uses semantic search across content descriptions to provide personalized recommendations with natural language explanations.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_content_discovery_assistant",
                "description": "AI assistant for content discovery using natural language. Understands questions about themes, narratives, and characteristics to provide personalized recommendations with explanations. Reduces 34% search dismissal rate.",
                "tags": ["rag", "assistant", "discovery", "esql"]
            },
            "query": """FROM content_catalog METADATA _id
| WHERE MATCH(description, ?user_question)
  AND availability == "On-demand"
| KEEP content_id, title, description, themes, genre, tone, narrative_complexity, _id
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "Based on these TV shows and movies, answer the user's question: '", 
    ?user_question, 
    "'. Available content:\\n",
    "1. ", title, " (", genre, ") - ", description, "\\n",
    "Themes: ", TO_STRING(themes), "\\n",
    "Tone: ", tone, ", Complexity: ", narrative_complexity
  )
| COMPLETION answer = prompt WITH {{"inference_id": "completion-vulcan"}}
| KEEP content_id, title, genre, themes, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "text",
                    "description": "Natural language question about content (e.g., 'What shows explore family dynamics with emotional depth?')",
                    "required": True
                }
            ],
            "pain_point": "Keyword-based search misses semantic intent and nuanced preferences - 34% of search results dismissed without engagement"
        })

        # RAG Query 2: Recommendation Explanation Assistant
        queries.append({
            "name": "Recommendation Explanation Assistant",
            "description": "AI assistant that explains why content was recommended to users. Provides transparent, natural language explanations of recommendation reasoning to build trust and enable feedback.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_explanation_assistant",
                "description": "AI assistant explaining why content was recommended. Provides transparent reasoning in natural language to build user trust and enable feedback. Addresses 42% trust gap from black-box recommendations.",
                "tags": ["rag", "explainability", "trust", "esql"]
            },
            "query": """FROM recommendation_explanations METADATA _id
| WHERE MATCH(explanation_text, ?user_question)
| LOOKUP JOIN content_catalog ON content_id
| KEEP recommendation_id, title, explanation_text, reasoning_factors, similarity_score, genre, themes, _id
| SORT similarity_score DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "Explain these content recommendations to the user. Question: '",
    ?user_question,
    "'. Recommendations:\\n",
    "1. ", title, " (", genre, ")\\n",
    "Explanation: ", explanation_text, "\\n",
    "Reasoning: ", TO_STRING(reasoning_factors), "\\n",
    "Similarity: ", TO_STRING(similarity_score), "\\n",
    "Themes: ", TO_STRING(themes)
  )
| COMPLETION answer = prompt WITH {{"inference_id": "completion-vulcan"}}
| KEEP recommendation_id, title, explanation_text, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "text",
                    "description": "Question about recommendations (e.g., 'Why was this show recommended to me?')",
                    "required": True
                }
            ],
            "pain_point": "No explainability in recommendations - 42% of users report lower trust due to black-box collaborative filtering"
        })

        # RAG Query 3: Theme Exploration Assistant
        queries.append({
            "name": "Theme Exploration Assistant",
            "description": "AI assistant for exploring content themes and discovering related thematic elements. Helps users understand theme relationships and find content with specific narrative characteristics.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_theme_exploration_assistant",
                "description": "AI assistant for exploring content themes and discovering related thematic elements. Helps users understand theme relationships beyond static 2015 taxonomies with 3-5 day lag.",
                "tags": ["rag", "themes", "exploration", "esql"]
            },
            "query": """FROM content_themes METADATA _id
| WHERE MATCH(theme_description, ?user_question)
| KEEP theme_name, theme_description, parent_theme, related_themes, emotional_tone, narrative_elements, _id
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "Help the user explore content themes. Question: '",
    ?user_question,
    "'. Relevant themes:\\n",
    "1. ", theme_name, " (", parent_theme, " genre)\\n",
    "Description: ", theme_description, "\\n",
    "Emotional tone: ", emotional_tone, "\\n",
    "Related themes: ", TO_STRING(related_themes), "\\n",
    "Narrative elements: ", TO_STRING(narrative_elements)
  )
| COMPLETION answer = prompt WITH {{"inference_id": "completion-vulcan"}}
| KEEP theme_name, parent_theme, related_themes, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "text",
                    "description": "Question about themes (e.g., 'What themes involve personal transformation and growth?')",
                    "required": True
                }
            ],
            "pain_point": "Static content taxonomies from 2015 requiring manual updates with 3-5 day lag for new content"
        })

        # RAG Query 4: Content Comparison Assistant
        queries.append({
            "name": "Content Comparison Assistant",
            "description": "AI assistant that compares multiple pieces of content based on themes, tone, and narrative elements. Helps users understand similarities and differences to make informed viewing choices.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_content_comparison_assistant",
                "description": "AI assistant comparing content based on themes, tone, and narrative elements. Helps users understand similarities and differences for informed viewing choices, improving engagement.",
                "tags": ["rag", "comparison", "analysis", "esql"]
            },
            "query": """FROM content_catalog METADATA _id
| WHERE MATCH(description, ?comparison_query)
| KEEP content_id, title, description, themes, genre, tone, narrative_complexity, subgenres, _id
| SORT _score DESC
| LIMIT 3
| EVAL prompt = CONCAT(
    "Compare these shows/movies for the user. Question: '",
    ?comparison_query,
    "'. Content to compare:\\n",
    "1. ", title, " (", genre, ")\\n",
    "Description: ", description, "\\n",
    "Themes: ", TO_STRING(themes), "\\n",
    "Tone: ", tone, ", Complexity: ", narrative_complexity, "\\n",
    "Subgenres: ", TO_STRING(subgenres)
  )
| COMPLETION answer = prompt WITH {{"inference_id": "completion-vulcan"}}
| KEEP content_id, title, genre, themes, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "comparison_query",
                    "type": "text",
                    "description": "Comparison question (e.g., 'Compare shows with political intrigue and moral complexity')",
                    "required": True
                }
            ],
            "pain_point": "No understanding of content attributes beyond surface-level metadata - cannot distinguish narrative complexity, tone, or perspective"
        })

        # RAG Query 5: Personalized Content Advisor
        queries.append({
            "name": "Personalized Content Advisor",
            "description": "AI advisor that provides personalized content recommendations based on semantic understanding of user preferences and content characteristics. Combines preference matching with natural language explanations.",
            "tool_metadata": {
                "tool_id": "verizon_fios_consumer_t_personalized_advisor",
                "description": "AI advisor providing personalized recommendations based on semantic understanding of preferences and content. Combines preference matching with natural language explanations for better engagement.",
                "tags": ["rag", "personalization", "advisor", "esql"]
            },
            "query": """FROM content_catalog METADATA _id
| WHERE MATCH(description, ?preference_query)
  AND narrative_complexity IN ("Complex", "Very Complex")
| KEEP content_id, title, description, themes, genre, tone, narrative_complexity, cast, director, _id
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "Provide personalized content advice for this user preference: '",
    ?preference_query,
    "'. Recommended content:\\n",
    "1. ", title, " (", genre, ")\\n",
    "Description: ", description, "\\n",
    "Themes: ", TO_STRING(themes), "\\n",
    "Tone: ", tone, ", Complexity: ", narrative_complexity, "\\n",
    "Cast: ", TO_STRING(cast), ", Director: ", director
  )
| COMPLETION answer = prompt WITH {{"inference_id": "completion-vulcan"}}
| KEEP content_id, title, genre, themes, tone, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "preference_query",
                    "type": "text",
                    "description": "User preference description (e.g., 'I enjoy complex narratives with strong character development')",
                    "required": True
                }
            ],
            "pain_point": "Cold start problems - takes 20-40 viewing sessions to develop reasonable preference model"
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Progression strategy:
        1. Start with semantic discovery to show advanced search
        2. Demonstrate hybrid and fuzzy search capabilities
        3. Show cold start and personalization features
        4. Display analytics and insights
        5. Highlight explainability and trust features
        6. Showcase parameterized personalization
        7. Finish with RAG assistants for conversational AI
        """
        return [
            # Phase 1: Advanced Search Capabilities
            "Semantic Content Discovery - Thematic Similarity",
            "Weighted Hybrid Search - Balancing Semantic and Exact Match",
            "Fuzzy Search for Typo-Tolerant Content Discovery",
            "Multi-Term Precision Search with Minimum Match Threshold",
            
            # Phase 2: Cold Start and Personalization
            "Cold Start Content Discovery - Thematic Expansion",
            "User Preference Analysis with Theme Affinity",
            
            # Phase 3: Negative Signal Learning
            "Negative Signal Detection - Skip and Dismissal Patterns",
            
            # Phase 4: Content Analytics
            "Content Performance by Narrative Complexity",
            "Theme Relationship Network Analysis",
            
            # Phase 5: Explainability and Trust
            "Recommendation Explanation Quality Analysis",
            "Explainable Recommendation Retrieval",
            
            # Phase 6: Parameterized Personalization
            "Preference-Aware Content Retrieval with Negative Filtering",
            "Personalized Content Discovery by Theme and Tone",
            "User Viewing Pattern Analysis",
            "Content Recommendation by Similarity Score Threshold",
            "Cold Start User Content Onboarding",
            "Theme-Based Content Search with Preference Matching",
            
            # Phase 7: AI Assistants (RAG)
            "Content Discovery Assistant - Semantic Q&A",
            "Recommendation Explanation Assistant",
            "Theme Exploration Assistant",
            "Content Comparison Assistant",
            "Personalized Content Advisor"
        ]
