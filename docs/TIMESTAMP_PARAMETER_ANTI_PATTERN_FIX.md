# @timestamp Parameter Anti-Pattern Fix

## Issue Summary

Generated parameterized queries continue to include the anti-pattern:
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

Despite having guidance in `src/prompts/esql_strict_rules.py` warning against this pattern.

## Why This Anti-Pattern is Bad

1. **Poor UX**: Users must provide exact timestamp ranges matching index ingestion times
2. **Elasticsearch Limitation**: @timestamp is a system field representing document ingestion time, not business time
3. **Better Alternative Exists**: Use `NOW() - X days/hours` for relative time filtering

## Root Cause

### What We Already Had

✅ Guidance in `esql_strict_rules.py` (line 289, 323, 333):
```python
❌ WRONG:
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date

✅ CORRECT:
| WHERE @timestamp >= NOW() - 7 days
```

✅ This guidance was included in parameterized query prompts via:
```python
esql_rules = self._get_esql_strict_rules()  # Line 523
{esql_rules}  # Line 567
```

### Why It Wasn't Working

**The Problem**: The anti-pattern guidance was **buried in the middle** of a long rules document.

**LLM Attention Bias**: LLMs pay most attention to:
1. **Beginning** of prompts (priming)
2. **End** of prompts (recency bias)
3. **Visually distinctive** content (emoji, caps, repetition)

Our guidance was:
- In the middle of a 350-line document
- Not visually emphasized
- Competing with other instructions about BUSINESS date fields

The **ending instruction** the LLM saw was:
```
"ALWAYS use 'type': 'parameterized' for ALL queries."
```

This overshadowed the timestamp guidance.

## Solution Applied

### Strategy: Aggressive Recency-Based Warning

Added a **visually prominent, repetitive warning** at the **END** of both parameterized query generation prompts, just before the LLM generates code.

### Files Modified

#### 1. `src/framework/module_generator.py` Line 569-583

Added to `_generate_parameterized_queries_with_schema()`:

```python
🚨🚨🚨 CRITICAL - @timestamp ANTI-PATTERN 🚨🚨🚨
NEVER EVER parameterize @timestamp! This is the #1 most common mistake!

❌ WRONG (DO NOT GENERATE THIS):
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

✅ CORRECT (USE THIS INSTEAD):
```esql
| WHERE @timestamp >= NOW() - 7 days  # Relative time with NOW()
```

If you see @timestamp in the query plan, IGNORE any parameter suggestions and use NOW() instead!
The ONLY time-based parameters allowed are for BUSINESS date fields (order_date, created_at, etc.) - NEVER @timestamp!
```

#### 2. `src/framework/module_generator.py` Line 952-965

Added to `_generate_parameterized_queries()`:

```python
🚨🚨🚨 CRITICAL - @timestamp ANTI-PATTERN 🚨🚨🚨
NEVER EVER parameterize @timestamp! This is the #1 most common mistake!

❌ WRONG (DO NOT GENERATE THIS):
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

✅ CORRECT (USE THIS INSTEAD):
```esql
| WHERE @timestamp >= NOW() - 7 days  # Relative time with NOW()
```

The ONLY time-based parameters allowed are for BUSINESS date fields (order_date, created_at, etc.) - NEVER @timestamp!
```

## Why This Fix Works

### 1. **Recency Bias**
The warning is the **last thing** the LLM reads before generating code, making it freshest in memory.

### 2. **Visual Prominence**
- 🚨 Emoji (catches attention)
- ALL CAPS for key words
- Repetition ("NEVER EVER", "CRITICAL")

### 3. **Concrete Example**
Shows the EXACT anti-pattern to avoid:
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

Not just "don't parameterize @timestamp" (too vague).

### 4. **Immediate Correct Alternative**
Provides the solution right next to the problem:
```esql
| WHERE @timestamp >= NOW() - 7 days
```

### 5. **Override Instructions**
Explicitly says "IGNORE any parameter suggestions" if @timestamp appears in the query plan.

## Testing

### Before Fix
Generated query contained:
```python
queries.append({
    'query': """FROM subscriber_sessions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| ...
""",
    'parameters': {
        {'name': 'start_date', 'type': 'date', ...},
        {'name': 'end_date', 'type': 'date', ...}
    }
})
```

### After Fix (Expected)
Generated query should contain:
```python
queries.append({
    'query': """FROM subscriber_sessions
| WHERE @timestamp >= NOW() - 7 days
| WHERE session_result == ?session_result
| ...
""",
    'parameters': {
        {'name': 'session_result', 'type': 'string', ...}
        # NO start_date/end_date parameters!
    }
})
```

## Verification Checklist

After next demo generation:
- [ ] No `?start_date` or `?end_date` parameters in parameterized queries
- [ ] No `@timestamp >= ?` patterns in query strings
- [ ] Business date fields (order_date, created_at) CAN still be parameterized
- [ ] @timestamp filtering uses `NOW() - X days/hours` if present

## Related Documentation

- `src/prompts/esql_strict_rules.py` lines 285-342 - Original timestamp guidance
- `src/services/query_strategy_generator.py` line 280 - Analytics strategy guidance
- `src/services/search_strategy_generator.py` line 248 - Search strategy guidance

## Lessons Learned

### Why Previous Fixes Failed

1. **Insufficient Emphasis**: Guidance was present but not prominent
2. **Buried in Long Documents**: Lost among 350 lines of other rules
3. **Competing Instructions**: Other requirements overshadowed timestamp rules
4. **No Recency**: Critical rule appeared early/middle, not at decision time

### Principles for Future Anti-Pattern Prevention

1. ✅ **Place critical rules at the END** of prompts (recency bias)
2. ✅ **Use visual distinction** (emoji, caps, repetition)
3. ✅ **Show EXACT anti-pattern** (not just description)
4. ✅ **Provide immediate alternative** (wrong + correct side-by-side)
5. ✅ **Override conflicting instructions** ("IGNORE X if Y")
6. ✅ **Repetition across methods** (if multiple code paths, repeat warning)

### When to Use This Approach

Use aggressive end-of-prompt warnings when:
- Anti-pattern is **persistent** despite existing guidance
- Anti-pattern has **high severity** (breaks functionality, poor UX)
- Anti-pattern is **simple** (one clear wrong pattern, one clear right pattern)
- LLM has **multiple competing instructions** that might confuse it

## Status

✅ **Fix Applied**: Aggressive warnings added to both parameterized query methods
⏳ **Pending Verification**: Needs testing with next demo generation
📊 **Historical Frequency**: Observed in 6+ generated demos before fix

---

**Date**: 2024-11-14
**Issue**: Persistent `@timestamp >= ?start_date` anti-pattern in parameterized queries
**Resolution**: Added aggressive, visually prominent warnings at END of parameterized query prompts
**Files**: `src/framework/module_generator.py` (lines 569-583, 952-965)
