"""
LLM Service for intelligent conversation handling
Implements test-driven requirements for demo generation
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context gathered during conversation"""
    company_name: Optional[str] = None
    department: Optional[str] = None
    industry: Optional[str] = None
    pain_points: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    scale: Optional[str] = None
    urgency: Optional[str] = None
    audience: Optional[str] = None
    metrics: List[str] = field(default_factory=list)
    conversation_phase: str = "discovery"


@dataclass
class LLMResponse:
    """Response from LLM service"""
    content: str
    extracted_context: ConversationContext
    suggested_use_cases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMService:
    """Service for handling LLM interactions"""

    def __init__(self, provider: Optional[str] = None):
        """Initialize LLM service with specified provider"""
        self.provider = provider or self._detect_provider()
        self.client = self._initialize_client()

    def _detect_provider(self) -> str:
        """Detect which LLM provider to use based on available API keys"""
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        else:
            logger.warning("No API keys found, using mock mode")
            return "mock"

    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except ImportError:
                logger.error("Anthropic library not installed")
                self.provider = "mock"
                return None

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                logger.error("OpenAI library not installed")
                self.provider = "mock"
                return None

        return None  # Mock mode

    def process_message(
        self,
        message: str,
        context: ConversationContext,
        conversation_history: List[Dict[str, str]]
    ) -> LLMResponse:
        """Process user message and generate response"""

        # Extract context from message
        extracted = self._extract_context(message)

        # Merge with existing context
        updated_context = self._merge_contexts(context, extracted)

        # Update conversation phase
        updated_context.conversation_phase = self._determine_phase(updated_context)

        metadata = {}
        try:
            # Generate response based on provider
            if self.provider == "mock":
                response_content = self._generate_mock_response(
                    message, updated_context, conversation_history
                )
            else:
                response_content = self._call_api(
                    message, updated_context, conversation_history
                )
            metadata = {"phase": updated_context.conversation_phase, "mode": self.provider}
        except Exception as e:
            logger.error(f"API call failed: {e}")
            response_content = "I apologize, but I'm having trouble processing your request. Let me help you build your demo step by step."
            # Add error to metadata
            metadata = {"error": str(e), "mode": "fallback", "phase": updated_context.conversation_phase}

        # Generate suggested use cases if in appropriate phase
        suggested_use_cases = []
        if updated_context.conversation_phase == "use_case_selection":
            suggested_use_cases = self._generate_use_case_suggestions(updated_context)

        return LLMResponse(
            content=response_content,
            extracted_context=updated_context,
            suggested_use_cases=suggested_use_cases,
            metadata=metadata
        )

    def _extract_context(self, message: str) -> ConversationContext:
        """Extract context information from message"""
        context = ConversationContext()

        # Extract company name
        company_patterns = [
            r"([A-Z][A-Za-z0-9\s&'.-]+?)(?:'s|'s)\s+(?:Supply Chain|Customer Success|Marketing|Sales|[A-Z][a-z]+)\s+team",
            r"(?:for|with|at)\s+([A-Z][A-Za-z\s&'.-]+?)(?:'s|'s|team|division)",
            r"^([A-Z][A-Za-z\s&'.-]+?)(?:'s|'s)\s+(?:team|department)",
        ]

        for pattern in company_patterns:
            match = re.search(pattern, message)
            if match:
                context.company_name = match.group(1).strip()
                break

        # Extract department
        dept_keywords = {
            "Supply Chain": ["supply chain", "logistics", "inventory"],
            "Sales": ["sales", "revenue", "account"],
            "Marketing": ["marketing", "campaign", "brand"],
            "Customer Success": ["customer success", "cs team", "churn"],
            "Emergency Department": ["emergency", "ER", "ED"],
            "E-commerce": ["e-commerce", "ecommerce", "online"],
        }

        message_lower = message.lower()
        for dept, keywords in dept_keywords.items():
            if any(kw in message_lower for kw in keywords):
                context.department = dept
                break

        # Extract pain points
        if any(word in message_lower for word in ["lose", "loss", "lost"]):
            # Extract dollar amounts
            dollar_match = re.search(r"\$([0-9.]+)([BMK])", message)
            if dollar_match:
                context.pain_points.append(f"Financial losses: ${dollar_match.group(1)}{dollar_match.group(2)}")

        if "stockout" in message_lower or "out of stock" in message_lower:
            context.pain_points.append("Inventory stockouts")

        if "visibility" in message_lower:
            context.pain_points.append("Lack of visibility")

        if "roi" in message_lower:
            context.pain_points.append("ROI tracking")

        if "churn" in message_lower:
            context.pain_points.append("Customer churn")

        if "fraud" in message_lower:
            context.pain_points.append("Fraud detection")

        # Extract scale
        scale_patterns = [
            r"(\d+[,\d]*)\+?\s*(stores?|locations?|accounts?|transactions?|hospitals?)",
            r"(\d+[,\d]*)\s*([BMK])\s+(?:in\s+)?(\w+)",
        ]

        for pattern in scale_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                context.scale = match.group(0)
                break

        # Infer industry
        if context.company_name:
            company_lower = context.company_name.lower()
            if "walmart" in company_lower or "target" in company_lower:
                context.industry = "Retail"
            elif "kaiser" in company_lower or "clinic" in company_lower:
                context.industry = "Healthcare"
            elif "adobe" in company_lower or "microsoft" in company_lower or "salesforce" in company_lower:
                context.industry = "Technology"
            elif "chase" in company_lower or "goldman" in company_lower:
                context.industry = "Financial"

        return context

    def _merge_contexts(
        self,
        existing: ConversationContext,
        extracted: ConversationContext
    ) -> ConversationContext:
        """Merge extracted context with existing context"""
        # Create new context with merged values
        merged = ConversationContext(
            company_name=extracted.company_name or existing.company_name,
            department=extracted.department or existing.department,
            industry=extracted.industry or existing.industry,
            pain_points=list(set(existing.pain_points + extracted.pain_points)),
            use_cases=list(set(existing.use_cases + extracted.use_cases)),
            scale=extracted.scale or existing.scale,
            urgency=extracted.urgency or existing.urgency,
            audience=extracted.audience or existing.audience,
            metrics=list(set(existing.metrics + extracted.metrics)),
            conversation_phase=existing.conversation_phase
        )
        return merged

    def _determine_phase(self, context: ConversationContext) -> str:
        """Determine current conversation phase based on context"""
        if not context.company_name:
            return "discovery"
        elif not context.department:
            return "discovery"
        elif not context.pain_points:
            return "discovery"
        elif not context.use_cases:
            return "use_case_selection"
        else:
            return "confirmation"

    def _generate_mock_response(
        self,
        message: str,
        context: ConversationContext,
        history: List[Dict[str, str]]
    ) -> str:
        """Generate mock response for testing"""
        phase = context.conversation_phase

        # Check if Adobe was mentioned in history
        adobe_in_history = any("adobe" in h.get("content", "").lower() for h in history)

        if phase == "discovery":
            if not context.company_name:
                return "I'd love to help create your demo! Which company is this for?"
            elif not context.department:
                return f"Great! Tell me about {context.company_name}'s team and their needs."
            else:
                return f"What challenges is {context.company_name}'s {context.department} team facing?"

        elif phase == "use_case_selection":
            # Industry-specific responses
            if context.industry == "Healthcare":
                return f"""Based on {context.company_name}'s needs, here are relevant use cases:
1. Patient Flow Optimization
2. Clinical Analytics
3. Resource Utilization

Which resonates most?"""
            else:
                base_response = f"Based on {context.company_name}'s needs, here are relevant use cases:\n"
                # Add Adobe campaign reference if in history
                if adobe_in_history or "campaign" in message.lower() or "roi" in message.lower():
                    base_response += "1. Campaign Performance Analytics\n"
                    base_response += "2. ROI Tracking\n"
                    base_response += "3. Customer Journey Analysis\n"
                else:
                    base_response += "1. Real-time Analytics\n"
                    base_response += "2. Predictive Insights\n"
                    base_response += "3. Automated Monitoring\n"
                base_response += "\nWhich resonates most?"
                return base_response

        elif phase == "confirmation":
            return f"""Ready to generate a demo for {context.company_name}!
I'll create datasets, queries, and agents tailored to their needs.
Type 'Generate demo' to proceed."""

        return "Tell me more about your customer's needs."

    def _call_api(
        self,
        message: str,
        context: ConversationContext,
        history: List[Dict[str, str]]
    ) -> str:
        """Call actual LLM API"""
        # This method is mocked during testing
        if self.provider == "anthropic":
            return self._call_anthropic(message, context, history)
        elif self.provider == "openai":
            return self._call_openai(message, context, history)
        else:
            return self._generate_mock_response(message, context, history)

    def _call_anthropic(
        self,
        message: str,
        context: ConversationContext,
        history: List[Dict[str, str]]
    ) -> str:
        """Call Anthropic Claude API"""
        if not self.client:
            raise Exception("Anthropic client not initialized")

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Build messages
        messages = []
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        # Call API
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            system=system_prompt,
            messages=messages,
            max_tokens=1000
        )

        return response.content[0].text

    def _call_openai(
        self,
        message: str,
        context: ConversationContext,
        history: List[Dict[str, str]]
    ) -> str:
        """Call OpenAI GPT API"""
        if not self.client:
            raise Exception("OpenAI client not initialized")

        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt(context)}
        ]

        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        # Call API
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000
        )

        return response.choices[0].message.content

    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build system prompt based on context"""
        return f"""You are an expert Elastic Solutions Architect helping create Agent Builder demos.

