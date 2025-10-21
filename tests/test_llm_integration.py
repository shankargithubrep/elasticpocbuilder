"""
Test-driven development for LLM integration
Tests written BEFORE implementation to ensure proper functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.llm_service import LLMService, LLMResponse, ConversationContext


class TestLLMService(unittest.TestCase):
    """Test cases for LLM service integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.llm_service = LLMService()
        self.test_context = ConversationContext(
            company_name="Acme Corp",
            department="Sales",
            industry="Technology",
            pain_points=["Slow reporting", "Manual processes"],
            conversation_phase="discovery"
        )

    def test_llm_service_initialization(self):
        """Test that LLM service initializes correctly"""
        self.assertIsNotNone(self.llm_service)
        self.assertTrue(hasattr(self.llm_service, 'process_message'))
        self.assertTrue(hasattr(self.llm_service, 'generate_demo_plan'))

    def test_process_message_with_context(self):
        """Test processing a message with existing context"""
        message = "We need help with customer churn analysis"

        response = self.llm_service.process_message(
            message=message,
            context=self.test_context,
            conversation_history=[]
        )

        self.assertIsInstance(response, LLMResponse)
        self.assertIsNotNone(response.content)
        self.assertIsNotNone(response.extracted_context)
        self.assertIn("phase", response.metadata)

    def test_context_extraction_from_detailed_prompt(self):
        """Test extracting context from a detailed customer description"""
        detailed_prompt = """
        Walmart's Supply Chain team manages 4,700 stores and needs real-time
        inventory visibility. They lose $2.3B annually to stockouts.
        """

        response = self.llm_service.process_message(
            message=detailed_prompt,
            context=ConversationContext(),
            conversation_history=[]
        )

        # Should extract company, department, pain points, and scale
        self.assertEqual(response.extracted_context.company_name, "Walmart")
        self.assertIn("Supply Chain", response.extracted_context.department)
        self.assertGreater(len(response.extracted_context.pain_points), 0)
        self.assertIsNotNone(response.extracted_context.scale)

    def test_conversation_phase_progression(self):
        """Test that conversation phases progress correctly"""
        # Start with discovery phase
        context = ConversationContext(conversation_phase="discovery")

        # Provide company info
        response1 = self.llm_service.process_message(
            message="This is for Adobe's marketing team",
            context=context,
            conversation_history=[]
        )
        self.assertEqual(response1.extracted_context.company_name, "Adobe")

        # Add pain points
        context.company_name = "Adobe"
        context.department = "Marketing"
        response2 = self.llm_service.process_message(
            message="They struggle with campaign ROI tracking",
            context=context,
            conversation_history=[{"role": "user", "content": "This is for Adobe"}]
        )
        self.assertIn("ROI", str(response2.extracted_context.pain_points))

        # Should move to use case selection
        self.assertIn(response2.metadata["phase"], ["use_case_selection", "confirmation"])

    def test_generate_demo_plan(self):
        """Test generating a complete demo plan"""
        # Full context
        context = ConversationContext(
            company_name="Target",
            department="E-commerce",
            industry="Retail",
            pain_points=["Fraud detection", "Cart abandonment"],
            use_cases=["Transaction monitoring", "Customer analytics"],
            scale="10M transactions/day",
            conversation_phase="confirmation"
        )

        plan = self.llm_service.generate_demo_plan(context)

        self.assertIsNotNone(plan)
        self.assertIn("datasets", plan)
        self.assertIn("queries", plan)
        self.assertIn("agent_config", plan)
        self.assertIsInstance(plan["datasets"], list)
        self.assertGreater(len(plan["datasets"]), 0)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_anthropic_client_initialization(self):
        """Test that Anthropic client initializes with API key"""
        service = LLMService(provider="anthropic")
        self.assertEqual(service.provider, "anthropic")
        self.assertIsNotNone(service.client)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_openai_client_initialization(self):
        """Test that OpenAI client initializes with API key"""
        service = LLMService(provider="openai")
        self.assertEqual(service.provider, "openai")
        self.assertIsNotNone(service.client)

    def test_mock_mode_fallback(self):
        """Test that mock mode works when no API keys are present"""
        with patch.dict(os.environ, {}, clear=True):
            service = LLMService()
            self.assertEqual(service.provider, "mock")

            response = service.process_message(
                message="Test message",
                context=ConversationContext(),
                conversation_history=[]
            )

            self.assertIsNotNone(response)
            self.assertIn("mock", response.metadata.get("mode", ""))

    def test_error_handling_for_api_failures(self):
        """Test graceful error handling when API calls fail"""
        service = LLMService()

        # Simulate API failure - patch the method that's actually called in mock mode
        with patch.object(service, '_generate_mock_response', side_effect=Exception("API Error")):
            response = service.process_message(
                message="Test message",
                context=ConversationContext(),
                conversation_history=[]
            )

            # Should return a helpful error response, not crash
            self.assertIsNotNone(response)
            self.assertIn("error", response.metadata)

    def test_conversation_history_handling(self):
        """Test that conversation history is properly used"""
        history = [
            {"role": "user", "content": "I need a demo for Adobe"},
            {"role": "assistant", "content": "Great! Tell me more about Adobe's needs"},
            {"role": "user", "content": "They need campaign analytics"}
        ]

        response = self.llm_service.process_message(
            message="Focus on ROI tracking",
            context=self.test_context,
            conversation_history=history
        )

        # Response should be contextual based on history
        self.assertIsNotNone(response.content)
        # Should understand this is about Adobe campaigns
        self.assertTrue(
            "Adobe" in str(response.extracted_context.company_name) or
            "campaign" in response.content.lower() or
            "ROI" in response.content
        )

    def test_use_case_suggestion_generation(self):
        """Test that appropriate use cases are suggested based on context"""
        context = ConversationContext(
            company_name="Kaiser Permanente",
            department="Emergency Department",
            industry="Healthcare",
            pain_points=["Long wait times", "Bed management"],
            conversation_phase="use_case_selection"
        )

        response = self.llm_service.process_message(
            message="What use cases do you recommend?",
            context=context,
            conversation_history=[]
        )

        # Should suggest healthcare-specific use cases
        self.assertIn("patient", response.content.lower())
        self.assertGreater(len(response.suggested_use_cases), 0)
        self.assertTrue(any("flow" in uc.lower() or "wait" in uc.lower()
                          for uc in response.suggested_use_cases))

    def test_demo_readiness_check(self):
        """Test that system correctly identifies when ready to generate demo"""
        # Incomplete context
        incomplete_context = ConversationContext(
            company_name="Acme Corp"
        )
        self.assertFalse(self.llm_service.is_ready_to_generate(incomplete_context))

        # Complete context
        complete_context = ConversationContext(
            company_name="Acme Corp",
            department="Sales",
            pain_points=["Slow reporting"],
            use_cases=["Sales analytics"],
            conversation_phase="confirmation"
        )
        self.assertTrue(self.llm_service.is_ready_to_generate(complete_context))


