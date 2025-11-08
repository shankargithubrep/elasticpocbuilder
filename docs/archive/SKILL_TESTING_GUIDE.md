# ES|QL Skill Effectiveness Testing Guide

## Overview

This guide explains how to test whether properly structured Claude Code skills improve ES|QL query generation quality compared to the current approach.

## Background

We discovered that the existing ES|QL skill files (`.claude/skills/esql-*.md`) were using an outdated flat-file format without proper YAML frontmatter. According to Claude Code documentation, skills require:

1. **Directory structure**: `.claude/skills/skill-name/`
2. **SKILL.md file** with YAML frontmatter containing `name` and `description`
3. **Progressive disclosure**: Keep SKILL.md under 500 lines, split detailed content into reference files

The old flat files were likely **not being loaded** by Claude Code, meaning our ES|QL knowledge wasn't being utilized during query generation.

## What We've Built

### New Properly Structured Skills

Located in `.claude/skills/*-new/`:

1. **esql-search-patterns-new/** - Document retrieval, search, RAG queries
2. **esql-advanced-commands-new/** - Analytics, aggregations, LOOKUP JOIN
3. **esql-validator-new/** - Query validation and auto-fixing
4. **agent-builder-new/** - Overall Agent Builder demo creation

Each follows best practices:
- ✅ YAML frontmatter with clear `description` including **when to use**
- ✅ Under 500 lines
- ✅ Clear activation triggers
- ✅ Concise, assumes Claude intelligence
- ✅ Third-person voice

### Test Harness

`tests/test_skill_effectiveness.py` - Compares query generation with/without skills

**Metrics evaluated:**
- **Quality Score**: Ratio of best practices to total patterns (0.0-1.0)
- **Pattern Coverage**: Percentage of expected patterns found (0.0-1.0)
- **Issues Count**: Number of syntax/logic problems detected
- **Best Practices Count**: Number of correct patterns applied

**Test Scenarios:**
1. E-commerce Customer Analytics (should use LOOKUP JOIN, TO_DOUBLE)
2. Healthcare Patient Search (should use MATCH, semantic_text, LIMIT)
3. SaaS Product Analytics (should use DATE_TRUNC, aggregations)

## Running the Tests

### Option 1: Run Full Comparison Report

```bash
# Activate virtual environment
source venv/bin/activate

# Run comparison report
python tests/test_skill_effectiveness.py
```

This will:
1. Generate queries for each scenario WITHOUT skills (baseline)
2. Generate queries for each scenario WITH skills enabled
3. Compare quality metrics
4. Provide recommendation on whether to enable skills

### Option 2: Run Individual Pytest Tests

```bash
# Run baseline tests only
pytest tests/test_skill_effectiveness.py::TestSkillEffectiveness::test_baseline_query_generation -v -s

# Run skill-enabled tests only
pytest tests/test_skill_effectiveness.py::TestSkillEffectiveness::test_skill_enabled_query_generation -v -s

# Run both
pytest tests/test_skill_effectiveness.py -v -s
```

**Note**: Tests require `ANTHROPIC_API_KEY` environment variable set.

## Interpreting Results

### Quality Score Interpretation

- **0.8-1.0**: Excellent - Most best practices followed, few issues
- **0.6-0.8**: Good - Solid patterns, minor issues
- **0.4-0.6**: Fair - Some issues, improvement needed
- **0.0-0.4**: Poor - Major issues, many anti-patterns

### Pattern Coverage Interpretation

- **0.8-1.0**: Excellent - Uses all expected patterns for the use case
- **0.6-0.8**: Good - Most patterns present
- **0.4-0.6**: Fair - Missing some key patterns
- **0.0-0.4**: Poor - Missing most expected patterns

### Comparison Outcomes

The test will recommend one of three outcomes:

#### ✅ RECOMMEND: Enable Skills
**When**: `avg_skill_quality > avg_baseline_quality + 0.1`
- Skills demonstrably improve query quality
- **Action**: Rename `-new` directories to remove suffix, archive old flat files

#### ⚖️ NEUTRAL: No Significant Impact
**When**: `abs(avg_skill_quality - avg_baseline_quality) < 0.1`
- No clear benefit or harm from skills
- **Action**: Consider other factors (token usage, maintenance burden)

#### ❌ CAUTION: Skills May Reduce Quality
**When**: `avg_skill_quality < avg_baseline_quality - 0.1`
- Current baseline performs better than skills
- **Action**: Investigate why skills hurt performance, refine skill content

## Common Issues Detected

The test harness automatically checks for:

### Syntax Issues
- ❌ Division without `TO_DOUBLE` (returns 0 for integers)
- ❌ `LOOKUP JOIN` after `STATS` (fields lost)
- ❌ `DATE_EXTRACT` with lowercase units or wrong parameter order
- ❌ Unsupported functions (`RANK()`, `LAG()`, `SEMANTIC()`, `ENRICH`)

### Search Best Practices
- ❌ `MATCH` without `METADATA _score` (no relevance scoring)
- ❌ Search query without `LIMIT` (unbounded results)

### Expected Patterns
Based on use case, checks for:
- **Analytics queries**: `LOOKUP JOIN`, `TO_DOUBLE`, `STATS`, `DATE_TRUNC`
- **Search queries**: `MATCH`, `semantic_text`, `LIMIT`, `METADATA _score`

## Next Steps Based on Results

### If Skills Improve Quality (✅ RECOMMEND)

1. **Activate the new skills:**
   ```bash
   cd .claude/skills
   mv esql-search-patterns-new esql-search-patterns-skill
   mv esql-advanced-commands-new esql-advanced-commands-skill
   mv esql-validator-new esql-validator-skill
   mv agent-builder-new agent-builder-skill
   ```

2. **Archive old flat files:**
   ```bash
   mkdir -p archive
   mv esql-*.md agent-builder.md archive/
   ```

3. **Update module_generator.py** to explicitly reference skills in prompts

4. **Re-run integration tests** to ensure no regressions

### If Skills Show No Impact (⚖️ NEUTRAL)

1. **Investigate why skills aren't activating:**
   - Check description clarity
   - Add more specific activation triggers
   - Test with different model versions (Haiku, Sonnet, Opus)

2. **Consider token cost:**
   - Skills add to context window
   - If no quality benefit, may not be worth the cost

3. **Gather more data:**
   - Run tests on more diverse scenarios
   - Test with actual customer demo contexts

### If Skills Hurt Quality (❌ CAUTION)

1. **Analyze why:**
   - Are skills too prescriptive?
   - Do they conflict with other system prompts?
   - Is the content misleading or outdated?

2. **Refine skill content:**
   - Simplify instructions
   - Remove ambiguous guidance
   - Add more examples

3. **Re-test:**
   - Run comparison again after refinements
   - Test individual skills in isolation

## Maintenance

Once skills are enabled:

1. **Keep SKILL.md under 500 lines** - split detailed content into reference files
2. **Update descriptions** when adding new capabilities
3. **Add test scenarios** for new use cases
4. **Re-run effectiveness tests** quarterly or after major updates

## Reference

- **Claude Code Skills Docs**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills
- **Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Test Suite**: `tests/test_skill_effectiveness.py`
- **New Skills**: `.claude/skills/*-new/`

---

**Last Updated**: 2025-10-31