Current Context:
- Company: {context.company_name or 'Unknown'}
- Department: {context.department or 'Unknown'}
- Industry: {context.industry or 'Unknown'}
- Pain Points: {', '.join(context.pain_points) if context.pain_points else 'Not identified'}
- Phase: {context.conversation_phase}

Your goal is to have a conversation to gather context, then create a tailored demo.
Be specific, helpful, and guide the user through the process."""

    def _generate_use_case_suggestions(self, context: ConversationContext) -> List[str]:
        """Generate relevant use case suggestions based on context"""
        use_cases = []

        # Industry-specific use cases
        if context.industry == "Healthcare":
            use_cases.extend([
                "Patient Flow Optimization",
                "Clinical Analytics",
                "Resource Utilization"
            ])
        elif context.industry == "Retail":
            use_cases.extend([
                "Inventory Optimization",
                "Customer Journey Analytics",
                "Fraud Detection"
            ])
        elif context.industry == "Technology":
            use_cases.extend([
                "Customer Success Analytics",
                "Usage Pattern Analysis",
                "Churn Prediction"
            ])
        elif context.industry == "Financial":
            use_cases.extend([
                "Transaction Monitoring",
                "Risk Analytics",
                "Compliance Automation"
            ])

        # Pain point specific additions
        if any("churn" in p.lower() for p in context.pain_points):
            use_cases.append("Predictive Churn Analysis")
        if any("roi" in p.lower() for p in context.pain_points):
            use_cases.append("ROI Tracking Dashboard")
        if any("fraud" in p.lower() for p in context.pain_points):
            use_cases.append("Real-time Fraud Detection")

        return list(set(use_cases))[:5]  # Return top 5 unique use cases

    def is_ready_to_generate(self, context: ConversationContext) -> bool:
        """Check if we have enough context to generate a demo"""
        return all([
            context.company_name,
            context.department,
            len(context.pain_points) > 0,
            len(context.use_cases) > 0 or context.conversation_phase == "confirmation"
        ])

    def generate_demo_plan(self, context: ConversationContext) -> Dict[str, Any]:
        """Generate a complete demo plan based on context"""
        if not self.is_ready_to_generate(context):
            raise ValueError("Insufficient context to generate demo plan")

        plan = {
            "customer": {
                "company": context.company_name,
                "department": context.department,
                "industry": context.industry
            },
            "datasets": self._plan_datasets(context),
            "queries": self._plan_queries(context),
            "agent_config": self._plan_agent_config(context)
        }

        return plan

    def _plan_datasets(self, context: ConversationContext) -> List[Dict]:
        """Plan datasets based on context"""
        datasets = []

        # Base datasets for most scenarios
        datasets.append({
            "name": "transactions",
            "type": "events",
            "records": 100000,
            "description": "Transaction or event data"
        })

        # Add industry-specific datasets
        if context.industry == "Retail":
            datasets.extend([
                {"name": "products", "type": "reference", "records": 5000},
                {"name": "customers", "type": "reference", "records": 10000},
                {"name": "inventory", "type": "metrics", "records": 50000}
            ])
        elif context.industry == "Healthcare":
            datasets.extend([
                {"name": "patients", "type": "reference", "records": 10000},
                {"name": "departments", "type": "reference", "records": 50},
                {"name": "visits", "type": "events", "records": 50000}
            ])
        elif context.industry == "Technology":
            datasets.extend([
                {"name": "accounts", "type": "reference", "records": 5000},
                {"name": "usage_metrics", "type": "time_series", "records": 100000},
                {"name": "features", "type": "reference", "records": 100}
            ])

        return datasets

    def _plan_queries(self, context: ConversationContext) -> List[Dict]:
        """Plan ES|QL queries based on context"""
        queries = []

        # Add queries based on pain points
        if any("roi" in p.lower() for p in context.pain_points):
            queries.append({
                "name": "ROI Analysis",
                "type": "aggregation",
                "complexity": "intermediate"
            })

        if any("churn" in p.lower() for p in context.pain_points):
            queries.append({
                "name": "Churn Risk Score",
                "type": "calculation",
                "complexity": "complex"
            })

        if any("fraud" in p.lower() for p in context.pain_points):
            queries.append({
                "name": "Anomaly Detection",
                "type": "pattern",
                "complexity": "complex"
            })

        # Add basic queries
        queries.extend([
            {"name": "Overview Dashboard", "type": "aggregation", "complexity": "simple"},
            {"name": "Trend Analysis", "type": "time_series", "complexity": "intermediate"}
        ])

        return queries

    def _plan_agent_config(self, context: ConversationContext) -> Dict:
        """Plan agent configuration based on context"""
        return {
            "name": f"{context.company_name} {context.department} Assistant",
            "description": f"Intelligent assistant for {context.department} analytics",
            "capabilities": context.use_cases[:3] if context.use_cases else ["Analytics", "Monitoring", "Insights"],
            "tools": [
                "query_runner",
                "alert_manager",
                "report_generator"
            ]
        }