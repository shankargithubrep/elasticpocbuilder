# NULL Handling Anti-Pattern Detection & Prevention

## Issue Summary

ES|QL **silently excludes** documents with NULL/missing fields when using negative filters (`!=`, `NOT`, `NOT LIKE`), causing data loss. This is especially critical for security/SIEM queries where missing data could mean missed threats.

```esql
-- ❌ WRONG: Silent data loss
FROM security_events
| WHERE auth_result != "success"
-- Silently EXCLUDES documents where auth_result is NULL!

-- ✅ CORRECT: Include NULL values explicitly
FROM security_events
| WHERE auth_result != "success" OR auth_result IS NULL
-- Includes ALL non-successful authentications, including missing/NULL values
```

## Why This is Critical

Unlike other ES|QL errors, NULL exclusion:

1. **No Error Thrown**: Query executes successfully
2. **Silent Data Loss**: Documents are excluded without warning
3. **Security Impact**: Missing data = missed threats in SIEM/security contexts
4. **Analytics Inaccuracy**: "Not X" should include "unknown" but doesn't
5. **Hard to Detect**: Requires understanding ES|QL behavior to catch

### Real-World Security Impact

```esql
-- Security Query: Find failed auth attempts
FROM security_events
| WHERE auth_result != "success"
| STATS failures = COUNT(*) BY user
```

**Problem**:
- Auth attempts with `auth_result = NULL` are **silently excluded**
- Missing auth data could indicate:
  - System failures
  - Data collection issues
  - Potential security blind spots
  - Attempted attacks that bypassed logging

**Impact**: Security team misses potential threats because incomplete logs are excluded.

**Solution**:
```esql
FROM security_events
| WHERE auth_result != "success" OR auth_result IS NULL
| STATS failures = COUNT(*) BY user
-- Now includes ALL non-successful attempts, including data collection failures
```

## How ES|QL NULL Handling Works

### Negative Filter Behavior

In ES|QL, negative filters (`!=`, `NOT`, `NOT LIKE`) **exclude NULL values**:

| Filter Type | NULL Behavior | Documents Matched |
|-------------|---------------|-------------------|
| `field == "value"` | Excludes NULL | Only docs where field = "value" |
| `field != "value"` | **Excludes NULL** | Only docs where field exists AND ≠ "value" |
| `NOT(field LIKE "pattern")` | **Excludes NULL** | Only docs where field exists AND doesn't match |
| `NOT(field == "value")` | **Excludes NULL** | Only docs where field exists AND ≠ "value" |

### Examples

**Scenario**: 100 documents
- 80 with `status = "success"`
- 15 with `status = "failed"`
- 5 with `status` field missing (NULL)

```esql
-- Query: Find non-successful documents
| WHERE status != "success"
-- Result: Returns 15 documents (only "failed")
-- MISSING: 5 documents where status is NULL!

-- Correct Query:
| WHERE status != "success" OR status IS NULL
-- Result: Returns 20 documents (15 "failed" + 5 NULL)
```

## When NULL Handling is Critical

### 1. Security/SIEM Queries (HIGHEST PRIORITY)

ANY negative filter in security contexts:

```esql
-- Authentication failures (CRITICAL)
| WHERE auth_result != "success" OR auth_result IS NULL

-- Non-approved actions (CRITICAL)
| WHERE user_action != "approved" OR user_action IS NULL

-- Anomalous patterns (CRITICAL)
| WHERE NOT(threat_level == "low") OR threat_level IS NULL

-- Non-compliant events (CRITICAL)
| WHERE compliance_status != "passed" OR compliance_status IS NULL
```

**Why CRITICAL**: Missing security data often indicates:
- Logging failures (data collection issues)
- System compromises (attackers disabling logs)
- Blind spots in monitoring
- Incomplete forensic evidence

### 2. Compliance & Audit Queries

```esql
-- Non-compliant transactions
| WHERE NOT(compliance_status == "passed") OR compliance_status IS NULL

-- Unverified records
| WHERE verification_status != "verified" OR verification_status IS NULL
```

### 3. Analytics & Reporting

