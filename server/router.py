"""
API router for the CodeGuard server.

Endpoints
---------
POST /analyze   – Analyse uploaded Python files and return issues + charts.
POST /alerts    – Lightweight analysis with issues only (no chart generation).
GET  /health    – Simple liveness check.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from server.analyzer import CodeAnalyzer
from server.chart_generator import ChartGenerator
from server.history_store import HistoryStore, PushRecord
from server.models import AnalysisResponse, AlertsResponse, FileAnalysisResult

router = APIRouter()
_analyzer = CodeAnalyzer()
_history_store = HistoryStore()
_chart_generator = ChartGenerator(history_store=_history_store)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _analyse_files(files: List[UploadFile]) -> List[FileAnalysisResult]:
    """Decode and analyse each uploaded file."""
    results: List[FileAnalysisResult] = []
    for upload in files:
        try:
            source = upload.file.read().decode("utf-8", errors="replace")
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read file '{upload.filename}': {exc}",
            )
        results.append(_analyzer.analyze_source(upload.filename or "unknown.py", source))
    return results


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health() -> JSONResponse:
    """Liveness probe – always returns 200 OK."""
    return JSONResponse({"status": "ok"})


@router.post("/analyze", response_model=AnalysisResponse)
def analyze(files: List[UploadFile] = File(...)) -> AnalysisResponse:
    """
    Accepts one or more Python source files and returns a full analysis
    including generated PNG charts.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    results = _analyse_files(files)
    total_issues = sum(len(r.issues) for r in results)

    # Persist to history so the line chart can track trends
    _history_store.append(PushRecord(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        total_issues=total_issues,
        filenames=[r.filename for r in results],
    ))

    graphs = _chart_generator.generate_all(results)

    return AnalysisResponse(
        files=results,
        total_issues=total_issues,
        graphs=graphs,
    )


@router.post("/alerts", response_model=AlertsResponse)
def alerts(files: List[UploadFile] = File(...)) -> AlertsResponse:
    """
    Lightweight endpoint – returns issues only, no chart generation.
    Useful for CI pipelines where speed matters more than visualisation.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    results = _analyse_files(files)
    total_issues = sum(len(r.issues) for r in results)

    return AlertsResponse(files=results, total_issues=total_issues)
