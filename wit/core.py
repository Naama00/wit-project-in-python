from wit.file_utils import WitUtils
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
    def add_to_ignore(self, filename): pass

    @abstractmethod
    def log(self): pass

    @abstractmethod
    def checkout(self, commit_id): pass

    @abstractmethod
    def push(self): pass  # Placeholder for future push implementation

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
        source = Path(path).absolute()  # שימוש בנתיב מלא למניעת בלבול
        if not self.wit_dir.exists(): return "Error: Run 'init' first."
        if not source.exists(): return f"Error: {path} not found."

        # הגנה: לא להוסיף את תיקיית המערכת של wit או git לתוך ה-staging
        if ".wit" in source.parts or ".git" in source.parts or ".venv" in source.parts:
            return f"Skipping system directory: {source.name}"

        try:
            # יצירת נתיב יעד בתוך staging ששומר על המבנה המקורי
            destination = self.staging_dir / source.name

            if source.is_file():
                WitUtils.copy_file(source, destination)
            elif source.is_dir():
                WitUtils.copy_directory(source, destination)
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
            # חדש:
            import json
            from datetime import datetime

            parent_id = None
            if self.refs_path.exists():
                content = self.refs_path.read_text()
                if "HEAD=" in content:
                    parent_id = content.split("HEAD=")[1].strip() or None

            metadata = {
                "id": commit_id,
                "message": message,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "parent_id": parent_id,
            }
            (new_commit_path / "metadata.json").write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
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

    def add_to_ignore(self, filename: str) -> str:
        if not self.wit_dir.exists():
            return "Error: Run 'init' first."
        witignore = Path.cwd() / ".witignore"
        witignore.touch()
        existing = witignore.read_text(encoding="utf-8").splitlines()
        if filename in existing:
            return f"'{filename}' is already in .witignore."
        with open(witignore, "a", encoding="utf-8") as f:
            f.write(filename + "\n")
        return f"Added '{filename}' to .witignore."

    def log(self) -> str:
        if not self.wit_dir.exists(): return "Error: Run 'init' first."
        commits = list(self.repo_dir.iterdir())
        if not commits: return "No commits yet."

        log_output = "--- Commit History ---\n"
        import json
        for commit_path in sorted(commits):
            metadata_path = commit_path / "metadata.json"
            if metadata_path.exists():
                try:
                    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
                    log_output += (
                        f"Commit: {meta.get('id', '?')}\n"
                        f"Date:   {meta.get('timestamp', '?')}\n"
                        f"Parent: {meta.get('parent_id') or 'none'}\n"
                        f"        {meta.get('message', '')}\n"
                    )
                except (json.JSONDecodeError, KeyError):
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
                if item.name == "metadata.json": continue

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

    def _read_server_url(self) -> str:
        """
        Reads the server URL from .wit/config.json.
        Falls back to localhost if the file doesn't exist.
        """
        import json
        config_path = self.wit_dir / "config.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                return config.get("server_url", "http://127.0.0.1:8000")
            except (json.JSONDecodeError, KeyError):
                pass
        return "http://127.0.0.1:8000"

    def push(self) -> str:
        """
        Sends all Python files from the latest commit to CodeGuard server for analysis
        and saves the generated summary graphs locally.
        """
        import os
        import requests

        if not self.wit_dir.exists():
            return "Error: Run 'init' first."

        # 1. קריאת ה-Commit ID האחרון מתוך קובץ ה-references.txt המותאם שלך
        if not self.refs_path.exists():
            return "Error: Nothing to push. No commits found."

        content = self.refs_path.read_text()
        if "HEAD=" not in content:
            return "Error: Nothing to push. No commits found."

        commit_id = content.split("HEAD=")[1].strip()
        if not commit_id:
            return "Error: Nothing to push. No commits found."

        # 2. הגדרת הנתיב הפיזי של ה-Commit בתוך תיקיית repository
        commit_images_dir = self.repo_dir / commit_id
        if not commit_images_dir.exists():
            return f"Error: Commit directory {commit_id} not found."

        # 3. סריקה ואיסוף של כל קבצי ה-Python (.py) מתוך ה-Commit
        files_to_send = []
        opened_files = []
        for root, _, files in os.walk(str(commit_images_dir)):
            for file in files:
                if file.endswith('.py'):
                    full_path = Path(root) / file
                    rel_name = full_path.relative_to(commit_images_dir)
                    try:
                        f = open(full_path, 'rb')
                        opened_files.append(f)
                        files_to_send.append(('files', (str(rel_name), f, 'text/x-python')))
                    except Exception as e:
                        return f"Error opening file {file}: {e}"

        if not files_to_send:
            return "Nothing to push: no Python files found in the latest commit."

        # 4. קריאת כתובת השרת הדינמית ושליחת הבקשות
        server_url = self._read_server_url()
        print(f"Pushing commit {commit_id} to CodeGuard Server ({server_url})...")

        try:
            # בקשה ראשונה - קבלת אזהרות טקסטואליות
            alerts_response = requests.post(f"{server_url}/alerts", files=files_to_send, timeout=30)

            # איפוס פוזיציית הקבצים לקריאה שנייה בשרת
            for f in opened_files:
                f.seek(0)

            # בקשה שנייה - קבלת קובץ הגרפים
            analyze_response = requests.post(f"{server_url}/analyze", files=files_to_send, timeout=30)

            # סגירת משאבי הקבצים
            for f in opened_files:
                f.close()

            # 5. עיבוד והבניית הפלט בצורה יבשה ומובנית
            lines = ["", "=== CodeGuard Analysis Results ==="]

            if alerts_response.status_code == 200:
                alerts = alerts_response.json().get("alerts", [])
                if not alerts:
                    lines.append("  ✅ No issues found.")
                else:
                    for alert in alerts:
                        lines.append(f"  ⚠️ File: {alert['file']} | [{alert['type']}] {alert['message']}")
            else:
                lines.append(f"  ❌ Failed to retrieve alerts. Server status: {alerts_response.status_code}")

            if analyze_response.status_code == 200:
                graphs_dir = Path.cwd() / "graphs"
                graphs_dir.mkdir(exist_ok=True)
                output_graph_path = graphs_dir / "analysis_summary.png"

                with open(output_graph_path, 'wb') as graph_file:
                    graph_file.write(analyze_response.content)
                lines.append(f"\nCharts saved: graphs/analysis_summary.png")
            else:
                lines.append(f"  ❌ Failed to retrieve charts. Server status: {analyze_response.status_code}")

            lines.append("==================================")
            return "\n".join(lines)

        except requests.RequestException as e:
            # סגירת קבצים במקרה של שגיאת תקשורת
            for f in opened_files:
                f.close()
            return f"Push failed: could not reach server at {server_url}. Error: {e}"