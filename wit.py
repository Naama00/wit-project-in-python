import click
import shutil
import uuid
import hashlib
from pathlib import Path

@click.group()
def cli():
    """Wit - מערכת ניהול גרסאות אישית"""
    pass


@cli.command()
def init():
    """מאתחל מאגר wit חדש בתיקייה הנוכחית"""
    wit_dir = Path.cwd() / ".wit"
    if wit_dir.exists():
        click.echo("Error: .wit directory already exists.")
        return

    try:
        wit_dir.mkdir()
        (wit_dir / "staging").mkdir()
        (wit_dir / "repository").mkdir()
        (wit_dir / "references.txt").touch()

        # --- השורה שמוסיפה את הקובץ כבר בהתחלה ---
        (Path.cwd() / ".witignore").touch()

        click.echo("Initialized empty Wit repository and created .witignore")
    except Exception as e:
        click.echo(f"Error: {e}")


# --- הפונקציה החדשה שמאפשרת למשתמש להוסיף קבצים להתעלמות בקלות ---
@cli.command()
@click.argument('filename')
def ignore(filename):
    """מוסיף קובץ לרשימת ההתעלמות"""
    ignore_file = Path.cwd() / ".witignore"
    try:
        with open(ignore_file, "a", encoding="utf-8") as f:
            f.write(f"{filename}\n")
        click.echo(f"Added '{filename}' to .witignore")
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.command()
@click.argument('path')
def add(path):
    """מוסיף קובץ או תיקייה ל-staging עם תמיכה בסינון חכם"""
    source = Path(path)
    wit_dir = Path.cwd() / ".wit"
    staging_dir = wit_dir / "staging"

    # שלב א: בדיקה אם ה-init בוצע
    if not wit_dir.exists():
        click.echo("Error: Please run 'init' first.")
        return

    # שלב ב: האם הנתיב קיים?
    if not source.exists():
        click.echo(f"Error: Path '{path}' does not exist.")
        return

    # שלב ג: קריאת חוקי ההתעלמות מ-.witignore
    ignored_patterns = []
    ignore_file_path = Path.cwd() / ".witignore"
    if ignore_file_path.exists():
        # קורא את השורות ומנקה רווחים או שורות ריקות
        ignored_patterns = [line.strip() for line in ignore_file_path.read_text().splitlines() if line.strip()]

    # שלב ד: בדיקה האם הקובץ/תיקייה תואמים לאחת התבניות
    for pattern in ignored_patterns:
        if source.match(pattern) or any(parent.match(pattern) for parent in source.parents):
            click.echo(f"Ignoring {source.name} (matches pattern '{pattern}' in .witignore)")
            return

    # שלב ה: העתקה ל-staging
    try:
        if source.is_file():
            shutil.copy(source, staging_dir / source.name)
            click.echo(f"Successfully added {source.name} to staging.")
        elif source.is_dir():
            dest_dir = staging_dir / source.name
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(source, dest_dir)
            click.echo(f"Successfully added directory {source.name} to staging.")
    except Exception as e:
        click.echo(f"Failed to add: {e}")


@cli.command()
@click.option('--message', '-m', required=True, help='הודעה המתארת את השינויים')
def commit(message):
    """יוצר צילום מצב (Snapshot) של ה-staging ומעביר ל-repository"""
    wit_dir = Path.cwd() / ".wit"
    staging_dir = wit_dir / "staging"
    repo_dir = wit_dir / "repository"

    # 1. בדיקה אם יש בכלל מה לעשות קומיט
    if not any(staging_dir.iterdir()):
        click.echo("Nothing to commit (staging area is empty).")
        return

    # 2. השוואת Staging ל-HEAD (כדי לא לייצר קומיט זהה)
    # ... (הלוגיקה של ה-Hash שכתבנו קודם) ...
    # אם אין שינויים, עוצרים פה.

    # 3. יצירת מזהה ייחודי לקומיט (Commit ID)
    commit_id = str(uuid.uuid4())[:8]
    new_commit_path = repo_dir / commit_id

    try:
        # 4. העתקת תוכן ה-staging לתיקיית הקומיט החדשה
        shutil.copytree(staging_dir, new_commit_path)

        # 5. שמירת metadata
        with open(new_commit_path / "metadata.txt", "w", encoding="utf-8") as f:
            f.write(f"Message: {message}\n")
            f.write(f"ID: {commit_id}\n")

        # 6. עדכון HEAD
        with open(wit_dir / "references.txt", "w", encoding="utf-8") as f:
            f.write(f"HEAD={commit_id}")

        # --- התיקון: ניקוי ה-staging area לאחר קומיט מוצלח ---
        for item in staging_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        # --------------------------------------------------

        click.echo(f"Successfully created commit: {commit_id}")
        click.echo(f"Message: {message}")

    except Exception as e:
        click.echo(f"Commit failed: {e}")


