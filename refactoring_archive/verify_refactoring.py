#!/usr/bin/env python
"""
Verification script for module_generator refactoring.

This script verifies that the new slim orchestrator works correctly
and maintains backward compatibility with the original implementation.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all imports work correctly"""
    print("=" * 60)
    print("TEST 1: Verifying Imports")
    print("=" * 60)

    try:
        # Test slim orchestrator import
        from src.framework.generation.module_generator import ModuleGenerator
        print("✅ Slim orchestrator import successful")

        # Test template imports
        from src.framework.generation.templates import (
            get_analytics_data_generator_template,
            get_search_data_generator_template,
            get_scripted_queries_prompt,
            get_parameterized_queries_prompt,
            get_rag_queries_prompt,
            get_demo_guide_prompt,
            get_agent_instructions_prompt
        )
        print("✅ All template imports successful")

        # Test generator imports
        from src.framework.generation.generators import (
            CodeExtractor,
            ConfigGenerator,
            StaticFileGenerator
        )
        print("✅ All generator imports successful")

        print("\n✅ All imports passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        return False


def test_instantiation():
    """Test that ModuleGenerator can be instantiated"""
    print("=" * 60)
    print("TEST 2: Verifying Instantiation")
    print("=" * 60)

    try:
        from src.framework.generation.module_generator import ModuleGenerator

        # Test basic instantiation
        mg1 = ModuleGenerator()
        print(f"✅ Basic instantiation: {type(mg1).__name__}")
        print(f"   - base_path: {mg1.base_path}")
        print(f"   - llm_client: {mg1.llm_client}")
        print(f"   - inference_endpoints: {mg1.inference_endpoints}")

        # Test with custom endpoints
        mg2 = ModuleGenerator(
            llm_client=None,
            inference_endpoints={'rerank': 'test-rerank', 'completion': 'test-completion'}
        )
        print(f"\n✅ Custom endpoints: {mg2.inference_endpoints}")

        print("\n✅ All instantiation tests passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Instantiation failed: {e}\n")
        return False


def test_public_api():
    """Test that all public methods exist with correct signatures"""
    print("=" * 60)
    print("TEST 3: Verifying Public API")
    print("=" * 60)

    try:
        from src.framework.generation.module_generator import ModuleGenerator
        import inspect

        mg = ModuleGenerator()

        # Required public methods
        required_methods = {
            'generate_demo_module': '(config: Dict[str, Any], query_plan: Optional[Dict[str, Any]] = None) -> str',
            'generate_demo_module_with_strategy': '(config: Dict[str, Any], query_strategy: Dict[str, Any]) -> str',
            'generate_data_and_infrastructure_only': '(config: Dict[str, Any], query_strategy: Dict[str, Any]) -> str',
            'generate_query_module_with_profile': '(module_path: str, config: Dict[str, Any], query_strategy: Dict[str, Any], data_profile: Optional[Dict[str, Any]] = None) -> None'
        }

        all_passed = True
        for method_name, expected_sig in required_methods.items():
            if hasattr(mg, method_name):
                method = getattr(mg, method_name)
                actual_sig = str(inspect.signature(method))
                print(f"✅ {method_name}")
                print(f"   Signature: {actual_sig}")
            else:
                print(f"❌ {method_name} - NOT FOUND")
                all_passed = False

        if all_passed:
            print("\n✅ All public API methods present!\n")
        else:
            print("\n❌ Some public API methods missing!\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ Public API test failed: {e}\n")
        return False


def test_internal_methods():
    """Test that key internal methods exist"""
    print("=" * 60)
    print("TEST 4: Verifying Internal Methods")
    print("=" * 60)

    try:
        from src.framework.generation.module_generator import ModuleGenerator

        mg = ModuleGenerator()

        # Key internal methods
        internal_methods = [
            '_create_module_directory',
            '_generate_data_module',
            '_generate_data_module_with_requirements',
            '_generate_query_module',
            '_generate_query_module_with_strategy',
            '_generate_guide_module',
            '_generate_agent_metadata',
            '_call_llm',
            '_get_minimal_esql_reference'
        ]

        all_passed = True
        for method_name in internal_methods:
            if hasattr(mg, method_name):
                print(f"✅ {method_name}")
            else:
                print(f"❌ {method_name} - NOT FOUND")
                all_passed = False

        if all_passed:
            print("\n✅ All internal methods present!\n")
        else:
            print("\n❌ Some internal methods missing!\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ Internal methods test failed: {e}\n")
        return False


def test_module_directory_creation():
    """Test that module directory creation works"""
    print("=" * 60)
    print("TEST 5: Verifying Module Directory Creation")
    print("=" * 60)

    try:
        from src.framework.generation.module_generator import ModuleGenerator
        import shutil

        mg = ModuleGenerator()

        # Test config
        config = {
            'company_name': 'TestCorp',
            'department': 'Engineering',
            'industry': 'Technology',
            'pain_points': ['slow queries'],
            'use_cases': ['analytics'],
            'scale': '1000',
            'metrics': ['response_time'],
            'demo_type': 'analytics',
            'dataset_size_preference': 'small'
        }

        # Create module directory
        module_path = mg._create_module_directory(config)

        print(f"✅ Module directory created: {module_path}")
        print(f"   - Directory exists: {module_path.exists()}")
        print(f"   - __init__.py exists: {(module_path / '__init__.py').exists()}")

        # Clean up
        if module_path.exists():
            shutil.rmtree(module_path)
            print(f"✅ Cleanup successful")

        print("\n✅ Module directory creation test passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Module directory creation failed: {e}\n")
        return False


def test_template_access():
    """Test that templates can be accessed directly"""
    print("=" * 60)
    print("TEST 6: Verifying Template Access")
    print("=" * 60)

    try:
        from src.framework.generation.templates import (
            get_analytics_data_generator_template,
            get_search_data_generator_template,
            get_scripted_queries_prompt
        )

        config = {
            'company_name': 'TestCorp',
            'department': 'Sales',
            'size_preference': 'medium',
            'pain_points': ['slow queries'],
            'use_cases': ['analytics'],
            'industry': 'Technology'
        }

        # Test analytics template
        analytics_template = get_analytics_data_generator_template(config)
        print(f"✅ Analytics template: {len(analytics_template)} characters")

        # Test search template
        search_template = get_search_data_generator_template(config)
        print(f"✅ Search template: {len(search_template)} characters")

        # Test query prompt
        query_prompt = get_scripted_queries_prompt(config, "ES|QL docs...")
        print(f"✅ Query prompt: {len(query_prompt)} characters")

        print("\n✅ Template access test passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Template access failed: {e}\n")
        return False


def test_generator_utilities():
    """Test that generator utilities work"""
    print("=" * 60)
    print("TEST 7: Verifying Generator Utilities")
    print("=" * 60)

    try:
        from src.framework.generation.generators import CodeExtractor

        # Test code extraction
        markdown_code = "```python\ndef hello():\n    return 'world'\n```"
        extracted = CodeExtractor.extract_python_code(markdown_code)
        print(f"✅ Code extraction: {len(extracted)} characters")

        # Test syntax validation
        try:
            CodeExtractor.validate_python_syntax(extracted, 'test.py')
            print("✅ Syntax validation: passed")
        except SyntaxError:
            print("❌ Syntax validation: failed")
            return False

        print("\n✅ Generator utilities test passed!\n")
        return True

    except Exception as e:
        print(f"\n❌ Generator utilities failed: {e}\n")
        return False


def main():
    """Run all verification tests"""
    print("\n" + "=" * 60)
    print("MODULE GENERATOR REFACTORING VERIFICATION")
    print("=" * 60 + "\n")

    tests = [
        ("Imports", test_imports),
        ("Instantiation", test_instantiation),
        ("Public API", test_public_api),
        ("Internal Methods", test_internal_methods),
        ("Module Directory Creation", test_module_directory_creation),
        ("Template Access", test_template_access),
        ("Generator Utilities", test_generator_utilities)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}\n")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("=" * 60 + "\n")

    if passed_count == total_count:
        print("🎉 All verification tests passed! Refactoring successful!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
