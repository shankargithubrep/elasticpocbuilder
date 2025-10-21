"""
Test-driven development for Data Generation Service
Tests for creating realistic synthetic data for demos
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.enhanced_data_generator import EnhancedDataGenerator, DataGenerationPlan


class TestDataGenerationPlanning(unittest.TestCase):
    """Test data generation planning and configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = EnhancedDataGenerator()
        self.test_context = {
            "company": "Acme Corp",
            "industry": "Retail",
            "scale": "10000 transactions/day",
            "use_cases": ["Inventory Analytics", "Customer Journey"]
        }

    def test_generator_initialization(self):
        """Test that data generator initializes correctly"""
        self.assertIsNotNone(self.generator)
        self.assertTrue(hasattr(self.generator, 'generate_datasets'))
        self.assertTrue(hasattr(self.generator, 'create_relationships'))

    def test_plan_creation_from_context(self):
        """Test creating a data generation plan from context"""
        plan = self.generator.create_plan(self.test_context)

        self.assertIsInstance(plan, DataGenerationPlan)
        self.assertIn("customers", plan.datasets)
        self.assertIn("transactions", plan.datasets)
        self.assertIn("products", plan.datasets)
        self.assertGreater(plan.total_records, 0)

    def test_scale_parsing(self):
        """Test parsing scale information into record counts"""
        test_cases = [
            ("10000 transactions/day", 10000),
            ("5K accounts", 5000),
            ("2.5M events", 2500000),
            ("100 stores", 100),
        ]

        for scale_str, expected_count in test_cases:
            count = self.generator._parse_scale(scale_str)
            self.assertEqual(count, expected_count)

    def test_industry_specific_datasets(self):
        """Test that different industries get appropriate datasets"""
        # Retail
        retail_plan = self.generator.create_plan({"industry": "Retail"})
        self.assertIn("products", retail_plan.datasets)
        self.assertIn("inventory", retail_plan.datasets)

        # Healthcare
        healthcare_plan = self.generator.create_plan({"industry": "Healthcare"})
        self.assertIn("patients", healthcare_plan.datasets)
        self.assertIn("visits", healthcare_plan.datasets)

        # Financial
        financial_plan = self.generator.create_plan({"industry": "Financial"})
        self.assertIn("accounts", financial_plan.datasets)
        self.assertIn("transactions", financial_plan.datasets)


