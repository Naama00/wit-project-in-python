"""
CodeAnalyzer – AST-based code quality analysis for Python source files.

Checks performed:
  - long_function:        function body exceeds MAX_FUNCTION_LINES lines
  - long_file:            file exceeds MAX_FILE_LINES total lines
  - missing_docstring:    function has no docstring
  - unused_variable:      variable assigned but never read
  - non_english_variable: identifier contains non-ASCII characters (bonus)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List

from server.models import CodeIssue, FileAnalysisResult

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

MAX_FUNCTION_LINES = 20
MAX_FILE_LINES = 200


# ---------------------------------------------------------------------------
# CodeAnalyzer
# ---------------------------------------------------------------------------

class CodeAnalyzer:
    """
    Analyses a single Python source file using the built-in ast module.

    Usage::

        result = CodeAnalyzer().analyze_file(Path("my_script.py"))
        result = CodeAnalyzer().analyze_source("my_script.py", source_code)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_file(self, filepath: Path) -> FileAnalysisResult:
        """Reads *filepath* from disk and analyses it."""
        source = filepath.read_text(encoding="utf-8", errors="replace")
        return self.analyze_source(filepath.name, source)

    def analyze_source(self, filename: str, source: str) -> FileAnalysisResult:
        """
        Analyses *source* (a string of Python code) and returns a
        :class:`FileAnalysisResult`.

        Args:
            filename: Display name used in the result (e.g. ``"main.py"``).
            source:   Full source code of the file.
        """
        issues: List[CodeIssue] = []
        function_lengths: List[int] = []
        total_lines = len(source.splitlines())

        # File-level check
        if total_lines > MAX_FILE_LINES:
            issues.append(CodeIssue(
                function_name="<module>",
                line_number=1,
                issue_type="long_file",
                detail=f"File has {total_lines} lines (max {MAX_FILE_LINES}).",
            ))

        # Parse AST – if the file has syntax errors we return what we have
        try:
            tree = ast.parse(source, filename=filename)
        except SyntaxError as exc:
            issues.append(CodeIssue(
                function_name="<module>",
                line_number=exc.lineno or 1,
                issue_type="long_file",   # closest available type for parse errors
                detail=f"SyntaxError: {exc.msg}",
            ))
            return FileAnalysisResult(
                filename=filename,
                total_lines=total_lines,
                function_count=0,
                issues=issues,
                function_lengths=[],
                has_non_english_variables=False,
            )

        # Walk the tree
        has_non_english = False

        for node in ast.walk(tree):
            # ----------------------------------------------------------------
            # Check every Name / arg / FunctionDef for non-ASCII identifiers
            # ----------------------------------------------------------------
            identifier = None
            if isinstance(node, (ast.Name, ast.FunctionDef, ast.AsyncFunctionDef)):
                identifier = node.id if isinstance(node, ast.Name) else node.name
            elif isinstance(node, ast.arg):
                identifier = node.arg

            if identifier and self._is_non_english(identifier):
                has_non_english = True
                issues.append(CodeIssue(
                    function_name="<module>",
                    line_number=getattr(node, "lineno", 1),
                    issue_type="non_english_variable",
                    detail=f"Non-English identifier: '{identifier}'.",
                ))

            # ----------------------------------------------------------------
            # Function-level checks
            # ----------------------------------------------------------------
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_issues, length = self._check_function(node, source)
                issues.extend(func_issues)
                function_lengths.append(length)

        # Unused-variable check (requires full tree)
        issues.extend(self._check_unused_variables(tree))

        return FileAnalysisResult(
            filename=filename,
            total_lines=total_lines,
            function_count=len(function_lengths),
            issues=issues,
            function_lengths=function_lengths,
            has_non_english_variables=has_non_english,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, source: str
    ) -> tuple[List[CodeIssue], int]:
        """
        Checks a single function node for long_function and missing_docstring.

        Returns (list_of_issues, function_line_count).
        """
        issues: List[CodeIssue] = []

        # Calculate function length
        source_lines = source.splitlines()
        start = node.lineno - 1          # ast lines are 1-indexed
        end = node.end_lineno or start   # end_lineno available in Python 3.8+
        length = end - start + 1
        function_lengths_local = length

        if length > MAX_FUNCTION_LINES:
            issues.append(CodeIssue(
                function_name=node.name,
                line_number=node.lineno,
                issue_type="long_function",
                detail=(
                    f"Function '{node.name}' is {length} lines long "
                    f"(max {MAX_FUNCTION_LINES})."
                ),
            ))

        # Missing docstring check
        if not (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            issues.append(CodeIssue(
                function_name=node.name,
                line_number=node.lineno,
                issue_type="missing_docstring",
                detail=f"Function '{node.name}' has no docstring.",
            ))

        return issues, function_lengths_local

    def _check_unused_variables(self, tree: ast.Module) -> List[CodeIssue]:
        """
        Detects variables that are assigned but never read within the same
        function scope.

        Limitation: only checks simple ``Name`` assignments (``x = ...``).
        Augmented assignments (``x += 1``) and attribute assignments are
        out of scope.
        """
        issues: List[CodeIssue] = []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Collect all assigned names and all loaded names in this function
            assigned: dict[str, int] = {}   # name → line number of first assignment
            loaded: set[str] = set()

            for child in ast.walk(node):
                if isinstance(child, ast.Name):
                    if isinstance(child.ctx, ast.Store):
                        # Only record the FIRST assignment
                        if child.id not in assigned:
                            assigned[child.id] = child.lineno
                    elif isinstance(child.ctx, ast.Load):
                        loaded.add(child.id)

            for name, lineno in assigned.items():
                if name not in loaded and not name.startswith("_"):
                    issues.append(CodeIssue(
                        function_name=node.name,
                        line_number=lineno,
                        issue_type="unused_variable",
                        detail=f"Variable '{name}' is assigned but never used.",
                    ))

        return issues

    @staticmethod
    def _is_non_english(name: str) -> bool:
        """Returns True if *name* contains any non-ASCII character."""
        try:
            name.encode("ascii")
            return False
        except UnicodeEncodeError:
            return True