"""
Conversation handler for Streamlit UI integration
Bridges the LLM service with the Streamlit interface
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from src.services.llm_service import LLMService, ConversationContext

logger = logging.getLogger(__name__)


class ConversationHandler:
    """Handles conversation flow in the Streamlit UI"""

    def __init__(self):
        """Initialize conversation handler"""
        self.llm_service = LLMService()
        self.context = ConversationContext()

    def process_user_input(self, message: str) -> Dict[str, Any]:
        """Process user input and return response with actions"""

        # Get conversation history from session state if available
        try:
            history = st.session_state.get("messages", [])
        except:
            # Running outside Streamlit context (e.g., tests)
            history = []

        # Process message through LLM service
        response = self.llm_service.process_message(
            message=message,
            context=self.context,
            conversation_history=history
        )

        # Update context with extracted information
        self.context = response.extracted_context

        # Update session state if available
        try:
            if "demo_context" in st.session_state:
                st.session_state.demo_context.update({
                    "company_name": self.context.company_name,
                    "department": self.context.department,
                    "industry": self.context.industry,
                    "pain_points": self.context.pain_points,
                    "use_cases": self.context.use_cases,
                    "scale": self.context.scale,
                    "metrics": self.context.metrics
                })
        except:
            # Running outside Streamlit context
            pass

        # Check if user wants to generate demo
        should_generate = False
        demo_plan = None

        if "generate demo" in message.lower() and self.llm_service.is_ready_to_generate(self.context):
            should_generate = True
            demo_plan = self.llm_service.generate_demo_plan(self.context)

        return {
            "response": response.content,
            "context": self.context,
            "metadata": response.metadata,
            "should_generate": should_generate,
            "demo_plan": demo_plan,
            "suggested_use_cases": response.suggested_use_cases
        }

    def get_context_summary(self) -> Dict[str, Any]:
        """Get current context summary for display"""
        return {
            "company": self.context.company_name,
            "department": self.context.department,
            "industry": self.context.industry,
            "pain_points": self.context.pain_points,
            "use_cases": self.context.use_cases,
            "scale": self.context.scale,
            "phase": self.context.conversation_phase,
            "ready_to_generate": self.llm_service.is_ready_to_generate(self.context)
        }

    def reset_conversation(self):
        """Reset conversation context"""
        self.context = ConversationContext()

    def load_context(self, saved_context: Dict[str, Any]):
        """Load previously saved context"""
        self.context = ConversationContext(
            company_name=saved_context.get("company_name"),
            department=saved_context.get("department"),
            industry=saved_context.get("industry"),
            pain_points=saved_context.get("pain_points", []),
            use_cases=saved_context.get("use_cases", []),
            scale=saved_context.get("scale"),
            urgency=saved_context.get("urgency"),
            audience=saved_context.get("audience"),
            metrics=saved_context.get("metrics", []),
            conversation_phase=saved_context.get("conversation_phase", "discovery")
        )