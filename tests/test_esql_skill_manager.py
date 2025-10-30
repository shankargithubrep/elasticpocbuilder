"""
Tests for ES|QL Skill Manager
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.services.esql_skill_manager import ESQLSkillManager, get_skill_manager


class TestESQLSkillManager:
    """Test suite for ES|QL Skill Manager"""

    def setup_method(self):
        """Set up test fixtures"""
        # Create a temporary directory for test documentation
        self.temp_dir = tempfile.mkdtemp()
        self.test_docs_path = Path(self.temp_dir) / "esql"
        self.test_docs_path.mkdir()

        # Create test documentation files
        self._create_test_docs()

        # Initialize skill manager with test docs
        self.skill_manager = ESQLSkillManager(str(self.test_docs_path))

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_docs(self):
        """Create test documentation files"""
        # Create syntax guide
        syntax_guide = """# ES|QL Syntax Guide
## Basic Syntax
FROM index | WHERE field > value | STATS count = COUNT(*)
"""
        (self.test_docs_path / "ESQL_SYNTAX_GUIDE.md").write_text(syntax_guide)

        # Create commands reference
        commands = """# ES|QL Commands
## FROM
Load data from an index
## WHERE
Filter data
## STATS
Aggregate data
## CHANGE_POINT
Detect anomalies - NO BY clause supported
"""
        (self.test_docs_path / "ESQL_COMMANDS.md").write_text(commands)

        # Create functions reference
        functions = """# ES|QL Functions
### COUNT
Count records
### AVG
Calculate average
### DATE_EXTRACT
Extract date parts: DATE_EXTRACT(part, date_field)
"""
        (self.test_docs_path / "ESQL_FUNCTIONS.md").write_text(functions)

        # Create patterns
        patterns = """# ES|QL Common Patterns
## Retail
- Sales by category
- Inventory tracking
## Technology
- API metrics
- Error rates
"""
        (self.test_docs_path / "ESQL_COMMON_PATTERNS.md").write_text(patterns)

        # Create error handling
        error_handling = """# ES|QL Error Handling
