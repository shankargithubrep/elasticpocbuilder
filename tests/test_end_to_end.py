"""
End-to-End Integration Test
Verifies the complete demo generation workflow
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.llm_service import LLMService, ConversationContext
from src.services.enhanced_data_generator import EnhancedDataGenerator
from src.services.demo_orchestrator import DemoOrchestrator
from src.ui.conversation_handler import ConversationHandler


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete demo generation workflow"""

    def test_complete_demo_generation(self):
        """Test generating a complete demo from context"""
        print("\n" + "="*70)
        print("TESTING END-TO-END DEMO GENERATION")
        print("="*70)

        # Step 1: Create context (simulating user input)
        print("\n1️⃣ Creating customer context...")
        context = ConversationContext(
            company_name="Acme Corp",
            department="Sales",
            industry="Technology",
            pain_points=["Slow reporting", "Manual processes", "Lack of real-time insights"],
            use_cases=["Sales Analytics", "Revenue Forecasting"],
            scale="50000 transactions/day",
            metrics=["Revenue", "Conversion Rate", "Customer Lifetime Value"],
            conversation_phase="ready"
        )
        print(f"   ✅ Context: {context.company_name} - {context.department}")

        # Step 2: Test LLM service
        print("\n2️⃣ Testing LLM service...")
        llm_service = LLMService()
        demo_plan = llm_service.generate_demo_plan(context)
        self.assertIn("datasets", demo_plan)
        self.assertIn("queries", demo_plan)
        print(f"   ✅ Generated plan with {len(demo_plan['datasets'])} datasets")

        # Step 3: Test data generation
        print("\n3️⃣ Testing data generation...")
        data_generator = EnhancedDataGenerator()
        data_plan = data_generator.create_plan({
            "industry": context.industry,
            "scale": context.scale
        })
        datasets = data_generator.generate_datasets(data_plan)
        self.assertGreater(len(datasets), 0)

        total_records = sum(len(df) for df in datasets.values())
        print(f"   ✅ Generated {len(datasets)} datasets with {total_records:,} records")

        # Step 4: Test orchestrator
        print("\n4️⃣ Testing demo orchestrator...")
        orchestrator = DemoOrchestrator()

        # Track progress
        progress_updates = []

        def progress_callback(progress: float, message: str):
            progress_updates.append((progress, message))
            print(f"   {int(progress*100):3d}% - {message}")

        demo_package = orchestrator.generate_demo(context, progress_callback)

        self.assertIsNotNone(demo_package)
        self.assertEqual(demo_package.customer_name, "Acme Corp")
        self.assertGreater(len(demo_package.datasets), 0)
        self.assertGreater(len(demo_package.queries), 0)
        self.assertIsNotNone(demo_package.agent_config)
        self.assertIsNotNone(demo_package.demo_guide)

        print(f"\n   ✅ Demo package created: {demo_package.demo_id}")

        # Step 5: Test conversation handler
        print("\n5️⃣ Testing conversation handler...")
        handler = ConversationHandler()
        handler.context = context

        result = handler.process_user_input("Generate demo")
        self.assertTrue(result["should_generate"])
        self.assertIn("demo_plan", result)
        print("   ✅ Conversation handler triggers generation correctly")

        # Step 6: Validate outputs
        print("\n6️⃣ Validating outputs...")

        # Check demo guide
        self.assertIn("Executive Summary", demo_package.demo_guide)
        self.assertIn("Pain Points", demo_package.demo_guide)
        self.assertIn("Demo Flow", demo_package.demo_guide)
        print("   ✅ Demo guide contains all sections")

        # Check queries
        for query in demo_package.queries[:3]:
            self.assertIn("name", query)
            self.assertIn("esql", query)
            print(f"   ✅ Query: {query['name']}")

        # Check datasets
        for name, df in list(demo_package.datasets.items())[:3]:
            self.assertFalse(df.empty)
            print(f"   ✅ Dataset '{name}': {len(df)} records")

        # Summary
        print("\n" + "="*70)
        print("✅ END-TO-END TEST SUCCESSFUL!")
        print(f"   Demo ID: {demo_package.demo_id}")
        print(f"   Datasets: {len(demo_package.datasets)}")
        print(f"   Total Records: {sum(len(df) for df in demo_package.datasets.values()):,}")
        print(f"   Queries: {len(demo_package.queries)}")
        print(f"   Progress Updates: {len(progress_updates)}")
        print("="*70)

    def test_error_handling(self):
        """Test error handling in the workflow"""
        print("\n🧪 Testing error handling...")

        orchestrator = DemoOrchestrator()

        # Test with incomplete context
        incomplete_context = ConversationContext(
            company_name="Test Corp"
            # Missing required fields
        )

        with self.assertRaises(ValueError):
            orchestrator.generate_demo(incomplete_context)

        print("   ✅ Properly handles incomplete context")

    def test_performance(self):
        """Test performance of demo generation"""
        import time

        print("\n⚡ Testing performance...")

        context = ConversationContext(
            company_name="Performance Test Corp",
            department="Engineering",
            industry="Technology",
            pain_points=["Performance issues"],
            use_cases=["Performance Monitoring"],
            scale="100000 records"
        )

        orchestrator = DemoOrchestrator()

        start_time = time.time()
        demo_package = orchestrator.generate_demo(context)
        generation_time = time.time() - start_time

        print(f"   ✅ Demo generated in {generation_time:.2f} seconds")
        self.assertLess(generation_time, 10.0)  # Should complete in < 10 seconds


def run_tests():
    """Run all tests and report results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("🎉 ALL END-TO-END TESTS PASSED!")
    else:
        print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)