# ES|QL Skill System Accuracy Strategy

## The Problem
As discovered with CHANGE_POINT, incorrect documentation or assumptions can lead to:
- Generated queries with wrong field names (e.g., `change_point_detected` instead of `type`)
- Misunderstanding of function signatures
- Incorrect usage patterns being taught

## Multi-Layer Validation Approach

### 1. Documentation Validation Pipeline
```python
class DocumentationValidator:
    def validate_against_elasticsearch(self):
        """Test each documented feature against live Elasticsearch"""
        # For each command/function in docs:
        # 1. Generate minimal test query
        # 2. Execute against Elasticsearch
        # 3. Verify output columns match documentation
        # 4. Flag discrepancies
```

### 2. Automated Documentation Testing

#### Test Generation from Docs
```python
def generate_tests_from_docs(doc_file):
    """
    Parse documentation and generate executable tests

    Example for CHANGE_POINT:
    - Extract: "returns type and pvalue columns"
    - Generate: Test that verifies these exact columns exist
    """
    tests = []

    # Parse return values section
    if "returns" in doc_content:
        expected_columns = extract_column_names(doc_content)
        test = f"""
        FROM test_data
        | CHANGE_POINT value_field
        | LIMIT 1
        """
        tests.append({
            'query': test,
            'expected_columns': expected_columns,
            'command': 'CHANGE_POINT'
        })

    return tests
```

#### Continuous Validation
```yaml
# .github/workflows/validate-esql-docs.yml
name: Validate ES|QL Documentation
on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  push:
    paths:
      - 'docs/esql/**'

jobs:
  validate:
    steps:
      - name: Test Documentation Against Elasticsearch
        run: |
          python scripts/validate_esql_docs.py
          python scripts/test_documented_examples.py
```

### 3. Learning from Query Execution

#### Feedback Loop System
```python
class ESQLSkillManager:
    def __init__(self):
        self.execution_feedback = {}  # Track what actually works

    def learn_from_execution(self, query, result, error=None):
        """
        Update knowledge based on query execution results
        """
        if error:
            # Parse error to understand what went wrong
            self.record_failure_pattern(query, error)
        else:
            # Record successful patterns and actual column names
            self.record_success_pattern(query, result.columns)

    def record_success_pattern(self, query, actual_columns):
        """
        Example: CHANGE_POINT actually returns ['type', 'pvalue']
        not ['change_point_detected', 'change_point_score']
        """
        command = self.extract_command(query)
        self.execution_feedback[command] = {
            'verified_columns': actual_columns,
            'last_verified': datetime.now()
        }
```

### 4. Test-Driven Documentation

#### Example Test Suite for CHANGE_POINT
```python
# tests/test_esql_change_point.py
import pytest
from tests.esql_test_base import ESQLTestBase

class TestChangePoint(ESQLTestBase):

    def test_change_point_columns(self):
        """Verify CHANGE_POINT returns correct columns"""
        query = """
        ROW value=[1,2,3,4,5,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
        | MV_EXPAND value
        | CHANGE_POINT value
        """
        result = self.execute_query(query)

        # Document says it returns 'type' and 'pvalue'
        assert 'type' in result.columns
        assert 'pvalue' in result.columns

        # These should NOT exist (common misconceptions)
        assert 'change_point_detected' not in result.columns
        assert 'change_point_score' not in result.columns

    def test_change_point_on_clause(self):
        """Test CHANGE_POINT with ON clause for custom ordering"""
        query = """
        FROM sample_data
        | CHANGE_POINT metric_field ON timestamp_field
        """
        result = self.execute_query(query)
        assert result.success

    def test_change_point_as_clause(self):
        """Test CHANGE_POINT with AS clause for custom column names"""
        query = """
        FROM sample_data
        | CHANGE_POINT value AS change_type, significance
        """
        result = self.execute_query(query)
        assert 'change_type' in result.columns
        assert 'significance' in result.columns
```

### 5. Documentation Source of Truth

#### Structured Documentation Format
```markdown
---
command: CHANGE_POINT
verified: 2024-10-29
test_file: tests/test_esql_change_point.py
---

# CHANGE_POINT

## Signature
```
CHANGE_POINT value [ON key] [AS type_name, pvalue_name]
```

## Returns
| Column | Type | Description | Verified |
|--------|------|-------------|----------|
| type | keyword | Change type (spike, dip, etc.) | ✅ 2024-10-29 |
| pvalue | double | Statistical significance (0-1) | ✅ 2024-10-29 |

## Common Mistakes
- ❌ Using `change_point_detected` (doesn't exist)
- ❌ Using `change_point_score` (actually `pvalue`)
- ❌ Using `@timestamp` hardcoded (use field variables)
```

