#!/usr/bin/env python3
"""
Query Refinement Loop Test
Demonstrates the iterative query fixing capability
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class QueryRefinementTest:
    """Test the query refinement loop with known issues"""

    def __init__(self):
        self.test_cases = self.create_test_cases()
        self.fixes_applied = []

    def create_test_cases(self) -> List[Dict]:
        """Create test cases with known issues"""
        return [
            {
                "name": "Integer Division Issue",
                "bad_query": """FROM metrics
| EVAL efficiency = success_count / total_count * 100
| STATS avg_efficiency = AVG(efficiency)
| SORT avg_efficiency DESC""",
                "expected_fix": """FROM metrics
| EVAL efficiency = TO_DOUBLE(success_count) / total_count * 100
| STATS avg_efficiency = AVG(efficiency)
| SORT avg_efficiency DESC""",
                "issue": "integer_division"
            },
            {
                "name": "JOIN After Aggregation",
                "bad_query": """FROM orders
| STATS total_revenue = SUM(revenue) BY product_id
| LOOKUP JOIN products ON product_id
| SORT total_revenue DESC""",
                "expected_fix": """FROM orders
| LOOKUP JOIN products ON product_id
| STATS total_revenue = SUM(revenue) BY product_id
| SORT total_revenue DESC""",
                "issue": "join_after_aggregation"
            },
            {
                "name": "Missing LIMIT on Large Result Set",
                "bad_query": """FROM events
| WHERE status == "error"
| SORT timestamp DESC""",
                "expected_fix": """FROM events
| WHERE status == "error"
| SORT timestamp DESC
| LIMIT 1000""",
                "issue": "missing_limit"
            },
            {
                "name": "Multiple Division Operations",
                "bad_query": """FROM metrics
| EVAL ctr = clicks / impressions * 100
| EVAL cvr = conversions / clicks * 100
| STATS avg_ctr = AVG(ctr), avg_cvr = AVG(cvr)""",
                "expected_fix": """FROM metrics
| EVAL ctr = TO_DOUBLE(clicks) / impressions * 100
| EVAL cvr = TO_DOUBLE(conversions) / clicks * 100
| STATS avg_ctr = AVG(ctr), avg_cvr = AVG(cvr)""",
                "issue": "multiple_divisions"
            },
            {
                "name": "Complex Query with Multiple Issues",
                "bad_query": """FROM campaign_performance
| WHERE clicks > 0
| EVAL roi = (revenue - cost) / cost * 100
| STATS total_roi = SUM(roi) BY campaign_id
| LOOKUP JOIN campaigns ON campaign_id
| WHERE total_roi > 0""",
                "expected_fix": """FROM campaign_performance