def get_staged_files():
    """סורק את תיקיית ה-staging ומחזיר רשימת נתיבים מנורמלים"""
    staging_dir = Path.cwd() / ".wit" / "staging"
    if not staging_dir.exists():
        return set()
    # אנחנו הופכים כל נתיב למחרוזת בפורמט POSIX (עם לוכסן /)
    return {p.relative_to(staging_dir).as_posix() for p in staging_dir.rglob('*') if p.is_file()}

def get_last_commit_files():
    """מחזירה סט של קבצים בקומיט האחרון עם נתיבים מנורמלים"""
    wit_dir = Path.cwd() / ".wit"
    ref_path = wit_dir / "references.txt"
    if not ref_path.exists():
        return set()

    with open(ref_path, "r") as f:
        head_id = f.read().split("=")[1].strip()

    commit_dir = wit_dir / "repository" / head_id
    return {p.relative_to(commit_dir).as_posix() for p in commit_dir.rglob('*') if
            p.is_file() and p.name != "metadata.txt"}


def is_ignored(path_obj):
    """
    קובעת האם להתעלם מקובץ/תיקייה מסוימת.
    מתעלמת מקבצי מערכת, אך מציגה קבצי פרויקט שטרם נוספו (untracked).
    """
    # רשימת תיקיות וקבצי מערכת טכניים שאנו לא רוצים להציג למשתמש
    ignored_names = {
        '.wit',  # תיקיית ניהול הגרסאות עצמה
        '.venv',  # סביבה וירטואלית של פייתון
        '.git',  # אם קיים, לא רלוונטי ל-wit
        '.idea',  # הגדרות של PyCharm
        '.DS_Store',  # קבצי מערכת של Mac
        '__pycache__',  # קבצי זיכרון של פייתון
    }

    # בדיקה האם שם הקובץ או אחת התיקיות בנתיב מופיעה ברשימת ההתעלמות
    return any(part in ignored_names for part in path_obj.parts)


