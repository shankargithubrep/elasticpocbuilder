"""
Code extraction utilities for module generation.

This module handles extraction and validation of generated Python code
from LLM responses.
"""

import ast
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CodeExtractor:
    """Extracts and validates Python code from LLM responses"""

    @staticmethod
    def extract_python_code(response: str) -> str:
        """Extract Python code from LLM response.

        Handles markdown-wrapped code blocks and returns clean Python code.

        Args:
            response: LLM response that may contain markdown code blocks

        Returns:
            Extracted Python code, or the response if no code blocks found

        Examples:
            >>> response = '```python\\nprint("hello")\\n```'
            >>> code = CodeExtractor.extract_python_code(response)
            >>> code == 'print("hello")'
            True
        """
        # Try to extract from markdown code block
        if "```python" in response:
            try:
                code = response.split("```python")[1].split("```")[0]
                logger.info(f"✂️  Extracted Python code from markdown: {len(code)} characters")
                return code.strip()
            except (IndexError, ValueError):
                logger.warning("Failed to extract from ```python``` block, trying generic ```")

        # Try generic code block
        if "```" in response:
            try:
                parts = response.split("```")
                if len(parts) >= 3:
                    code = parts[1]
                    logger.info(f"✂️  Extracted Python code from generic block: {len(code)} characters")
                    return code.strip()
            except (IndexError, ValueError):
                logger.warning("Failed to extract from ``` block")

        # Return as-is if no code block found
        logger.info(f"No markdown code block found, using response as-is: {len(response)} characters")
        return response.strip()

    @staticmethod
    def validate_python_syntax(code: str, module_name: str = 'generated.py') -> None:
        """Validate Python syntax and raise error if invalid.

        Args:
            code: Python code to validate
            module_name: Name of module being validated (for error messages)

        Raises:
            SyntaxError: If code has syntax errors

        Examples:
            >>> # Valid code - returns without error
            >>> CodeExtractor.validate_python_syntax('x = 1')

            >>> # Invalid code - raises SyntaxError
            >>> CodeExtractor.validate_python_syntax('x = ')
            Traceback (most recent call last):
                ...
            SyntaxError: Generated code has syntax error...
        """
        try:
            compile(code, module_name, 'exec')
            logger.info(f"✅ Syntax validation passed for {module_name}")
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in generated {module_name}: {e}")
            logger.error(f"Error at line {e.lineno}: {e.text}")
            raise SyntaxError(f"Generated code has syntax error at line {e.lineno}: {e.msg}")

    @staticmethod
    def validate_query_module_methods(code: str) -> Dict[str, bool]:
        """Validate that query module has all required methods using AST parsing.

        Checks for the presence of three required methods in the generated query module:
        - generate_queries()
        - generate_parameterized_queries()
        - generate_rag_queries()

        Args:
            code: Python code to validate

        Returns:
            Dict mapping method names to boolean (True if present, False if missing)

        Examples:
            >>> code = '''
            ... class QueryGen:
            ...     def generate_queries(self): pass
            ...     def generate_parameterized_queries(self): pass
            ...     def generate_rag_queries(self): pass
            ... '''
            >>> result = CodeExtractor.validate_query_module_methods(code)
            >>> all(result.values())
            True
        """
        required_methods = {
            'generate_queries': False,
            'generate_parameterized_queries': False,
            'generate_rag_queries': False
        }

        try:
            tree = ast.parse(code)

            # Find all method definitions in classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name in required_methods:
                                required_methods[item.name] = True

            # Log results
            logger.info("🔍 Query module method validation:")
            for method, present in required_methods.items():
                status = "✅" if present else "❌"
                logger.info(f"  {status} {method}: {'FOUND' if present else 'MISSING'}")

            return required_methods

        except Exception as e:
            logger.error(f"❌ Failed to parse code for method validation: {e}")
            return required_methods
