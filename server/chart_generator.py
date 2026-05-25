"""
Tests for server.analyzer.CodeAnalyzer

Run with:  pytest tests/test_analyzer.py -v
"""

from server.analyzer import CodeAnalyzer, MAX_FUNCTION_LINES, MAX_FILE_LINES

analyzer = CodeAnalyzer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _issues_of_type(result, issue_type: str):
    return [i for i in result.issues if i.issue_type == issue_type]


# ---------------------------------------------------------------------------
# Long function
# ---------------------------------------------------------------------------

def test_detects_long_function():
    source = "def big_func():\n" + "    x = 1\n" * (MAX_FUNCTION_LINES + 1)
    result = analyzer.analyze_source("test.py", source)
    assert _issues_of_type(result, "long_function"), "Expected a long_function issue."


def test_accepts_short_function():
    source = "def small_func():\n    '''Docs.'''\n    return 1\n"
    result = analyzer.analyze_source("test.py", source)
    assert not _issues_of_type(result, "long_function")


# ---------------------------------------------------------------------------
# Missing docstring
# ---------------------------------------------------------------------------

def test_detects_missing_docstring():
    source = "def no_docs():\n    pass\n"
    result = analyzer.analyze_source("test.py", source)
    assert _issues_of_type(result, "missing_docstring")


def test_accepts_function_with_docstring():
    source = 'def with_docs():\n    """This function is documented."""\n    pass\n'
    result = analyzer.analyze_source("test.py", source)
    assert not _issues_of_type(result, "missing_docstring")


# ---------------------------------------------------------------------------
# Long file
# ---------------------------------------------------------------------------

def test_detects_long_file():
    source = "x = 1\n" * (MAX_FILE_LINES + 1)
    result = analyzer.analyze_source("big_file.py", source)
    assert _issues_of_type(result, "long_file")


def test_accepts_short_file():
    source = "x = 1\n" * 10
    result = analyzer.analyze_source("small_file.py", source)
    assert not _issues_of_type(result, "long_file")


# ---------------------------------------------------------------------------
# Unused variables
# ---------------------------------------------------------------------------

def test_detects_unused_variable():
    source = (
        "def func():\n"
        "    '''Docs.'''\n"
        "    unused = 42\n"
        "    return 1\n"
    )
    result = analyzer.analyze_source("test.py", source)
    assert _issues_of_type(result, "unused_variable")


def test_accepts_used_variable():
    source = (
        "def func():\n"
        "    '''Docs.'''\n"
        "    value = 42\n"
        "    return value\n"
    )
    result = analyzer.analyze_source("test.py", source)
    assert not _issues_of_type(result, "unused_variable")


def test_underscore_variable_not_flagged():
    source = (
        "def func():\n"
        "    '''Docs.'''\n"
        "    _ignored = some_call()\n"
        "    return 1\n"
    )
    result = analyzer.analyze_source("test.py", source)
    assert not _issues_of_type(result, "unused_variable")


# ---------------------------------------------------------------------------
# Non-English variables (bonus)
# ---------------------------------------------------------------------------

def test_detects_hebrew_variable():
    source = "מספר = 5\n"
    result = analyzer.analyze_source("test.py", source)
    assert result.has_non_english_variables


def test_accepts_english_variable():
    source = "number = 5\n"
    result = analyzer.analyze_source("test.py", source)
    assert not result.has_non_english_variables


# ---------------------------------------------------------------------------
# Syntax error resilience
# ---------------------------------------------------------------------------

def test_handles_syntax_error_gracefully():
    source = "def broken(\n"
    result = analyzer.analyze_source("broken.py", source)
    assert result.issues, "Expected at least one issue for broken syntax."
    assert result.function_count == 0


# ---------------------------------------------------------------------------
# Function length tracking
# ---------------------------------------------------------------------------

def test_function_lengths_recorded():
    source = (
        "def short():\n"
        "    '''Docs.'''\n"
        "    return 1\n"
        "\n"
        "def also_short():\n"
        "    '''Docs.'''\n"
        "    return 2\n"
    )
    result = analyzer.analyze_source("test.py", source)
    assert len(result.function_lengths) == 2
