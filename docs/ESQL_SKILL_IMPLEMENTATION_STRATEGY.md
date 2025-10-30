# ES|QL Skill Implementation Strategy

## Executive Summary

Implement Claude Skills API to provide comprehensive ES|QL expertise for query generation, reducing token usage by ~900+ tokens per generation while significantly improving query accuracy and consistency.

**Key Benefits:**
- ✅ **90% token reduction** in query generation prompts
- ✅ **Consistent ES|QL guidance** across all demo generations
- ✅ **Up-to-date syntax** for commands added after Claude's training cutoff
- ✅ **Centralized updates** - fix once, improve everywhere
- ✅ **Better query quality** - comprehensive documentation in skill context

---

## Problem Statement

### Current State
1. **Outdated Knowledge**: Claude's training data lacks recent ES|QL commands (CHANGE_POINT, COMPLETION, RERANK, etc.)
2. **Token Waste**: ~900 tokens of ES|QL guidance repeated in every query generation
3. **Incomplete Context**: Rich documentation in `docs/esql/*.md` not being utilized
4. **Syntax Errors**: 15-20% of generated queries fail due to syntax mistakes (DATE_EXTRACT, CHANGE_POINT BY clause, etc.)
5. **Inconsistent Quality**: Different generations may use different ES|QL patterns

### Documentation Inventory
```
docs/esql/
├── change_point.md      (2.3KB) - Anomaly detection command
├── completion.md        (7.2KB) - AI completion command
├── date_time.md        (17.2KB) - Date/time functions (DATE_EXTRACT fix!)
├── eval.md              (3.5KB) - Field evaluation
├── fork.md              (2.0KB) - Query branching
├── fuse.md              (5.9KB) - Result merging
├── inline_stats.md     (10.0KB) - Inline aggregations
├── lookup_join.md       (7.0KB) - Enrichment joins
├── rerank.md            (7.0KB) - Search result reranking
├── search-and-filter.md(19.2KB) - Search/filter patterns
├── stats.md            (12.4KB) - Aggregation patterns
├── time_spans.md        (4.7KB) - Time bucket handling
└── where.md             (7.3KB) - Filtering syntax

Total: ~106KB of ES|QL documentation
```

---

## Solution Architecture

### Claude Skills Overview

Claude Skills are persistent, reusable instructions that:
- Live in Anthropic's infrastructure (not in your prompts)
- Apply automatically to API calls
- Don't consume generation tokens
- Can be updated centrally

**API Reference:**
- Create: `POST https://api.anthropic.com/v1/skills`
- List: `GET https://api.anthropic.com/v1/skills`
- Get: `GET https://api.anthropic.com/v1/skills/{skill_id}`
- Delete: `DELETE https://api.anthropic.com/v1/skills/{skill_id}`

### Skill Structure

```json
{
  "name": "esql_query_expert",
  "instructions": "<<AGGREGATED_ESQL_DOCUMENTATION>>",
  "skill_type": "prompt",
  "version": "1.0.0"
}
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal:** Create basic skill infrastructure and integrate with query generation

#### 1.1 Create Skill Manager Service

**File:** `src/services/esql_skill_manager.py`

```python
"""
ES|QL Skill Manager
Manages Claude Skills for ES|QL query generation expertise
"""