| WHERE clicks > 0
| LOOKUP JOIN campaigns ON campaign_id
| EVAL roi = TO_DOUBLE(revenue - cost) / cost * 100
| STATS total_roi = SUM(roi) BY campaign_id
| WHERE total_roi > 0
| LIMIT 1000""",
                "issue": "complex_multiple"
            }
        ]

    def detect_issues(self, query: str) -> List[str]:
        """Detect issues in a query"""
        issues = []

        # Integer division check
        if "/" in query and "TO_DOUBLE" not in query.upper():
            issues.append("integer_division")

        # JOIN after STATS check
        lines = query.upper().split("\n")
        stats_line = -1
        for i, line in enumerate(lines):
            if "STATS" in line:
                stats_line = i
            if "JOIN" in line and stats_line >= 0 and i > stats_line:
                issues.append("join_after_aggregation")

        # Missing LIMIT check
        if "LIMIT" not in query.upper() and "STATS" not in query.upper():
            issues.append("missing_limit")

        return issues

    def apply_fixes(self, query: str, issues: List[str]) -> str:
        """Apply fixes to a query based on detected issues"""
        fixed = query

        if "integer_division" in issues:
            # Fix division operations
            import re
            # Find patterns like "field1 / field2" and wrap field1 in TO_DOUBLE
            pattern = r'(\w+)\s*/\s*(\w+)'

            def replace_division(match):
                return f"TO_DOUBLE({match.group(1)}) / {match.group(2)}"

            fixed = re.sub(pattern, replace_division, fixed)
            self.fixes_applied.append("Applied TO_DOUBLE to division operations")

        if "join_after_aggregation" in issues:
            # Reorder query to put JOIN before STATS
            lines = fixed.split("\n")
            join_lines = []
            stats_lines = []
            other_lines = []
            after_stats = False

            for line in lines:
                if "STATS" in line.upper():
                    after_stats = True
                    stats_lines.append(line)
                elif "JOIN" in line.upper():
                    join_lines.append(line)
                elif after_stats:
                    stats_lines.append(line)
                else:
                    other_lines.append(line)

            # Reconstruct: FROM -> JOIN -> other -> STATS
            if join_lines and stats_lines:
                from_line = other_lines[0] if other_lines else ""
                rest_lines = other_lines[1:] if len(other_lines) > 1 else []

                fixed_lines = [from_line] + join_lines + rest_lines + stats_lines
                fixed = "\n".join(fixed_lines)
                self.fixes_applied.append("Reordered JOIN before STATS")

        if "missing_limit" in issues:
            # Add LIMIT at the end
            if not fixed.strip().endswith("| LIMIT 1000"):
                fixed = fixed.strip() + "\n| LIMIT 1000"
                self.fixes_applied.append("Added LIMIT 1000")

        return fixed

    def run_test(self):
        """Run the query refinement test"""
        logger.info("=" * 60)
        logger.info("QUERY REFINEMENT LOOP TEST")
        logger.info("=" * 60)

        success_count = 0
        total_count = len(self.test_cases)

        for i, test_case in enumerate(self.test_cases, 1):
            logger.info(f"\nTest {i}: {test_case['name']}")
            logger.info("-" * 40)

            # Show original query
            logger.info("Original Query:")
            for line in test_case["bad_query"].split("\n"):
                logger.info(f"  {line}")

            # Detect issues
            detected_issues = self.detect_issues(test_case["bad_query"])
            logger.info(f"\nDetected Issues: {detected_issues}")

            # Apply fixes
            self.fixes_applied = []
            fixed_query = self.apply_fixes(test_case["bad_query"], detected_issues)

            logger.info("\nFixed Query:")
            for line in fixed_query.split("\n"):
                logger.info(f"  {line}")

            logger.info(f"\nFixes Applied:")
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")

            # Validate fix
            remaining_issues = self.detect_issues(fixed_query)

            if not remaining_issues:
                logger.info("✅ All issues resolved!")
                success_count += 1
            else:
                logger.info(f"❌ Remaining issues: {remaining_issues}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

        if success_count == total_count:
            logger.info("🎉 All query refinements successful!")
        else:
            logger.info(f"⚠️ {total_count - success_count} queries need manual review")

        return success_count == total_count


def demonstrate_iterative_refinement():
    """Demonstrate the iterative refinement process"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMONSTRATING ITERATIVE REFINEMENT")
    logger.info("=" * 60)

    # Simulate a complex query that needs multiple rounds of fixes
    query = """FROM campaign_performance
| WHERE revenue > 0
| EVAL roi = (revenue - spend) / spend * 100
| EVAL efficiency = conversions / clicks
| STATS
    avg_roi = AVG(roi),
    avg_efficiency = AVG(efficiency),
    total_revenue = SUM(revenue)
  BY campaign_id
| LOOKUP JOIN campaigns ON campaign_id
| WHERE avg_roi > 50
| SORT total_revenue DESC"""

    logger.info("\nInitial Query (with multiple issues):")
    logger.info(query)

    # Iteration 1
    logger.info("\n--- Iteration 1: Detect Issues ---")
    test = QueryRefinementTest()
    issues = test.detect_issues(query)
    logger.info(f"Found issues: {issues}")

    if issues:
        query = test.apply_fixes(query, issues)
        logger.info("\nAfter Iteration 1:")
        logger.info(query)

    # Iteration 2
    logger.info("\n--- Iteration 2: Verify Fixes ---")
    issues = test.detect_issues(query)

    if issues:
        logger.info(f"Remaining issues: {issues}")
        query = test.apply_fixes(query, issues)
        logger.info("\nAfter Iteration 2:")
        logger.info(query)
    else:
        logger.info("✅ No remaining issues!")

    # Final validation
    logger.info("\n--- Final Validation ---")
    final_issues = test.detect_issues(query)

    if not final_issues:
        logger.info("✅ Query is now valid and optimized!")
    else:
        logger.info(f"⚠️ Manual review needed for: {final_issues}")

    logger.info("\nFinal Optimized Query:")
    logger.info(query)


def main():
    """Run all tests"""
    # Run structured test cases
    test = QueryRefinementTest()
    success = test.run_test()

    # Demonstrate iterative refinement
    demonstrate_iterative_refinement()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())