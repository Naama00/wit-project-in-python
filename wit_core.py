from utils import WitUtils
from pathlib import Path
from abc import ABC, abstractmethod
class WitInterface(ABC):
    @abstractmethod
    def init(self): pass

    @abstractmethod
    def add(self, path): pass

    @abstractmethod
    def commit(self, message): pass

    @abstractmethod
    def status(self): pass

class WitImplementation(WitInterface):
    def __init__(self):
        self.wit_dir = Path.cwd() / ".wit"
        self.staging_dir = self.wit_dir / "staging"
        self.repo_dir = self.wit_dir / "repository"
        self.refs_path = self.wit_dir / "references.txt"

    def init(self) -> str:
        if self.wit_dir.exists():
            return "Error: .wit directory already exists."
        try:
            self.wit_dir.mkdir()
            self.staging_dir.mkdir()
            self.repo_dir.mkdir()
            self.refs_path.touch()
            (Path.cwd() / ".witignore").touch()
            return "Initialized empty Wit repository."
        except Exception as e:
            return f"Error: {e}"

    def add(self, path: str) -> str:
        source = Path(path)
        if not self.wit_dir.exists(): return "Error: Run 'init' first."
        if not source.exists(): return f"Error: {path} not found."

        try:
            if source.is_file():
                WitUtils.copy_file(source, self.staging_dir / source.name)
            elif source.is_dir():
                WitUtils.copy_directory(source, self.staging_dir / source.name)
            return f"Added {path} to staging."
        except Exception as e:
            return f"Failed to add: {e}"

    def commit(self, message: str) -> str:
        if not any(self.staging_dir.iterdir()):
            return "Nothing to commit."

        commit_id = WitUtils.generate_id()
        new_commit_path = self.repo_dir / commit_id

        try:
            WitUtils.copy_directory(self.staging_dir, new_commit_path)
            with open(new_commit_path / "metadata.txt", "w") as f:
                f.write(f"Message: {message}\nID: {commit_id}")

            self.refs_path.write_text(f"HEAD={commit_id}")
            return f"Commit {commit_id} created."
        except Exception as e:
            return f"Commit failed: {e}"

    # שאר הפונקציות (status, log, checkout) נשארות דומות אך משתמשות ב-WitUtils