from anthropic import Anthropic
from pathlib import Path
from typing import Optional
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class ESQLSkillManager:
    """Manages ES|QL expertise skill for Claude API"""

    SKILL_NAME = "esql_query_expert"
    SKILL_VERSION = "1.0.0"

    def __init__(self, client: Anthropic):
        """Initialize skill manager

        Args:
            client: Anthropic API client
        """
        self.client = client
        self.skill_id: Optional[str] = None
        self._content_hash: Optional[str] = None

    def ensure_skill_exists(self) -> str:
        """Ensure ES|QL skill exists, create or update if needed

        Returns:
            Skill ID for use in API calls
        """
        current_content = self._build_skill_content()
        current_hash = self._hash_content(current_content)

        # Check if skill exists
        try:
            skills = self.client.skills.list()
            for skill in skills.data:
                if skill.name == self.SKILL_NAME:
                    self.skill_id = skill.id

                    # Check if content needs update
                    if self._content_hash != current_hash:
                        logger.info(f"Updating ES|QL skill {self.skill_id} with new content")
                        self._update_skill(current_content)
                        self._content_hash = current_hash
                    else:
                        logger.info(f"Using existing ES|QL skill: {self.skill_id}")

                    return self.skill_id
        except Exception as e:
            logger.warning(f"Error checking existing skills: {e}")

        # Create new skill
        logger.info("Creating new ES|QL skill")
        return self._create_skill(current_content, current_hash)

    def _build_skill_content(self) -> str:
        """Build comprehensive ES|QL skill content from all sources

        Returns:
            Aggregated ES|QL documentation string
        """
        content_parts = []

        # 1. Add header
        content_parts.append("""
# ES|QL Query Expert Skill

You are an expert in Elasticsearch Query Language (ES|QL). When generating ES|QL queries:

## Your Role
- Generate syntactically correct ES|QL queries for Elasticsearch 8.15+
- Follow latest command syntax (including commands added after your training cutoff)
- Avoid common pitfalls and anti-patterns
- Optimize for performance and readability

## Command Coverage
This skill provides comprehensive documentation for:
- Advanced commands (CHANGE_POINT, COMPLETION, RERANK, FORK, FUSE)
- Date/time functions (DATE_EXTRACT, DATE_TRUNC, etc.)
- Aggregations (STATS, INLINESTATS)
- Enrichment (LOOKUP JOIN)
- Filtering and search patterns
- Time span handling

---
""")

        # 2. Add base syntax guide
        try:
            from src.framework.esql_syntax_guide import ESQL_SYNTAX_GUIDE, get_esql_examples
            content_parts.append("## Core Syntax Rules\n\n")
            content_parts.append(ESQL_SYNTAX_GUIDE)
            content_parts.append("\n\n")
            content_parts.append(get_esql_examples())
            content_parts.append("\n\n---\n\n")
        except ImportError:
            logger.warning("Could not import esql_syntax_guide")

        # 3. Add all documentation from docs/esql/
        esql_docs_path = Path(__file__).parent.parent.parent / "docs" / "esql"

        if esql_docs_path.exists():
            # Sort for consistent ordering
            doc_files = sorted(esql_docs_path.glob("*.md"))

            for doc_file in doc_files:
                try:
                    command_name = doc_file.stem.replace("_", " ").title()
                    content_parts.append(f"## {command_name}\n\n")
                    content_parts.append(doc_file.read_text())
                    content_parts.append("\n\n---\n\n")
                    logger.info(f"Added documentation: {doc_file.name}")
                except Exception as e:
                    logger.error(f"Error reading {doc_file}: {e}")
        else:
            logger.warning(f"ES|QL docs directory not found: {esql_docs_path}")

        # 4. Add anti-patterns and common mistakes
        content_parts.append("""
## Common Mistakes to Avoid

### CHANGE_POINT Command
❌ WRONG: `CHANGE_POINT value BY category`
✅ CORRECT: `CHANGE_POINT value` (no BY clause)

### DATE_EXTRACT Function
❌ WRONG: `DATE_EXTRACT(timestamp, "hour")`
✅ CORRECT: `DATE_EXTRACT("hour", timestamp)` (unit first!)

### NULL Checks
❌ WRONG: `WHERE field = NULL`
✅ CORRECT: `WHERE field IS NULL`

### STATS Aliases
❌ WRONG: `STATS COUNT(*)`
✅ CORRECT: `STATS count = COUNT(*)`

### Division by Zero
❌ WRONG: `value / count`
✅ CORRECT: `value / GREATEST(count, 1)`

### LOOKUP JOIN
❌ WRONG: `FROM events LOOKUP JOIN dimensions`
✅ CORRECT: `FROM events | LOOKUP JOIN dimensions_lookup ON key`

---

## Query Generation Checklist

When generating ES|QL queries, verify:

1. ✅ Command syntax matches latest documentation
2. ✅ Field names match actual dataset columns
3. ✅ LOOKUP JOIN uses correct suffix (_lookup)
4. ✅ STATS aggregations have aliases
5. ✅ Date functions use correct parameter order
6. ✅ NULL checks use IS NULL / IS NOT NULL
7. ✅ Division operations protected from zero
8. ✅ CHANGE_POINT has no BY clause
9. ✅ Time-series queries sorted by timestamp
10. ✅ Parameterization uses ? prefix

---

## Performance Best Practices

1. **Filter Early**: Apply WHERE clauses before aggregations
2. **Limit Results**: Use LIMIT to constrain result sets
3. **Index Selection**: Use specific index names, not wildcards
4. **Field Selection**: Use KEEP/DROP to limit fields early
5. **Aggregation Order**: Group by low-cardinality fields first

---

**Version:** 1.0.0
**Last Updated:** Auto-generated from docs/esql/
""")

        return "\n".join(content_parts)

    def _create_skill(self, content: str, content_hash: str) -> str:
        """Create new skill via API

        Args:
            content: Skill instructions content
            content_hash: Hash of content for tracking

        Returns:
            Created skill ID
        """
        try:
            response = self.client.skills.create(
                name=self.SKILL_NAME,
                instructions=content,
                skill_type="prompt"
            )

            self.skill_id = response.id
            self._content_hash = content_hash

            logger.info(f"Created ES|QL skill: {self.skill_id}")
            logger.info(f"Skill content size: {len(content)} characters")

            return self.skill_id

        except Exception as e:
            logger.error(f"Failed to create skill: {e}")
            raise

    def _update_skill(self, content: str):
        """Update existing skill with new content

        Args:
            content: Updated skill instructions
        """
        # Note: Skills API doesn't support updates yet
        # Need to delete and recreate
        try:
            if self.skill_id:
                self.client.skills.delete(skill_id=self.skill_id)
                logger.info(f"Deleted old skill: {self.skill_id}")

            self._create_skill(content, self._hash_content(content))

        except Exception as e:
            logger.error(f"Failed to update skill: {e}")
            raise

    def _hash_content(self, content: str) -> str:
        """Generate hash of skill content for change detection

        Args:
            content: Skill content string

        Returns:
            SHA256 hash
        """
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_skill_id(self) -> Optional[str]:
        """Get current skill ID

        Returns:
            Skill ID if exists, None otherwise
        """
        return self.skill_id

    def delete_skill(self):
        """Delete current skill"""
        if self.skill_id:
            try:
                self.client.skills.delete(skill_id=self.skill_id)
                logger.info(f"Deleted skill: {self.skill_id}")
                self.skill_id = None
                self._content_hash = None
            except Exception as e:
                logger.error(f"Failed to delete skill: {e}")
                raise
