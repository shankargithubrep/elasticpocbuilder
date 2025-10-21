"""
Scenario Generator Service
Creates demo scenarios based on customer profile
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generate demo scenarios tailored to customer needs"""

    def __init__(self):
        self.scenario_templates = {
            "performance_analytics": {
                "name": "Performance Analytics Dashboard",
                "description": "Real-time performance monitoring and analysis",
                "datasets": [
                    {"name": "metrics", "records": 100000, "type": "time_series"},
                    {"name": "entities", "records": 1000, "type": "reference"},
                    {"name": "events", "records": 50000, "type": "events"}
                ],
                "relationships": ["entities->metrics", "entities->events"],
                "time_range": "30_days"
            },
            "customer_360": {
                "name": "Customer 360 Analytics",
                "description": "Comprehensive customer behavior and journey analysis",
                "datasets": [
                    {"name": "customers", "records": 5000, "type": "reference"},
                    {"name": "transactions", "records": 50000, "type": "events"},
                    {"name": "interactions", "records": 100000, "type": "events"}
                ],
                "relationships": ["customers->transactions", "customers->interactions"],
                "time_range": "90_days"
            },
            "fraud_detection": {
                "name": "Fraud Detection System",
                "description": "Real-time fraud detection and risk scoring",
                "datasets": [
                    {"name": "accounts", "records": 10000, "type": "reference"},
                    {"name": "transactions", "records": 100000, "type": "events"},
                    {"name": "risk_scores", "records": 50000, "type": "metrics"}
                ],
                "relationships": ["accounts->transactions", "transactions->risk_scores"],
                "time_range": "7_days"
            },
            "operational_intelligence": {
                "name": "Operational Intelligence",
                "description": "Operational efficiency and resource optimization",
                "datasets": [
                    {"name": "resources", "records": 500, "type": "reference"},
                    {"name": "utilization", "records": 50000, "type": "metrics"},
                    {"name": "incidents", "records": 5000, "type": "events"}
                ],
                "relationships": ["resources->utilization", "resources->incidents"],
                "time_range": "30_days"
            }
        }

    def generate_scenario(self, customer_profile: Dict, use_case: str = None) -> Dict:
        """
        Generate a demo scenario based on customer profile

        Args:
            customer_profile: Customer profile information
            use_case: Specific use case to focus on

        Returns:
            Complete scenario configuration
        """
        logger.info(f"Generating scenario for {customer_profile.get('company_name', 'Unknown')}")

        # Select template based on use case or profile
        template = self._select_template(customer_profile, use_case)

        # Customize template for customer
        scenario = self._customize_template(template, customer_profile)

        # Add query suggestions
        scenario["suggested_queries"] = self._generate_query_suggestions(scenario)

        # Add agent configuration
        scenario["agent_config"] = self._generate_agent_config(customer_profile, scenario)

        logger.info(f"Generated scenario: {scenario['name']}")
        return scenario

    def _select_template(self, customer_profile: Dict, use_case: str = None) -> Dict:
        """Select appropriate template based on profile"""
        if use_case:
            use_case_lower = use_case.lower()
            if "fraud" in use_case_lower:
                return self.scenario_templates["fraud_detection"]
            elif "customer" in use_case_lower:
                return self.scenario_templates["customer_360"]
            elif "operation" in use_case_lower:
                return self.scenario_templates["operational_intelligence"]

        # Default to performance analytics
        return self.scenario_templates["performance_analytics"]

    def _customize_template(self, template: Dict, customer_profile: Dict) -> Dict:
        """Customize template for specific customer"""
        scenario = template.copy()

        # Customize naming
        company_name = customer_profile.get("company_name", "Customer")
        scenario["name"] = f"{company_name} {template['name']}"
        scenario["customer"] = company_name

        # Adjust data volumes based on company size
        size = customer_profile.get("size", "enterprise")
        multiplier = {"small": 0.1, "medium": 0.5, "enterprise": 1.0, "large": 2.0}.get(size, 1.0)

        for dataset in scenario["datasets"]:
            dataset["records"] = int(dataset["records"] * multiplier)

        # Add customer-specific context
        scenario["context"] = {
            "industry": customer_profile.get("industry", "technology"),
            "department": customer_profile.get("department", "general"),
            "pain_points": customer_profile.get("pain_points", []),
            "use_cases": customer_profile.get("use_cases", [])
        }

        return scenario

    def _generate_query_suggestions(self, scenario: Dict) -> List[Dict]:
        """Generate suggested queries for the scenario"""
        queries = []

        # Base queries for all scenarios
        queries.append({
            "name": "Top Performers",
            "description": "Identify top performing entities",
            "complexity": "simple"
        })

        queries.append({
            "name": "Trend Analysis",
            "description": "Analyze trends over time",
            "complexity": "medium"
        })

        # Add dataset-specific queries
        for dataset in scenario["datasets"]:
            if dataset["type"] == "metrics":
                queries.append({
                    "name": f"{dataset['name'].title()} Aggregation",
                    "description": f"Aggregate {dataset['name']} by key dimensions",
                    "complexity": "medium"
                })
            elif dataset["type"] == "events":
                queries.append({
                    "name": f"{dataset['name'].title()} Pattern Analysis",
                    "description": f"Analyze patterns in {dataset['name']}",
                    "complexity": "complex"
                })

        # Add relationship queries
        if scenario.get("relationships"):
            queries.append({
                "name": "Cross-Dataset Analysis",
                "description": "Join and analyze across multiple datasets",
                "complexity": "complex"
            })

        return queries[:8]  # Limit to 8 queries

    def _generate_agent_config(self, customer_profile: Dict, scenario: Dict) -> Dict:
        """Generate agent configuration for the scenario"""
        company = customer_profile.get("company_name", "Customer")
        industry = customer_profile.get("industry", "general")

        return {
            "id": f"agent_{company.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}",
            "display_name": f"{company} Analytics Expert",
            "description": f"AI-powered analytics agent for {company}'s {scenario['name']}",
            "instructions": f"""You are an expert analytics agent for {company}, specializing in {industry} industry analytics.

Your role is to help analyze data from the following sources:
{', '.join([d['name'] for d in scenario['datasets']])}

Focus on providing insights related to:
{', '.join(customer_profile.get('use_cases', ['general analytics'])[:3])}

Always provide specific metrics and actionable recommendations.""",
            "labels": [industry, "demo", customer_profile.get("department", "general").lower()]
        }

    def validate_scenario(self, scenario: Dict) -> bool:
        """
        Validate that scenario is complete and valid

        Args:
            scenario: Scenario configuration

        Returns:
            True if valid
        """
        required_fields = ["name", "datasets", "suggested_queries", "agent_config"]

        for field in required_fields:
            if field not in scenario:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate datasets
        if not scenario["datasets"] or len(scenario["datasets"]) == 0:
            logger.error("No datasets defined")
            return False

        # Validate each dataset
        for dataset in scenario["datasets"]:
            if "name" not in dataset or "records" not in dataset:
                logger.error(f"Invalid dataset: {dataset}")
                return False

        logger.info("Scenario validation passed")
        return True