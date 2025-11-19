
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class AdobeIncQueryGenerator(QueryGeneratorModule):
    """Query generator for Adobe Inc. - Brand Concierge AI/ML & Product Engineering
    
    Addresses pain points:
    - No framework for retrieval experimentation and optimization
    - Limited context understanding across multi-turn conversations
    - No ability to combine multiple specialized retrieval strategies
    - High maintenance burden for query template management
    - Difficulty debugging poor retrieval results
    - Static query patterns unable to handle complex retrieval needs
    - Inability to reason about retrieval quality and iterate
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ============================================================
        # SCRIPTED QUERIES - Basic exploration without parameters
        # ============================================================

        # Query 1: Semantic Brand Asset Discovery
        queries.append({
            'name': 'Semantic Brand Asset Discovery',
            'description': 'Find brand assets using natural language queries that understand intent beyond keywords - eliminating need for clarifying questions',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_semantic_asset_search',
                'description': 'Discovers brand assets using semantic understanding of natural language queries. Eliminates 42% of clarifying questions by understanding user intent beyond exact keywords.',
                'tags': ['semantic', 'brand_assets', 'discovery', 'esql', 'retrieval']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_description, "modern minimalist logo design for technology startup")
  AND approval_status == "approved"
| KEEP asset_id, asset_name, asset_description, asset_type, brand_name, tags, _score
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': 'Static query patterns unable to handle complex retrieval needs - 42% of AI Assistant queries require 2+ clarifying questions'
        })

        # Query 2: Weighted Hybrid Search - Balancing Semantic and Exact Match
        queries.append({
            'name': 'Weighted Hybrid Search - Balancing Semantic and Exact Match',
            'description': 'Advanced retrieval optimization: Balance semantic understanding (75% weight) with exact brand name matching (25% weight) for precision',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_hybrid_weighted_search',
                'description': 'Combines semantic search (75% weight) with exact brand matching (25% weight) for optimal precision. Reduces 2-3 day engineering cycles for new retrieval strategies to minutes.',
                'tags': ['hybrid', 'weighted', 'brand_assets', 'esql', 'precision']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_description, "Adobe Creative Cloud promotional banner", {"boost": 0.75})
   OR MATCH(brand_name, "Brand Alpha", {"boost": 0.25})
| WHERE asset_type == "image"
| KEEP asset_id, asset_name, brand_name, asset_type, tags, _score
| SORT _score DESC
| LIMIT 15''',
            'query_type': 'scripted',
            'pain_point': 'No ability to combine multiple specialized retrieval strategies - engineers spend 2-3 days writing new Query DSL for new requirements'
        })

        # Query 3: Fuzzy Asset Search with Typo Tolerance
        queries.append({
            'name': 'Fuzzy Asset Search with Typo Tolerance',
            'description': 'Best practice: Handle misspellings and typos automatically without requiring query rewrites or user corrections',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_fuzzy_typo_search',
                'description': 'Handles misspellings and typos automatically using fuzzy matching. Improves user experience by eliminating need for query corrections and reducing failed searches.',
                'tags': ['fuzzy', 'typo_tolerance', 'brand_assets', 'esql', 'ux']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_name, "Marketing Template", {"fuzziness": "AUTO"})
  AND file_format IN ("psd", "ai", "pdf")
| KEEP asset_id, asset_name, asset_description, file_format, brand_name, _score
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'Static query patterns unable to handle complex retrieval needs - users make typos in asset searches'
        })

        # Query 4: Multi-Term Precision Search with Minimum Match
        queries.append({
            'name': 'Multi-Term Precision Search with Minimum Match',
            'description': 'Advanced precision control: Require at least 3 out of 5 query terms to match, reducing noise and improving retrieval quality',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_precision_multi_term',
                'description': 'Analyzes poor-quality conversations using minimum match requirements. Reduces unhelpful responses by 31% through improved precision control and noise reduction.',
                'tags': ['precision', 'quality', 'conversations', 'esql', 'analytics']
            },
            'query': '''FROM ai_assistant_conversations METADATA _score
| WHERE MATCH(query_text, "configure brand asset approval workflow automation", {
    "operator": "OR",
    "minimum_should_match": 3
  })
  AND quality_rating == "poor"
  AND helpful == false
| KEEP conversation_id, query_text, response_text, retrieval_strategy, quality_rating, _score
| SORT _score DESC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': 'Inability to reason about retrieval quality and iterate - 31% of responses rated unhelpful, 68% due to poor document retrieval'
        })

        # Query 5: Conversation-Aware Contextual Retrieval
        queries.append({
            'name': 'Conversation-Aware Contextual Retrieval',
            'description': 'Retrieve multi-turn conversations to analyze context patterns and improve stateful retrieval strategies',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_contextual_multi_turn',
                'description': 'Analyzes multi-turn conversation patterns to understand context dependencies. Solves stateless retrieval problem where each query is independent of previous turns.',
                'tags': ['contextual', 'multi_turn', 'conversations', 'esql', 'stateful']
            },
            'query': '''FROM ai_assistant_conversations METADATA _score
| WHERE MATCH(query_text, "how do I export that asset in different format")
  AND conversation_turn > 1
  AND context_from_previous_turn IS NOT NULL
| KEEP conversation_id, query_text, conversation_turn, context_from_previous_turn, retrieved_documents, helpful, _score
| SORT _score DESC
| LIMIT 15''',
            'query_type': 'scripted',
            'pain_point': 'Limited context understanding across multi-turn conversations - each query to Elasticsearch is independent and stateless'
        })

        # Query 6: Retrieval Quality Incident Debug Search
        queries.append({
            'name': 'Retrieval Quality Incident Debug Search',
            'description': 'Find similar retrieval failures using exact phrase matching to quickly identify patterns and reduce debug time',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_incident_debug_search',
                'description': 'Identifies similar retrieval failure patterns using phrase matching. Reduces debug time from 30-60 minutes to under 10 minutes by surfacing known resolution patterns.',
                'tags': ['debugging', 'incidents', 'phrase_match', 'esql', 'troubleshooting']
            },
            'query': '''FROM retrieval_quality_incidents METADATA _score
| WHERE MATCH_PHRASE(resolution_notes, "Resolved by adjusting embedding", {"slop": 2})
  AND debug_time_minutes > 30
  AND resolved == true
| KEEP incident_id, user_query, failure_reason, debug_time_minutes, resolution_notes, _score
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': 'Difficulty debugging poor retrieval results - 30-60 minutes per incident with limited visibility'
        })

        # Query 7: Retrieval Experiment A/B Test Results Search
        queries.append({
            'name': 'Retrieval Experiment A/B Test Results Search',
            'description': 'Find high-performing retrieval experiments with specific quality thresholds to accelerate model evaluation',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_experiment_results',
                'description': 'Discovers high-performing retrieval experiments meeting quality thresholds. Reduces 3-week embedding model evaluation cycles to days through rapid experimentation.',
                'tags': ['experiments', 'ab_testing', 'quality', 'esql', 'optimization']
            },
            'query': '''FROM retrieval_experiments METADATA _score
| WHERE MATCH(test_query, "brand asset search with filters")
  AND precision_at_5 >= 0.80
  AND recall_at_10 >= 0.70
  AND deployed_to_production == false
| KEEP experiment_id, experiment_name, retrieval_strategy, embedding_model, precision_at_5, recall_at_10, mrr_score, _score
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'No framework for retrieval experimentation and optimization - 3-week engineering project to evaluate new embedding models'
        })

        # Query 8: Enriched Asset Search with Customer Context
        queries.append({
            'name': 'Enriched Asset Search with Customer Context',
            'description': 'Combine semantic asset search with customer account enrichment for personalized retrieval results',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_enriched_customer_search',
                'description': 'Combines semantic asset search with customer account context for personalized results. Demonstrates intelligent tool composition by merging multiple data sources automatically.',
                'tags': ['enriched', 'lookup_join', 'personalization', 'esql', 'composition']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_description, "healthcare patient education infographic")
  AND approval_status == "approved"
| LOOKUP JOIN customer_accounts ON customer_account_id
| WHERE industry == "Healthcare"
  AND tier IN ("Enterprise", "Professional")
| KEEP asset_id, asset_name, asset_description, brand_name, company_name, tier, _score
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': 'Static query patterns unable to handle complex retrieval needs - need to combine asset search with customer account details'
        })

        # Query 9: High-Value Asset Usage Analytics
        queries.append({
            'name': 'High-Value Asset Usage Analytics',
            'description': 'Identify most-used approved assets by brand to understand content effectiveness and reuse patterns',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_asset_usage_analytics',
                'description': 'Analyzes asset usage patterns to identify high-value content. Provides insights for content strategy and helps reduce maintenance burden on underutilized templates.',
                'tags': ['analytics', 'usage', 'brand_assets', 'esql', 'insights']
            },
            'query': '''FROM brand_assets
| WHERE approval_status == "approved"
| STATS 
    total_assets = COUNT(*),
    avg_usage = AVG(usage_count),
    max_usage = MAX(usage_count),
    total_usage = SUM(usage_count)
  BY brand_name, asset_type
| WHERE total_assets > 5
| EVAL usage_per_asset = TO_DOUBLE(total_usage) / total_assets
| SORT total_usage DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'High maintenance burden for query template management - need visibility into which assets are actually valuable'
        })

        # Query 10: Conversation Quality by Retrieval Strategy
        queries.append({
            'name': 'Conversation Quality by Retrieval Strategy',
            'description': 'Compare retrieval strategy effectiveness by analyzing quality ratings and helpfulness metrics',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_strategy_quality_comparison',
                'description': 'Compares retrieval strategy effectiveness using quality metrics. Enables data-driven decisions on which strategies to optimize or deprecate, reducing maintenance burden.',
                'tags': ['quality', 'comparison', 'strategies', 'esql', 'analytics']
            },
            'query': '''FROM ai_assistant_conversations
| STATS 
    total_conversations = COUNT(*),
    helpful_count = SUM(CASE(helpful == true, 1, 0)),
    excellent_count = SUM(CASE(quality_rating == "excellent", 1, 0)),
    poor_count = SUM(CASE(quality_rating == "poor", 1, 0)),
    avg_latency = AVG(retrieval_latency_ms)
  BY retrieval_strategy
| EVAL helpfulness_rate = TO_DOUBLE(helpful_count) * 100.0 / total_conversations
| EVAL excellence_rate = TO_DOUBLE(excellent_count) * 100.0 / total_conversations
| EVAL poor_rate = TO_DOUBLE(poor_count) * 100.0 / total_conversations
| SORT helpfulness_rate DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': 'Inability to reason about retrieval quality and iterate - 31% of responses rated unhelpful, 68% due to poor document retrieval'
        })

        # Query 11: Template Complexity vs Performance Analysis
        queries.append({
            'name': 'Template Complexity vs Performance Analysis',
            'description': 'Analyze query template maintenance burden by correlating complexity scores with performance ratings',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_template_complexity_analysis',
                'description': 'Analyzes template maintenance burden vs performance. Identifies candidates for deprecation or simplification among 40+ Query DSL templates requiring 1-2 weeks to update.',
                'tags': ['templates', 'complexity', 'maintenance', 'esql', 'optimization']
            },
            'query': '''FROM query_templates
| WHERE deprecated == false
| STATS 
    template_count = COUNT(*),
    avg_complexity = AVG(complexity_score),
    total_maintenance_hours = SUM(maintenance_hours),
    excellent_count = SUM(CASE(performance_rating == "excellent", 1, 0)),
    poor_count = SUM(CASE(performance_rating == "poor", 1, 0))
  BY use_case
| EVAL avg_maintenance_per_template = total_maintenance_hours / template_count
| EVAL excellence_rate = TO_DOUBLE(excellent_count) * 100.0 / template_count
| SORT total_maintenance_hours DESC
| LIMIT 15''',
            'query_type': 'scripted',
            'pain_point': 'High maintenance burden for query template management - 40+ Query DSL templates requiring 1-2 weeks to update'
        })

        # Query 12: Incident Resolution Time by Failure Type
        queries.append({
            'name': 'Incident Resolution Time by Failure Type',
            'description': 'Identify which failure types take longest to debug to prioritize tooling improvements',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_incident_resolution_time',
                'description': 'Identifies failure types with longest debug times. Prioritizes tooling improvements to reduce 30-60 minute incident resolution times through better visibility.',
                'tags': ['incidents', 'debugging', 'resolution', 'esql', 'analytics']
            },
            'query': '''FROM retrieval_quality_incidents
| STATS 
    incident_count = COUNT(*),
    avg_debug_time = AVG(debug_time_minutes),
    max_debug_time = MAX(debug_time_minutes),
    resolved_count = SUM(CASE(resolved == true, 1, 0))
  BY failure_reason
| EVAL resolution_rate = TO_DOUBLE(resolved_count) * 100.0 / incident_count
| WHERE incident_count > 10
| SORT avg_debug_time DESC
| LIMIT 10''',
            'query_type': 'scripted',
            'pain_point': 'Difficulty debugging poor retrieval results - 30-60 minutes per incident with limited visibility'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Parameterized Semantic Asset Search
        queries.append({
            'name': 'Parameterized Semantic Asset Search',
            'description': 'User-customizable semantic search for brand assets with approval status filter',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_param_semantic_search',
                'description': 'Searches brand assets using natural language with customizable approval filters. Enables self-service asset discovery without engineering support for each new query pattern.',
                'tags': ['semantic', 'parameterized', 'brand_assets', 'esql', 'self_service']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_description, ?search_query)
  AND approval_status == ?approval_status
| KEEP asset_id, asset_name, asset_description, asset_type, brand_name, tags, approval_status, _score
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Natural language description of the asset you are looking for',
                    'required': True,
                    'example': 'modern minimalist logo design for technology startup'
                },
                {
                    'name': 'approval_status',
                    'type': 'string',
                    'description': 'Asset approval status filter',
                    'required': True,
                    'example': 'approved',
                    'allowed_values': ['approved', 'pending', 'rejected', 'draft']
                }
            ],
            'pain_point': 'Static query patterns unable to handle complex retrieval needs - 42% of AI Assistant queries require 2+ clarifying questions'
        })

        # Query 2: Parameterized Hybrid Search with Brand Filter
        queries.append({
            'name': 'Parameterized Hybrid Search with Brand Filter',
            'description': 'Customizable hybrid search balancing semantic and exact brand matching',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_param_hybrid_brand',
                'description': 'Combines semantic and exact brand matching with user-controlled weights. Eliminates 2-3 day engineering cycles by allowing dynamic strategy composition.',
                'tags': ['hybrid', 'parameterized', 'brand_filter', 'esql', 'flexible']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_description, ?search_query, {"boost": 0.75})
   OR MATCH(brand_name, ?brand_name, {"boost": 0.25})
| WHERE asset_type == ?asset_type
| KEEP asset_id, asset_name, brand_name, asset_type, tags, file_format, _score
| SORT _score DESC
| LIMIT 20''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Natural language asset description',
                    'required': True,
                    'example': 'promotional banner for creative cloud'
                },
                {
                    'name': 'brand_name',
                    'type': 'string',
                    'description': 'Specific brand name to boost in results',
                    'required': True,
                    'example': 'Brand Alpha'
                },
                {
                    'name': 'asset_type',
                    'type': 'string',
                    'description': 'Type of asset to filter',
                    'required': True,
                    'example': 'image',
                    'allowed_values': ['image', 'video', 'audio', 'logo', 'template', 'document']
                }
            ],
            'pain_point': 'No ability to combine multiple specialized retrieval strategies - engineers spend 2-3 days writing new Query DSL for new requirements'
        })

        # Query 3: Parameterized Conversation Quality Analysis
        queries.append({
            'name': 'Parameterized Conversation Quality Analysis',
            'description': 'Analyze conversation quality for specific retrieval strategies and time ranges',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_param_quality_analysis',
                'description': 'Analyzes conversation quality metrics for specified strategies and time periods. Enables rapid A/B testing and quality iteration without custom query development.',
                'tags': ['quality', 'parameterized', 'analytics', 'esql', 'ab_testing']
            },
            'query': '''FROM ai_assistant_conversations
| WHERE retrieval_strategy == ?retrieval_strategy
  AND quality_rating == ?quality_rating
| STATS 
    conversation_count = COUNT(*),
    helpful_count = SUM(CASE(helpful == true, 1, 0)),
    avg_latency = AVG(retrieval_latency_ms),
    clarification_needed_count = SUM(CASE(clarification_needed == true, 1, 0))
  BY conversation_turn
| EVAL helpfulness_rate = TO_DOUBLE(helpful_count) * 100.0 / conversation_count
| EVAL clarification_rate = TO_DOUBLE(clarification_needed_count) * 100.0 / conversation_count
| SORT conversation_turn ASC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'retrieval_strategy',
                    'type': 'string',
                    'description': 'Retrieval strategy to analyze',
                    'required': True,
                    'example': 'semantic',
                    'allowed_values': ['keyword', 'semantic', 'hybrid', 'composed', 'multi_step', 'filtered']
                },
                {
                    'name': 'quality_rating',
                    'type': 'string',
                    'description': 'Quality rating filter',
                    'required': True,
                    'example': 'poor',
                    'allowed_values': ['excellent', 'good', 'fair', 'poor']
                }
            ],
            'pain_point': 'Inability to reason about retrieval quality and iterate - 31% of responses rated unhelpful, 68% due to poor document retrieval'
        })

        # Query 4: Parameterized Experiment Performance Search
        queries.append({
            'name': 'Parameterized Experiment Performance Search',
            'description': 'Find experiments meeting custom quality thresholds for specific embedding models',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_param_experiment_search',
                'description': 'Discovers experiments meeting custom quality thresholds for specified models. Accelerates 3-week embedding evaluation cycles through flexible experimentation framework.',
                'tags': ['experiments', 'parameterized', 'quality', 'esql', 'evaluation']
            },
            'query': '''FROM retrieval_experiments METADATA _score
| WHERE embedding_model == ?embedding_model
  AND precision_at_5 >= ?min_precision
  AND recall_at_10 >= ?min_recall
  AND deployed_to_production == false
| KEEP experiment_id, experiment_name, retrieval_strategy, embedding_model, precision_at_5, recall_at_10, mrr_score, latency_ms
| SORT precision_at_5 DESC, recall_at_10 DESC
| LIMIT 20''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'embedding_model',
                    'type': 'string',
                    'description': 'Embedding model to evaluate',
                    'required': True,
                    'example': 'text-embedding-ada-002',
                    'allowed_values': ['text-embedding-ada-002', 'e5-large-v2', 'all-MiniLM-L6-v2', 'bge-large-en', 'gte-large', 'instructor-xl']
                },
                {
                    'name': 'min_precision',
                    'type': 'number',
                    'description': 'Minimum precision@5 threshold (0.0 to 1.0)',
                    'required': True,
                    'example': 0.75
                },
                {
                    'name': 'min_recall',
                    'type': 'number',
                    'description': 'Minimum recall@10 threshold (0.0 to 1.0)',
                    'required': True,
                    'example': 0.70
                }
            ],
            'pain_point': 'No framework for retrieval experimentation and optimization - 3-week engineering project to evaluate new embedding models'
        })

        # Query 5: Parameterized Incident Debug Pattern Search
        queries.append({
            'name': 'Parameterized Incident Debug Pattern Search',
            'description': 'Search for similar incidents by failure reason to accelerate debugging',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_param_incident_search',
                'description': 'Finds similar incidents by failure type with custom debug time thresholds. Reduces 30-60 minute debug sessions by surfacing known resolution patterns.',
                'tags': ['incidents', 'parameterized', 'debugging', 'esql', 'troubleshooting']
            },
            'query': '''FROM retrieval_quality_incidents METADATA _score
| WHERE failure_reason == ?failure_reason
  AND resolved == true
  AND debug_time_minutes > ?min_debug_time
| KEEP incident_id, user_query, failure_reason, debug_time_minutes, resolution_notes, _score
| SORT debug_time_minutes DESC
| LIMIT 15''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'failure_reason',
                    'type': 'string',
                    'description': 'Type of retrieval failure to search for',
                    'required': True,
                    'example': 'embedding_mismatch',
                    'allowed_values': ['wrong_filter', 'embedding_mismatch', 'incorrect_ranking', 'missing_context', 'empty_results', 'poor_relevance', 'timeout']
                },
                {
                    'name': 'min_debug_time',
                    'type': 'number',
                    'description': 'Minimum debug time in minutes to filter incidents',
                    'required': True,
                    'example': 30
                }
            ],
            'pain_point': 'Difficulty debugging poor retrieval results - 30-60 minutes per incident with limited visibility'
        })

        # Query 6: Parameterized Customer-Specific Asset Search
        queries.append({
            'name': 'Parameterized Customer-Specific Asset Search',
            'description': 'Search assets with customer context enrichment for personalized results',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_param_customer_asset',
                'description': 'Searches assets with customer industry and tier context for personalization. Demonstrates intelligent tool composition by automatically merging multiple data sources.',
                'tags': ['enriched', 'parameterized', 'customer_context', 'esql', 'personalization']
            },
            'query': '''FROM brand_assets METADATA _score
| WHERE MATCH(asset_description, ?search_query)
  AND approval_status == "approved"
| LOOKUP JOIN customer_accounts ON customer_account_id
| WHERE industry == ?industry
  AND tier == ?tier
| KEEP asset_id, asset_name, asset_description, brand_name, company_name, industry, tier, _score
| SORT _score DESC
| LIMIT 15''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'search_query',
                    'type': 'string',
                    'description': 'Natural language asset description',
                    'required': True,
                    'example': 'patient education materials'
                },
                {
                    'name': 'industry',
                    'type': 'string',
                    'description': 'Customer industry to filter',
                    'required': True,
                    'example': 'Healthcare',
                    'allowed_values': ['Education', 'Technology', 'Manufacturing', 'Media', 'Finance', 'Retail', 'Healthcare']
                },
                {
                    'name': 'tier',
                    'type': 'string',
                    'description': 'Customer tier to filter',
                    'required': True,
                    'example': 'Enterprise',
                    'allowed_values': ['Professional', 'Standard', 'Enterprise']
                }
            ],
            'pain_point': 'Static query patterns unable to handle complex retrieval needs - need to combine asset search with customer account details'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        Semantic fields from strategy:
        - brand_assets.asset_description
        - ai_assistant_conversations.query_text
        - retrieval_experiments.test_query
        - retrieval_quality_incidents.user_query
        """
        queries = []

        # RAG Query 1: Brand Asset Discovery Assistant
        queries.append({
            'name': 'Brand Asset Discovery Assistant',
            'description': 'AI-powered assistant that finds relevant brand assets and explains why they match user needs',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_rag_asset_assistant',
                'description': 'AI assistant that discovers brand assets using semantic search and provides natural language explanations. Eliminates 42% of clarifying questions through intelligent context understanding.',
                'tags': ['rag', 'semantic', 'brand_assets', 'esql', 'ai_assistant']
            },
            'query': '''FROM brand_assets METADATA _id, _score
| WHERE MATCH(asset_description, ?user_question)
  AND approval_status == "approved"
| SORT _score DESC
| LIMIT 5
| KEEP _id, asset_id, asset_name, asset_description, brand_name, asset_type, tags, _score
| EVAL context = CONCAT(
    "Asset: ", asset_name, " | ",
    "Brand: ", brand_name, " | ",
    "Type: ", asset_type, " | ",
    "Description: ", asset_description, " | ",
    "Tags: ", tags
  )
| EVAL prompt = CONCAT(
    "Based on these brand assets, answer the user's question: ", ?user_question, "\\n\\n",
    "Available Assets:\\n", context, "\\n\\n",
    "Provide a helpful answer explaining which assets best match their needs and why."
  )''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'User question about brand assets',
                    'required': True,
                    'example': 'What approved logos do we have for digital marketing campaigns?'
                }
            ],
            'pain_point': 'Static query patterns unable to handle complex retrieval needs - 42% of AI Assistant queries require 2+ clarifying questions'
        })

        # RAG Query 2: Conversation Quality Insights Assistant
        queries.append({
            'name': 'Conversation Quality Insights Assistant',
            'description': 'AI assistant that analyzes conversation patterns and provides actionable quality improvement recommendations',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_rag_quality_insights',
                'description': 'Analyzes conversation quality patterns and provides AI-generated improvement recommendations. Helps reduce 31% unhelpful response rate through data-driven insights.',
                'tags': ['rag', 'quality', 'conversations', 'esql', 'insights']
            },
            'query': '''FROM ai_assistant_conversations METADATA _id, _score
| WHERE MATCH(query_text, ?user_question)
  AND quality_rating IN ("poor", "fair")
| SORT _score DESC
| LIMIT 5
| KEEP _id, conversation_id, query_text, response_text, retrieval_strategy, quality_rating, helpful, clarification_needed, _score
| EVAL context = CONCAT(
    "Query: ", query_text, " | ",
    "Strategy: ", retrieval_strategy, " | ",
    "Quality: ", quality_rating, " | ",
    "Helpful: ", TO_STRING(helpful), " | ",
    "Clarification Needed: ", TO_STRING(clarification_needed)
  )
| EVAL prompt = CONCAT(
    "Analyze these low-quality conversations and answer: ", ?user_question, "\\n\\n",
    "Conversation Examples:\\n", context, "\\n\\n",
    "Provide specific recommendations for improving retrieval quality based on these patterns."
  )''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Question about conversation quality patterns',
                    'required': True,
                    'example': 'Why are users rating these conversations as unhelpful?'
                }
            ],
            'pain_point': 'Inability to reason about retrieval quality and iterate - 31% of responses rated unhelpful, 68% due to poor document retrieval'
        })

        # RAG Query 3: Retrieval Experiment Recommendation Assistant
        queries.append({
            'name': 'Retrieval Experiment Recommendation Assistant',
            'description': 'AI assistant that analyzes experiment results and recommends optimal retrieval strategies',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_rag_experiment_advisor',
                'description': 'Analyzes experiment results and provides AI-powered recommendations for optimal retrieval strategies. Accelerates 3-week model evaluation cycles through intelligent insights.',
                'tags': ['rag', 'experiments', 'recommendations', 'esql', 'optimization']
            },
            'query': '''FROM retrieval_experiments METADATA _id, _score
| WHERE MATCH(test_query, ?user_question)
| SORT _score DESC
| LIMIT 5
| KEEP _id, experiment_id, experiment_name, retrieval_strategy, embedding_model, precision_at_5, recall_at_10, mrr_score, latency_ms, _score
| EVAL context = CONCAT(
    "Experiment: ", experiment_name, " | ",
    "Strategy: ", retrieval_strategy, " | ",
    "Model: ", embedding_model, " | ",
    "Precision@5: ", TO_STRING(precision_at_5), " | ",
    "Recall@10: ", TO_STRING(recall_at_10), " | ",
    "MRR: ", TO_STRING(mrr_score), " | ",
    "Latency: ", TO_STRING(latency_ms), "ms"
  )
| EVAL prompt = CONCAT(
    "Based on these experiment results, answer: ", ?user_question, "\\n\\n",
    "Experiment Results:\\n", context, "\\n\\n",
    "Provide recommendations on which retrieval strategy and embedding model to use based on the metrics."
  )''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Question about experiment results and recommendations',
                    'required': True,
                    'example': 'Which embedding model performs best for brand asset searches?'
                }
            ],
            'pain_point': 'No framework for retrieval experimentation and optimization - 3-week engineering project to evaluate new embedding models'
        })

        # RAG Query 4: Incident Troubleshooting Assistant
        queries.append({
            'name': 'Incident Troubleshooting Assistant',
            'description': 'AI assistant that analyzes retrieval failures and suggests resolution strategies based on historical patterns',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_rag_incident_troubleshoot',
                'description': 'Analyzes retrieval failure patterns and provides AI-generated troubleshooting guidance. Reduces 30-60 minute debug sessions through intelligent pattern matching.',
                'tags': ['rag', 'incidents', 'troubleshooting', 'esql', 'debugging']
            },
            'query': '''FROM retrieval_quality_incidents METADATA _id, _score
| WHERE MATCH(user_query, ?user_question)
  AND resolved == true
| SORT _score DESC
| LIMIT 5
| KEEP _id, incident_id, user_query, failure_reason, debug_time_minutes, resolution_notes, _score
| EVAL context = CONCAT(
    "Query: ", user_query, " | ",
    "Failure: ", failure_reason, " | ",
    "Debug Time: ", TO_STRING(debug_time_minutes), " min | ",
    "Resolution: ", resolution_notes
  )
| EVAL prompt = CONCAT(
    "Based on these resolved incidents, answer: ", ?user_question, "\\n\\n",
    "Similar Incidents:\\n", context, "\\n\\n",
    "Provide step-by-step troubleshooting guidance based on how similar issues were resolved."
  )''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Question about troubleshooting a retrieval issue',
                    'required': True,
                    'example': 'How do I fix embedding mismatch errors in asset searches?'
                }
            ],
            'pain_point': 'Difficulty debugging poor retrieval results - 30-60 minutes per incident with limited visibility'
        })

        # RAG Query 5: Multi-Turn Context Understanding Assistant
        queries.append({
            'name': 'Multi-Turn Context Understanding Assistant',
            'description': 'AI assistant that analyzes multi-turn conversation patterns to improve context-aware retrieval',
            'tool_metadata': {
                'tool_id': 'adobe_inc.brand_conc_rag_context_advisor',
                'description': 'Analyzes multi-turn conversation patterns and provides recommendations for context-aware retrieval. Solves stateless query problem where each search is independent.',
                'tags': ['rag', 'contextual', 'multi_turn', 'esql', 'stateful']
            },
            'query': '''FROM ai_assistant_conversations METADATA _id, _score
| WHERE MATCH(query_text, ?user_question)
  AND conversation_turn > 1
  AND context_from_previous_turn IS NOT NULL
| SORT _score DESC
| LIMIT 5
| KEEP _id, conversation_id, query_text, conversation_turn, context_from_previous_turn, retrieved_documents, helpful, _score
| EVAL context = CONCAT(
    "Turn: ", TO_STRING(conversation_turn), " | ",
    "Query: ", query_text, " | ",
    "Previous Context: ", context_from_previous_turn, " | ",
    "Helpful: ", TO_STRING(helpful)
  )
| EVAL prompt = CONCAT(
    "Analyze these multi-turn conversations and answer: ", ?user_question, "\\n\\n",
    "Conversation Patterns:\\n", context, "\\n\\n",
    "Explain how context from previous turns affects retrieval quality and provide recommendations for improvement."
  )''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Question about multi-turn conversation patterns',
                    'required': True,
                    'example': 'How can we better maintain context across conversation turns?'
                }
            ],
            'pain_point': 'Limited context understanding across multi-turn conversations - each query to Elasticsearch is independent and stateless'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Story arc:
        1. Start with core pain point - static retrieval patterns
        2. Show semantic understanding capabilities
        3. Demonstrate advanced composition and optimization
        4. Highlight debugging and quality analysis
        5. Showcase experimentation framework
        6. End with AI-powered assistants (RAG)
        """
        return [
            # Foundation: Semantic Understanding
            'Semantic Brand Asset Discovery',
            'Weighted Hybrid Search - Balancing Semantic and Exact Match',
            'Fuzzy Asset Search with Typo Tolerance',
            
            # Advanced Composition
            'Enriched Asset Search with Customer Context',
            'Multi-Term Precision Search with Minimum Match',
            
            # Context & Conversations
            'Conversation-Aware Contextual Retrieval',
            'Conversation Quality by Retrieval Strategy',
            
            # Quality & Debugging
            'Retrieval Quality Incident Debug Search',
            'Incident Resolution Time by Failure Type',
            
            # Experimentation & Optimization
            'Retrieval Experiment A/B Test Results Search',
            'Template Complexity vs Performance Analysis',
            'High-Value Asset Usage Analytics',
            
            # Parameterized Self-Service
            'Parameterized Semantic Asset Search',
            'Parameterized Hybrid Search with Brand Filter',
            'Parameterized Conversation Quality Analysis',
            'Parameterized Experiment Performance Search',
            'Parameterized Incident Debug Pattern Search',
            'Parameterized Customer-Specific Asset Search',
            
            # AI-Powered Assistants (RAG)
            'Brand Asset Discovery Assistant',
            'Conversation Quality Insights Assistant',
            'Retrieval Experiment Recommendation Assistant',
            'Incident Troubleshooting Assistant',
            'Multi-Turn Context Understanding Assistant'
        ]
