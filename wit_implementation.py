import shutil
import uuid
import hashlib
from pathlib import Path
from wit_interface import WitInterface


class WitImplementation(WitInterface):
    """מימוש אמיתי של ממשק Wit באמצעות מערכת הקבצים."""

    def __init__(self):
        # הגדרת נתיבים בסיסיים
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
            # קובץ התעלמות
            (Path.cwd() / ".witignore").touch()
            return "Initialized empty Wit repository and created .witignore"
        except Exception as e:
            return f"Error: {e}"

    def add(self, path: str) -> str:
        source = Path(path)
        if not self.wit_dir.exists():
            return "Error: Please run 'init' first."
        if not source.exists():
            return f"Error: Path '{path}' does not exist."

        # קריאת חוקי התעלמות
        ignored_patterns = []
        ignore_file_path = Path.cwd() / ".witignore"
        if ignore_file_path.exists():
            ignored_patterns = [line.strip() for line in ignore_file_path.read_text().splitlines() if line.strip()]

        # בדיקת תבניות התעלמות
        for pattern in ignored_patterns:
            if source.match(pattern) or any(parent.match(pattern) for parent in source.parents):
                return f"Ignoring {source.name} (matches pattern '{pattern}' in .witignore)"

        # העתקה ל-staging
        try:
            if source.is_file():
                shutil.copy(source, self.staging_dir / source.name)
                return f"Successfully added {source.name} to staging."
            elif source.is_dir():
                dest_dir = self.staging_dir / source.name
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(source, dest_dir)
                return f"Successfully added directory {source.name} to staging."
        except Exception as e:
            return f"Failed to add: {e}"

    def commit(self, message: str) -> str:
        if not any(self.staging_dir.iterdir()):
            return "Nothing to commit (staging area is empty)."

        commit_id = str(uuid.uuid4())[:8]
        new_commit_path = self.repo_dir / commit_id

        try:
            # העתקת תוכן ה-staging לתיקיית הקומיט
            shutil.copytree(self.staging_dir, new_commit_path)

            # שמירת metadata
            with open(new_commit_path / "metadata.txt", "w", encoding="utf-8") as f:
                f.write(f"Message: {message}\n")
                f.write(f"ID: {commit_id}\n")

            # עדכון HEAD
            with open(self.refs_path, "w", encoding="utf-8") as f:
                f.write(f"HEAD={commit_id}")

            # ניקוי staging
            for item in self.staging_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

            return f"Successfully created commit: {commit_id}\nMessage: {message}"
        except Exception as e:
            return f"Commit failed: {e}"

    def status(self) -> str:
        if not self.wit_dir.exists():
            return "Error: Not a wit repository."

        # שימוש בפונקציות עזר פנימיות
        staged_files = self._get_staged_files()
        last_commit_files = self._get_last_commit_files()
        head_id = self._get_head_id()

        working_dir_files = set()
        for p in Path.cwd().rglob('*'):
            if self._is_ignored(p) or p.is_dir() or ".wit" in p.parts:
                continue
            working_dir_files.add(p.relative_to(Path.cwd()).as_posix())

        # חישוב שינויים
        modified_not_staged = set()
        deleted_not_staged = set()
        for f in working_dir_files:
            current_file_path = Path.cwd() / f
            staged_file_path = self.staging_dir / f
            if f in staged_files:
                if self._get_file_hash(current_file_path) != self._get_file_hash(staged_file_path):
                    modified_not_staged.add(f)
            elif head_id:
                last_commit_dir = self.repo_dir / head_id
                last_file_path = last_commit_dir / f
                if last_file_path.exists():
                    if self._get_file_hash(current_file_path) != self._get_file_hash(last_file_path):
                        modified_not_staged.add(f)

        if head_id:
            for f in last_commit_files:
                if not (Path.cwd() / f).exists():
                    deleted_not_staged.add(f)

        untracked = working_dir_files - last_commit_files - staged_files

        # בניית מחרוזת הסטטוס
        status_output = "On branch master\n\n"

        status_output += "Changes to be committed:\n"
        if staged_files:
            for f in staged_files: status_output += f"\tnew file: {f}\n"
        else:
            status_output += "\t(no changes staged for commit)\n"

        status_output += "\nChanges not staged for commit:\n"
        changes_not_staged = modified_not_staged | deleted_not_staged
        if changes_not_staged:
            for f in modified_not_staged: status_output += f"\tmodified: {f}\n"
            for f in deleted_not_staged: status_output += f"\tdeleted: {f}\n"
        else:
            status_output += "\t(no changes added to commit)\n"

        status_output += "\nUntracked files:\n"
        if untracked:
            for f in untracked: status_output += f"\t{f}\n"
        else:
            status_output += "\t(nothing untracked)\n"

        return status_output

    def checkout(self, commit_id: str) -> str:
        target_commit_dir = self.repo_dir / commit_id
        if not self.wit_dir.exists():
            return "Error: Not a wit repository."
        if not target_commit_dir.exists():
            return f"Error: Commit ID {commit_id} not found."
        if any(self.staging_dir.iterdir()):
            return "Error: You have uncommitted changes. Please commit or stash them."

        try:
            # מחיקת קבצים נוכחיים
            for item in Path.cwd().iterdir():
                if item.name in [".wit", ".venv", ".git", "wit.py", "wit.bat"]: continue
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

            # העתקת קבצי הקומיט
            for item in target_commit_dir.iterdir():
                if item.name == "metadata.txt": continue
                if item.is_dir():
                    shutil.copytree(item, Path.cwd() / item.name)
                else:
                    shutil.copy2(item, Path.cwd() / item.name)

            with open(self.refs_path, "w", encoding="utf-8") as f:
                f.write(f"HEAD={commit_id}")
            return f"Successfully checked out commit: {commit_id}"
        except Exception as e:
            return f"Checkout failed: {e}"

    def log(self) -> str:
        if not self.repo_dir.exists():
            return "Error: No repository found."

        current_head = self._get_head_id()
        log_output = "--- Wit Commit History ---\n"
        commits = list(self.repo_dir.iterdir())
        commits.sort(key=lambda x: x.stat().st_ctime, reverse=True)

        if not commits:
            return "No commits found yet."

        for commit_path in commits:
            commit_id = commit_path.name
            metadata_file = commit_path / "metadata.txt"
            if metadata_file.exists():
                metadata = metadata_file.read_text(encoding="utf-8")
                if commit_id == current_head:
                    log_output += f"Commit ID: {commit_id} (HEAD)\n"
                else:
                    log_output += f"Commit ID: {commit_id}\n"
                log_output += f"{metadata}\n"
                log_output += "-" * 25 + "\n"
        return log_output

    def add_to_ignore(self, filename: str) -> str:
        """מוסיף קובץ לרשימת ההתעלמות"""
        ignore_file = Path.cwd() / ".witignore"
        try:
            with open(ignore_file, "a", encoding="utf-8") as f:
                f.write(f"{filename}\n")
            return f"Added '{filename}' to .witignore"
        except Exception as e:
            return f"Error: {e}"

    # --- פונקציות עזר פנימיות ---
    def _get_staged_files(self) -> set:
        if not self.staging_dir.exists(): return set()
        return {p.relative_to(self.staging_dir).as_posix() for p in self.staging_dir.rglob('*') if p.is_file()}

    def _get_last_commit_files(self) -> set:
        head_id = self._get_head_id()
        if not head_id: return set()
        commit_dir = self.repo_dir / head_id
        if not commit_dir.exists(): return set()
        return {p.relative_to(commit_dir).as_posix() for p in commit_dir.rglob('*') if
                p.is_file() and p.name != "metadata.txt"}

    def _get_head_id(self) -> str:
        if not self.refs_path.exists(): return ""
        content = self.refs_path.read_text()
        if "=" not in content: return ""
        return content.split("=")[1].strip()

    def _is_ignored(self, path_obj) -> bool:
        ignored_names = {
            '.wit', '.venv', '.git', '.idea', '.DS_Store', '__pycache__',
            'wit.py', 'wit_implementation.py', 'wit_interface.py', 'wit.bat', 'wit.sh'
        }
        return any(part in ignored_names for part in path_obj.parts)

    def _get_file_hash(self, filepath) -> str:
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()