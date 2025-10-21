"""
Customer Research Service
Gathers context about customers for demo customization
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CustomerProfile:
    """Customer profile information"""
    company_name: str
    industry: str
    department: str
    pain_points: List[str]
    use_cases: List[str]
    size: str = "enterprise"
    region: str = "global"


class CustomerResearcher:
    """Research customers and identify relevant use cases"""

    def __init__(self):
        # Industry templates with common pain points and use cases
        self.industry_templates = {
            "retail": {
                "pain_points": [
                    "Inventory optimization",
                    "Customer churn",
                    "Supply chain visibility",
                    "Fraud detection"
                ],
                "use_cases": [
                    "Real-time inventory analytics",
                    "Customer behavior analysis",
                    "Sales performance tracking",
                    "Product recommendation"
                ],
                "key_metrics": ["conversion_rate", "cart_value", "customer_lifetime_value"]
            },
            "financial": {
                "pain_points": [
                    "Fraud detection",
                    "Compliance monitoring",
                    "Risk assessment",
                    "Customer experience"
                ],
                "use_cases": [
                    "Transaction monitoring",
                    "AML compliance",
                    "Credit risk scoring",
                    "Customer 360 view"
                ],
                "key_metrics": ["fraud_rate", "compliance_score", "risk_score"]
            },
            "healthcare": {
                "pain_points": [
                    "Patient outcomes",
                    "Operational efficiency",
                    "Resource utilization",
                    "Readmission rates"
                ],
                "use_cases": [
                    "Patient journey analytics",
                    "Clinical outcomes tracking",
                    "Resource optimization",
                    "Predictive health monitoring"
                ],
                "key_metrics": ["readmission_rate", "patient_satisfaction", "treatment_efficacy"]
            },
            "technology": {
                "pain_points": [
                    "System performance",
                    "Security threats",
                    "Development velocity",
                    "Infrastructure costs"
                ],
                "use_cases": [
                    "Application performance monitoring",
                    "Security threat detection",
                    "DevOps analytics",
                    "Cost optimization"
                ],
                "key_metrics": ["uptime", "mttr", "deployment_frequency", "error_rate"]
            },
            "marketing": {
                "pain_points": [
                    "Campaign ROI",
                    "Attribution",
                    "Content performance",
                    "Lead quality"
                ],
                "use_cases": [
                    "Campaign performance analytics",
                    "Multi-touch attribution",
                    "Content engagement tracking",
                    "Lead scoring"
                ],
                "key_metrics": ["roi", "conversion_rate", "engagement_rate", "cac"]
            }
        }

    def research_company(self, company_name: str, department: str = None) -> CustomerProfile:
        """
        Research a company and create a customer profile

        Args:
            company_name: Name of the company
            department: Specific department or team

        Returns:
            CustomerProfile with relevant information
        """
        logger.info(f"Researching company: {company_name}")

        # Detect industry from company name (simple heuristic)
        industry = self._detect_industry(company_name)

        # Get template for industry
        template = self.industry_templates.get(industry, self.industry_templates["technology"])

        # Customize for department if specified
        if department:
            pain_points = self._customize_for_department(template["pain_points"], department)
            use_cases = self._customize_for_department(template["use_cases"], department)
        else:
            pain_points = template["pain_points"][:3]  # Top 3 pain points
            use_cases = template["use_cases"][:3]  # Top 3 use cases

        profile = CustomerProfile(
            company_name=company_name,
            industry=industry,
            department=department or "General",
            pain_points=pain_points,
            use_cases=use_cases
        )

        logger.info(f"Created profile for {company_name}: {industry} industry, {len(use_cases)} use cases")
        return profile

    def _detect_industry(self, company_name: str) -> str:
        """Detect industry from company name (simple heuristic)"""
        name_lower = company_name.lower()

        # Check for industry keywords
        if any(word in name_lower for word in ["bank", "financial", "capital", "invest"]):
            return "financial"
        elif any(word in name_lower for word in ["health", "medical", "pharma", "bio"]):
            return "healthcare"
        elif any(word in name_lower for word in ["retail", "shop", "store", "commerce"]):
            return "retail"
        elif any(word in name_lower for word in ["market", "media", "advertis", "brand", "adobe"]):
            return "marketing"
        else:
            return "technology"

    def _customize_for_department(self, items: List[str], department: str) -> List[str]:
        """Customize pain points or use cases for specific department"""
        dept_lower = department.lower()

        # Filter based on department
        if "security" in dept_lower:
            return [item for item in items if any(
                word in item.lower() for word in ["security", "threat", "fraud", "risk"]
            )][:3]
        elif "marketing" in dept_lower or "sales" in dept_lower:
            return [item for item in items if any(
                word in item.lower() for word in ["customer", "campaign", "roi", "conversion"]
            )][:3]
        elif "operations" in dept_lower or "ops" in dept_lower:
            return [item for item in items if any(
                word in item.lower() for word in ["efficiency", "performance", "optimization", "resource"]
            )][:3]
        else:
            return items[:3]

    def suggest_demo_focus(self, profile: CustomerProfile) -> Dict:
        """
        Suggest demo focus areas based on customer profile

        Args:
            profile: Customer profile

        Returns:
            Demo focus recommendations
        """
        return {
            "primary_use_case": profile.use_cases[0] if profile.use_cases else "General Analytics",
            "datasets_needed": self._suggest_datasets(profile),
            "key_queries": self._suggest_queries(profile),
            "success_metrics": self._get_metrics_for_industry(profile.industry)
        }

    def _suggest_datasets(self, profile: CustomerProfile) -> List[str]:
        """Suggest datasets based on profile"""
        industry = profile.industry

        dataset_map = {
            "retail": ["products", "orders", "customers", "inventory"],
            "financial": ["transactions", "accounts", "customers", "risk_scores"],
            "healthcare": ["patients", "treatments", "appointments", "outcomes"],
            "technology": ["logs", "metrics", "alerts", "deployments"],
            "marketing": ["campaigns", "leads", "content", "conversions"]
        }

        return dataset_map.get(industry, ["entities", "events", "metrics"])[:3]

    def _suggest_queries(self, profile: CustomerProfile) -> List[str]:
        """Suggest key queries based on profile"""
        use_case = profile.use_cases[0] if profile.use_cases else ""

        queries = []
        if "performance" in use_case.lower():
            queries.append("Performance metrics over time")
        if "customer" in use_case.lower():
            queries.append("Customer segmentation analysis")
        if "fraud" in use_case.lower() or "threat" in use_case.lower():
            queries.append("Anomaly detection patterns")
        if "optimization" in use_case.lower():
            queries.append("Resource utilization analysis")

        # Add default queries
        queries.extend([
            "Top performing entities",
            "Trend analysis",
            "Comparative metrics"
        ])

        return queries[:5]

    def _get_metrics_for_industry(self, industry: str) -> List[str]:
        """Get key metrics for industry"""
        template = self.industry_templates.get(industry, self.industry_templates["technology"])
        return template.get("key_metrics", ["count", "sum", "average"])