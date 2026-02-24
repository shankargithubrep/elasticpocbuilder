# Prompt Contamination Issue & Fix

## The Problem: Template Examples Leak Into Generated Output

### What Happened

**V2 Template Enhancement** (prompt_templates_v2.py) added concrete examples to help the LLM create realistic values:

```markdown
**Value Examples**: List 3-5 REAL example values for each categorical field

✅ DO:
- `specialty_description`: "Cardiology", "Orthopedic Surgery", "Pediatrics", "Family Medicine", "Dermatology"
- `network_plans`: "UnitedHealthcare Choice Plus", "Aetna PPO", "Blue Cross Blue Shield", "Cigna Open Access"
- `state`: "CA", "NY", "TX", "FL", "IL"
```

**Unintended Consequence**: These example values contaminated every expansion!

```
User Input 1: "Healthcare provider search focusing on cardiology"
Expanded Output: Uses Cardiology ✓ + Bariatric Surgery ✗ + Orthopedics ✗ + Pediatrics ✗

User Input 2: "Healthcare provider search for family medicine"
Expanded Output: Uses Family Medicine ✓ + Bariatric Surgery ✗ + Cardiology ✗ + Orthopedics ✗

User Input 3: "Healthcare search for orthopedic surgeons"
Expanded Output: Uses Orthopedic ✓ + Bariatric Surgery ✗ + Cardiology ✗ + Pediatrics ✗

User Input 4: "Healthcare general provider directory"
Expanded Output: Uses Bariatric Surgery ✗ + Cardiology ✗ + Orthopedics ✗ + Pediatrics ✗
```

**Result**: 4 demos in a row, all containing "bariatric surgery" even though only the template examples mentioned it!

### Why This Is A Critical Issue

1. **Example Leakage**: Template examples become output instead of user-derived values
2. **Reduced Variety**: Same concrete examples appear in every demo
3. **Ignores User Intent**: User says "cardiology" but gets entire example list
4. **False Positives**: "Bariatric surgery" appears even when user never mentioned it
5. **Repetitive Demos**: All demos from same domain look identical

### Root Cause Analysis

**Intent**: Help LLM create realistic values instead of placeholders like "Specialty A", "Specialty B"

**Implementation**: Showed concrete examples: "Cardiology", "Orthopedic Surgery", "Pediatrics"

**Failure Mode**: LLM interpreted examples as "use these specific values" instead of "use this pattern to create domain-appropriate values from user input"

This is a classic **prompt contamination** problem where guidance artifacts leak into generation.

## The Fix: Descriptive Guidance Instead of Concrete Examples

### V3 Approach (prompt_templates_v3.py)

Instead of showing concrete domain values, V3 provides **meta-guidance** about value creation:

#### Before (V2 - Contaminating)
```markdown
✅ DO:
- `specialty_description`: "Cardiology", "Orthopedic Surgery", "Pediatrics"
- `network_plans`: "UnitedHealthcare Choice Plus", "Aetna PPO"
```

#### After (V3 - Non-Contaminating)
```markdown
* **Value Diversity Requirements**:
  - `specialty_description`: Need 8-10 medical specialties. Include the user's mentioned focus (cardiology) and diversify with common related and unrelated specialties (e.g., other cardiovascular, primary care, surgical, diagnostic)
  - `network_plans`: Need 4-6 insurance network names. Use networks realistic for the user's geographic market and payer mix
```

### Key Differences

| Aspect | V2 (Contaminating) | V3 (Non-Contaminating) |
|--------|-------------------|------------------------|
| **Examples** | Concrete values: "Cardiology", "Bariatric Surgery" | Descriptive categories: "cardiovascular, primary care, surgical" |
| **Instruction** | "Use realistic values like these" | "Include user's mentioned terms plus related categories" |
| **Source Priority** | Template examples first | User input first, template guidance second |
| **Variety** | Same examples in every demo | Different values per demo based on user input |
| **Leakage Risk** | High - examples become defaults | Low - guidance doesn't specify exact values |

### V3 Principles

1. **Extract from User Input FIRST**
   ```markdown
   If user mentions specific entities (e.g., "cardiology", "fishing gear"), use those
   If user describes a domain (e.g., "healthcare providers"), infer appropriate categories
   ```

2. **Describe VALUE SPACE, not specific values**
   ```markdown
   ✅ GOOD: "Need 8-10 distinct medical specialties relevant to user's focus areas"
   ❌ BAD: "Cardiology, Orthopedic Surgery, Pediatrics" (these leak)
   ```

3. **Reference User Context Explicitly**
   ```markdown
   "Include the user's mentioned specialty (cardiology) plus 4-6 related specialties"
   ```

4. **Use FORMAT examples, not CONTENT examples**
   ```markdown
   Example format: "value_1", "value_2", "value_3" (FORMAT only)
   Actual values should be: [derived from user input]
   ```

## Testing The Fix

### Test Case 1: User Mentions Cardiology
```
Input: "Healthcare provider search focusing on cardiology"

V2 Output (Contaminated):
- specialty_description values: "Cardiology", "Bariatric Surgery", "Orthopedic Surgery", "Pediatrics"
  (All 4 specialties from template examples)

V3 Output (User-Derived):
- specialty_description values: "Cardiology", "Interventional Cardiology", "Electrophysiology", "Vascular Surgery"
  (Cardiology from user + related cardiovascular specialties)
```

