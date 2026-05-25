# CodeGuard 🛡️

> Automatic code-quality analysis integrated directly into `wit push`.

CodeGuard combines a lightweight version-control system (**wit**) with a
**FastAPI** backend that analyses every staged Python file using the `ast`
module and returns visual charts with actionable insights.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Folder Structure](#folder-structure)
3. [Installation](#installation)
4. [Running the Server](#running-the-server)
5. [Using wit](#using-wit)
6. [API Endpoints](#api-endpoints)
7. [Code Quality Checks](#code-quality-checks)
8. [Generated Charts](#generated-charts)

---

## Project Overview

Every time a developer runs `wit push`, staged `.py` files are sent to the
CodeGuard server which:

1. Parses each file with Python's built-in `ast` module.
2. Detects common code-quality issues (long functions, missing docstrings, etc.).
3. Generates PNG charts summarising the findings.
4. Returns a structured JSON response that `wit` prints in a readable format.

---

## Folder Structure

```
codeguard/
├── wit/                    # Version-control engine
│   ├── __init__.py
│   ├── cli.py              # Click CLI (entry point for the `wit` command)
│   ├── core.py             # All VCS logic + push integration
│   └── file_utils.py       # Low-level file system helpers
│
├── server/                 # FastAPI backend
│   ├── __init__.py
│   ├── main.py             # App factory + static file mounting
│   ├── router.py           # /analyze and /alerts endpoints
│   ├── analyzer.py         # AST-based code analysis
│   ├── chart_generator.py  # Matplotlib chart generation
│   ├── models.py           # Pydantic request/response schemas
│   └── history_store.py    # Persistent push history (for line chart)
│
├── tests/
│   ├── test_analyzer.py    # Unit tests – analyzer
│   ├── test_wit_core.py    # Unit tests – wit VCS
│   └── sample_files/       # Python files used as test fixtures
│       ├── clean_code.py
│       └── messy_code.py
│
├── graphs/                 # Auto-created at runtime; PNG charts saved here
│   └── .gitkeep
│
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md
```

---

## Installation

```bash
# 1 – Clone the repository
git clone <your-repo-url>
cd codeguard

# 2 – Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3 – Install all dependencies
pip install -r requirements.txt

# 4 – Install the `wit` command globally (editable mode)
pip install -e .
```

---

## Running the Server

```bash
uvicorn server.main:app --reload
```

The server starts on **http://127.0.0.1:8000**.  
Interactive API docs are available at **http://127.0.0.1:8000/docs**.

---

## Using wit

```bash
# Initialise a repository in the current directory
wit init

# Stage files
wit add my_script.py
wit add src/

# Commit staged files
wit commit -m "add initial implementation"

# View history
wit log

# Push staged files to CodeGuard for analysis
wit push

# Restore a previous commit
wit checkout <commit-id>
```

The server URL defaults to `http://127.0.0.1:8000` and is stored in
`.wit/config.json` so it can be changed without touching any code.

---

## API Endpoints

| Method | Endpoint   | Description                                          |
|--------|------------|------------------------------------------------------|
| POST   | `/analyze` | Full analysis: AST checks + PNG chart generation     |
| POST   | `/alerts`  | Lightweight: AST checks only, no charts              |

Both endpoints accept one or more `.py` files as `multipart/form-data`.

**Example with curl:**
```bash
curl -X POST http://127.0.0.1:8000/analyze \
     -F "files=@my_script.py" \
     -F "files=@another.py"
```

---

## Code Quality Checks

| Check                    | Threshold              | Issue Type              |
|--------------------------|------------------------|-------------------------|
| Function too long        | > 20 lines             | `long_function`         |
| File too long            | > 200 lines            | `long_file`             |
| Missing docstring        | any function           | `missing_docstring`     |
| Unused variable          | assigned but not read  | `unused_variable`       |
| Non-English identifiers  | any non-ASCII name     | `non_english_variable`  |

---

## Generated Charts

After each `wit push` the server saves four PNG charts to `graphs/` and
serves them at `/graphs/<filename>`:

| File                                 | Description                              |
|--------------------------------------|------------------------------------------|
| `histogram_function_lengths.png`     | Distribution of function lengths         |
| `pie_chart_issue_types.png`          | Proportion of each issue type            |
| `bar_chart_issues_per_file.png`      | Issue count per analysed file            |
| `line_chart_issues_over_time.png`    | Total issues per push over time (bonus)  |

---

## Running Tests

```bash
pytest tests/ -v
```