```esql
-- Non-active users
| WHERE user_status != "active" OR user_status IS NULL

-- Incomplete records
| WHERE NOT(data_quality == "complete") OR data_quality IS NULL

-- Error analysis
| WHERE log_level != "INFO" OR log_level IS NULL
```

## When NULL Handling Can Be Skipped

### Safe to Skip (Rare Cases)

1. **Guaranteed Fields**: Fields that ALWAYS exist
   ```esql
   | WHERE @timestamp != "value"  -- @timestamp always exists
   ```

2. **Explicit NULL Exclusion**: When NULL values should genuinely be excluded
   ```esql
   -- Find records with EXPLICIT non-success status (exclude NULL/unknown)
   | WHERE status != "success"
   -- Document in description: "Excludes records with missing status"
   ```

3. **Data Quality Checks**: When finding records with specific values
   ```esql
   -- Find records where field is set to a specific incorrect value
   | WHERE field_name == "incorrect_value"  -- Positive filter, NULL not relevant
   ```

## Solution Implemented

### Two-Pronged Approach

1. **Prevention**: Aggressive prompting to generate correct code
2. **Detection**: Post-generation warnings during query testing

### 1. Prevention - Aggressive Prompt Warnings

Added prominent warnings to **all four** query generation methods in `src/framework/module_generator.py`:

**Locations:**
- `_generate_scripted_queries_with_schema()` (lines 533-554)
- `_generate_scripted_queries()` (lines 942-963)
- `_generate_parameterized_queries_with_schema()` (lines 652-673)
- `_generate_parameterized_queries()` (lines 1124-1145)

**Warning Content:**
```
🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)
```

### 2. Detection - Query Testing Warnings

Added automatic detection in `src/services/query_test_runner.py`:

**New Functionality:**
- Implemented `_detect_null_handling_issues()` method (lines 541-657)
- Integrated detection after successful query execution (lines 185-190)
- Special flagging for security/SIEM queries

**Detection Logic:**

The scanner:
1. Identifies negative filter patterns:
   - `field != "value"`
   - `NOT(field LIKE "pattern")`
   - `NOT(field == "value")`
2. Checks if field already has NULL handling (`OR field IS NULL`)
3. Skips guaranteed fields (`@timestamp`)
4. Detects security queries by keywords: `security`, `auth`, `threat`, `compliance`, `audit`, `siem`, `detection`, `alert`, `incident`, `vulnerability`
5. Generates specific warnings with suggested fixes

**Warning Output:**

```python
{
    'type': 'missing_null_check',
    'field': 'auth_result',
    'message': "Negative filter on 'auth_result' missing NULL check (silently excludes docs where field is NULL) - CRITICAL for security queries (missing data = missed threats)",
    'pattern': 'auth_result != "success"',
    'suggested_fix': '| WHERE auth_result != "success" OR auth_result IS NULL',
    'is_security_query': True
}
```

**Where Warnings Appear:**
- Logged during query testing: `⚠️ Query 'Failed Auth Detection': Negative filter on 'auth_result'...`
- Saved to `query_testing_results.json` in demo module
- Accessible for manual review and debugging

### 3. Baseline Guidance

Added to `src/prompts/esql_strict_rules.py` as **Rule 20** (lines 350-399):

Provides comprehensive guidance on:
- When to include NULL checks
- When it's safe to skip
- Common patterns for security, compliance, and analytics
- Warning template for generated queries

## Testing

### Test Case 1: Regular Analytics Query

```python
esql = """FROM logs
| WHERE status != "success"
| STATS count = COUNT(*) BY service"""

warnings = _detect_null_handling_issues(esql, "Error Analysis", "Analyze errors")
# Result: 1 warning detected ✅
```

**Output:**
```
⚠️ Negative filter on 'status' missing NULL check (silently excludes docs where field is NULL)
   Suggested Fix: | WHERE status != "success" OR status IS NULL
```

### Test Case 2: Security Query (CRITICAL)

```python
esql = """FROM security_events
| WHERE auth_result != "success"
| STATS failures = COUNT(*) BY user"""

warnings = _detect_null_handling_issues(esql, "Failed Authentication Detection", "Security monitoring")
# Result: 1 warning with CRITICAL flag ✅
```