### Test Case 2: User Mentions Orthopedics
```
Input: "Provider directory for orthopedic surgeons"

V2 Output (Contaminated):
- specialty_description values: "Orthopedic Surgery", "Cardiology", "Bariatric Surgery", "Pediatrics"
  (Ortho from user + all template examples)

V3 Output (User-Derived):
- specialty_description values: "Orthopedic Surgery", "Sports Medicine", "Joint Replacement", "Spine Surgery"
  (Orthopedics from user + related musculoskeletal specialties)
```

### Test Case 3: User Doesn't Mention Specific Specialty
```
Input: "General healthcare provider directory"

V2 Output (Contaminated):
- specialty_description values: "Cardiology", "Orthopedic Surgery", "Bariatric Surgery", "Pediatrics", "Dermatology"
  (Entire template example list)

V3 Output (User-Derived):
- specialty_description values: "Family Medicine", "Internal Medicine", "Pediatrics", "Obstetrics/Gynecology", "General Practice"
  (Common primary care specialties, no bariatric surgery!)
```

### Expected Behavior Change

**V2 (Contaminated)**:
- ✗ "Bariatric surgery" appears in 4/4 healthcare demos
- ✗ Same 5 specialties in every healthcare demo
- ✗ User-mentioned terms mixed with template defaults

**V3 (User-Derived)**:
- ✓ "Bariatric surgery" only appears if user mentions it
- ✓ Different specialties in each demo based on user's focus
- ✓ User-mentioned terms + contextually related terms

## Additional V3 Improvements

### 1. Common Filter Combinations
**V2**: Showed concrete scenario:
```
"Find cardiologists in California accepting new patients on UnitedHealthcare Choice Plus"
```

**V3**: Describes pattern without hardcoding:
```
"[Describe realistic user search behavior in their domain]"
- Combines: [list 3-4 field names that logically filter together]
- Guidance for data generation: Ensure [X%] of documents have combinations populated
```

**Result**: Each demo gets scenarios derived from its own context, not template examples.

### 2. Use Case Example Queries
**V2**: Showed concrete examples:
```
✅ "Find cardiologists near ZIP code 90210 accepting UnitedHealthcare"
❌ "Find [resource type] near [location] with [attributes]"
```

**V3**: Shows format only:
```
Format: "[Search for/Find/Retrieve] [entity from user's domain] [with/near] [criteria from user's context]"

CRITICAL: Use terminology from USER INPUT, not template examples
```

**Result**: Query examples use user's own entities, not template contamination.

## Validation

### Before Deployment, Test:
1. ✅ Same healthcare prompt 3 times → should get DIFFERENT specialties each time
2. ✅ Cardiology-focused prompt → should have cardiology-related specialties (not bariatric)
3. ✅ Retail prompt → should have retail categories (not healthcare terms at all)
4. ✅ No hardcoded values from template should appear unless user mentioned them

### After Deployment, Monitor:
1. ✅ Term frequency: "bariatric surgery" should appear <5% of healthcare demos (not 100%)
2. ✅ Value variety: No single specialty should dominate >30% of demos
3. ✅ User alignment: Values in output should correlate with user input terms

## Rollback Plan

If V3 causes issues:
1. **Immediate**: Switch back to original `SEARCH_EXPANSION_TEMPLATE` (no examples at all)
2. **Investigation**: Check if guidance is too vague, causing placeholder generation
3. **Iteration**: Add more specific descriptive guidance without concrete examples

## Lessons Learned

### What We Tried To Solve
- **Problem**: LLM creates placeholder values like "Specialty A", "Network 1"
- **Solution Attempt (V2)**: Show concrete examples like "Cardiology", "UnitedHealthcare"
- **Outcome**: Fixed placeholders but created contamination

### What We Actually Solved
- **Problem**: Template examples contaminate all output
- **Solution (V3)**: Descriptive guidance + user extraction priority + format examples only
- **Outcome**: User-derived values without placeholders or contamination

### General Principle
**Prompt Engineering Anti-Pattern**:
> "If you want realistic values, show realistic examples"

**Better Pattern**:
> "If you want realistic values, describe the VALUE SPACE and prioritize USER INPUT extraction"

## Recommendation

**Deploy V3 with A/B testing**:
1. Run 3-5 demos with V2 (contaminated)
2. Run 3-5 demos with V3 (non-contaminated) using SAME user prompts
3. Compare:
   - Value variety across demos
   - User term alignment
   - Frequency of specific terms (e.g., "bariatric")
4. Decision based on data

**Expected Outcome**: V3 should show:
- Higher value variety between demos
- Better alignment with user terminology
- Lower frequency of any single term across demos
- No "bariatric surgery" contamination

---

## Summary

**Problem**: V2 template improvements caused prompt contamination where concrete examples leaked into every generated demo.

**Root Cause**: LLM interpreted example values as defaults instead of format guidance.

**Solution**: V3 uses descriptive guidance about value spaces without concrete domain-specific examples.

**Result**: Each demo should derive values from user input instead of template contamination.
