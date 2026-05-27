"""
Tests for server.analyzer
F
Run with:  pytest tests/test_analyzer.py -v
"""

import pytest
from server.analyzer import CodeAnalyzer


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def analyze(source: str):
    """Convenience wrapper – analyze a code string directly."""
    return CodeAnalyzer().analyze_source("<test>", source)


# ---------------------------------------------------------------------------
# long_function
# ---------------------------------------------------------------------------

def test_long_function_detected():
    # Build a function with 25 lines of body
    body = "\n".join(f"    x{i} = {i}" for i in range(25))
    source = f"def big_func():\n    '''doc'''\n{body}\n"
    result = analyze(source)
    types = [i.issue_type for i in result.issues]
    assert "long_function" in types


def test_short_function_no_issue():
    source = "def small():\n    '''doc'''\n    return 1\n"
    result = analyze(source)
    types = [i.issue_type for i in result.issues]
    assert "long_function" not in types


# ---------------------------------------------------------------------------
# missing_docstring
# ---------------------------------------------------------------------------

def test_missing_docstring_detected():
    source = "def no_doc():\n    x = 1\n"
    result = analyze(source)
    types = [i.issue_type for i in result.issues]
    assert "missing_docstring" in types


def test_docstring_present_no_issue():
    source = "def with_doc():\n    '''I have a docstring.'''\n    return 1\n"
    result = analyze(source)
    types = [i.issue_type for i in result.issues]
    assert "missing_docstring" not in types


# ---------------------------------------------------------------------------
# unused_variable
# ---------------------------------------------------------------------------

def test_unused_variable_detected():
    source = "def func():\n    '''doc'''\n    unused = 42\n"
    result = analyze(source)
    types = [i.issue_type for i in result.issues]
    assert "unused_variable" in types


def test_used_variable_no_issue():
    source = "def func():\n    '''doc'''\n    x = 1\n    return x\n"
    result = analyze(source)
    types = [i.issue_type for i in result.issues]
    assert "unused_variable" not in types


# ---------------------------------------------------------------------------
# non_english_variable (bonus)
# ---------------------------------------------------------------------------

def test_non_english_variable_detected():
    source = "def func():\n    '''doc'''\n    מספר = 5\n    return מספר\n"
    result = analyze(source)
    assert result.has_non_english_variables is True


def test_english_variable_no_flag():
    source = "def func():\n    '''doc'''\n    number = 5\n    return number\n"
    result = analyze(source)
    assert result.has_non_english_variables is False