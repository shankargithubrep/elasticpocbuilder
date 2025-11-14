# Integer Division Anti-Pattern Detection & Prevention

## Issue Summary

ES|QL performs **integer division** when dividing two integer values, truncating the result to 0. This produces plausible-looking but incorrect results, especially in percentage calculations.

```esql
-- ❌ WRONG: Integer division
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / auth_attempts) * 100
-- Result: 0 or 100 only (truncated)

-- ✅ CORRECT: Float division with TO_DOUBLE()
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / TO_DOUBLE(auth_attempts)) * 100
-- Result: 95.7, 87.3, etc. (accurate percentages)
```

## Why This is Critical

Unlike other ES|QL errors that produce exceptions, integer division **silently produces wrong results**:

1. **No Error Thrown**: Query executes successfully
2. **Plausible Results**: Returns 0 or 100, which look valid for percentages
3. **Hard to Detect**: Requires manual inspection or data validation to catch
4. **Widespread Impact**: Affects any division of aggregated fields (STATS results)

### Real-World Example

From user-reported issue with T-Mobile demo:

```esql
FROM diameter_transactions
| WHERE command_code == "Authentication-Information"
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS
    auth_attempts = COUNT(*),
    auth_failures = COUNT(*) WHERE transaction_success == false,
    avg_response_ms = AVG(response_time_ms),
    p95_response_ms = PERCENTILE(response_time_ms, 95)
  BY time_bucket, hss_node
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / auth_attempts) * 100
```

**Problem**: The last EVAL returns either 0 or 100 for `success_rate_pct`.

**Reason**:
- `auth_attempts` and `auth_failures` are both integers (from COUNT())
- `(100 - 5) / 100 = 95 / 100 = 0` (integer division)
- `0 * 100 = 0` (wrong!)

**Solution**:
```esql
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / TO_DOUBLE(auth_attempts)) * 100
```

Now: `95 / 100.0 = 0.95`, then `0.95 * 100 = 95.0` ✅

## How ES|QL Division Works

### Integer Division Rules

In ES|QL (like most typed languages):
- `integer / integer = integer` (result is truncated)
- `integer / float = float` (result has decimal precision)
- `float / integer = float` (result has decimal precision)

### Examples

```esql
-- Integer division (WRONG for most use cases)
| EVAL result = 95 / 100           -- Result: 0
| EVAL result = 1 / 2               -- Result: 0
| EVAL result = 99 / 100            -- Result: 0
| EVAL result = 100 / 100           -- Result: 1
| EVAL result = 101 / 100           -- Result: 1

-- Float division (CORRECT)
| EVAL result = 95 / TO_DOUBLE(100)  -- Result: 0.95
| EVAL result = 1 / 2.0              -- Result: 0.5
| EVAL result = 99 / TO_DOUBLE(100)  -- Result: 0.99
| EVAL result = 100 * 1.0 / 100      -- Result: 1.0
```

### Why Percentage Calculations Are Affected

Percentage calculations follow this pattern:
```
percentage = (part / total) * 100
```

If `part` and `total` are both integers:
- `(part / total)` performs integer division → 0 (if part < total)
- `0 * 100 = 0`

If `total` is converted to float:
- `(part / TO_DOUBLE(total))` performs float division → 0.XX
- `0.XX * 100 = XX.X`

## Solution Implemented

### Two-Pronged Approach

1. **Prevention**: Aggressive prompting to generate correct code
2. **Detection**: Post-generation warnings during query testing

### 1. Prevention - Aggressive Prompt Warnings

Added prominent warnings to **all four** query generation methods in `src/framework/module_generator.py`:

**Locations:**
- `_generate_scripted_queries_with_schema()` (lines 511-531)
- `_generate_scripted_queries()` (lines 874-894)
- `_generate_parameterized_queries_with_schema()` (lines 585-605)
- `_generate_parameterized_queries()` (lines 989-1009)