## Common Errors
- Division by zero: Use COALESCE or GREATEST
- Field not found: Check field names
"""
        (self.test_docs_path / "ESQL_ERROR_HANDLING.md").write_text(error_handling)

    def test_initialization(self):
        """Test that skill manager initializes correctly"""
        assert self.skill_manager is not None
        assert self.skill_manager.docs_path == self.test_docs_path
        assert len(self.skill_manager.cache) > 0

    def test_documentation_loading(self):
        """Test that documentation is loaded into cache"""
        # Check that key documentation is loaded
        assert "syntax_guide" in self.skill_manager.cache
        assert "commands" in self.skill_manager.cache
        assert "functions" in self.skill_manager.cache
        assert "common_patterns" in self.skill_manager.cache
        assert "error_handling" in self.skill_manager.cache

        # Verify content is loaded
        assert "Basic Syntax" in self.skill_manager.cache["syntax_guide"]
        assert "CHANGE_POINT" in self.skill_manager.cache["commands"]

    def test_query_generation_prompt(self):
        """Test query generation prompt creation"""
        context = {
            "industry": "Retail",
            "department": "Analytics",
            "use_cases": ["Sales tracking", "Inventory management"],
            "metrics": ["Revenue", "Stock levels"]
        }

        prompt = self.skill_manager.get_query_generation_prompt(context)

        # Verify prompt contains context
        assert "Retail" in prompt
        assert "Analytics" in prompt
        assert "Sales tracking" in prompt

        # Verify skill reference
        assert "ES|QL Skill" in prompt or "esql-query-generator" in prompt

        # Check metrics are tracked
        assert self.skill_manager.metrics["prompts_generated"] == 1
        assert self.skill_manager.metrics["tokens_saved"] > 0

    def test_syntax_reference_general(self):
        """Test getting general syntax reference"""
        reference = self.skill_manager.get_syntax_reference()

        assert "Basic Syntax" in reference
        assert "FROM index" in reference
        assert self.skill_manager.metrics["cache_hits"] == 1

    def test_syntax_reference_specific_command(self):
        """Test getting reference for specific command"""
        reference = self.skill_manager.get_syntax_reference("CHANGE_POINT")

        assert "CHANGE_POINT" in reference
        assert "NO BY clause" in reference
        assert self.skill_manager.metrics["cache_hits"] == 1

    def test_function_reference_general(self):
        """Test getting general function reference"""
        reference = self.skill_manager.get_function_reference()

        assert "COUNT" in reference
        assert "AVG" in reference
        assert "DATE_EXTRACT" in reference

    def test_function_reference_specific(self):
        """Test getting reference for specific function"""
        reference = self.skill_manager.get_function_reference("DATE_EXTRACT")

        assert "DATE_EXTRACT" in reference
        assert "Extract date parts" in reference

    def test_common_patterns_general(self):
        """Test getting common patterns"""
        patterns = self.skill_manager.get_common_patterns()

        assert "Retail" in patterns
        assert "Sales by category" in patterns
        assert "Technology" in patterns

    def test_common_patterns_industry_specific(self):
        """Test getting industry-specific patterns"""
        patterns = self.skill_manager.get_common_patterns("Retail")

        # Currently returns all patterns, but could be enhanced
        assert "Retail" in patterns

    def test_error_handling_guide(self):
        """Test getting error handling guide"""
        guide = self.skill_manager.get_error_handling_guide()

        assert "Division by zero" in guide
        assert "COALESCE" in guide
        assert "Field not found" in guide

    def test_validate_syntax(self):
        """Test syntax validation"""
        # Test valid query
        result = self.skill_manager.validate_syntax("FROM index | WHERE field > 10")
        assert result["valid"] == True
        assert len(result["issues"]) == 0

        # Test query with potential issues
        result = self.skill_manager.validate_syntax("FROM index | WHERE value / 0")
        assert len(result["issues"]) > 0
        assert any("Division by zero" in issue for issue in result["suggestions"])

        # Test DATE_EXTRACT issue
        result = self.skill_manager.validate_syntax("FROM index | EVAL day = DATE_EXTRACT(timestamp, 'day')")
        assert len(result["issues"]) > 0

    def test_optimization_hints(self):
        """Test query optimization hints"""
        # Test EVAL after STATS suggestion
        query = "FROM index | EVAL new_field = field * 2 | STATS avg = AVG(new_field)"
        hints = self.skill_manager.get_optimization_hints(query)
        assert any("EVAL after STATS" in hint for hint in hints)

        # Test missing WHERE before STATS
        query = "FROM index | STATS count = COUNT(*)"
        hints = self.skill_manager.get_optimization_hints(query)
        assert any("WHERE clause" in hint for hint in hints)

        # Test SORT without LIMIT
        query = "FROM index | SORT timestamp DESC"
        hints = self.skill_manager.get_optimization_hints(query)
        assert any("LIMIT" in hint for hint in hints)

    def test_metrics_tracking(self):
        """Test that metrics are tracked correctly"""
        # Reset metrics
        self.skill_manager.reset_metrics()
        assert self.skill_manager.metrics["prompts_generated"] == 0

        # Generate prompt
        context = {"industry": "Tech"}
        self.skill_manager.get_query_generation_prompt(context)
        assert self.skill_manager.metrics["prompts_generated"] == 1
        assert self.skill_manager.metrics["tokens_saved"] == 900

        # Access cache
        self.skill_manager.get_syntax_reference()
        assert self.skill_manager.metrics["cache_hits"] == 1

    def test_export_skill_definition(self):
        """Test exporting skill definition"""
        definition = self.skill_manager.export_skill_definition()

        assert definition["name"] == "esql-query-generator"
        assert definition["version"] == "1.0.0"
        assert len(definition["capabilities"]) > 0
        assert "documentation" in definition
        assert definition["documentation"]["sections"] == list(self.skill_manager.cache.keys())

    def test_singleton_pattern(self):
        """Test that get_skill_manager returns singleton"""
        manager1 = get_skill_manager(str(self.test_docs_path))
        manager2 = get_skill_manager(str(self.test_docs_path))

        # Should be the same instance
        assert manager1 is manager2

    def test_missing_docs_directory(self):
        """Test handling of missing documentation directory"""
        # Create skill manager with non-existent path
        manager = ESQLSkillManager("/non/existent/path")

        # Should initialize without error
        assert manager is not None
        assert len(manager.cache) == 0

        # Should handle missing docs gracefully
        reference = manager.get_syntax_reference()
        assert "not available" in reference

    def test_token_savings_calculation(self):
        """Test that token savings are calculated correctly"""
        # Reset metrics
        self.skill_manager.reset_metrics()

        # Generate multiple prompts
        context = {"industry": "Retail"}
        for _ in range(5):
            self.skill_manager.get_query_generation_prompt(context)

        # Should save 900 tokens per prompt
        assert self.skill_manager.metrics["tokens_saved"] == 900 * 5

    def test_cache_efficiency(self):
        """Test cache hit/miss tracking"""
        # Reset metrics
        self.skill_manager.reset_metrics()

        # Access cached content
        self.skill_manager.get_syntax_reference()
        assert self.skill_manager.metrics["cache_hits"] == 1
        assert self.skill_manager.metrics["cache_misses"] == 0

        # Clear cache and access again
        self.skill_manager.cache.clear()
        self.skill_manager.get_syntax_reference()
        assert self.skill_manager.metrics["cache_misses"] == 1


class TestIntegrationWithModuleGenerator:
    """Test integration with ModuleGenerator"""

    @patch('src.framework.module_generator.get_skill_manager')
    def test_module_generator_uses_skill_manager(self, mock_get_skill_manager):
        """Test that ModuleGenerator uses ESQLSkillManager when available"""
        from src.framework.module_generator import ModuleGenerator

        # Create mock skill manager
        mock_skill_manager = Mock()
        mock_skill_manager.get_query_generation_prompt.return_value = "Skill-based prompt"
        mock_skill_manager.get_metrics.return_value = {"tokens_saved": 900, "prompts_generated": 1}
        mock_get_skill_manager.return_value = mock_skill_manager

        # Create generator with skills enabled
        generator = ModuleGenerator(llm_client=None, use_esql_skills=True)

        # Verify skill manager was initialized
        assert generator.esql_skill_manager is not None

    def test_module_generator_without_skills(self):
        """Test that ModuleGenerator works without skill manager"""
        from src.framework.module_generator import ModuleGenerator

        # Create generator with skills disabled
        generator = ModuleGenerator(llm_client=None, use_esql_skills=False)

        # Should work without skill manager
        assert generator.esql_skill_manager is None