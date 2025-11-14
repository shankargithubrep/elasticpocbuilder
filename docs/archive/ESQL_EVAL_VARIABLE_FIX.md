# ES|QL EVAL Variable Reuse Fix

## Issue Discovered

**Demo**: t-mobile_network operations_20251113_112020
**Query**: MME Split-Brain and Signaling Storm Detection
**Date**: 2025-11-13

### The Problem

The LLM was generating EVAL commands that tried to use newly defined variables within the same EVAL command:

```esql
❌ WRONG:
| EVAL
    z_score_failures = (failure_count - avg_failures) / COALESCE(stddev_failures, 1),
    multi_host_indicator = CASE(unique_mme_hosts >= 2, 1, 0),
    storm_probability = z_score_failures * multi_host_indicator  ← ERROR!
```

**Error**: `Unknown column [z_score_failures]`

**Why It Fails**: ES|QL evaluates all expressions in an EVAL command **simultaneously**, so variables aren't available to other expressions in the same command.

### The Fix

Split into multiple EVAL commands:

```esql
✅ CORRECT:
| EVAL
    z_score_failures = (failure_count - avg_failures) / COALESCE(stddev_failures, 1),
    multi_host_indicator = CASE(unique_mme_hosts >= 2, 1, 0)
| EVAL storm_probability = z_score_failures * multi_host_indicator  ← Separate command
```

## Implementation

### File Modified

**Location**: `src/prompts/esql_strict_rules.py`

**Added**: Rule #17 - "EVAL Variable Reuse - CANNOT Use Newly Defined Variables in Same Command"

### Rule Details

The new rule includes:

1. **Critical Warning**: Marked as `⚠️⚠️ CRITICAL`
2. **Wrong Pattern**: Shows the exact anti-pattern from the T-Mobile demo
3. **Correct Pattern**: Shows how to split into separate EVALs
4. **Explanation**: Why it fails (simultaneous evaluation)
5. **Common Examples**: Additional failing patterns and their fixes
6. **Exception**: Clarifies you CAN use existing fields from source data

### Rule Content

```
### 17. EVAL Variable Reuse - CANNOT Use Newly Defined Variables in Same Command ⚠️⚠️ CRITICAL

❌ WRONG - Using variable defined in same EVAL:
| EVAL
    z_score = (count - avg) / stddev,
    multi_host = CASE(hosts >= 2, 1, 0),
    storm_prob = z_score * multi_host  -- ERROR: Unknown column [z_score]

✅ CORRECT - Use separate EVAL commands:
| EVAL
    z_score = (count - avg) / stddev,
    multi_host = CASE(hosts >= 2, 1, 0)
| EVAL storm_prob = z_score * multi_host  -- Now z_score is available

Rule: Variables defined in an EVAL command are NOT available to other
expressions in the SAME EVAL command. You must use a subsequent EVAL
(or other command) to reference newly created variables.
```

## Impact

### Queries Affected

This pattern is common in **analytics queries** that calculate:
- Z-scores (need intermediate calculations)
- Percentages (need totals first)
- Conditional metrics (need flags, then use them)
- Compound scores (combine multiple factors)

### Prevention

The rule is now included in:
1. **Query generation prompts** via `get_rules_for_module_generation()`
2. **All future demos** - LLM will see this rule during generation
3. **Centralized location** - `esql_strict_rules.py` is the single source of truth

## Testing

### Validation Test

Created `/tmp/test_esql_rule_added.py` to verify:
- ✅ Rule is present in rules output
- ✅ Contains error example from T-Mobile demo
- ✅ Shows correct pattern (separate EVALs)
- ✅ Marked as CRITICAL
- ✅ Includes explanation

**Result**: All checks passed ✅

### How to Re-test

```bash
source venv/bin/activate
python /tmp/test_esql_rule_added.py
```

## Examples of Corrected Patterns

### Pattern 1: Z-Score Calculations

**Before (Wrong)**:
```esql
| EVAL
    z_score = (value - avg) / stddev,
    is_anomaly = CASE(z_score > 3, true, false)  -- ❌
```

**After (Correct)**:
```esql
| EVAL z_score = (value - avg) / stddev
| EVAL is_anomaly = CASE(z_score > 3, true, false)  -- ✅
```

### Pattern 2: Percentage Calculations

**Before (Wrong)**:
```esql
| EVAL
    total = a + b,
    percentage = (total / max) * 100  -- ❌
```

**After (Correct)**:
```esql
| EVAL total = a + b
| EVAL percentage = (total / max) * 100  -- ✅
```

### Pattern 3: Date Arithmetic

**Before (Wrong)**:
```esql
| EVAL
    days_ago = (TO_LONG(NOW()) - TO_LONG(@timestamp)) / 86400000,
    is_recent = CASE(days_ago <= 7, true, false)  -- ❌
```

**After (Correct)**:
```esql
| EVAL days_ago = (TO_LONG(NOW()) - TO_LONG(@timestamp)) / 86400000
| EVAL is_recent = CASE(days_ago <= 7, true, false)  -- ✅
```

## Related Rules

This complements existing ES|QL rules:

- **Rule #7**: INLINESTATS syntax (single BY clause)
- **Rule #8**: STATS conditional aggregation
- **Rule #13**: Division and type casting

All rules are centralized in `src/prompts/esql_strict_rules.py`.

## Next Steps

### For Existing Demos

Existing demos with this pattern should be:
1. Identified (search for multi-line EVAL with variable dependencies)
2. Fixed manually or regenerated
3. Tested to ensure queries work

### For New Demos

The rule is now active and will prevent this issue in all future generation.

## Summary

**Problem**: LLM generated EVAL commands that tried to reuse variables within the same command
**Root Cause**: ES|QL evaluates EVAL expressions simultaneously
**Solution**: Added Rule #17 to ES|QL strict rules
**Impact**: Prevents this anti-pattern in all future query generation
**Status**: ✅ Fixed and tested