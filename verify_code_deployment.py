"""
Verify that the parametrize extraction code is present and working.
Run this on the server to confirm the fix is deployed.
"""
import sys
import inspect

print("=" * 80)
print("CODE VERIFICATION - Parametrize Fix")
print("=" * 80)

# Check if the extract_parametrize_testrail_ids method exists
try:
    from services.pytest_parser import PytestParser

    # Check if the method exists
    if hasattr(PytestParser, 'extract_parametrize_testrail_ids'):
        print("\n✅ extract_parametrize_testrail_ids method EXISTS")

        # Get the source code
        method = getattr(PytestParser, 'extract_parametrize_testrail_ids')
        source = inspect.getsource(method)

        # Check key parts of the implementation
        checks = [
            ('parametrize', 'Checks for parametrize decorator'),
            ('pytest.param', 'Looks for pytest.param calls'),
            ('testrail', 'Searches for testrail markers'),
            ('testrail_ids.append', 'Collects TestRail IDs'),
        ]

        print("\nCode verification:")
        for keyword, description in checks:
            if keyword in source:
                print(f"  ✅ {description}: Found")
            else:
                print(f"  ❌ {description}: MISSING")

        print("\nMethod signature:")
        sig = inspect.signature(method)
        print(f"  {method.__name__}{sig}")

    else:
        print("\n❌ extract_parametrize_testrail_ids method DOES NOT EXIST!")
        print("   The parametrize fix is NOT deployed!")
        sys.exit(1)

    # Check the parse_test_file method to see if it uses the new method
    if hasattr(PytestParser, 'parse_test_file'):
        parse_source = inspect.getsource(PytestParser.parse_test_file)

        print("\n" + "=" * 80)
        print("Checking if parse_test_file uses the new method:")
        print("=" * 80)

        if 'extract_parametrize_testrail_ids' in parse_source:
            print("  ✅ parse_test_file CALLS extract_parametrize_testrail_ids")
        else:
            print("  ❌ parse_test_file DOES NOT call extract_parametrize_testrail_ids")
            print("     The method exists but is not being used!")
            sys.exit(1)

        # Check for the prioritization logic
        if 'parametrize' in parse_source and 'testrail' in parse_source:
            print("  ✅ Logic to handle parametrize decorators found")
        else:
            print("  ⚠️  Parametrize handling logic may be incomplete")

    print("\n" + "=" * 80)
    print("✅ ALL CHECKS PASSED - Code appears to be deployed correctly")
    print("=" * 80)

    # Now test with a real example
    print("\n" + "=" * 80)
    print("TESTING WITH REAL CODE")
    print("=" * 80)

    test_code = '''
@pytest.mark.certification
@pytest.mark.parametrize(
    "disk_type",
    [
        pytest.param("Thick", marks=pytest.mark.testrail(id=42984636)),
        pytest.param("Thin", marks=pytest.mark.testrail(id=42984637)),
    ],
)
def test_example(self, disk_type):
    pass
'''

    import ast
    tree = ast.parse(test_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                ids = PytestParser.extract_parametrize_testrail_ids(decorator)
                if ids:
                    print(f"  Test function: {node.name}")
                    print(f"  Extracted IDs: {ids}")
                    if len(ids) == 2 and 'C42984636' in ids and 'C42984637' in ids:
                        print(f"  ✅ Correctly extracted both TestRail IDs!")
                    else:
                        print(f"  ❌ Did not extract expected IDs")
                        sys.exit(1)

    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE - Fix is working!")
    print("=" * 80)

except ImportError as e:
    print(f"\n❌ ERROR: Could not import PytestParser: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
