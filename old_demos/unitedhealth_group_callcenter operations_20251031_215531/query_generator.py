from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class UnitedHealthGroupQueryGenerator(QueryGeneratorModule):
    """Query generator for UnitedHealth Group - Callcenter Operations

    Generates three types of queries:
    1. Scripted (tested, non-parameterized)
    2. Parameterized (Agent Builder tools)
    3. RAG (semantic search + LLM completion)
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate scripted (non-parameterized) ES|QL queries
    
        Access datasets via self.datasets
        """
        queries = []
        
        # Query 1: Verification Friction Analysis
        queries.append({
            "name": "Verification Friction Analysis",
            "description": "Analyze correlation between verification steps and call duration over last 30 days. Compare each transaction against team averages to identify outliers where excessive verification causes delays.",
            "pain_point": "Multiple verification steps for security causing friction",
            "query_type": "scripted",
            "datasets": ["call_center_transactions", "agents"],
            "esql_query": """
    FROM call_center_transactions
    | WHERE @timestamp >= NOW() - 30 days
    | EVAL verification_impact = call_duration_seconds / verification_steps_count
    | STATS 
        avg_duration = AVG(call_duration_seconds),
        avg_verification_steps = AVG(verification_steps_count),
        avg_processing_time = AVG(processing_time_seconds),
        total_calls = COUNT(*)
      BY agent_id
    | LOOKUP agents ON agent_id
    | INLINESTATS team_avg_duration = AVG(avg_duration) BY team
    | EVAL duration_variance_pct = ROUND(((avg_duration - team_avg_duration) / team_avg_duration) * 100, 2)
    | EVAL is_outlier = CASE(
        ABS(duration_variance_pct) > 50, "High Variance",
        ABS(duration_variance_pct) > 25, "Moderate Variance",
        "Normal"
      )
    | WHERE is_outlier != "Normal"
    | SORT duration_variance_pct DESC
    | KEEP agent_id, agent_name, team, avg_duration, avg_verification_steps, avg_processing_time, team_avg_duration, duration_variance_pct, is_outlier, total_calls
    | LIMIT 100
            """.strip()
        })
        
        # Query 2: Prior Authorization Bottleneck Detection
        queries.append({
            "name": "Prior Authorization Bottleneck Detection",
            "description": "Identify urgent prior authorizations pending over 3 days. Detect sudden spikes in pending authorizations by provider or specialty and calculate related call volume.",
            "pain_point": "Urgent medication needs and delays in provider submissions",
            "query_type": "scripted",
            "datasets": ["prior_authorizations", "provider_network", "call_center_transactions"],
            "esql_query": """
    FROM prior_authorizations
    | WHERE status == "pending" AND days_pending > 3 AND urgency_flag == true
    | LOOKUP provider_network ON provider_id
    | STATS 
        urgent_pending_count = COUNT(*),
        avg_days_pending = AVG(days_pending),
        max_days_pending = MAX(days_pending),
        oldest_submission = MIN(submission_date)
      BY provider_id, provider_name, specialty, network_status
    | EVAL risk_score = CASE(
        avg_days_pending > 7 AND urgent_pending_count > 5, "Critical",
        avg_days_pending > 5 OR urgent_pending_count > 3, "High",
        avg_days_pending > 3, "Medium",
        "Low"
      )
    | INLINESTATS 
        specialty_avg_pending = AVG(urgent_pending_count),
        specialty_avg_days = AVG(avg_days_pending)
      BY specialty
    | EVAL performance_vs_specialty = ROUND(((avg_days_pending - specialty_avg_days) / specialty_avg_days) * 100, 2)
    | WHERE risk_score IN ("Critical", "High")
    | SORT urgent_pending_count DESC, avg_days_pending DESC
    | KEEP provider_id, provider_name, specialty, network_status, urgent_pending_count, avg_days_pending, max_days_pending, oldest_submission, risk_score, performance_vs_specialty
    | LIMIT 50
            """.strip()
        })
        
        # Query 3: Cost Efficiency Anomaly Detection
        queries.append({
            "name": "Cost Efficiency Anomaly Detection",
            "description": "Multi-faceted analysis of cost per transaction by call type, processing time trends by agent team, and efficiency rates by plan complexity. Flags transactions significantly above average cost.",
            "pain_point": "Need to optimize cost per transaction and processing time",
            "query_type": "scripted",
            "datasets": ["call_center_transactions", "agents", "member_plans"],
            "esql_query": """
    FROM call_center_transactions
    | WHERE @timestamp >= NOW() - 30 days
    | LOOKUP agents ON agent_id
    | LOOKUP member_plans ON member_id
    | INLINESTATS 
        overall_avg_cost = AVG(transaction_cost),
        overall_avg_processing = AVG(processing_time_seconds)
    | INLINESTATS 
        call_type_avg_cost = AVG(transaction_cost),
        call_type_avg_processing = AVG(processing_time_seconds)
      BY call_type
    | INLINESTATS
        team_avg_cost = AVG(transaction_cost),
        team_avg_processing = AVG(processing_time_seconds)
      BY team
    | EVAL cost_variance_overall = ROUND(((transaction_cost - overall_avg_cost) / overall_avg_cost) * 100, 2)
    | EVAL cost_variance_call_type = ROUND(((transaction_cost - call_type_avg_cost) / call_type_avg_cost) * 100, 2)
    | EVAL processing_variance = ROUND(((processing_time_seconds - overall_avg_processing) / overall_avg_processing) * 100, 2)
    | EVAL is_cost_anomaly = CASE(
        transaction_cost >= (overall_avg_cost * 2), true,
        false
      )
    | EVAL efficiency_score = ROUND((efficiency_rating * 100) / (processing_time_seconds / 60), 2)
    | WHERE is_cost_anomaly == true OR ABS(cost_variance_call_type) > 100
    | EVAL complexity_tier = CASE(
        plan_type IN ("PPO", "HMO") AND coverage_tier == "Platinum", "High Complexity",
        plan_type IN ("PPO", "HMO"), "Medium Complexity",
        "Low Complexity"
      )
    | STATS
        anomaly_count = COUNT(*),
        avg_anomaly_cost = AVG(transaction_cost),
        avg_anomaly_processing = AVG(processing_time_seconds),
        avg_efficiency_score = AVG(efficiency_score),
        resolution_rate = ROUND(AVG(CASE(resolution_status == "resolved", 1.0, 0.0)) * 100, 2)
      BY team, call_type, complexity_tier
    | EVAL cost_per_resolution = ROUND(avg_anomaly_cost / (resolution_rate / 100), 2)
    | SORT avg_anomaly_cost DESC
    | KEEP team, call_type, complexity_tier, anomaly_count, avg_anomaly_cost, avg_anomaly_processing, avg_efficiency_score, resolution_rate, cost_per_resolution
    | LIMIT 100
            """.strip()
        })
        
        # Query 4: Provider Network Currency Analysis
        queries.append({
            "name": "Provider Network Currency Analysis",
            "description": "Identify providers with outdated verification dates causing call volume spikes. Correlate stale network data with member inquiries.",
            "pain_point": "Network directories not always being current",
            "query_type": "scripted",
            "datasets": ["provider_network", "call_center_transactions", "prior_authorizations"],
            "esql_query": """
    FROM provider_network
    | EVAL days_since_verification = (NOW() - last_verified_date) / 1000 / 86400
    | EVAL verification_status = CASE(
        days_since_verification > 90, "Stale",
        days_since_verification > 60, "Aging",
        days_since_verification > 30, "Due Soon",
        "Current"
      )
    | WHERE verification_status IN ("Stale", "Aging")
    | STATS 
        provider_count = COUNT(*)
      BY provider_id, provider_name, specialty, network_status, accepting_patients, verification_status, days_since_verification
    | SORT days_since_verification DESC
    | EVAL potential_impact = CASE(
        accepting_patients == false AND network_status == "in_network", "High - Accepting Status Unclear",
        network_status == "out_of_network" AND days_since_verification > 90, "High - Status May Have Changed",
        days_since_verification > 120, "Medium - Very Outdated",
        "Low"
      )
    | KEEP provider_id, provider_name, specialty, network_status, accepting_patients, verification_status, days_since_verification, potential_impact
    | LIMIT 100
            """.strip()
        })
        
        # Query 5: Denial Code Resolution Effectiveness
        queries.append({
            "name": "Denial Code Resolution Effectiveness",
            "description": "Analyze denial patterns, resolution times, and agent effectiveness in handling medical coding complexity issues.",
            "pain_point": "Medical coding complexity and coordination of benefits issues",
            "query_type": "scripted",
            "datasets": ["call_center_transactions", "claims_denials", "agents"],
            "esql_query": """
    FROM call_center_transactions
    | WHERE denial_code IS NOT NULL AND @timestamp >= NOW() - 60 days
    | LOOKUP claims_denials ON denial_code
    | LOOKUP agents ON agent_id
    | STATS
        call_count = COUNT(*),
        avg_call_duration = AVG(call_duration_seconds),
        avg_processing_time = AVG(processing_time_seconds),
        resolution_rate = ROUND(AVG(CASE(resolution_status == "resolved", 1.0, 0.0)) * 100, 2),
        avg_verification_steps = AVG(verification_steps_count)
      BY denial_code, category, team, specialization
    | LOOKUP claims_denials ON denial_code
    | EVAL effectiveness_gap = ROUND(appeal_success_rate - resolution_rate, 2)
    | EVAL complexity_score = ROUND((avg_processing_time / 60) * avg_verification_steps, 2)
    | EVAL performance_rating = CASE(
        resolution_rate >= appeal_success_rate - 10 AND avg_processing_time < 300, "Excellent",
        resolution_rate >= appeal_success_rate - 20, "Good",
        resolution_rate >= appeal_success_rate - 35, "Needs Improvement",
        "Poor"
      )
    | WHERE call_count >= 5
    | SORT effectiveness_gap DESC, call_count DESC
    | KEEP denial_code, category, team, specialization, call_count, avg_call_duration, avg_processing_time, resolution_rate, appeal_success_rate, effectiveness_gap, complexity_score, performance_rating
    | LIMIT 100
            """.strip()
        })
        
        # Query 6: Member Plan Confusion Indicator
        queries.append({
            "name": "Member Plan Confusion Indicator",
            "description": "Identify plan types and coverage tiers generating highest call volumes and longest durations, indicating terminology and benefit confusion.",
            "pain_point": "Plans vary significantly and customers don't understand insurance terminology",
            "query_type": "scripted",
            "datasets": ["call_center_transactions", "member_plans", "agents"],
            "esql_query": """
    FROM call_center_transactions
    | WHERE @timestamp >= NOW() - 30 days AND call_type IN ("benefits_inquiry", "coverage_question", "eligibility_check")
    | LOOKUP member_plans ON member_id
    | STATS
        inquiry_count = COUNT(*),
        avg_call_duration = AVG(call_duration_seconds),
        avg_verification_steps = AVG(verification_steps_count),
        unresolved_rate = ROUND(AVG(CASE(resolution_status != "resolved", 1.0, 0.0)) * 100, 2),
        unique_members = COUNT_DISTINCT(member_id)
      BY plan_type, plan_name, coverage_tier, call_type
    | EVAL confusion_score = ROUND(
        (avg_call_duration / 60) * 
        (unresolved_rate / 10) * 
        (avg_verification_steps / 2), 
        2
      )
    | EVAL repeat_caller_rate = ROUND((inquiry_count / unique_members), 2)
    | INLINESTATS 
        overall_avg_duration = AVG(avg_call_duration),
        overall_avg_unresolved = AVG(unresolved_rate)
    | EVAL complexity_indicator = CASE(
        confusion_score > 50 AND repeat_caller_rate > 2.0, "Critical - High Confusion",
        confusion_score > 30 OR repeat_caller_rate > 1.5, "High Confusion",
        confusion_score > 15, "Moderate Confusion",
        "Low Confusion"
      )
    | WHERE complexity_indicator IN ("Critical - High Confusion", "High Confusion")
    | SORT confusion_score DESC, inquiry_count DESC
    | KEEP plan_type, plan_name, coverage_tier, call_type, inquiry_count, unique_members, repeat_caller_rate, avg_call_duration, unresolved_rate, confusion_score, complexity_indicator
    | LIMIT 100
            """.strip()
        })
        
        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized ES|QL queries with ?parameter syntax for Agent Builder
    
        Access datasets via self.datasets
        """
        queries = []
        
        # Query 1: Find Members by Plan and Coverage Status
        queries.append({
            "name": "Find Members by Plan and Coverage Status",
            "description": "Interactive tool to search members by plan type and eligibility status. Shows member coverage details with recent call history and call volume statistics compared to plan type averages.",
            "pain_point": "Coverage and benefits verification - pulling member plan details and eligibility",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "plan_type",
                    "type": "keyword",
                    "description": "Filter by plan type (e.g., HMO, PPO, Medicare Advantage)",
                    "required": True
                },
                {
                    "name": "eligibility_status",
                    "type": "keyword",
                    "description": "Filter by eligibility status (e.g., Active, Pending, Terminated)",
                    "required": True
                }
            ],
            "datasets_used": ["member_plans", "call_center_transactions"],
            "esql_query": """FROM member_plans
    | WHERE plan_type == ?plan_type AND eligibility_status == ?eligibility_status
    | LOOKUP JOIN call_center_transactions ON member_id
    | WHERE @timestamp >= NOW() - 30 days OR @timestamp IS NULL
    | EVAL days_since_effective = (NOW() - effective_date) / 86400000
    | STATS 
        recent_call_count = COUNT(transaction_id),
        last_call_date = MAX(@timestamp),
        total_call_duration = SUM(call_duration_seconds)
      BY member_id, plan_type, plan_name, coverage_tier, eligibility_status, 
         deductible_remaining, out_of_pocket_max, effective_date
    | INLINESTATS avg_calls_by_plan = AVG(recent_call_count) BY plan_type
    | EVAL calls_vs_avg = recent_call_count - avg_calls_by_plan
    | SORT recent_call_count DESC
    | LIMIT 100""",
            "output_fields": [
                "member_id",
                "plan_type",
                "plan_name",
                "coverage_tier",
                "eligibility_status",
                "deductible_remaining",
                "out_of_pocket_max",
                "effective_date",
                "recent_call_count",
                "last_call_date",
                "total_call_duration",
                "avg_calls_by_plan",
                "calls_vs_avg"
            ],
            "use_case": "Agents can quickly verify member coverage and eligibility while seeing their recent interaction history and identifying members who call more frequently than average for their plan type."
        })
        
        # Query 2: Provider Network Search and Verification
        queries.append({
            "name": "Provider Network Search and Verification",
            "description": "Search providers by specialty and network status. Identifies potentially outdated provider records and shows pending prior authorization counts to help agents provide accurate network information.",
            "pain_point": "Network directories not always being current",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "specialty",
                    "type": "keyword",
                    "description": "Filter by provider specialty (e.g., Cardiology, Primary Care, Endocrinology)",
                    "required": True
                },
                {
                    "name": "network_status",
                    "type": "keyword",
                    "description": "Filter by network status (e.g., In-Network, Out-of-Network, Pending)",
                    "required": True
                }
            ],
            "datasets_used": ["provider_network", "prior_authorizations"],
            "esql_query": """FROM provider_network
    | WHERE specialty == ?specialty AND network_status == ?network_status
    | EVAL days_since_verification = (NOW() - last_verified_date) / 86400000
    | EVAL verification_status = CASE(
        days_since_verification > 90, "OUTDATED - Needs Verification",
        days_since_verification > 60, "Verification Due Soon",
        "Current"
      )
    | LOOKUP JOIN prior_authorizations ON provider_id
    | WHERE status == "Pending" OR status IS NULL
    | STATS 
        pending_prior_auths = COUNT(prior_auth_id),
        oldest_pending_days = MAX(days_pending),
        urgent_count = SUM(CASE(urgency_flag == true, 1, 0))
      BY provider_id, provider_name, specialty, network_status, 
         accepting_patients, address, phone, last_verified_date, 
         days_since_verification, verification_status
    | EVAL priority_score = days_since_verification + (pending_prior_auths * 5) + (urgent_count * 10)
    | SORT priority_score DESC, days_since_verification DESC
    | LIMIT 50""",
            "output_fields": [
                "provider_id",
                "provider_name",
                "specialty",
                "network_status",
                "accepting_patients",
                "address",
                "phone",
                "last_verified_date",
                "days_since_verification",
                "verification_status",
                "pending_prior_auths",
                "oldest_pending_days",
                "urgent_count",
                "priority_score"
            ],
            "use_case": "Helps agents find providers while flagging potentially outdated directory information. Priority score highlights providers needing urgent directory updates based on verification age and pending authorizations."
        })
        
        # Query 3: Claims Denial Code Lookup and Resolution
        queries.append({
            "name": "Claims Denial Code Lookup and Resolution",
            "description": "Interactive denial code lookup tool that provides denial explanations, resolution guidance, and appeal success rates. Shows frequency of denial codes to identify systemic issues.",
            "pain_point": "Claims issues and denials - accessing claim status and explaining denial codes",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "denial_code",
                    "type": "keyword",
                    "description": "The specific denial code to lookup (e.g., CO-16, CO-97, PR-1)",
                    "required": True
                }
            ],
            "datasets_used": ["claims_denials", "call_center_transactions"],
            "esql_query": """FROM claims_denials
    | WHERE denial_code == ?denial_code
    | LOOKUP JOIN call_center_transactions ON denial_code
    | WHERE @timestamp >= NOW() - 90 days OR @timestamp IS NULL
    | EVAL resolution_success = CASE(
        resolution_status == "Resolved", 1,
        resolution_status == "Escalated", 0,
        resolution_status == "Pending", 0,
        NULL
      )
    | STATS 
        total_occurrences_90d = COUNT(transaction_id),
        resolved_count = SUM(CASE(resolution_status == "Resolved", 1, 0)),
        escalated_count = SUM(CASE(resolution_status == "Escalated", 1, 0)),
        avg_processing_time = AVG(processing_time_seconds),
        avg_call_duration = AVG(call_duration_seconds),
        last_occurrence = MAX(@timestamp)
      BY denial_code, denial_reason, common_resolution, appeal_success_rate, category
    | EVAL resolution_rate = ROUND(resolved_count / total_occurrences_90d * 100, 2)
    | EVAL avg_processing_minutes = ROUND(avg_processing_time / 60, 1)
    | EVAL avg_call_minutes = ROUND(avg_call_duration / 60, 1)
    | EVAL trend_indicator = CASE(
        total_occurrences_90d > 100, "HIGH VOLUME",
        total_occurrences_90d > 50, "MODERATE",
        "LOW"
      )
    | SORT total_occurrences_90d DESC""",
            "output_fields": [
                "denial_code",
                "denial_reason",
                "common_resolution",
                "appeal_success_rate",
                "category",
                "total_occurrences_90d",
                "resolved_count",
                "escalated_count",
                "resolution_rate",
                "avg_processing_minutes",
                "avg_call_minutes",
                "last_occurrence",
                "trend_indicator"
            ],
            "use_case": "Agents can instantly lookup denial codes to explain reasons to members, provide resolution steps, and set expectations based on appeal success rates. Volume trends help identify systemic denial issues requiring process improvements."
        })
        
        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries with MATCH -> RERANK -> COMPLETION pipeline
    
        Access datasets via self.datasets
        """
        queries = []
        
        # Query 1: Insurance Terminology and Policy Explanation
        queries.append({
            "name": "Insurance Terminology and Policy Explanation",
            "description": "Semantic search knowledge base to find articles explaining insurance terms, plan differences, and coverage details based on customer questions",
            "pain_point": "Plans vary significantly and customers don't understand insurance terminology",
            "query_type": "rag",
            "datasets": ["insurance_knowledge_base"],
            "parameters": [
                {
                    "name": "customer_question",
                    "type": "string",
                    "description": "The customer's question about insurance terminology or plan details",
                    "required": True,
                    "example": "What is the difference between a deductible and out-of-pocket maximum?"
                },
                {
                    "name": "top_k",
                    "type": "integer",
                    "description": "Number of articles to retrieve before reranking",
                    "required": False,
                    "default": 10
                },
                {
                    "name": "rerank_limit",
                    "type": "integer",
                    "description": "Number of top articles to keep after reranking",
                    "required": False,
                    "default": 3
                }
            ],
            "esql_query": """
    FROM insurance_knowledge_base
    | WHERE MATCH(title, ?customer_question) OR MATCH(content, ?customer_question)
    | EVAL relevance_score = _score
    | SORT relevance_score DESC
    | LIMIT ?top_k
    | KEEP article_id, title, content, category, topic_tags, last_updated, relevance_score
            """.strip(),
            "rerank": {
                "enabled": True,
                "field": "content",
                "query_param": "customer_question",
                "limit": "?rerank_limit"
            },
            "completion": {
                "enabled": True,
                "prompt_template": """You are a helpful insurance customer service assistant for UnitedHealth Group.
    
    Based on the following knowledge base articles, provide a clear, plain-language explanation to answer the customer's question.
    
    Customer Question: {customer_question}
    
    Relevant Articles:
    {context}
    
    Instructions:
    - Explain insurance terminology in simple, everyday language
    - Avoid jargon or define any technical terms you must use
    - Be specific about how this applies to UnitedHealth Group plans
    - Keep the explanation concise but complete
    - If the articles mention specific plan types or coverage tiers, include those details
    
    Provide a helpful, customer-friendly response:""",
                "context_fields": ["title", "content", "category"],
                "max_tokens": 500,
                "temperature": 0.7
            },
            "output_fields": [
                "article_id",
                "title",
                "content",
                "category",
                "topic_tags",
                "last_updated",
                "relevance_score",
                "rerank_score",
                "generated_explanation"
            ],
            "use_case": "Agent support tool to quickly find and explain insurance concepts to customers during calls",
            "expected_latency_ms": 800,
            "sample_questions": [
                "What is the difference between a deductible and out-of-pocket maximum?",
                "What does copay mean?",
                "How does a PPO plan differ from an HMO?",
                "What is coinsurance?",
                "What does prior authorization mean?",
                "What is a formulary?",
                "What are in-network vs out-of-network benefits?"
            ]
        })
        
        return queries

    def get_query_progression(self) -> List[str]:
        """Order to present SCRIPTED queries (for demos)"""
        # Extract query names from scripted queries
        queries = self.generate_queries()
        return [q.get('name', f'query_{i}') for i, q in enumerate(queries)]
