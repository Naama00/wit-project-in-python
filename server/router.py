"""
Pydantic data models shared across the server package.

Keeping models in a dedicated module avoids circular imports and gives a
single source of truth for every API schema.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Issue types
# ---------------------------------------------------------------------------

IssueType = Literal[
    "long_function",
    "long_file",
    "missing_docstring",
    "unused_variable",
    "non_english_variable",
]


class CodeIssue(BaseModel):
    """Represents a single code quality problem found in a file."""

    function_name: str = Field(
        description="Name of the function that contains the issue, or '<module>' for file-level issues."
    )
    line_number: int = Field(ge=1, description="Source line where the issue begins.")
    issue_type: IssueType = Field(description="Machine-readable category of the issue.")
    detail: str = Field(description="Human-readable explanation shown to the developer.")


# ---------------------------------------------------------------------------
# Per-file analysis result
# ---------------------------------------------------------------------------

class FileAnalysisResult(BaseModel):
    """All analysis data collected for a single Python source file."""

    filename: str
    total_lines: int = Field(ge=0)
    function_count: int = Field(ge=0)
    issues: List[CodeIssue] = Field(default_factory=list)
    function_lengths: List[int] = Field(
        default_factory=list,
        description="Line-count of every function, used for the histogram chart.",
    )
    has_non_english_variables: bool = Field(
        default=False,
        description="True when at least one identifier contains non-ASCII characters.",
    )


# ---------------------------------------------------------------------------
# Full analysis response
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    """Top-level response returned by POST /analyze."""

    files: List[FileAnalysisResult]
    total_issues: int = Field(ge=0)
    graphs: List[str] = Field(
        default_factory=list,
        description="Server-relative URLs of the generated PNG charts.",
    )


# ---------------------------------------------------------------------------
# Alerts-only response
# ---------------------------------------------------------------------------

class AlertsResponse(BaseModel):
    """Lightweight response returned by POST /alerts (no charts)."""

    files: List[FileAnalysisResult]
    total_issues: int = Field(ge=0)
