# Enhanced Mode × Dataset Size Interaction

## Feature Overview

The **Dataset Size** slider and **Enhanced Mode** toggle control **different aspects** of data generation:

| Feature | What it Controls | Values |
|---------|-----------------|---------|
| **Dataset Size** | Number of records | Small (1-3k), Medium (5-10k), Large (15-30k) |
| **Enhanced Mode** | Data distribution | OFF (uniform random), ON (realistic clustering) |

These features are **orthogonal** - they work independently but combine for different effects.

---

## Interaction Matrix

### Small Dataset (1,000-3,000 records)

| Mode | Data Pattern | Query Results | Best For |
|------|-------------|---------------|----------|
| **Standard** | Uniform random distribution | Sparse: 1-2 events per bucket ❌ | Quick testing, not production |
| **Enhanced** | Clustered with incidents | Moderate: 5-15 events per bucket ✅ | Quick demos, proof of concept |

**Enhanced Mode Impact:**
- ✅ Significantly better than standard small
- ⚠️ Percentiles less stable (smaller sample)
- ⚠️ UI shows: "💡 **Tip:** Enhanced mode works best with Medium or Large dataset sizes"

**Math:**
```
Standard: 2000 records ÷ 100 cells ÷ 90 days = ~1-2 per bucket
Enhanced: 2000 × 70% clustered ÷ 10 incidents ÷ 15 cells = ~10 per bucket during incidents
```

---

### Medium Dataset (5,000-10,000 records) ⭐ RECOMMENDED

| Mode | Data Pattern | Query Results | Best For |
|------|-------------|---------------|----------|
| **Standard** | Uniform random distribution | Sparse: 2-5 events per bucket ❌ | Not recommended |
| **Enhanced** | Clustered with incidents | Good: 20-50 events per bucket ✅ | **Production demos, customer presentations** |

**Enhanced Mode Impact:**
- ✅ **SWEET SPOT** for enhanced mode
- ✅ Stable percentiles (large enough sample)
- ✅ Fast generation (not too large)
- ✅ UI shows: "✅ **Optimal:** Medium size is perfect for enhanced mode!"

**Math:**
```
Standard: 7500 records ÷ 100 cells ÷ 90 days = ~3-4 per bucket
Enhanced: 7500 × 70% clustered ÷ 10 incidents ÷ 15 cells = ~35 per bucket during incidents
```

---

### Large Dataset (15,000-30,000 records)

| Mode | Data Pattern | Query Results | Best For |
|------|-------------|---------------|----------|
| **Standard** | Uniform random distribution | Moderate: 5-12 events per bucket ⚠️ | Large scale demos |
| **Enhanced** | Clustered with incidents | Excellent: 50-150 events per bucket ✅ | Enterprise demos, detailed analysis |

**Enhanced Mode Impact:**
- ✅ **EXCELLENT** results
- ✅ Very stable percentiles
- ✅ Rich analytics queries
- ⚠️ Longer generation time (30-60 seconds)
- ✅ UI shows: "✅ **Excellent:** Large datasets provide the most stable percentile-based queries!"

**Math:**
```
Standard: 20000 records ÷ 100 cells ÷ 90 days = ~8-10 per bucket
Enhanced: 20000 × 70% clustered ÷ 10 incidents ÷ 15 cells = ~93 per bucket during incidents
```

---

## Decision Guide

### Use Case: Quick Testing / Proof of Concept
**Recommendation:** Small + Enhanced
- Fast generation (~10 seconds)
- Adequate clustering
- Good enough for testing

### Use Case: Customer Demo / Sales Presentation
**Recommendation:** Medium + Enhanced ⭐
- Balanced generation time (~20 seconds)
- Stable percentiles
- Professional results

### Use Case: Enterprise Demo / Detailed Analysis
**Recommendation:** Large + Enhanced
- Comprehensive data (~60 seconds)
- Very stable percentiles
- Rich analytics

### Use Case: Legacy Workflows / Quick & Dirty
**Recommendation:** Small + Standard (not recommended for analytics)
- Fastest generation (~5 seconds)
- Uniform random data
- Queries may return 0 results

---

## Why We DON'T Override the Slider

### Reasons to Keep Them Independent:

1. **Flexibility**: Users might want quick testing with small + enhanced
2. **User Control**: Don't be prescriptive, offer guidance instead
3. **Valid Use Cases**: Small + enhanced is better than small + standard
4. **Progressive Enhancement**: Users can see the difference between sizes

### What We DO Instead:

**Smart Guidance** - The UI shows contextual messages:

- **Small + Enhanced**:
  ```
  💡 Tip: Enhanced mode works best with Medium or Large dataset sizes
  for more stable percentile calculations.
  ```

- **Medium + Enhanced**:
  ```
  ✅ Optimal: Medium size is perfect for enhanced mode!
  ```

- **Large + Enhanced**:
  ```
  ✅ Excellent: Large datasets provide the most stable percentile-based queries!
  ```

This approach **educates** without **restricting**.

---

## Technical Details: How Enhanced Mode Scales

### Clustering Parameters (Same for All Sizes)

```python
baseline_ratio = 0.3      # 30% of events are baseline (random)
incident_ratio = 0.7      # 70% of events are clustered
num_incidents = 10         # Number of incident periods
affected_cells = 15        # Cells affected per incident
```

### Why This Works at All Scales

**Small Dataset (2,000 records):**
```
Incident events = 2000 × 0.7 = 1400
Events per incident = 1400 ÷ 10 = 140
Events per cell = 140 ÷ 15 = ~10 per bucket ✓
```

**Medium Dataset (7,500 records):**
```
Incident events = 7500 × 0.7 = 5250
Events per incident = 5250 ÷ 10 = 525
Events per cell = 525 ÷ 15 = ~35 per bucket ✓
```

**Large Dataset (20,000 records):**
```
Incident events = 20000 × 0.7 = 14000
Events per incident = 14000 ÷ 10 = 1400
Events per cell = 1400 ÷ 15 = ~93 per bucket ✓
```

The clustering logic **scales naturally** with dataset size because we're dividing by constants. More records = more events per incident, which is exactly what we want!

---

## Percentile Stability by Size

### p90 Threshold Stability

| Size | Total Records | p90 Count | Stability |
|------|--------------|-----------|-----------|
| Small | 2,000 | 200 | Moderate (±5%) |
| Medium | 7,500 | 750 | Good (±2%) |
| Large | 20,000 | 2,000 | Excellent (±1%) |

**Why This Matters:**
- Smaller samples have more variance in percentile calculations
- With 2,000 records, p90 might vary by 5% between runs
- With 20,000 records, p90 is very stable

**Impact on Queries:**
- Small: Threshold might be 0.80 or 0.84 (varies)
- Large: Threshold consistently 0.82 (stable)

For demos, **medium is stable enough** for professional results.

---

## Summary

### ✅ Keep Features Independent

- Dataset Size and Enhanced Mode control different aspects
- They complement each other without conflict
- All combinations are valid use cases

### ✅ Provide Smart Guidance

- UI shows contextual recommendations
- Users understand trade-offs
- Freedom to choose based on their needs

### ✅ Optimal Combination

**Medium Dataset + Enhanced Mode** is the sweet spot:
- Fast enough for interactive demos (~20 seconds)
- Large enough for stable percentiles
- Good clustering for realistic patterns
- Professional results for customer presentations

### 🎯 Recommendation for Most Users

```
Dataset Size: Medium
Enhanced Mode: ON
```

This provides the best balance of generation speed, data quality, and query effectiveness.