def get_file_hash(filepath):
    """מחשב חתימה (MD5 Hash) לתוכן של קובץ"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


@cli.command()
def status():
    """מציג את סטטוס הפרויקט בדומה ל-git status"""
    wit_dir = Path.cwd() / ".wit"
    if not wit_dir.exists():
        click.echo("Error: Not a wit repository.")
        return

    # 1. איסוף מידע מכל המקורות
    staged_files = {Path(f).as_posix() for f in get_staged_files()}
    last_commit_files = {Path(f).as_posix() for f in get_last_commit_files()}

    # הבאת ה-head_id לצורך השוואת קבצים
    ref_path = wit_dir / "references.txt"
    head_id = ""
    if ref_path.exists():
        with open(ref_path, "r") as f:
            content = f.read()
            if "=" in content:
                head_id = content.split("=")[1].strip()

    working_dir_files = set()
    for p in Path.cwd().rglob('*'):
        if is_ignored(p) or p.is_dir() or ".wit" in p.parts:
            continue
        working_dir_files.add(p.relative_to(Path.cwd()).as_posix())

    # 2. חישוב הקטגוריות
    modified_not_staged = set()
    deleted_not_staged = set()

    # א. קבצים שנוספו לסטייג'ינג (ירוק)
    staged = staged_files

    # ב. בדיקת שינויים בדיסק מול ה-Staging או ה-Commit האחרון
    for f in working_dir_files:
        current_file_path = Path.cwd() / f
        staged_file_path = wit_dir / "staging" / f

        # אם הקובץ נמצא ב-Staging, נבדוק אם הוא שונה מהדיסק
        if f in staged_files:
            if get_file_hash(current_file_path) != get_file_hash(staged_file_path):
                modified_not_staged.add(f)
        # אם לא ב-Staging, נבדוק מול הקומיט האחרון
        elif head_id:
            last_commit_dir = wit_dir / "repository" / head_id
            last_file_path = last_commit_dir / f
            if last_file_path.exists():
                if get_file_hash(current_file_path) != get_file_hash(last_file_path):
                    modified_not_staged.add(f)

    # ג. בדיקה לקבצים שנמחקו מהדיסק
    if head_id:
        for f in last_commit_files:
            if not (Path.cwd() / f).exists():
                deleted_not_staged.add(f)

    # ד. קבצים לא עוקבים (אדום)
    untracked = working_dir_files - last_commit_files - staged_files

    # 3. הדפסה למשתמש
    click.echo(f"On branch master\n")

    # הצגת קבצים להפקדה (ירוק)
    click.echo("Changes to be committed:")
    if staged:
        for f in staged:
            click.secho(f"\tnew file: {f}", fg="green")
    else:
        click.echo("\t(no changes staged for commit)")

    # הצגת שינויים שלא נוספו (אדום)
    click.echo("\nChanges not staged for commit:")

    changes_not_staged = modified_not_staged | deleted_not_staged

    if changes_not_staged:
        for f in modified_not_staged:
            click.secho(f"\tmodified: {f}", fg="red")
        for f in deleted_not_staged:
            click.secho(f"\tdeleted: {f}", fg="red")
    else:
        click.echo("\t(no changes added to commit)")

    # הצגת קבצים לא עוקבים (אדום)
    click.echo("\nUntracked files:")
    if untracked:
        for f in untracked:
            click.secho(f"\t{f}", fg="red")
    else:
        click.echo("\t(nothing untracked)")

@cli.command()
@click.argument('commit_id')
def checkout(commit_id):
    """משחזר את מצב הפרויקט לקומיט המצוין"""
    wit_dir = Path.cwd() / ".wit"
    staging_dir = wit_dir / "staging"
    repo_dir = wit_dir / "repository"
    target_commit_dir = repo_dir / commit_id

    # 1. בדיקה אם ה-init בוצע
    if not wit_dir.exists():
        click.echo("Error: Not a wit repository.")
        return

    # 2. בדיקה אם הקומיט קיים
    if not target_commit_dir.exists():
        click.echo(f"Error: Commit ID {commit_id} not found.")
        return

    # 3. בדיקה אם קיימים שינויים שלא עברו קומיט (חסום)
    if any(staging_dir.iterdir()):
        click.echo("Error: You have uncommitted changes. Please commit or stash them before checking out.")
        return

    # 4. שחזור המצב (העתקת תוכן הקומיט לתיקייה הראשית)
    try:
        # א. מחיקת קבצים נוכחיים (חוץ מתיקיות/קבצים מוגנים)
        for item in Path.cwd().iterdir():
            # --- התיקון: דילוג על תיקיות מוגנות ---
            if item.name in [".wit", ".venv", ".git", "wit.py", "wit.bat"]:
                continue
            # -------------------------------------
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # ב. העתקת קבצי הקומיט לתיקייה הראשית
        for item in target_commit_dir.iterdir():
            if item.name == "metadata.txt":
                continue
            if item.is_dir():
                shutil.copytree(item, Path.cwd() / item.name)
            else:
                shutil.copy2(item, Path.cwd() / item.name)

        # ג. עדכון ה-HEAD
        with open(wit_dir / "references.txt", "w", encoding="utf-8") as f:
            f.write(f"HEAD={commit_id}")

        click.echo(f"Successfully checked out commit: {commit_id}")

    except Exception as e:
        click.echo(f"Checkout failed: {e}")
if __name__ == "__main__":
    cli()
