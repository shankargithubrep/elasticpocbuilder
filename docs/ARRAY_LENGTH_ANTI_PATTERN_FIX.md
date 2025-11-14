# Array Length Anti-Pattern Fix

## Issue Summary

Generated data modules were crashing with `ValueError: All arrays must be of the same length` when creating pandas DataFrames.

## Root Cause

The LLM was generating code that:
1. Defined a small reference pool (6 items)
2. Tried to slice more items than existed (10 items)
3. Used the short slice in a DataFrame alongside other arrays of correct length

### Example of Bug

```python
# Line 51: Define pool with only 6 items
hss_nodes = [f'hss-{dc}-{i:02d}' for dc in ['east', 'west'] for i in range(1, 4)]
# Creates: ['hss-east-01', 'hss-east-02', 'hss-east-03', 'hss-west-01', 'hss-west-02', 'hss-west-03']

# Line 78-84: Try to create 10-row DataFrame
n_hss = 10
datasets['hss_nodes'] = pd.DataFrame({
    'network.hss.node_id': hss_nodes[:n_hss],  # ❌ Only returns 6 items, need 10!
    'network.hss.database_instance': self.safe_choice(hss_db_instances, n_hss),  # ✓ 10 items
    'network.hss.datacenter': self.safe_choice(datacenters, n_hss),  # ✓ 10 items
    'network.hss.node_role': self.safe_choice(hss_roles, n_hss)  # ✓ 10 items
})
# ERROR: Arrays have lengths [6, 10, 10, 10] - mismatched!
```

## Why Existing Guidance Wasn't Enough

We already had extensive array length guidance in `src/framework/module_generator.py` at lines 1396-1446, including:

✅ General rule about all arrays needing same length
✅ Warning about static lists like `['a', 'b', 'c']`
✅ Warning about wrong size parameters
✅ Warning about list comprehensions with wrong range
✅ Warning about reusing arrays from different datasets

**But we were missing:**
❌ **Warning about slicing pre-defined reference pools**

The LLM pattern was:
- Define a "reference pool" variable for semantic clarity
- Assume slicing `pool[:n]` would always return `n` items
- Not realizing Python slices return `min(len(pool), n)` items

## Fix Applied

Added new anti-pattern #5 to the data generation prompt at line 1430:

```python
5. ❌ **SLICING PRE-DEFINED REFERENCE POOLS** (MOST COMMON ERROR):
   # WRONG: Define small pool, then slice more items than exist
   hss_nodes = ['hss-01', 'hss-02', 'hss-03']  # Only 3 items
   n_hss = 10
   df = pd.DataFrame({'node_id': hss_nodes[:n_hss]})  # ❌ CRASH! Slices only return 3, need 10

   # CORRECT Option 1: Generate exact count inline
   n_hss = 10
   df = pd.DataFrame({'node_id': [f'hss-{i:02d}' for i in range(1, n_hss+1)]})  # ✓ 10 items

   # CORRECT Option 2: Use np.random.choice with replacement to sample from pool
   hss_pool = ['hss-east-01', 'hss-east-02', 'hss-west-01']  # Pool of 3
   n_hss = 10
   df = pd.DataFrame({'node_id': np.random.choice(hss_pool, n_hss)})  # ✓ Samples 10 with replacement

   **NEVER slice a reference pool expecting more items than it contains!**
```

## Files Modified

### 1. `src/framework/module_generator.py` (Prompt Update)
- **Line 1430-1446**: Added anti-pattern #5 with concrete wrong/correct examples
- **Impact**: Future generated modules will avoid this pattern

### 2. `demos/t-mobile_network operations_20251113_181902/data_generator.py` (Manual Fix)
- **Line 80**: Changed from `hss_nodes[:n_hss]` to inline list comprehension
- **Impact**: Immediate fix for this specific demo

## Verification

To verify the fix works for future generations:

1. **Test Prompt Enhancement**: Generate a new demo with reference data requirements
2. **Expected**: LLM should either:
   - Generate IDs inline with exact count: `[f'id-{i}' for i in range(n)]`
   - Use `np.random.choice(pool, n)` to sample with replacement
3. **Should NOT**: Define small pool then slice with `pool[:n]`

## Lessons Learned

### Why This Happens

LLMs often think in terms of "semantic clarity" and prefer:
```python
# Define meaningful variable names
hss_nodes = [list of nodes]
# Use them later
df['node_id'] = hss_nodes[:n]
```

Rather than:
```python
# Inline generation
df['node_id'] = [f'hss-{i}' for i in range(n)]
```

The first pattern LOOKS cleaner but fails when the pool is smaller than needed.

### Solution Strategy

**Explicit anti-patterns work better than general principles**:
- ✅ "NEVER slice a pool: `pool[:n]`" → Concrete, searchable
- ❌ "Make sure arrays match" → Too vague, easily overlooked

**Show both wrong AND correct examples**:
- LLMs learn from contrast
- Seeing the exact buggy pattern helps recognition
- Providing 2 correct alternatives gives flexibility

### Future Prevention

When adding new guidance:
1. ✅ Show EXACTLY the buggy code pattern
2. ✅ Explain WHY it fails (slice returns fewer items)
3. ✅ Provide 2+ correct alternatives
4. ✅ Use strong language ("NEVER", "MOST COMMON ERROR")
5. ✅ Put critical patterns near the top or in caps

## Related Issues

- Empty list errors (already covered in line 298-304)
- Template formatting mismatches (already covered in line 290-296)
- Timestamp generation errors (already covered in line 276-283)

## Testing Checklist

- [ ] Generate new demo with reference datasets
- [ ] Verify no `[:n]` slicing patterns in generated code
- [ ] Verify all DataFrame columns have same length
- [ ] Run demo generation end-to-end without crashes
- [ ] Check if LLM uses inline generation or `np.random.choice` correctly

## Status

✅ **Fix Applied**: Prompt updated in `module_generator.py`
✅ **Immediate Workaround**: Manual fix applied to T-Mobile demo
⏳ **Pending Verification**: Needs testing with new demo generation

---

**Date**: 2024-11-13
**Issue**: Array length mismatch in generated data modules
**Resolution**: Added explicit anti-pattern #5 to data generation prompt
**Files**: `src/framework/module_generator.py`, demo-specific `data_generator.py`