**Warning Content:**
```
🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`
```

**Why This Works:**
- **Recency Bias**: Placed at END of prompt, freshest in LLM memory
- **Visual Prominence**: 🚨 emoji, ALL CAPS, concrete examples
- **Specific Pattern**: Shows EXACT anti-pattern to avoid
- **Multiple Valid Solutions**: Provides 3 acceptable patterns

### 2. Detection - Query Testing Warnings

Added automatic detection in `src/services/query_test_runner.py`:

**New Functionality:**
- Added `warnings` field to `QueryTestResult` dataclass (line 32)
- Implemented `_detect_integer_division_patterns()` method (lines 452-532)
- Integrated detection after successful query execution (lines 178-183)

**Detection Logic:**

The scanner:
1. Finds all `EVAL` statements with division (`/`)
2. Checks if division is already protected:
   - ✅ Skip if `TO_DOUBLE()` present
   - ✅ Skip if dividing by float literal (`/ 1000.0`)
   - ✅ Skip if multiplying by float first (`* 100.0 /`)
3. Detects unprotected integer division patterns
4. Identifies percentage calculations (field name contains `rate` or `pct`)
5. Generates specific warnings with suggested fixes

**Warning Output:**

```python
{
    'type': 'integer_division',
    'field': 'success_rate_pct',
    'message': "Potential integer division in EVAL success_rate_pct: '((auth_attempts - auth_failures) / auth_attempts' (percentage calculation - integer division will truncate to 0 or 100)",
    'pattern': '((auth_attempts - auth_failures) / auth_attempts',
    'suggested_fix': '| EVAL success_rate_pct = ((auth_attempts - auth_failures) / TO_DOUBLE(auth_attempts)',
    'full_expression': '((auth_attempts - auth_failures) / auth_attempts) * 100',
    'is_percentage': True
}
```

**Where Warnings Appear:**
- Logged during query testing: `⚠️ Query 'Auth Success Rate': Potential integer division...`
- Saved to `query_testing_results.json` in demo module
- Accessible for manual review and debugging

## Testing

### Test Case 1: Problematic Query

```python
esql = """FROM diameter_transactions
| WHERE command_code == "Authentication-Information"
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS
    auth_attempts = COUNT(*),
    auth_failures = COUNT(*) WHERE transaction_success == false
  BY time_bucket, hss_node
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / auth_attempts) * 100"""