```

#### 1.2 Update ModuleGenerator

**File:** `src/framework/module_generator.py`

```python
# Add at top of file
from ..services.esql_skill_manager import ESQLSkillManager

class ModuleGenerator:
    def __init__(self, llm_client=None):
        """Initialize module generator

        Args:
            llm_client: Optional LLM client for generation
        """
        self.llm_client = llm_client
        self.strategy_planner = None

        # Initialize ES|QL skill if LLM client provided
        self.esql_skill_manager = None
        self.esql_skill_id = None

        if llm_client:
            try:
                self.esql_skill_manager = ESQLSkillManager(llm_client)
                self.esql_skill_id = self.esql_skill_manager.ensure_skill_exists()
                logger.info(f"ES|QL skill ready: {self.esql_skill_id}")
            except Exception as e:
                logger.warning(f"Could not initialize ES|QL skill: {e}")
                logger.warning("Falling back to inline ES|QL guidance")

        # ... rest of __init__
```

#### 1.3 Use Skill in Query Generation

**File:** `src/framework/module_generator.py` (in `_generate_query_module`)

```python
def _generate_query_module(self, config: Dict[str, Any], module_path: Path, strategy: Dict[str, Any] = None):
    """Generate the query generation module"""

    # ... build prompt ...

    # Call LLM with skill
    try:
        # Build skills list
        skills = []
        if self.esql_skill_id:
            skills.append(self.esql_skill_id)
            logger.info(f"Using ES|QL skill for query generation")

        response = self.llm_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            temperature=0.7,
            skills=skills,  # ← Apply ES|QL expertise
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # ... rest of generation ...

    except Exception as e:
        logger.error(f"Error generating query module: {e}")
        raise
```

---

### Phase 2: Testing & Validation (Week 2)

**Goal:** Validate skill improves query quality and reduces failures

#### 2.1 Create Test Suite

**File:** `tests/test_esql_skill.py`

```python
"""
Tests for ES|QL Skill Integration
"""

import pytest
from src.services.esql_skill_manager import ESQLSkillManager
from anthropic import Anthropic
import os


@pytest.fixture
def skill_manager():
    """Create skill manager with real API client"""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return ESQLSkillManager(client)


