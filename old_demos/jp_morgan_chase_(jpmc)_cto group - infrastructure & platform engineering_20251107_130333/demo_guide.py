from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class JPMorganChaseJPMCDemoGuide(DemoGuideModule):
    """Demo guide for JP Morgan Chase (JPMC) - CTO Group - Infrastructure & Platform Engineering"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        # Extract pain points
        pain_points = ', '.join(self.config.pain_points[:2]) if self.config.pain_points else 'operational challenges'

        # Extract query names
        query_names = [q.get('name', f'Query {i+1}') for i, q in enumerate(self.queries[:5])]
        query_list = '\n'.join([f'{i+1}. {name}' for i, name in enumerate(query_names)])

        return f"""# Demo Guide: {self.config.company_name} - {self.config.department}

## Overview
**Industry:** {self.config.industry}
**Focus Areas:** {pain_points}

## Demo Flow
1. **Introduction** - Establish context around their key challenges
2. **Data Exploration** - Show {len(self.queries)} targeted queries addressing pain points
3. **Business Impact** - Highlight speed, accuracy, and insights gained

## Key Queries
{query_list}

## Value Proposition
- **Speed:** Insights in seconds vs hours/days
- **Scalability:** Handles growing data volumes
- **Self-Service:** Empowers teams with intuitive query language

## Closing Points
- ES|QL provides SQL-like simplicity with Elasticsearch power
- Queries run directly on indexed data (millisecond response times)
- Most teams productive within days, not weeks
"""

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
