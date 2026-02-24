# Search Expansion Template Improvements

## Executive Summary

The original `SEARCH_EXPANSION_TEMPLATE` is **good and well-structured**, but can be enhanced to address the root causes of 0-result queries we just fixed with query refinement.

**Key Issue**: The expansion template doesn't strongly enough guide the LLM to create:
1. **Realistic field value examples** (leads to placeholder values like "1234567890")
2. **Common filter combinations** (leads to invalid multi-criteria queries)
3. **Concrete use case examples** (uses `[placeholders]` instead of actual terms)

## What We Already Have ✅

The current search template (`prompt_templates.py:195-342`) already:
- ✅ Separates search from observability content
- ✅ Focuses on document collections and field types
- ✅ Covers search strategies (fuzzy, semantic, hybrid)
- ✅ Includes warnings about placeholders (lines 238, 287)
- ✅ Has early demo type detection in `expand_brief_prompt()`

**The architecture is solid!** This is more about **strengthening guidance** than fixing broken design.

## Specific Improvements Proposed

### 1. **Realistic Field Value Examples** (NEW Section)

**Problem**: Current template doesn't ask for example values for keyword fields.

**Impact**: LLM doesn't provide guidance to data generator, which then creates arbitrary values. Later, query strategy generator uses placeholder values that don't exist in the data.

**Current Template** (line 250-251):
```
* **Key Search Fields**:
  - `field_name` (field_type): Description and search behavior
```

**Enhanced Template**:
```
* **Key Search Fields**:
  - `field_name` (field_type): Description and search behavior
* **Value Examples**: List 3-5 REAL example values for each categorical field

**CRITICAL: Realistic Field Values**

For each `keyword` field, provide 3-5 REALISTIC example values:

✅ DO:
- `specialty_description`: "Cardiology", "Orthopedic Surgery", "Pediatrics"
- `network_plans`: "UnitedHealthcare Choice Plus", "Aetna PPO", "Blue Cross"
- `state`: "CA", "NY", "TX", "FL", "IL"

❌ DON'T:
- `specialty`: "Specialty A", "Specialty B", "Specialty C"
- `network`: "Network 1", "Network 2"
```

**Why It Helps**:
- Data generator gets realistic values to include in generated data
- Query strategy generator can reference these values instead of placeholders
- Reduces need for query refinement to fix invalid values

### 2. **Common Filter Combinations** (NEW Section)

**Problem**: Current template doesn't ask LLM to describe realistic multi-criteria search scenarios.

**Impact**: Query strategy generator creates queries with multiple AND conditions where the combination of values doesn't exist in the data (e.g., `network == "X" AND state == "Y"` where no documents have both).

**Current Template**: No guidance on filter combinations

**Enhanced Template**:
```
**Common Filter Combinations**

For each document collection, describe 2-3 realistic search scenarios where users combine multiple filters:

**Common Search Scenarios**:
1. "Find cardiologists in California accepting new patients on UnitedHealthcare Choice Plus"
   - Combines: specialty_description, state, accepting_new_patients, network_plans
   - Why realistic: Callers often have specific insurance and location requirements

2. "Locate orthopedic surgeons near ZIP 90210 with ratings above 4.0"
   - Combines: specialty_description, geo_location (near 90210), patient_rating
   - Why realistic: Members want quality providers nearby
```

**Why It Helps**:
- Data generator understands which field combinations should co-occur
- Query strategy generator knows realistic multi-criteria query patterns
- Data profiling finds these combinations in sample_combinations
- Query refinement uses valid combinations instead of arbitrary replacements

### 3. **Concrete Use Case Examples** (ENHANCED Section)

**Problem**: Current template still uses placeholder examples (lines 284-287):
```
- Example: "Find [resource type] near [location] with [attributes]"
- Example: "Is [specific item] covered/available for [conditions]?"

⚠️ Replace placeholders with terms from the customer's actual domain.
```

**Issue**: Warning is good but still shows placeholder format, which LLM might copy.

**Enhanced Template**:
```
**Example Query Pattern**: A CONCRETE, REALISTIC example query (NO PLACEHOLDERS)

🚨 USE ACTUAL EXAMPLES FROM YOUR DOMAIN:
✅ GOOD: "Find cardiologists near ZIP code 90210 accepting new patients on UnitedHealthcare"
✅ GOOD: "Is bariatric surgery covered for patients with BMI over 40 and diabetes?"
✅ GOOD: "Search knowledge base for 'how to reset password after account lockout'"

❌ BAD: "Find [resource type] near [location] with [attributes]"
❌ BAD: "Is [specific item] covered/available for [conditions]?"
❌ BAD: "Search for [entity] with [criteria]"
```

**Why It Helps**:
- Shows LLM what "good" looks like with positive examples first
- Explicitly marks bad examples with ❌
- Reinforces no-placeholder rule with concrete alternatives

### 4. **Multi-Criteria Use Case Requirement** (ENHANCED Guideline)

**Problem**: Current guidelines don't explicitly require a multi-criteria filtering use case.

**Current Template** (line 297-307):
```
**Use Case Guidelines:**
- Include at least one fuzzy/typo-tolerant search use case
- Include at least one semantic/natural language use case
- Include at least one use case combining multiple search strategies
```

**Enhanced Template**:
```
**Use Case Guidelines:**
- Include at least one fuzzy/typo-tolerant search use case
- Include at least one semantic/natural language use case
- Include at least one **multi-criteria filtering** use case (combining 3+ filters)
- Use CONCRETE examples with actual values from your domain (no placeholders!)
```