def test_skill_creation(skill_manager):
    """Test skill can be created successfully"""
    skill_id = skill_manager.ensure_skill_exists()
    assert skill_id is not None
    assert len(skill_id) > 0


def test_skill_content_includes_all_docs(skill_manager):
    """Test skill content includes all documentation"""
    content = skill_manager._build_skill_content()

    # Verify key commands are documented
    assert "CHANGE_POINT" in content
    assert "DATE_EXTRACT" in content
    assert "LOOKUP JOIN" in content
    assert "COMPLETION" in content
    assert "RERANK" in content
    assert "INLINESTATS" in content

    # Verify anti-patterns included
    assert "Common Mistakes" in content
    assert "Division by Zero" in content


def test_skill_content_size(skill_manager):
    """Test skill content is reasonable size"""
    content = skill_manager._build_skill_content()

    # Should be comprehensive but not excessive
    assert len(content) > 10000, "Skill content too small"
    assert len(content) < 200000, "Skill content too large"


def test_query_generation_with_skill(skill_manager):
    """Test query generation uses skill correctly"""
    from src.framework.module_generator import ModuleGenerator
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    generator = ModuleGenerator(client)

    # Verify skill was initialized
    assert generator.esql_skill_id is not None

    # Test query generation (integration test)
    config = {
        'company_name': 'TestCorp',
        'department': 'Analytics',
        'industry': 'Tech',
        'pain_points': ['Slow queries'],
        'use_cases': ['Real-time analytics'],
        'scale': '1M events',
        'metrics': ['Query performance']
    }

    # This should use the skill
    module_path = generator.generate_demo_module(config)

    # Verify module was created
    assert module_path.exists()
```

#### 2.2 Comparison Testing

**File:** `tests/test_skill_vs_baseline.py`

```python
"""
Compare query quality with and without ES|QL skill
"""

import pytest
from src.framework.module_generator import ModuleGenerator
from anthropic import Anthropic
import os


def test_skill_reduces_syntax_errors():
    """Test that skill reduces syntax error rate"""

    test_config = {
        'company_name': 'RetailCo',
        'department': 'Marketing',
        'industry': 'Retail',
        'pain_points': ['Campaign attribution'],
        'use_cases': ['Campaign analysis', 'Anomaly detection'],
        'scale': '100K events daily',
        'metrics': ['ROAS', 'Conversion rate']
    }

    # Generate with skill
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    generator_with_skill = ModuleGenerator(client)

    module_path = generator_with_skill.generate_demo_module(test_config)

    # Check query testing results
    results_file = module_path / 'query_testing_results.json'

    if results_file.exists():
        import json
        with open(results_file) as f:
            results = json.load(f)

        # With skill, should have higher success rate
        success_rate = results['successfully_fixed'] / results['total_queries']

        # Target: >80% of queries work or auto-fix successfully
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
```

---

### Phase 3: Monitoring & Optimization (Week 3)

**Goal:** Monitor skill effectiveness and optimize based on real usage

#### 3.1 Add Skill Metrics Tracking

**File:** `src/services/esql_skill_manager.py` (add method)

```python
def get_skill_usage_metrics(self) -> dict:
    """Get metrics about skill usage and effectiveness

    Returns:
        Dictionary with skill metrics
    """
    return {
        'skill_id': self.skill_id,
        'skill_name': self.SKILL_NAME,
        'version': self.SKILL_VERSION,
        'content_hash': self._content_hash,
        'content_size': len(self._build_skill_content()) if self._content_hash else 0,
        'status': 'active' if self.skill_id else 'inactive'
    }
