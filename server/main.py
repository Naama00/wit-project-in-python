"""
CodeGuard Server – FastAPI application entry point.

Start with:
    uvicorn server.main:app --reload

Or via the helper script:
    python -m server.main
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from server.router import router

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CodeGuard",
    description=(
        "Analyses Python source files for code-quality issues "
        "(long functions, missing docstrings, unused variables, …) "
        "and generates visual reports."
    ),
    version="1.0.0",
)

# Allow the wit CLI (running locally) to reach the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated PNG charts as static files under /graphs/
GRAPHS_DIR = Path("graphs")
GRAPHS_DIR.mkdir(exist_ok=True)
app.mount("/graphs", StaticFiles(directory=str(GRAPHS_DIR)), name="graphs")

# Register all API routes
app.include_router(router)


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=True)