class TestLLMIntegrationWithUI(unittest.TestCase):
    """Test LLM integration with Streamlit UI"""

    @patch('streamlit.session_state')
    def test_ui_context_update(self, mock_session_state):
        """Test that UI properly updates context from LLM responses"""
        from src.ui.conversation_handler import ConversationHandler

        handler = ConversationHandler()
        mock_session_state.demo_context = {
            "company_name": None,
            "department": None
        }

        # Simulate user message
        user_message = "This is for Microsoft's Azure team"
        response = handler.process_user_input(user_message)

        # Context should be updated
        self.assertIsNotNone(response)
        # Would need to check that session_state.demo_context was updated

    def test_demo_generation_trigger(self):
        """Test that 'Generate demo' properly triggers generation"""
        from src.ui.conversation_handler import ConversationHandler

        handler = ConversationHandler()

        # Set up complete context with use cases (required for generation)
        handler.context = ConversationContext(
            company_name="Test Corp",
            department="Sales",
            pain_points=["Testing"],
            use_cases=["Sales Analytics"],  # Added required use cases
            conversation_phase="confirmation"
        )

        # Trigger generation
        result = handler.process_user_input("Generate demo")

        self.assertTrue(result.get("should_generate", False))
        self.assertIn("demo_plan", result)


def run_tests():
    """Run all tests and report results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLLMService))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMIntegrationWithUI))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)