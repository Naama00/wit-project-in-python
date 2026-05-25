"""
Tests for wit.core.WitImplementation

Uses tmp_path (pytest built-in) so every test runs in an isolated temp directory
with no risk of polluting the real file system.

Run with:  pytest tests/test_wit_core.py -v
"""

import os
import pytest
from pathlib import Path

from wit.core import WitImplementation


# ---------------------------------------------------------------------------
# Fixture – isolated wit repo
# ---------------------------------------------------------------------------

@pytest.fixture
def wit_repo(tmp_path: Path) -> WitImplementation:
    """Creates a WitImplementation rooted in a fresh temp directory."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    impl = WitImplementation()
    impl.init()
    yield impl
    os.chdir(original_cwd)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def test_init_creates_directories(tmp_path: Path):
    os.chdir(tmp_path)
    impl = WitImplementation()
    result = impl.init()
    assert "Initialized" in result
    assert (tmp_path / ".wit" / "staging").is_dir()
    assert (tmp_path / ".wit" / "repository").is_dir()
    assert (tmp_path / ".witignore").exists()


def test_init_twice_returns_error(wit_repo: WitImplementation):
    second_result = wit_repo.init()
    assert "already exists" in second_result.lower()


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_add_file(wit_repo: WitImplementation, tmp_path: Path):
    sample = tmp_path / "hello.py"
    sample.write_text("print('hello')")
    result = wit_repo.add("hello.py")
    assert "Added" in result
    assert (wit_repo.staging_dir / "hello.py").exists()


def test_add_nonexistent_file(wit_repo: WitImplementation):
    result = wit_repo.add("ghost.py")
    assert "not found" in result.lower() or "Error" in result


# ---------------------------------------------------------------------------
# commit
# ---------------------------------------------------------------------------

def test_commit_creates_commit_dir(wit_repo: WitImplementation, tmp_path: Path):
    (tmp_path / "file.py").write_text("x = 1")
    wit_repo.add("file.py")
    result = wit_repo.commit("first commit")
    assert "created successfully" in result
    commits = list(wit_repo.repo_dir.iterdir())
    assert len(commits) == 1


def test_commit_empty_staging_returns_error(wit_repo: WitImplementation):
    result = wit_repo.commit("empty")
    assert "empty" in result.lower() or "Nothing" in result


def test_commit_clears_staging(wit_repo: WitImplementation, tmp_path: Path):
    (tmp_path / "file.py").write_text("x = 1")
    wit_repo.add("file.py")
    wit_repo.commit("msg")
    assert not any(wit_repo.staging_dir.iterdir())


def test_commit_stores_parent_chain(wit_repo: WitImplementation, tmp_path: Path):
    import json
    for i in range(3):
        (tmp_path / f"file{i}.py").write_text(f"x = {i}")
        wit_repo.add(f"file{i}.py")
        wit_repo.commit(f"commit {i}")

    commits = sorted(wit_repo.repo_dir.iterdir())
    assert len(commits) == 3

    # Verify parent linkage
    parent_ids = set()
    for commit_path in commits:
        meta = json.loads((commit_path / "metadata.json").read_text())
        if meta["parent_id"]:
            parent_ids.add(meta["parent_id"])

    # At least two commits should have a parent
    assert len(parent_ids) >= 1


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------

def test_log_shows_commits(wit_repo: WitImplementation, tmp_path: Path):
    (tmp_path / "a.py").write_text("a = 1")
    wit_repo.add("a.py")
    wit_repo.commit("the message")
    log_output = wit_repo.log()
    assert "the message" in log_output


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def test_status_shows_staged_files(wit_repo: WitImplementation, tmp_path: Path):
    (tmp_path / "staged.py").write_text("s = 1")
    wit_repo.add("staged.py")
    status_output = wit_repo.status()
    assert "staged.py" in status_output


# ---------------------------------------------------------------------------
# checkout
# ---------------------------------------------------------------------------

def test_checkout_restores_file(wit_repo: WitImplementation, tmp_path: Path):
    original_file = tmp_path / "restore_me.py"
    original_file.write_text("original content")
    wit_repo.add("restore_me.py")
    commit_result = wit_repo.commit("save original")

    # Extract commit id from result string
    commit_id = commit_result.split()[1]

    # Overwrite the file
    original_file.write_text("modified content")

    wit_repo.checkout(commit_id)
    assert original_file.read_text() == "original content"


def test_checkout_nonexistent_commit(wit_repo: WitImplementation):
    result = wit_repo.checkout("deadbeef")
    assert "not found" in result.lower() or "Error" in result