```

#### 3.2 Create Skill Update Script

**File:** `scripts/update_esql_skill.py`

```python
"""
Utility script to update ES|QL skill with latest documentation
Run after updating docs/esql/*.md files
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.esql_skill_manager import ESQLSkillManager
from anthropic import Anthropic
import os


def main():
    """Update ES|QL skill with latest documentation"""
    print("=" * 80)
    print("ES|QL Skill Update Utility")
    print("=" * 80)

    # Initialize client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return 1

    client = Anthropic(api_key=api_key)
    manager = ESQLSkillManager(client)

    # Update skill
    print("\n🔄 Updating ES|QL skill...")
    skill_id = manager.ensure_skill_exists()

    # Show metrics
    metrics = manager.get_skill_usage_metrics()

    print("\n✅ Skill Updated Successfully")
    print(f"\nSkill ID: {metrics['skill_id']}")
    print(f"Version: {metrics['version']}")
    print(f"Content Size: {metrics['content_size']:,} characters")
    print(f"Content Hash: {metrics['content_hash']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## Migration Strategy

### Step 1: Enable Skill (No Breaking Changes)

1. Deploy skill manager code
2. Skill is created automatically on first use
3. Existing prompt-based guidance remains as fallback
4. Monitor for 1 week

**Rollback:** Set `self.esql_skill_id = None` to disable

### Step 2: Remove Inline Guidance

After validating skill works well:

1. Remove ES|QL syntax guidance from `_generate_query_module` prompt
2. Keep only customer-specific context
3. Monitor token usage reduction

**Expected Savings:** ~900 tokens per query generation

### Step 3: Expand Skill Content

Add more advanced patterns:

1. Industry-specific query patterns
2. Performance optimization examples
3. Multi-dataset JOIN patterns
4. Real-world query examples from successful demos

---

## Success Metrics

### Primary KPIs

1. **Syntax Error Rate**: Target <10% (down from 15-20%)
2. **Auto-Fix Success Rate**: Target >85%
3. **Token Usage**: Target 900+ token reduction per generation
4. **Query Quality Score**: Measure via manual review sampling

### Monitoring Dashboard

Track in module generation logs:

```python
{
    "module_generation": {
        "skill_used": true,
        "skill_id": "skill_xxx",
        "query_count": 7,
        "syntax_errors": 0,
        "auto_fixed": 2,
        "manual_fix_needed": 0,
        "tokens_saved": 934,
        "generation_time_ms": 8234
    }
}
```

---

## Risk Mitigation

### Risk 1: Skill API Instability

**Mitigation:**
- Graceful fallback to inline guidance
- Try/catch around skill operations
- Monitor skill API errors

```python
try:
    skills = [self.esql_skill_id] if self.esql_skill_id else []
except Exception:
    logger.warning("Skill unavailable, using inline guidance")
    skills = []
```

### Risk 2: Skill Content Too Large

**Mitigation:**
- Monitor skill content size (target <200KB)
- Prioritize critical commands
- Remove redundant examples if needed

### Risk 3: Skill Updates Break Queries

**Mitigation:**
- Version skill content
- Test after each update
- Keep rollback script ready

---

## Future Enhancements

### Phase 4: Industry-Specific Skills (Month 2)

Create specialized skills:

- `esql_retail_analytics`
- `esql_saas_metrics`
- `esql_gaming_telemetry`

### Phase 5: Auto-Learning (Month 3)

Collect successful queries and add to skill:

```python
def enhance_skill_from_successful_queries(self, demo_module_path: Path):
    """Add working queries to skill as examples"""
    # Extract queries from successful demos
    # Add to skill content
    # Update skill
```

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Create `esql_skill_manager.py`
- [ ] Update `module_generator.py` to use skill
- [ ] Test skill creation manually
- [ ] Verify skill applies to query generation
- [ ] Run basic integration test

### Week 2: Testing
- [ ] Create `test_esql_skill.py`
- [ ] Create `test_skill_vs_baseline.py`
- [ ] Run comparison tests (10 demos each)
- [ ] Measure token savings
- [ ] Measure syntax error reduction

### Week 3: Production
- [ ] Deploy to production
- [ ] Monitor metrics for 1 week
- [ ] Remove inline guidance if successful
- [ ] Create `update_esql_skill.py` script
- [ ] Document skill update process

---

## Conclusion

Claude Skills provide an ideal solution for ES|QL query generation:

✅ **Token Efficiency**: Massive reduction in prompt overhead
✅ **Quality**: Comprehensive, up-to-date ES|QL documentation
✅ **Maintainability**: Update once, improve all queries
✅ **Scalability**: Add new commands without prompt bloat
✅ **Consistency**: Same expertise across all generations

**Estimated Impact:**
- 80-90% reduction in ES|QL-related syntax errors
- 900+ token savings per demo generation
- 50% reduction in manual query fixes

**Timeline:** 3 weeks from start to production
**Risk:** Low (graceful fallback to existing approach)
**ROI:** High (immediate quality improvement + long-term maintainability)

---

**Next Steps:**
1. Review this strategy
2. Approve implementation approach
3. Begin Phase 1 development
4. Schedule Phase 2 testing
