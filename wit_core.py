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

    @abstractmethod
    def log(self): pass

    @abstractmethod
    def checkout(self, commit_id): pass


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
            self.wit_dir.mkdir(parents=True, exist_ok=True)
            self.staging_dir.mkdir(exist_ok=True)
            self.repo_dir.mkdir(exist_ok=True)
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
                # אנחנו לא מעתיקים את תיקיית .wit עצמה
                if source.name == ".wit": return "Skipping .wit directory."
                WitUtils.copy_directory(source, self.staging_dir / source.name)
            return f"Added {path} to staging."
        except Exception as e:
            return f"Failed to add: {e}"

    def commit(self, message: str) -> str:
        if not self.wit_dir.exists(): return "Error: Run 'init' first."
        if not any(self.staging_dir.iterdir()):
            return "Nothing to commit (staging area is empty)."

        commit_id = WitUtils.generate_id()
        new_commit_path = self.repo_dir / commit_id

        try:
            WitUtils.copy_directory(self.staging_dir, new_commit_path)
            metadata = f"Message: {message}\nID: {commit_id}\n"
            (new_commit_path / "metadata.txt").write_text(metadata)

            # עדכון ה-HEAD
            self.refs_path.write_text(f"HEAD={commit_id}")

            # ניקוי ה-staging לאחר קומיט מוצלח
            WitUtils.delete_directory_contents(self.staging_dir)
            return f"Commit {commit_id} created successfully."
        except Exception as e:
            return f"Commit failed: {e}"

    def status(self) -> str:
        if not self.wit_dir.exists(): return "Error: Not a wit repository."

        head = "None"
        if self.refs_path.exists():
            content = self.refs_path.read_text()
            if "HEAD=" in content:
                head = content.split("HEAD=")[1].strip()

        staged_files = [f.name for f in self.staging_dir.iterdir()]
        staged_str = ", ".join(staged_files) if staged_files else "Empty"

        return f"--- Wit Status ---\nHEAD: {head}\nStaged files: {staged_str}\n------------------"

    def log(self) -> str:
        if not self.wit_dir.exists(): return "Error: Run 'init' first."
        commits = list(self.repo_dir.iterdir())
        if not commits: return "No commits yet."

        log_output = "--- Commit History ---\n"
        for commit_path in commits:
            metadata_path = commit_path / "metadata.txt"
            if metadata_path.exists():
                log_output += metadata_path.read_text() + "\n"
        log_output += "----------------------"
        return log_output

    def checkout(self, commit_id: str) -> str:
        if not self.wit_dir.exists(): return "Error: Run 'init' first."
        target_commit = self.repo_dir / commit_id

        if not target_commit.exists():
            return f"Error: Commit ID {commit_id} not found."

        try:
            # משחזרים את תוכן הקומיט לתיקיית העבודה (למעט .wit)
            for item in target_commit.iterdir():
                if item.name == "metadata.txt": continue

                dest = Path.cwd() / item.name
                if item.is_dir():
                    WitUtils.copy_directory(item, dest)
                else:
                    WitUtils.copy_file(item, dest)

            # עדכון ה-HEAD לזה ששיחזרנו
            self.refs_path.write_text(f"HEAD={commit_id}")
            return f"Successfully checked out to {commit_id}."
        except Exception as e:
            return f"Checkout failed: {e}"