**Why It Helps**:
- Ensures expansion covers the complex query patterns we just enhanced refinement for
- Forces LLM to think through realistic filter combinations
- Tests that the expansion provides enough detail for multi-field queries

## Comparison Table

| Aspect | Current Template | Enhanced Template | Impact on Query Refinement |
|--------|-----------------|-------------------|---------------------------|
| **Field Values** | Generic descriptions | 3-5 concrete examples per field | ✅ Reduces placeholder value issues |
| **Filter Combinations** | Not mentioned | 2-3 realistic scenarios | ✅ Reduces invalid combination issues |
| **Use Case Examples** | Shows placeholders (with warning) | Shows concrete examples only | ✅ Prevents placeholder propagation |
| **Multi-Criteria Queries** | Implicit | Explicit requirement | ✅ Ensures comprehensive coverage |
| **Validation Checklist** | 7 items | 11 items (4 new) | ✅ Stronger quality control |

## Example Expansion Output

### Current Template Output (Good but Generic)
```markdown
### Provider Directory
* **Purpose**: Searchable directory of healthcare providers
* **Key Search Fields**:
  - `provider_name` (text): Full name with fuzzy matching
  - `specialty` (keyword): Medical specialty for filtering
  - `network_status` (keyword): In-network or out-of-network
  - `state` (keyword): Provider state for filtering
```

### Enhanced Template Output (Concrete and Actionable)
```markdown
### Provider Directory
* **Purpose**: Searchable directory of healthcare providers for member services
* **Key Search Fields**:
  - `provider_name` (text): Full name with fuzzy matching for typo tolerance
  - `specialty_description` (keyword): Medical specialty for exact filtering
  - `network_plans` (keyword): Insurance plan participation
  - `state` (keyword): Two-letter state code
  - `accepting_new_patients` (boolean): Current acceptance status

* **Value Examples**:
  - `specialty_description`: "Cardiology", "Orthopedic Surgery", "Pediatrics", "Family Medicine", "Dermatology"
  - `network_plans`: "UnitedHealthcare Choice Plus", "Aetna PPO", "Blue Cross Blue Shield", "Cigna Open Access"
  - `state`: "CA", "NY", "TX", "FL", "IL"
  - `accepting_new_patients`: true, false

* **Common Search Scenarios**:
  1. "Find cardiologists in California accepting new patients on UnitedHealthcare Choice Plus"
     - Combines: specialty_description, state, accepting_new_patients, network_plans
     - Why realistic: Members call with specific insurance and location needs
```

## Implementation Path

### Option 1: Gradual Replacement (Recommended)
1. Keep current `SEARCH_EXPANSION_TEMPLATE` as default
2. Add enhanced version as `SEARCH_EXPANSION_TEMPLATE_V2` (already created in `prompt_templates_v2.py`)
3. A/B test both templates on a few demos
4. Compare quality of generated data and queries
5. Switch default if V2 shows clear improvement

### Option 2: Direct Replacement
1. Replace `SEARCH_EXPANSION_TEMPLATE` in `prompt_templates.py` with enhanced version
2. Test with existing use cases to ensure no regressions
3. Monitor for improvement in query success rates

### Option 3: Hybrid Approach
1. Extract the **new sections** (Value Examples, Common Filter Combinations) as separate guidance
2. Inject them into current template at appropriate locations
3. Keep rest of template unchanged

## Testing Recommendations

**Before Deployment**:
1. ✅ Test expansion with brief healthcare prompt (provider search)
2. ✅ Test expansion with brief e-commerce prompt (product catalog)
3. ✅ Verify expanded output includes realistic field values
4. ✅ Verify expanded output includes multi-criteria scenarios

**After Deployment**:
1. ✅ Monitor query success rate (% returning >0 results)
2. ✅ Track query refinement stats (% of queries needing refinement)
3. ✅ Compare before/after on same prompts

**Success Metrics**:
- **Query success rate**: Should increase from ~60% to >85%
- **Refinement rate**: Should decrease from ~70% to <30%
- **Placeholder value rate**: Should decrease from ~40% to <5%

## Risk Assessment

**Low Risk Changes** ✅:
- Adding new sections (Value Examples, Common Scenarios)
- Strengthening existing warnings
- Expanding validation checklist

**Medium Risk Changes** ⚠️:
- Changing example format (from placeholders to concrete)
- Adding explicit requirements

**Mitigation**:
- Keep current template as fallback
- Version the templates (V1, V2)
- Test both templates in parallel
- Easy rollback if issues arise

## Recommendation

**Proceed with Option 1: Gradual Replacement**

**Rationale**:
1. Current template works well for observability (don't break it!)
2. Enhanced version addresses specific search query challenges
3. A/B testing lets us validate improvements objectively
4. Low risk, easy rollback

**Next Steps**:
1. ✅ Created `prompt_templates_v2.py` with enhanced template
2. ⏭️ Add config option to select template version
3. ⏭️ Test V2 with 3-5 search demos
4. ⏭️ Compare query success rates V1 vs V2
5. ⏭️ Decision: Replace or keep both

---

## Conclusion

The current search expansion template is **good**, but the enhanced version should **reduce the need for query refinement** by:
1. Providing realistic field value examples upfront
2. Describing common filter combinations
3. Using concrete examples instead of placeholders

This aligns the expansion → data generation → query strategy → query refinement pipeline to work more smoothly together.
