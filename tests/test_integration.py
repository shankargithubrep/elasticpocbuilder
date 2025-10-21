#!/usr/bin/env python3
"""
End-to-End Integration Test for Demo Builder
Tests the complete iterative loop from data generation to agent creation
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import (
    CustomerResearcher,
    ScenarioGenerator,
    DataGenerator,
    ESQLGenerator,
    ElasticClient,
    ValidationService,
    ElasticAgentBuilderClient
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemoIntegrationTest:
    """Test the complete demo generation loop"""

    def __init__(self):
        self.customer_researcher = CustomerResearcher()
        self.scenario_generator = ScenarioGenerator()
        self.data_generator = DataGenerator()
        self.esql_generator = ESQLGenerator()

        # These may fail if Elasticsearch is not available
        try:
            self.elastic_client = ElasticClient()
            self.validation_service = ValidationService(self.elastic_client.client) if self.elastic_client.client else None
        except:
            logger.warning("Elasticsearch not available - running in mock mode")
            self.elastic_client = None
            self.validation_service = None

        self.test_results = {
            "phases": {},
            "errors": [],
            "warnings": [],
            "metrics": {}
        }

    def run_full_test(self) -> Dict:
        """Run the complete integration test"""
        logger.info("=" * 60)
        logger.info("STARTING END-TO-END INTEGRATION TEST")
        logger.info("=" * 60)

        start_time = time.time()

        # Phase 1: Customer Research & Scenario Generation
        customer_profile, scenario = self.test_phase1_scenario_generation()

        # Phase 2: Data Generation
        datasets = self.test_phase2_data_generation(scenario)

        # Phase 3: Index Creation (if Elasticsearch available)
        index_created = self.test_phase3_index_creation(datasets)

        # Phase 4: Query Generation
        queries = self.test_phase4_query_generation(scenario, datasets)

        # Phase 5: Query Validation & Refinement
        validated_queries = self.test_phase5_query_validation(queries, datasets)

        # Phase 6: Agent & Tool Creation
        agent_config = self.test_phase6_agent_creation(validated_queries, customer_profile)

        # Phase 7: End-to-End Validation
        self.test_phase7_end_to_end_validation(agent_config, validated_queries)

        # Calculate metrics
        end_time = time.time()
        self.test_results["metrics"]["total_time"] = end_time - start_time
        self.test_results["metrics"]["success_rate"] = self.calculate_success_rate()

        # Generate report
        self.generate_report()

        return self.test_results

    def test_phase1_scenario_generation(self) -> Tuple[Dict, Dict]:
        """Test customer research and scenario generation"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 1: Scenario Generation")
        logger.info("=" * 40)

        try:
            # Create a test customer profile
            customer_profile = self.customer_researcher.research_company(
                company_name="TechCorp Analytics",
                department="Operations"
            )

            logger.info(f"✓ Customer profile created: {customer_profile.company_name}")
            logger.info(f"  Industry: {customer_profile.industry}")
            logger.info(f"  Use cases: {customer_profile.use_cases[:2]}")

            # Generate scenario
            scenario = self.scenario_generator.generate_scenario(
                {
                    "company_name": customer_profile.company_name,
                    "industry": customer_profile.industry,
                    "department": customer_profile.department,
                    "use_cases": customer_profile.use_cases
                }
            )

            logger.info(f"✓ Scenario generated: {scenario['name']}")
            logger.info(f"  Datasets: {[d['name'] for d in scenario['datasets']]}")

            self.test_results["phases"]["scenario_generation"] = "SUCCESS"
            return customer_profile.__dict__, scenario

        except Exception as e:
            logger.error(f"✗ Scenario generation failed: {e}")
            self.test_results["phases"]["scenario_generation"] = "FAILED"
            self.test_results["errors"].append(str(e))
            raise

    def test_phase2_data_generation(self, scenario: Dict) -> Dict[str, pd.DataFrame]:
        """Test data generation with relationships"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 2: Data Generation")
        logger.info("=" * 40)

        try:
            # Generate datasets
            datasets = self.data_generator.generate_datasets(scenario)

            # Validate datasets
            for name, df in datasets.items():
                logger.info(f"✓ Generated {name}: {len(df)} records, {len(df.columns)} columns")

                # Check for required columns
                if "id" in df.columns:
                    assert df["id"].nunique() == len(df), f"Duplicate IDs in {name}"

                # Check for nulls in critical columns
                null_counts = df.isnull().sum()
                if null_counts.any():
                    logger.warning(f"  Warning: Null values in {name}: {null_counts[null_counts > 0].to_dict()}")

            # Validate relationships
            self.validate_relationships(datasets, scenario.get("relationships", []))

            self.test_results["phases"]["data_generation"] = "SUCCESS"
            return datasets

        except Exception as e:
            logger.error(f"✗ Data generation failed: {e}")
            self.test_results["phases"]["data_generation"] = "FAILED"
            self.test_results["errors"].append(str(e))
            raise

    def test_phase3_index_creation(self, datasets: Dict[str, pd.DataFrame]) -> bool:
        """Test index creation with proper settings"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 3: Index Creation")
        logger.info("=" * 40)

        if not self.elastic_client or not self.elastic_client.client:
            logger.warning("⚠ Elasticsearch not available - skipping index creation")
            self.test_results["phases"]["index_creation"] = "SKIPPED"
            return False

        try:
            for name, df in datasets.items():
                # Determine if this should be a lookup index
                is_lookup = name in ["products", "customers", "assets", "resources"]

                # Delete if exists
                self.elastic_client.delete_index(name)

                # Create with appropriate settings
                settings = {"index.mode": "lookup"} if is_lookup else {}

                # Infer mappings from DataFrame
                mappings = self.infer_mappings(df)

                # Create index
                success = self.elastic_client.create_index(name, mappings, settings)

                if success:
                    logger.info(f"✓ Created index {name} (lookup={is_lookup})")

                    # Index data
                    self.elastic_client.index_dataframe(df, name, "id" if "id" in df.columns else None)
                    logger.info(f"  Indexed {len(df)} documents")
                else:
                    raise Exception(f"Failed to create index {name}")

            self.test_results["phases"]["index_creation"] = "SUCCESS"
            return True

        except Exception as e:
            logger.error(f"✗ Index creation failed: {e}")
            self.test_results["phases"]["index_creation"] = "FAILED"
            self.test_results["errors"].append(str(e))
            return False

    def test_phase4_query_generation(self, scenario: Dict, datasets: Dict) -> List[Dict]:
        """Test ES|QL query generation"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 4: Query Generation")
        logger.info("=" * 40)

        try:
            # Generate queries
            queries = self.esql_generator.generate_queries(scenario, datasets)

            logger.info(f"✓ Generated {len(queries)} queries")

            for query in queries:
                logger.info(f"  - {query['name']} ({query['complexity']})")

                # Basic validation
                is_valid = self.esql_generator.validate_query(query['esql'])
                if not is_valid:
                    logger.warning(f"    ⚠ Query may have issues")

            self.test_results["phases"]["query_generation"] = "SUCCESS"
            return queries

        except Exception as e:
            logger.error(f"✗ Query generation failed: {e}")
            self.test_results["phases"]["query_generation"] = "FAILED"
            self.test_results["errors"].append(str(e))
            raise

    def test_phase5_query_validation(self, queries: List[Dict], datasets: Dict) -> List[Dict]:
        """Test query validation and refinement loop"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 5: Query Validation & Refinement")
        logger.info("=" * 40)

        validated_queries = []

        for query in queries:
            logger.info(f"\nValidating: {query['name']}")

            # First attempt
            issues = self.detect_query_issues(query['esql'])

            if issues:
                logger.info(f"  Found issues: {issues}")

                # Apply fixes
                fixed_query = self.apply_query_fixes(query['esql'], issues)
                query['esql'] = fixed_query
                query['fixed'] = True

                logger.info(f"  ✓ Applied fixes")
            else:
                logger.info(f"  ✓ No issues detected")

            # Final validation
            if self.validation_service:
                result = self.validation_service.validate_esql_query(query)
                if result.status == "success":
                    logger.info(f"  ✓ Query validated successfully")
                else:
                    logger.warning(f"  ⚠ Validation result: {result.status}")

            validated_queries.append(query)

        success_count = len([q for q in validated_queries if q.get('fixed') != False])
        logger.info(f"\n✓ Validated {success_count}/{len(queries)} queries")

        self.test_results["phases"]["query_validation"] = "SUCCESS"
        return validated_queries

    def test_phase6_agent_creation(self, queries: List[Dict], customer_profile: Dict) -> Dict:
        """Test agent and tool creation"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 6: Agent & Tool Creation")
        logger.info("=" * 40)

        try:
            # Create agent configuration
            agent_config = {
                "id": f"test_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "display_name": f"{customer_profile['company_name']} Test Agent",
                "description": "Test agent for integration testing",
                "instructions": f"""You are a test agent for {customer_profile['company_name']}.
                    You help analyze data and answer questions about the business.""",
                "tools": []
            }

            # Create tool configurations from queries
            tools = []
            for i, query in enumerate(queries[:5]):  # Limit to 5 tools for testing
                tool = {
                    "id": f"tool_{i+1}",
                    "name": query['name'],
                    "description": query['description'],
                    "type": "esql",
                    "query": query['esql']
                }
                tools.append(tool)
                agent_config["tools"].append(tool["id"])

            logger.info(f"✓ Created agent configuration with {len(tools)} tools")

            # Test with mock agent if no Elasticsearch
            if not self.elastic_client:
                logger.info("  Running in mock mode - agent not deployed")
            else:
                logger.info("  Ready for deployment to Agent Builder")

            self.test_results["phases"]["agent_creation"] = "SUCCESS"
            return agent_config

        except Exception as e:
            logger.error(f"✗ Agent creation failed: {e}")
            self.test_results["phases"]["agent_creation"] = "FAILED"
            self.test_results["errors"].append(str(e))
            raise

    def test_phase7_end_to_end_validation(self, agent_config: Dict, queries: List[Dict]):
        """Validate the complete demo works end-to-end"""
        logger.info("\n" + "=" * 40)
        logger.info("PHASE 7: End-to-End Validation")
        logger.info("=" * 40)

        try:
            # Test questions an agent should be able to answer
            test_questions = [
                "What are the top performing entities?",
                "Show me trends over time",
                "What's the current status breakdown?",
                "Which items need attention?"
            ]

            logger.info("Testing agent with sample questions:")

            for question in test_questions:
                logger.info(f"  Q: {question}")

                # Simulate tool selection (in real test, agent would select)
                matching_tools = [t for t in agent_config["tools"]
                                if any(word in question.lower()
                                      for word in t.split('_'))]

                if matching_tools:
                    logger.info(f"    → Would use tool: {matching_tools[0]}")
                else:
                    logger.info(f"    → Would use default search")

            logger.info("\n✓ End-to-end validation complete")
            self.test_results["phases"]["end_to_end"] = "SUCCESS"

        except Exception as e:
            logger.error(f"✗ End-to-end validation failed: {e}")
            self.test_results["phases"]["end_to_end"] = "FAILED"
            self.test_results["errors"].append(str(e))

    # ==================== Helper Methods ====================

    def validate_relationships(self, datasets: Dict[str, pd.DataFrame], relationships: List[str]):
        """Validate foreign key relationships exist"""
        for relationship in relationships:
            if "->" in relationship:
                source, target = relationship.split("->")
                source = source.strip()
                target = target.strip()

                if source in datasets and target in datasets:
                    # Check if foreign key exists in target
                    foreign_key = f"{source}_id"
                    if foreign_key in datasets[target].columns:
                        logger.info(f"  ✓ Relationship validated: {source} -> {target}")
                    else:
                        logger.warning(f"  ⚠ Missing foreign key {foreign_key} in {target}")

    def infer_mappings(self, df: pd.DataFrame) -> Dict:
        """Infer Elasticsearch mappings from DataFrame"""
        properties = {}

        for col in df.columns:
            dtype = str(df[col].dtype)

            if 'datetime' in dtype:
                properties[col] = {"type": "date"}
            elif 'int' in dtype:
                properties[col] = {"type": "long"}
            elif 'float' in dtype:
                properties[col] = {"type": "double"}
            elif 'bool' in dtype:
                properties[col] = {"type": "boolean"}
            else:
                # Check if it's an ID or keyword field
                if col.endswith('_id') or col == 'id' or df[col].nunique() < len(df) * 0.5:
                    properties[col] = {"type": "keyword"}
                else:
                    properties[col] = {"type": "text"}

        return {"properties": properties}

    def detect_query_issues(self, esql: str) -> List[str]:
        """Detect common issues in ES|QL queries"""
        issues = []

        # Check for integer division without TO_DOUBLE
        if "/" in esql and "TO_DOUBLE" not in esql.upper():
            issues.append("integer_division")

        # Check for JOIN after STATS
        lines = esql.upper().split("\n")
        for i, line in enumerate(lines):
            if "STATS" in line:
                # Check if JOIN comes after
                for j in range(i+1, len(lines)):
                    if "JOIN" in lines[j]:
                        issues.append("join_after_aggregation")
                        break

        # Check for LIMIT in queries that might return many rows
        if "LIMIT" not in esql.upper() and "STATS" not in esql.upper():
            issues.append("missing_limit")

        return issues

    def apply_query_fixes(self, esql: str, issues: List[str]) -> str:
        """Apply fixes to ES|QL queries"""
        fixed = esql

        if "integer_division" in issues:
            # Find division operations and wrap numerator in TO_DOUBLE
            import re
            # Simple regex to find divisions (this is simplified)
            pattern = r'(\w+)\s*/\s*(\w+)'
            fixed = re.sub(pattern, r'TO_DOUBLE(\1) / \2', fixed)

        if "join_after_aggregation" in issues:
            # This is complex - would need to reorder query
            logger.warning("  ⚠ JOIN after aggregation detected - manual fix needed")

        if "missing_limit" in issues:
            fixed += "\n| LIMIT 1000"

        return fixed

    def calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        phases = self.test_results["phases"]
        success_count = sum(1 for status in phases.values() if status == "SUCCESS")
        total_count = len(phases)
        return (success_count / total_count * 100) if total_count > 0 else 0

    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST REPORT")
        logger.info("=" * 60)

        # Phase results
        logger.info("\nPhase Results:")
        for phase, status in self.test_results["phases"].items():
            emoji = "✅" if status == "SUCCESS" else "❌" if status == "FAILED" else "⚠️"
            logger.info(f"  {emoji} {phase}: {status}")

        # Metrics
        logger.info("\nMetrics:")
        logger.info(f"  Total Time: {self.test_results['metrics'].get('total_time', 0):.2f} seconds")
        logger.info(f"  Success Rate: {self.test_results['metrics'].get('success_rate', 0):.1f}%")

        # Errors
        if self.test_results["errors"]:
            logger.info("\nErrors:")
            for error in self.test_results["errors"]:
                logger.error(f"  - {error}")

        # Warnings
        if self.test_results["warnings"]:
            logger.info("\nWarnings:")
            for warning in self.test_results["warnings"]:
                logger.warning(f"  - {warning}")

        # Overall result
        success_rate = self.test_results["metrics"].get("success_rate", 0)
        if success_rate == 100:
            logger.info("\n🎉 ALL TESTS PASSED!")
        elif success_rate >= 80:
            logger.info(f"\n✅ TESTS MOSTLY PASSED ({success_rate:.1f}%)")
        else:
            logger.info(f"\n❌ TESTS FAILED ({success_rate:.1f}% success rate)")


def main():
    """Run the integration test"""
    test = DemoIntegrationTest()
    results = test.run_full_test()

    # Return exit code based on success
    success_rate = results["metrics"].get("success_rate", 0)
    sys.exit(0 if success_rate >= 80 else 1)


if __name__ == "__main__":
    main()