**Output:**
```
⚠️ Negative filter on 'auth_result' missing NULL check (silently excludes docs where field is NULL) - CRITICAL for security queries (missing data = missed threats)
   Is Security Query: True
   Suggested Fix: | WHERE auth_result != "success" OR auth_result IS NULL
```

### Test Case 3: NOT LIKE Pattern

```python
esql = """FROM events
| WHERE NOT(error_message LIKE "*timeout*")
| SORT @timestamp DESC"""

warnings = _detect_null_handling_issues(esql, "Non-Timeout Errors", "Find non-timeout errors")
# Result: 1 warning detected ✅
```

**Output:**
```
⚠️ NOT LIKE filter on 'error_message' missing NULL check (silently excludes docs where field is NULL)
   Pattern: NOT(error_message LIKE "*timeout*")
   Suggested Fix: | WHERE NOT(error_message LIKE "*timeout*") OR error_message IS NULL
```

### Test Case 4: Query with Correct NULL Handling

```python
esql = """FROM logs
| WHERE status != "success" OR status IS NULL
| STATS count = COUNT(*) BY service"""

warnings = _detect_null_handling_issues(esql, "Error Analysis", "Analyze errors")
# Result: 0 warnings ✅
```

**Output:**
```
✅ No warnings - NULL handling already present!
```

### Test Case 5: Guaranteed Field (@timestamp)

```python
esql = """FROM logs
| WHERE @timestamp != "2024-01-01"
| STATS count = COUNT(*)"""

warnings = _detect_null_handling_issues(esql, "Time Filter", "Filter by time")
# Result: 0 warnings ✅
```

**Output:**
```
✅ No warnings - @timestamp is a guaranteed field!
```

## Common Patterns Affected

### 1. Authentication/Authorization

```esql
-- ❌ WRONG
| WHERE auth_result != "success"

-- ✅ CORRECT
| WHERE auth_result != "success" OR auth_result IS NULL
```

### 2. Status/State Filtering

```esql
-- ❌ WRONG
| WHERE user_status != "active"

-- ✅ CORRECT
| WHERE user_status != "active" OR user_status IS NULL
```

### 3. Pattern Exclusion

```esql
-- ❌ WRONG
| WHERE NOT(error_message LIKE "*timeout*")

-- ✅ CORRECT
| WHERE NOT(error_message LIKE "*timeout*") OR error_message IS NULL
```

### 4. Compliance Checks

```esql
-- ❌ WRONG
| WHERE NOT(compliance_status == "passed")

-- ✅ CORRECT
| WHERE NOT(compliance_status == "passed") OR compliance_status IS NULL
```

### 5. Data Quality

```esql
-- ❌ WRONG
| WHERE data_quality != "validated"

-- ✅ CORRECT
| WHERE data_quality != "validated" OR data_quality IS NULL
```

## Comparison to Other Anti-Patterns

| Aspect | NULL Handling | Integer Division | @timestamp Parameterization |
|--------|---------------|------------------|----------------------------|
| **Error** | None (silent data loss) | None (wrong results) | None (poor UX) |
| **Detection** | Negative filter scanning | EVAL division scanning | Strategy hint detection |
| **Impact** | **CRITICAL** - Security blind spots | Incorrect analytics | Stale demo data |
| **Fix Timing** | Must prevent at generation | Can fix post-generation | Must prevent at generation |
| **Validation** | Check for `OR field IS NULL` | Check for `TO_DOUBLE()` | Check for `?start_date` params |

## Best Practices

### 1. Default to Including NULL

When in doubt, **always include NULL**:
```esql
| WHERE field != "value" OR field IS NULL
```

Better to include extra documents than miss critical ones.

### 2. Document NULL Exclusion

If you intentionally exclude NULL values, document it:
```python
{
    'name': 'Explicit Status Errors',
    'description': 'Find records with EXPLICIT non-success status. Excludes records where status is missing/NULL.',
    'esql': '| WHERE status != "success"'  # Intentionally excludes NULL
}
```

### 3. Security Queries MUST Include NULL

