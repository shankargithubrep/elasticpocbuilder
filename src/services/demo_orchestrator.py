"""
Demo Orchestrator Service
Coordinates all services to generate complete demos
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
import json
import logging
from datetime import datetime

from .llm_service import LLMService, ConversationContext
from .enhanced_data_generator import EnhancedDataGenerator
from .esql_generator import ESQLGenerator
from .elastic_client import ElasticClient
from .validation_service import ValidationService

logger = logging.getLogger(__name__)


@dataclass
class DemoPackage:
    """Complete demo package with all artifacts"""
    demo_id: str
    customer_name: str
    department: str
    use_case: str
    datasets: Dict[str, pd.DataFrame]
    queries: List[Dict[str, str]]
    agent_config: Dict[str, Any]
    demo_guide: str
    validation_results: Dict[str, Any]
    created_at: datetime


class DemoOrchestrator:
    """Orchestrates the complete demo generation process"""

    def __init__(self):
        """Initialize orchestrator with all services"""
        self.llm_service = LLMService()
        self.data_generator = EnhancedDataGenerator()
        self.esql_generator = ESQLGenerator()
        self.elastic_client = None  # Initialize when needed
        self.validation_service = None  # Initialize when needed

    def generate_demo(
        self,
        context: ConversationContext,
        progress_callback: Optional[callable] = None
    ) -> DemoPackage:
        """Generate a complete demo package from context"""

        demo_id = f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Update progress
        if progress_callback:
            progress_callback(0.1, "📋 Creating demo plan...")

        # Step 1: Generate demo plan
        demo_plan = self.llm_service.generate_demo_plan(context)

        if progress_callback:
            progress_callback(0.2, "🏗️ Generating datasets...")

        # Step 2: Generate data
        data_plan = self.data_generator.create_plan({
            "company": context.company_name,
            "industry": context.industry,
            "scale": context.scale or "10000 records",
            "use_cases": context.use_cases
        })

        datasets = self.data_generator.generate_datasets(data_plan)

        # Apply relationships
        if data_plan.relationships:
            datasets = self.data_generator.create_relationships(
                datasets, data_plan.relationships
            )

        if progress_callback:
            progress_callback(0.4, "🔍 Creating ES|QL queries...")

        # Step 3: Generate queries
        queries = self.esql_generator.generate_queries({
            "datasets": list(datasets.keys()),
            "use_cases": context.use_cases,
            "metrics": context.metrics,
            "pain_points": context.pain_points
        })

        if progress_callback:
            progress_callback(0.6, "🤖 Configuring agent...")

        # Step 4: Create agent configuration
        agent_config = self._create_agent_config(context, queries)

        if progress_callback:
            progress_callback(0.7, "✅ Validating components...")

        # Step 5: Validate if Elasticsearch is available
        validation_results = self._validate_demo(datasets, queries)

        if progress_callback:
            progress_callback(0.9, "📝 Creating demo guide...")

        # Step 6: Generate demo guide
        demo_guide = self._generate_demo_guide(
            context, datasets, queries, agent_config
        )

        if progress_callback:
            progress_callback(1.0, "✅ Demo ready!")

        # Create demo package
        return DemoPackage(
            demo_id=demo_id,
            customer_name=context.company_name,
            department=context.department,
            use_case=context.use_cases[0] if context.use_cases else "Analytics",
            datasets=datasets,
            queries=queries,
            agent_config=agent_config,
            demo_guide=demo_guide,
            validation_results=validation_results,
            created_at=datetime.now()
        )

    def _create_agent_config(
        self,
        context: ConversationContext,
        queries: List[Dict]
    ) -> Dict[str, Any]:
        """Create agent configuration"""
        return {
            "name": f"{context.company_name} {context.department} Assistant",
            "description": f"AI assistant for {context.department} at {context.company_name}",
            "instructions": f"""You are an intelligent assistant helping {context.company_name}'s {context.department} team.

Your capabilities include:
- Analyzing {', '.join(context.use_cases[:3]) if context.use_cases else 'business data'}
- Answering questions about {', '.join(context.metrics) if context.metrics else 'key metrics'}
- Providing insights and recommendations

