import ast
import re
import os
import logging
import sys

logger = logging.getLogger(__name__)


def safe_unparse(node):
    """
    Safely convert AST node to source code string.
    Uses ast.unparse() for Python 3.9+ or astor for older versions.
    Falls back to basic string extraction if neither is available.
    """
    # Try ast.unparse (Python 3.9+)
    if hasattr(ast, 'unparse'):
        try:
            return ast.unparse(node)
        except Exception as e:
            logger.debug(f"ast.unparse failed: {e}")

    # Try astor library (if installed)
    try:
        import astor
        return astor.to_source(node).strip()
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"astor.to_source failed: {e}")

    # Fallback: Basic extraction using ast.get_source_segment (Python 3.8+)
    # or manual reconstruction for simple cases
    try:
        # For Name nodes
        if isinstance(node, ast.Name):
            return node.id
        # For Attribute nodes (e.g., pytest.mark.testrail)
        elif isinstance(node, ast.Attribute):
            value_str = safe_unparse(node.value) if hasattr(node, 'value') else ''
            return f"{value_str}.{node.attr}" if value_str else node.attr
        # For Call nodes
        elif isinstance(node, ast.Call):
            func_str = safe_unparse(node.func)
            # Try to get arguments
            args = []
            for arg in node.args:
                if isinstance(arg, ast.Constant):
                    args.append(repr(arg.value))
                elif isinstance(arg, (ast.Num, ast.Str)):  # Python 3.7 compatibility
                    args.append(repr(arg.n if hasattr(arg, 'n') else arg.s))

            kwargs = []
            for keyword in node.keywords:
                arg_name = keyword.arg
                if isinstance(keyword.value, ast.Constant):
                    kwargs.append(f"{arg_name}={repr(keyword.value.value)}")
                elif isinstance(keyword.value, ast.List):
                    # Handle list values like id=[123, 456]
                    list_items = []
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant):
                            list_items.append(str(elt.value))
                        elif hasattr(elt, 'n'):  # ast.Num in Python 3.7
                            list_items.append(str(elt.n))
                    kwargs.append(f"{arg_name}=[{', '.join(list_items)}]")
                elif hasattr(keyword.value, 'n'):  # ast.Num in Python 3.7
                    kwargs.append(f"{arg_name}={keyword.value.n}")

            all_args = args + kwargs
            return f"{func_str}({', '.join(all_args)})"
        # For simple constants
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, (ast.Num, ast.Str)):  # Python 3.7 compatibility
            return repr(node.n if hasattr(node, 'n') else node.s)
    except Exception as e:
        logger.debug(f"Fallback unparse failed: {e}")

    # Last resort: return empty string
    return ""