### 6. Skill System Self-Validation

```python
class ESQLSkillManager:
    def validate_documentation(self):
        """
        Self-check documentation accuracy
        """
        validation_report = {}

        for command, doc in self.detailed_docs.items():
            # Extract examples from documentation
            examples = self.extract_examples(doc)

            for example in examples:
                try:
                    # Test example against Elasticsearch
                    result = self.test_query(example)
                    validation_report[command] = {
                        'status': 'valid',
                        'tested': datetime.now()
                    }
                except Exception as e:
                    validation_report[command] = {
                        'status': 'invalid',
                        'error': str(e),
                        'documentation_needs_update': True
                    }

        return validation_report
```

### 7. Implementation Checklist

#### Immediate Actions
1. **Audit Existing Docs**: Review all docs/esql/*.md files for accuracy
2. **Create Test Suite**: Write tests for each ES|QL command/function
3. **Add Validation Script**: Create `scripts/validate_esql_docs.py`
4. **Update CHANGE_POINT**: Fix the documentation to reflect actual behavior

#### Validation Script Example
```python
#!/usr/bin/env python3
# scripts/validate_esql_docs.py

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.esql_skill_manager import ESQLSkillManager
from src.services.elasticsearch_service import ElasticsearchService

def validate_all_documentation():
    """Validate all ES|QL documentation against live Elasticsearch"""

    manager = ESQLSkillManager()
    es_service = ElasticsearchService()

    report = {
        'valid': [],
        'invalid': [],
        'untested': []
    }

    # Test each command
    for command in manager.command_index:
        doc_file = Path(f"docs/esql/{command.lower().replace('_', '-')}.md")

        if not doc_file.exists():
            report['untested'].append(command)
            continue

        # Extract test cases from documentation
        test_cases = extract_test_cases(doc_file)

        for test in test_cases:
            try:
                result = es_service.execute_esql(test['query'])

                # Verify expected columns exist
                if test.get('expected_columns'):
                    for col in test['expected_columns']:
                        assert col in result.columns

                report['valid'].append(command)
            except Exception as e:
                report['invalid'].append({
                    'command': command,
                    'error': str(e),
                    'test': test
                })

    return report

if __name__ == "__main__":
    report = validate_all_documentation()

    print("=" * 80)
    print("ES|QL DOCUMENTATION VALIDATION REPORT")
    print("=" * 80)

    print(f"\n✅ Valid: {len(report['valid'])} commands")
    print(f"❌ Invalid: {len(report['invalid'])} commands")
    print(f"⚠️  Untested: {len(report['untested'])} commands")

    if report['invalid']:
        print("\n❌ FAILED VALIDATIONS:")
        for failure in report['invalid']:
            print(f"\n  Command: {failure['command']}")
            print(f"  Error: {failure['error']}")

    # Exit with error if any invalid
    sys.exit(1 if report['invalid'] else 0)
```

### 8. Query Pattern Library

Build a library of verified patterns:

```python
# src/services/esql_patterns.py

VERIFIED_PATTERNS = {
    'change_point_basic': {
        'pattern': """
        FROM {index}
        | CHANGE_POINT {metric_field} ON {time_field}
        | WHERE type IS NOT NULL
        """,
        'returns': ['type', 'pvalue'],
        'verified': '2024-10-29',
        'notes': 'Use type IS NOT NULL, not change_point_detected'
    },

    'change_point_with_threshold': {
        'pattern': """
        FROM {index}
        | CHANGE_POINT {metric_field}
        | WHERE pvalue < 0.05  // Statistical significance
        """,
        'returns': ['type', 'pvalue'],
        'verified': '2024-10-29'
    }
}
```

## Benefits of This Approach

1. **Continuous Accuracy**: Daily validation ensures documentation stays correct
2. **Fail-Fast**: Tests catch documentation errors before they affect users
3. **Learning System**: Skill system improves from actual execution feedback
4. **Clear Source of Truth**: Verified patterns library
5. **Automated Correction**: System can auto-update based on test results

## Next Steps

1. Implement validation pipeline
2. Create comprehensive test suite for all ES|QL commands
3. Set up CI/CD to run validation on every change
4. Build feedback loop from query execution
5. Create verified pattern library

This ensures the skill system teaches correct information consistently!