Use the available tools to query data and provide accurate, helpful responses.""",
            "tools": [
                {
                    "name": query["name"].lower().replace(" ", "_"),
                    "description": query.get("description", f"Query for {query['name']}"),
                    "query": query["esql"]
                }
                for query in queries[:5]  # Top 5 queries as tools
            ],
            "model": "gpt-4",
            "temperature": 0.7
        }

    def _validate_demo(
        self,
        datasets: Dict[str, pd.DataFrame],
        queries: List[Dict]
    ) -> Dict[str, Any]:
        """Validate demo components if Elasticsearch is available"""
        validation_results = {
            "datasets_valid": True,
            "queries_valid": False,
            "elastic_available": False,
            "issues": []
        }

        # Check datasets
        for name, df in datasets.items():
            if df.empty:
                validation_results["datasets_valid"] = False
                validation_results["issues"].append(f"Dataset '{name}' is empty")

        # Check if Elasticsearch is available
        try:
            if self.elastic_client is None:
                from .elastic_client import ElasticClient
                self.elastic_client = ElasticClient()

            if self.elastic_client.is_connected():
                validation_results["elastic_available"] = True
                # Validate queries
                # ... query validation logic ...
        except:
            validation_results["elastic_available"] = False
            logger.info("Elasticsearch not available - skipping query validation")

        return validation_results

    def _generate_demo_guide(
        self,
        context: ConversationContext,
        datasets: Dict[str, pd.DataFrame],
        queries: List[Dict],
        agent_config: Dict
    ) -> str:
        """Generate a comprehensive demo guide"""
        guide = f"""# Demo Guide: {context.company_name} - {context.department}

## Executive Summary
This demo showcases how Elastic Agent Builder can transform {context.company_name}'s {context.department} operations by providing instant, AI-powered insights from complex data.

## Customer Context
- **Company:** {context.company_name}
- **Department:** {context.department}
- **Industry:** {context.industry}
- **Scale:** {context.scale}

## Pain Points Addressed
"""
        for pain_point in context.pain_points:
            guide += f"- {pain_point}\n"

        guide += """
## Demo Flow

### 1. Introduction (2 minutes)
- Acknowledge their current challenges
- Preview what you'll demonstrate
- Set expectations for outcomes

### 2. Data Overview (3 minutes)
Show the scale and complexity of data:
"""
        for name, df in datasets.items():
            guide += f"- **{name}**: {len(df):,} records\n"

        guide += """
### 3. Live Queries (10 minutes)
Demonstrate these queries in order:

"""
        for i, query in enumerate(queries[:5], 1):
            guide += f"""#### Query {i}: {query['name']}
**Purpose:** {query.get('description', 'Analyze data')}
**Expected Result:** {query.get('expected_result', 'Insights will appear')}
**Talk Track:** "Notice how quickly we can {query['name'].lower()}..."

```esql
{query['esql']}
```

"""

        guide += f"""### 4. Agent Interaction (5 minutes)
Show the AI assistant in action:

**Demo Questions:**
1. "What are our top performing {context.metrics[0] if context.metrics else 'metrics'}?"
2. "Show me any anomalies in the last 24 hours"
3. "What actions should we take based on this data?"

### 5. ROI Discussion (5 minutes)
Quantify the value:
- Time saved: Hours → Seconds
- Accuracy improvement: Manual errors eliminated
- Cost reduction: Fewer resources needed
- Scale: Handle 10x more data

## Key Differentiators
- **Real-time insights** instead of batch reports
- **Natural language** interface for non-technical users
- **Automated anomaly detection** reduces incidents
- **Scalable architecture** grows with your business

## Common Objections & Responses

**"How is this different from our current BI tools?"**
> Agent Builder provides conversational AI on top of real-time data, not just static dashboards.

**"What about data security?"**
> Elastic provides enterprise-grade security with encryption, RBAC, and audit logging.

**"How long does implementation take?"**
> Most customers are generating insights within days, not months.

## Call to Action
1. Propose a 2-week proof of concept
2. Offer to analyze their actual data
3. Schedule technical deep-dive with their team

## Resources
- [Agent Builder Documentation](https://elastic.co/agent-builder)
- [ES|QL Reference](https://elastic.co/guide/esql)
- [Customer Success Stories](https://elastic.co/customers)

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*Demo ID: {context.company_name.replace(' ', '_')}_{context.department.replace(' ', '_')}*
"""
        return guide


def create_demo_from_context(context: Dict[str, Any]) -> DemoPackage:
    """Convenience function to create demo from context dictionary"""
    # Convert dict to ConversationContext
    conv_context = ConversationContext(
        company_name=context.get("company_name"),
        department=context.get("department"),
        industry=context.get("industry"),
        pain_points=context.get("pain_points", []),
        use_cases=context.get("use_cases", []),
        scale=context.get("scale"),
        metrics=context.get("metrics", []),
        conversation_phase="ready"
    )

    orchestrator = DemoOrchestrator()
    return orchestrator.generate_demo(conv_context)