class PytestParser:
    """Parser for extracting pytest test information from Python files."""

    @staticmethod
    def extract_testrail_id(text):
        """
        Extract TestRail case ID from various formats:
        - @pytest.mark.testrail('C123')
        - @pytest.mark.testrail(id=123)  <-- Common format in vme-test-repo
        - @pytest.mark.testrail(id=[123, 456])  <-- Multiple IDs
        - @pytest.mark.testrail_id('C123')
        - testrail_case_id = 'C123' in docstring
        - TestRail Case: C123 in docstring

        For multiple IDs, returns comma-separated string: "C123,C456"
        """
        patterns = [
            # Multiple IDs in list: @pytest.mark.testrail(id=[123, 456])
            (r'testrail\s*\(\s*id\s*=\s*\[([0-9,\s]+)\]\s*\)', 'list'),
            # Single ID: @pytest.mark.testrail(id=123456)
            (r'testrail\s*\(\s*id\s*=\s*(\d+)\s*\)', 'single'),
            # Standard formats with C prefix
            (r'testrail\([\'"]([Cc]\d+)[\'"]\)', 'with_c'),
            (r'testrail_id\([\'"]([Cc]\d+)[\'"]\)', 'with_c'),
            (r'testrail[_\s]*case[_\s]*id[:\s]*[\'"]?([Cc]\d+)[\'"]?', 'with_c'),
            (r'TestRail[_\s]*Case[:\s]*([Cc]\d+)', 'with_c'),
            (r'@testrail\([\'"]([Cc]\d+)[\'"]\)', 'with_c'),
        ]

        for pattern, format_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_text = match.group(1)

                if format_type == 'list':
                    # Handle multiple IDs: "123, 456, 789" -> "C123,C456,C789"
                    ids = re.findall(r'\d+', matched_text)
                    case_ids = [f'C{id}' for id in ids if id]
                    return ','.join(case_ids) if case_ids else None

                elif format_type == 'single':
                    # Single numeric ID
                    return 'C' + matched_text

                else:  # format_type == 'with_c'
                    # ID with C prefix
                    case_id = matched_text.upper()
                    if not case_id.startswith('C'):
                        case_id = 'C' + case_id
                    return case_id

        return None

    @staticmethod
    def extract_markers(decorators):
        """
        Extract pytest markers from decorator list.
        Returns a list of marker names (e.g., ['always', 'run', 'testrail', 'smoke'])
        Excludes the testrail marker as it's stored separately.
        """
        markers = []

        for decorator in decorators:
            try:
                decorator_source = safe_unparse(decorator)

                # Match pytest.mark.* patterns
                # Examples: @pytest.mark.always, @pytest.mark.run(order=1), @pytest.mark.smoke
                match = re.search(r'pytest\.mark\.(\w+)', decorator_source)
                if match:
                    marker_name = match.group(1)
                    # Exclude 'testrail' as it's stored separately
                    if marker_name != 'testrail' and marker_name not in markers:
                        markers.append(marker_name)
            except Exception as e:
                logger.debug(f"Could not parse decorator: {e}")
                continue

        return markers

    @staticmethod
    def parse_test_file(file_path, file_content):
        """Parse a Python test file and extract test information."""
        tests = []

        try:
            tree = ast.parse(file_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_info = {
                        'test_id': None,
                        'test_name': node.name,
                        'test_file': file_path,
                        'test_class': None,
                        'description': ast.get_docstring(node),
                        'markers': [],
                        'testrail_case_id': None
                    }

                    # Get class name if test is inside a class
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            for child in parent.body:
                                if child == node:
                                    test_info['test_class'] = parent.name
                                    break

                    # Build test ID (file path + class + function name)
                    if test_info['test_class']:
                        test_info['test_id'] = f"{file_path}::{test_info['test_class']}::{test_info['test_name']}"
                    else:
                        test_info['test_id'] = f"{file_path}::{test_info['test_name']}"

                    # Extract markers from decorators
                    test_info['markers'] = PytestParser.extract_markers(node.decorator_list)

                    # Extract TestRail ID from decorators
                    for decorator in node.decorator_list:
                        decorator_source = safe_unparse(decorator)
                        testrail_id = PytestParser.extract_testrail_id(decorator_source)
                        if testrail_id:
                            test_info['testrail_case_id'] = testrail_id
                            break

                    # If not found in decorators, check docstring
                    if not test_info['testrail_case_id'] and test_info['description']:
                        testrail_id = PytestParser.extract_testrail_id(test_info['description'])
                        if testrail_id:
                            test_info['testrail_case_id'] = testrail_id

                    tests.append(test_info)

            logger.info(f"Parsed {len(tests)} tests from {file_path}")

        except SyntaxError as e:
            logger.error(f"Syntax error parsing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

        return tests

    @staticmethod
    def parse_repository(git_service):
        """Parse all test files in a repository."""
        all_tests = []

        test_files = git_service.find_test_files()
        logger.info(f"Found {len(test_files)} test files to parse")

        for test_file in test_files:
            content = git_service.get_file_content(test_file)
            if content:
                tests = PytestParser.parse_test_file(test_file, content)
                all_tests.extend(tests)

        logger.info(f"Total tests parsed: {len(all_tests)}")
        return all_tests