warnings = _detect_integer_division_patterns(esql)
# Result: 1 warning detected ✅
```

**Output:**
```
⚠️ Potential integer division in EVAL success_rate_pct: '((auth_attempts - auth_failures) / auth_attempts' (percentage calculation - integer division will truncate to 0 or 100)
   Pattern: ((auth_attempts - auth_failures) / auth_attempts
   Suggested Fix: | EVAL success_rate_pct = ((auth_attempts - auth_failures) / TO_DOUBLE(auth_attempts)
```

### Test Case 2: Corrected Query

```python
esql_fixed = """FROM diameter_transactions
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / TO_DOUBLE(auth_attempts)) * 100"""

warnings = _detect_integer_division_patterns(esql_fixed)
# Result: 0 warnings ✅
```

**Output:**
```
✅ No warnings - TO_DOUBLE() detected correctly!
```

### Test Case 3: Alternative Correct Patterns

All of these should pass without warnings:

```esql
-- Pattern 1: TO_DOUBLE() on denominator
| EVAL rate = successful / TO_DOUBLE(total)

-- Pattern 2: Multiply by float literal first
| EVAL rate = successful * 100.0 / total

-- Pattern 3: Divide by float literal
| EVAL seconds = milliseconds / 1000.0

-- Pattern 4: TO_DOUBLE() on numerator
| EVAL rate = TO_DOUBLE(successful) / total
```

## Common Patterns Affected

### 1. Success/Failure Rates

```esql
-- ❌ WRONG
| STATS total = COUNT(*), failures = COUNT(*) WHERE status == "failed"
  BY service
| EVAL failure_rate = failures / total

-- ✅ CORRECT
| STATS total = COUNT(*), failures = COUNT(*) WHERE status == "failed"
  BY service
| EVAL failure_rate = failures / TO_DOUBLE(total)
```

### 2. Percentages

```esql
-- ❌ WRONG
| STATS converted = COUNT(*) WHERE action == "purchase",
         visitors = COUNT(*)
  BY campaign
| EVAL conversion_pct = (converted / visitors) * 100

-- ✅ CORRECT
| STATS converted = COUNT(*) WHERE action == "purchase",
         visitors = COUNT(*)
  BY campaign
| EVAL conversion_pct = (converted / TO_DOUBLE(visitors)) * 100
```

### 3. Ratios

```esql
-- ❌ WRONG
| STATS revenue = SUM(amount), costs = SUM(cost)
  BY region
| EVAL roi = (revenue - costs) / costs

-- ✅ CORRECT
| STATS revenue = SUM(amount), costs = SUM(cost)
  BY region
| EVAL roi = (revenue - costs) / TO_DOUBLE(costs)
```

### 4. Averages (Manual Calculation)

```esql
-- ❌ WRONG
| STATS total_value = SUM(value), count = COUNT(*)
  BY category
| EVAL avg_value = total_value / count

-- ✅ CORRECT (Option 1: TO_DOUBLE)
| STATS total_value = SUM(value), count = COUNT(*)
  BY category
| EVAL avg_value = total_value / TO_DOUBLE(count)

-- ✅ CORRECT (Option 2: Use AVG directly - BEST)
| STATS avg_value = AVG(value)
  BY category
```

## When TO_DOUBLE() Is NOT Needed

### Safe Patterns (No Warning Needed)

1. **Dividing by float literal:**
   ```esql
   | EVAL seconds = milliseconds / 1000.0  -- ✅ 1000.0 is float
   ```

2. **Multiplying by float before division:**
   ```esql
   | EVAL pct = count * 100.0 / total  -- ✅ count becomes float after * 100.0
   ```

3. **Already using TO_DOUBLE():**
   ```esql
   | EVAL rate = success / TO_DOUBLE(total)  -- ✅ Explicit conversion
   ```

4. **Dividing float aggregations:**
   ```esql
   | STATS avg1 = AVG(field1), avg2 = AVG(field2)
   | EVAL ratio = avg1 / avg2  -- ✅ AVG returns float
   ```

5. **Time duration calculations with explicit decimals:**
   ```esql
   | EVAL hours = duration_ms / 3600000.0  -- ✅ Float literal
   ```

## Existing Guidance

We already had basic guidance in `src/prompts/esql_strict_rules.py`:

**Line 158-161:**
```python
### 13. Division and Type Casting ⚠️
✅ CORRECT: `EVAL rate = TO_DOUBLE(numerator) / denominator`
✅ CORRECT: `EVAL pct = numerator * 100.0 / denominator`
❌ WRONG: `EVAL rate = numerator / denominator` - Integer division loses precision
```

**Line 484:**
```python
| EVAL resolution_rate = TO_DOUBLE(resolved) * 100.0 / call_count
```

**Why It Wasn't Enough:**
- Buried in middle of 350-line document
- Competing with many other rules
- Not visually prominent
- Not repeated at point of code generation

## Prevention Strategy

Following lessons from `@timestamp` anti-pattern fix:

### 1. Aggressive End-of-Prompt Warnings
✅ Placed warnings at END of prompts (recency bias)
✅ Used visual distinction (🚨 emoji, CAPS)
✅ Showed EXACT anti-pattern to avoid
✅ Provided immediate correct alternative
✅ Repeated across all 4 generation methods

### 2. Post-Generation Detection
✅ Automated scanning during query testing
✅ Warnings even when query succeeds (no error)
✅ Specific suggestions for fixes
✅ Saved to test results for review

### 3. Documentation
✅ Comprehensive documentation (this file)
✅ Real-world examples from user reports
✅ Clear explanation of why it happens
✅ Multiple valid solution patterns

## Next Steps

### Verification Checklist

After next demo generation:
- [ ] No integer division warnings in query_testing_results.json
- [ ] All percentage calculations use TO_DOUBLE() or float literals
- [ ] Ratio calculations protected with TO_DOUBLE()
- [ ] Rate calculations (success_rate, failure_rate) use float division

### Manual Review

If warnings appear after generation:

1. Check `demos/[demo_name]/query_testing_results.json`
2. Look for queries with `warnings` field
3. Review `suggested_fix` for each warning
4. Update `demos/[demo_name]/query_generator.py` manually if needed
5. Re-test query to verify fix

### Future Enhancements

**Possible Auto-Fix:**
- Detect integer division in generated code
- Automatically rewrite with TO_DOUBLE()
- Re-test to verify fix works
- Save corrected version

This would require:
1. Parse ES|QL queries to AST
2. Find EVAL nodes with division
3. Check operand types
4. Insert TO_DOUBLE() if needed
5. Regenerate query string

## Related Files

- `src/framework/module_generator.py` - Query generation prompts (lines 511-531, 585-605, 874-894, 989-1009)
- `src/services/query_test_runner.py` - Detection logic (lines 452-532)
- `src/prompts/esql_strict_rules.py` - Original guidance (lines 158-161, 484)
- `docs/QUERY_STRATEGY_INTROSPECTION.md` - Related anti-pattern detection docs

## Lessons Learned

### Why This Anti-Pattern Is Particularly Dangerous

1. **Silent Failure**: No error message, query succeeds
2. **Plausible Results**: 0 and 100 are valid percentage values
3. **Hard to Notice**: Requires checking actual data to spot
4. **Widespread**: Affects any calculated metrics from aggregations

### Comparison to @timestamp Anti-Pattern

| Aspect | @timestamp Parameterization | Integer Division |
|--------|---------------------------|------------------|
| **Error** | None (works in testing) | None (works, wrong results) |
| **Detection** | Query strategy hints | Pattern scanning |
| **Impact** | Poor UX | Incorrect analytics |
| **Fix Timing** | Must prevent at generation | Can fix post-generation |
| **Validation** | Check for `?start_date` params | Check EVAL divisions |

### Best Practices for Anti-Pattern Prevention

1. ✅ **Recency**: Place critical warnings at END of prompts
2. ✅ **Visibility**: Use emoji, caps, and concrete examples
3. ✅ **Specificity**: Show exact pattern to avoid, not just description
4. ✅ **Alternatives**: Provide multiple valid solutions
5. ✅ **Detection**: Add post-generation scanning for verification
6. ✅ **Documentation**: Explain WHY, not just WHAT

---

**Date**: 2025-01-14
**Issue**: Integer division in ES|QL EVAL statements produces truncated results
**Reporter**: User discovered in T-Mobile demo with `diameter_transactions` query
**Resolution**: Aggressive prompting + automated detection during query testing
**Files Modified**: `module_generator.py`, `query_test_runner.py`
**Status**: ✅ Implemented, pending verification with next demo generation
