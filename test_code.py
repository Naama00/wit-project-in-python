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