For ANY security/SIEM query with negative filters:
```esql
-- ALWAYS include NULL checks
| WHERE threat_level != "low" OR threat_level IS NULL
| WHERE NOT(action == "approved") OR action IS NULL
```

### 4. Review Query Testing Results

After demo generation, check `query_testing_results.json` for NULL handling warnings:
```json
{
    "warnings": [
        {
            "type": "missing_null_check",
            "field": "auth_result",
            "message": "...",
            "is_security_query": true
        }
    ]
}
```

## Prevention Strategy

Following lessons from previous anti-patterns:

### 1. Aggressive End-of-Prompt Warnings ✅
- Placed warnings at END of prompts (recency bias)
- Used visual distinction (🚨 emoji, CAPS)
- Showed EXACT anti-pattern to avoid
- Provided immediate correct alternative
- Repeated across all 4 generation methods

### 2. Post-Generation Detection ✅
- Automated scanning during query testing
- Warnings even when query succeeds (no error)
- Specific suggestions for fixes
- Security query flagging
- Saved to test results for review

### 3. Comprehensive Baseline Guidance ✅
- Added to esql_strict_rules.py as Rule 20
- Clear explanation of behavior
- Common patterns for different use cases
- When to skip (rare cases)

### 4. Documentation ✅
- Comprehensive documentation (this file)
- Real-world security examples
- Clear explanation of risks
- Multiple testing scenarios

## Next Steps

### Verification Checklist

After next demo generation:
- [ ] No missing_null_check warnings in query_testing_results.json
- [ ] All negative filters include `OR field IS NULL` clauses
- [ ] Security queries properly handle NULL values
- [ ] Compliance/audit queries include NULL checks

### Manual Review

If warnings appear after generation:

1. Check `demos/[demo_name]/query_testing_results.json`
2. Look for queries with `warnings` field containing `type: "missing_null_check"`
3. Review `suggested_fix` for each warning
4. Update `demos/[demo_name]/query_generator.py` manually if needed
5. Pay special attention to security queries (`is_security_query: true`)
6. Re-test query to verify fix works

### Future Enhancements

**Possible Auto-Fix:**
- Detect negative filters in generated code
- Automatically append `OR field IS NULL`
- Re-test to verify fix works
- Save corrected version

This would require:
1. Parse ES|QL queries to AST
2. Find WHERE nodes with negative operators
3. Check for NULL handling
4. Insert `OR field IS NULL` if missing
5. Regenerate query string

## Related Files

- `src/framework/module_generator.py` - Query generation prompts (lines 533-554, 652-673, 942-963, 1124-1145)
- `src/services/query_test_runner.py` - Detection logic (lines 541-657)
- `src/prompts/esql_strict_rules.py` - Baseline guidance (lines 350-399, Rule 20)
- `docs/INTEGER_DIVISION_ANTI_PATTERN.md` - Related anti-pattern documentation
- `docs/QUERY_STRATEGY_INTROSPECTION.md` - Strategy validation documentation

## Lessons Learned

### Why This Anti-Pattern Is Particularly Dangerous

1. **Silent Failure**: No error message, query succeeds
2. **Security Impact**: Can result in missed threats
3. **Hard to Notice**: Requires deep ES|QL knowledge to spot
4. **Widespread**: Affects any analytics/security use case with negative filters

### Key Success Factors

1. ✅ **Recency**: Place critical warnings at END of prompts
2. ✅ **Visibility**: Use emoji, caps, and concrete examples
3. ✅ **Specificity**: Show exact pattern to avoid, not just description
4. ✅ **Context**: Flag security queries as CRITICAL
5. ✅ **Detection**: Add post-generation scanning for verification
6. ✅ **Documentation**: Explain security implications clearly

---

**Date**: 2025-01-14
**Issue**: ES|QL silently excludes NULL values from negative filters (!=, NOT, NOT LIKE)
**Reporter**: User provided NULL handling rule for query generation
**Resolution**: Aggressive prompting + automated detection + security flagging
**Files Modified**: `module_generator.py`, `query_test_runner.py`, `esql_strict_rules.py`
**Status**: ✅ Implemented, pending verification with next demo generation
