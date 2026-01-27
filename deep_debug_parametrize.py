"""
Deep debug of why parametrize extraction isn't working on server.
This will parse a specific file and show exactly what's happening.
"""
from services.pytest_parser import PytestParser
from services.git_service import GitService
from config import Config
import os
import ast

print("=" * 80)
print("DEEP DEBUG - Parametrize Extraction")
print("=" * 80)

# Initialize git service
git_service = GitService(
    Config.GIT_REPO_URL,
    Config.GIT_CLONE_PATH,
    Config.GIT_BRANCH,
    username=Config.GITHUB_USERNAME,
    token=Config.GITHUB_TOKEN
)

# Pick a specific file that should have parametrize tests
test_file = "morpheus_automation/tests/api/test_vme_exploratory_e2e.py"
print(f"\nTesting file: {test_file}")
print("-" * 80)

# Get the file content
content = git_service.get_file_content(test_file)
if not content:
    print("❌ Could not get file content!")
    exit(1)

print(f"✅ Got file content ({len(content)} chars)")

# Parse it
print("\nParsing with PytestParser...")
tests = PytestParser.parse_test_file(test_file, content)
print(f"✅ Parsed {len(tests)} tests")

# Find parametrized tests
print("\n" + "=" * 80)
print("PARAMETRIZED TESTS IN THIS FILE")
print("=" * 80)

parametrized_tests = [t for t in tests if 'parametrize' in (t.get('markers') or [])]
print(f"Found {len(parametrized_tests)} parametrized tests")

if parametrized_tests:
    for i, test in enumerate(parametrized_tests[:5], 1):
        print(f"\n{i}. {test['test_name']}")
        print(f"   Markers: {test['markers']}")
        print(f"   TestRail ID: {test['testrail_case_id']}")
        if test['testrail_case_id']:
            ids = test['testrail_case_id'].split(',')
            print(f"   Number of IDs: {len(ids)}")
            print(f"   Status: ✅ HAS IDs")
        else:
            print(f"   Status: ❌ NO IDs EXTRACTED")

# Now let's manually test the extraction on a specific test
print("\n" + "=" * 80)
print("MANUAL EXTRACTION TEST")
print("=" * 80)

# Find a specific test in the AST
tree = ast.parse(content)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'test_add_disk_with_disk_type_thick_thin':
        print(f"\nFound test: {node.name}")
        print(f"Number of decorators: {len(node.decorator_list)}")

        for i, decorator in enumerate(node.decorator_list):
            print(f"\n  Decorator {i}:")
            from services.pytest_parser import safe_unparse
            dec_source = safe_unparse(decorator)
            print(f"    Source: {dec_source[:100]}...")

            # Check if it's parametrize
            if 'parametrize' in dec_source:
                print(f"    ✅ This is a parametrize decorator")

                # Try to extract IDs
                ids = PytestParser.extract_parametrize_testrail_ids(decorator)
                print(f"    Extracted IDs: {ids}")

                if ids:
                    print(f"    ✅ SUCCESS - Extracted {len(ids)} IDs")
                else:
                    print(f"    ❌ FAILED - No IDs extracted")
                    print(f"    Debugging...")

                    # Debug the AST structure
                    print(f"\n    AST Structure:")
                    print(f"      Type: {type(decorator).__name__}")
                    if isinstance(decorator, ast.Call):
                        print(f"      Function: {safe_unparse(decorator.func)}")
                        print(f"      Number of args: {len(decorator.args)}")

                        # Check the second argument (parameter values)
                        if len(decorator.args) >= 2:
                            params_arg = decorator.args[1]
                            print(f"      Params type: {type(params_arg).__name__}")

                            if isinstance(params_arg, (ast.List, ast.Tuple)):
                                print(f"      Number of parameter sets: {len(params_arg.elts)}")

                                for j, element in enumerate(params_arg.elts):
                                    print(f"\n      Parameter set {j}:")
                                    print(f"        Type: {type(element).__name__}")
                                    elem_source = safe_unparse(element)
                                    print(f"        Source: {elem_source[:80]}...")

                                    if 'testrail' in elem_source:
                                        print(f"        ✅ Contains 'testrail'")
                                    else:
                                        print(f"        ❌ No 'testrail' found")
        break

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