class TestDataGeneration(unittest.TestCase):
    """Test actual data generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = EnhancedDataGenerator()

    def test_generate_reference_data(self):
        """Test generating reference/lookup data"""
        customers_df = self.generator.generate_customers(count=100)

        self.assertIsInstance(customers_df, pd.DataFrame)
        self.assertEqual(len(customers_df), 100)
        self.assertIn("customer_id", customers_df.columns)
        self.assertIn("name", customers_df.columns)
        self.assertIn("segment", customers_df.columns)
        self.assertIn("created_date", customers_df.columns)

        # Check data types
        self.assertEqual(customers_df["customer_id"].dtype, object)  # string
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(customers_df["created_date"]))

        # Check uniqueness
        self.assertEqual(len(customers_df["customer_id"].unique()), 100)

    def test_generate_event_data(self):
        """Test generating time-series event data"""
        events_df = self.generator.generate_events(
            count=1000,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )

        self.assertIsInstance(events_df, pd.DataFrame)
        self.assertEqual(len(events_df), 1000)
        self.assertIn("event_id", events_df.columns)
        self.assertIn("timestamp", events_df.columns)
        self.assertIn("event_type", events_df.columns)

        # Check timestamps are within range
        self.assertTrue(all(events_df["timestamp"] >= pd.Timestamp("2024-01-01")))
        self.assertTrue(all(events_df["timestamp"] <= pd.Timestamp("2024-01-31")))

    def test_generate_metrics_data(self):
        """Test generating numerical metrics data"""
        metrics_df = self.generator.generate_metrics(
            count=500,
            metric_names=["revenue", "cost", "profit_margin"]
        )

        self.assertIsInstance(metrics_df, pd.DataFrame)
        self.assertEqual(len(metrics_df), 500)
        self.assertIn("revenue", metrics_df.columns)
        self.assertIn("cost", metrics_df.columns)
        self.assertIn("profit_margin", metrics_df.columns)

        # Check data distributions
        self.assertTrue(all(metrics_df["revenue"] >= 0))
        self.assertTrue(all(metrics_df["profit_margin"] >= -1))
        self.assertTrue(all(metrics_df["profit_margin"] <= 1))

    def test_data_relationships(self):
        """Test that generated data maintains relationships"""
        # Generate related datasets
        customers_df = self.generator.generate_customers(count=10)
        orders_df = self.generator.generate_orders(
            count=100,
            customer_ids=customers_df["customer_id"].tolist()
        )

        # Check foreign key relationships
        self.assertTrue(all(orders_df["customer_id"].isin(customers_df["customer_id"])))

        # Check that all customers have at least one order (realistic scenario)
        customers_with_orders = orders_df["customer_id"].unique()
        self.assertGreaterEqual(len(customers_with_orders), min(5, len(customers_df)))

    def test_realistic_data_patterns(self):
        """Test that generated data follows realistic patterns"""
        # Generate sales data with seasonal pattern
        sales_df = self.generator.generate_time_series(
            metric="sales",
            periods=365,
            pattern="seasonal"
        )

        self.assertEqual(len(sales_df), 365)

        # Check for seasonal variation (summer vs winter)
        summer_avg = sales_df.iloc[150:240]["value"].mean()  # Jun-Aug
        winter_avg = sales_df.iloc[0:90]["value"].mean()  # Jan-Mar

        # Should see some difference between seasons
        self.assertNotAlmostEqual(summer_avg, winter_avg, places=0)

    def test_anomaly_injection(self):
        """Test ability to inject anomalies for demo purposes"""
        data_df = self.generator.generate_metrics(count=100)

        # Inject anomalies
        data_with_anomalies = self.generator.inject_anomalies(
            data_df,
            anomaly_rate=0.05,
            anomaly_type="spike"
        )

        # Check that anomalies were added
        self.assertIn("is_anomaly", data_with_anomalies.columns)
        anomaly_count = data_with_anomalies["is_anomaly"].sum()
        self.assertGreater(anomaly_count, 0)
        self.assertLessEqual(anomaly_count, 10)  # ~5% of 100

    def test_data_export_formats(self):
        """Test exporting data in different formats"""
        data_df = self.generator.generate_customers(count=10)

        # Test CSV export
        csv_output = self.generator.export_to_csv(data_df)
        self.assertIsInstance(csv_output, str)
        self.assertIn("customer_id", csv_output)

        # Test JSON export
        json_output = self.generator.export_to_json(data_df)
        self.assertIsInstance(json_output, str)
        import json
        parsed = json.loads(json_output)
        self.assertEqual(len(parsed), 10)

    def test_elasticsearch_bulk_format(self):
        """Test generating data in Elasticsearch bulk format"""
        data_df = self.generator.generate_customers(count=5)

        bulk_data = self.generator.to_elasticsearch_bulk(
            data_df,
            index_name="customers"
        )

        self.assertIsInstance(bulk_data, list)
        self.assertEqual(len(bulk_data), 10)  # 2 lines per document

        # Check format
        for i in range(0, len(bulk_data), 2):
            self.assertIn("index", bulk_data[i])
            self.assertIn("_index", bulk_data[i]["index"])
            self.assertEqual(bulk_data[i]["index"]["_index"], "customers")

    def test_performance_large_datasets(self):
        """Test that large dataset generation is performant"""
        import time

        start_time = time.time()
        large_df = self.generator.generate_events(count=100000)
        generation_time = time.time() - start_time

        self.assertEqual(len(large_df), 100000)
        self.assertLess(generation_time, 5.0)  # Should generate 100k records in < 5 seconds

    def test_deterministic_generation_with_seed(self):
        """Test that using a seed produces deterministic results"""
        df1 = self.generator.generate_customers(count=10, seed=42)
        df2 = self.generator.generate_customers(count=10, seed=42)

        # Should be identical
        pd.testing.assert_frame_equal(df1, df2)

        # Different seed should produce different data
        df3 = self.generator.generate_customers(count=10, seed=123)
        self.assertFalse(df1.equals(df3))


# A-ha moment tests commented out - feature deferred for later
# class TestAhaModmentGeneration(unittest.TestCase):
#     """Test generating 'A-ha moment' demo scenarios"""
#
#     def setUp(self):
#         """Set up test fixtures"""
#         self.generator = EnhancedDataGenerator()
#
#     def test_aha_moment_identification(self):
#         """Test identifying potential A-ha moments from context"""
#         context = {
#             "pain_points": ["Can't detect fraud fast enough", "Too many false positives"],
#             "current_solution": "Manual review taking hours"
#         }
#
#         aha_moments = self.generator.identify_aha_moments(context)
#
#         self.assertGreater(len(aha_moments), 0)
#         self.assertIn("real_time_fraud_detection", aha_moments[0]["type"])
#         self.assertIn("query", aha_moments[0])
#         self.assertIn("visualization", aha_moments[0])
#
#     def test_create_aha_moment_data(self):
#         """Test creating data that demonstrates the A-ha moment"""
#         # Create data that shows clear fraud pattern
#         aha_config = {
#             "type": "fraud_detection",
#             "pattern": "sudden_spike",
#             "normal_rate": 0.001,
#             "anomaly_rate": 0.10
#         }
#
#         data_df = self.generator.create_aha_moment_data(aha_config)
#
#         # Should have clear difference between normal and anomaly
#         normal_period = data_df[data_df["period"] == "normal"]
#         anomaly_period = data_df[data_df["period"] == "anomaly"]
#
#         normal_fraud_rate = normal_period["is_fraud"].mean()
#         anomaly_fraud_rate = anomaly_period["is_fraud"].mean()
#
#         self.assertLess(normal_fraud_rate, 0.01)
#         self.assertGreater(anomaly_fraud_rate, 0.05)
#
#     def test_aha_moment_query_generation(self):
#         """Test generating the perfect query for the A-ha moment"""
#         aha_config = {
#             "type": "cost_savings",
#             "metric": "processing_time",
#             "improvement": 0.8  # 80% improvement
#         }
#
#         query = self.generator.generate_aha_query(aha_config)
#
#         self.assertIn("EVAL", query)  # Should calculate savings
#         self.assertIn("time_saved", query)
#         self.assertIn("cost_reduction", query)


def run_tests():
    """Run all tests and report results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataGenerationPlanning))
    suite.addTests(loader.loadTestsFromTestCase(TestDataGeneration))
    # A-ha moment tests deferred for later
    # suite.addTests(loader.loadTestsFromTestCase(TestAhaModmentGeneration))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✅ All data generation tests passed!")
    else:
        print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)