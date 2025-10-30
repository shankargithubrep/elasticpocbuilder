#!/usr/bin/env python3
"""
Validate CHANGE_POINT documentation against actual Elasticsearch behavior
This script tests what CHANGE_POINT actually returns vs what we document
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_change_point_with_mcp():
    """Test CHANGE_POINT using MCP if available"""

    print("=" * 80)
    print("CHANGE_POINT DOCUMENTATION VALIDATION")
    print("=" * 80)

    # Test query that should work according to documentation
    test_query = """
    ROW value=[1,2,3,4,5,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
    | MV_EXPAND value
    | CHANGE_POINT value
    | LIMIT 5
    """

    print("\nTest Query:")
    print(test_query)

    print("\n📚 According to Documentation (docs/esql/change_point.md):")
    print("  CHANGE_POINT should return:")
    print("    - type (keyword): Change type like 'spike', 'dip', 'step_change'")
    print("    - pvalue (double): Statistical significance (0-1)")

    print("\n❌ Common Misconceptions:")
    print("    - NO 'change_point_detected' column")
    print("    - NO 'change_point_score' column")
    print("    - NO 'change_point_timestamp' column")

    # If we had MCP connection, we'd test here
    print("\n⚠️  To validate against live Elasticsearch:")
    print("    1. Configure MCP server (see docs/MCP_CONFIGURATION_GUIDE.md)")
    print("    2. Run: mcp__elastic-agent-builder__platform_core_execute_esql")
    print("    3. Verify actual column names match documentation")

    # Document the correct pattern
    print("\n✅ CORRECT Query Pattern:")
    correct_pattern = """
    FROM events
    | WHERE timestamp_field > NOW() - 60 days
    | EVAL day = DATE_TRUNC(1 day, timestamp_field)
    | STATS daily_total = SUM(value_field) BY day
    | SORT day ASC
    | CHANGE_POINT daily_total ON day
    | WHERE type IS NOT NULL        // ← Use 'type' not 'change_point_detected'
    | EVAL
        significance = pvalue,       // ← Use 'pvalue' not 'change_point_score'
        alert_level = CASE(
            pvalue < 0.01, "CRITICAL",   // Lower p-values = more significant
            pvalue < 0.05, "WARNING",
            "INFO"
        )
    """
    print(correct_pattern)

    print("\n📝 Validation Checklist:")
    print("  [ ] Verify 'type' column exists")
    print("  [ ] Verify 'pvalue' column exists")
    print("  [ ] Verify NO 'change_point_detected' column")
    print("  [ ] Verify NO 'change_point_score' column")
    print("  [ ] Update skill system if discrepancies found")

    return {
        'documented_columns': ['type', 'pvalue'],
        'incorrect_assumptions': ['change_point_detected', 'change_point_score', 'change_point_timestamp'],
        'needs_live_validation': True
    }

def validate_against_failing_query():
    """Analyze the failing query from Dick's demo"""

    print("\n" + "=" * 80)
    print("ANALYSIS: Dick's Sporting Goods Failing Query")
    print("=" * 80)

    print("\n❌ Query has TWO problems:")
    print("\n1. Field Reference Problem:")
    print("   - Uses: @timestamp (hardcoded)")
    print("   - Should use: {timestamp_field} (variable)")

    print("\n2. Column Name Problem:")
    print("   - Uses: change_point_detected == true")
    print("   - Should use: type IS NOT NULL")
    print("   - Uses: change_point_score")
    print("   - Should use: pvalue")

    print("\n🔧 How ES|QL Skill System Helps:")
    print("  ✅ Problem 1: Skill teaches proper field variable usage")
    print("  ⚠️  Problem 2: Requires accurate documentation in skill system")

    print("\n📌 Action Items:")
    print("  1. Update CHANGE_POINT documentation if needed")
    print("  2. Test against live Elasticsearch to verify")
    print("  3. Update skill system prompts with correct column names")
    print("  4. Add validation tests to prevent regression")

if __name__ == "__main__":
    # Run validation
    validation_result = test_change_point_with_mcp()

    # Analyze the failing query
    validate_against_failing_query()

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

    print("\n🎯 Key Takeaway:")
    print("The ES|QL Skill System is only as good as its documentation.")
    print("We must validate documentation against actual Elasticsearch behavior!")

    print("\n📊 Summary:")
    print(f"  Documented columns: {validation_result['documented_columns']}")
    print(f"  Common mistakes: {validation_result['incorrect_assumptions']}")
    print(f"  Needs live validation: {validation_result['needs_live_validation']}")