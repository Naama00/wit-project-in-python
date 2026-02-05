import click
import shutil
import uuid
import os
import fnmatch
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

    # 1. בדיקה אם יש בכלל מה לעשות קומיט (האם ה-staging לא ריק?)
    if not any(staging_dir.iterdir()):
        click.echo("Nothing to commit (staging area is empty).")
        return

    # 2. יצירת מזהה ייחודי לקומיט (Commit ID)
    commit_id = str(uuid.uuid4())[:8]  # לוקחים רק 8 תווים ראשונים
    new_commit_path = repo_dir / commit_id

    try:
        # 3. העתקת כל תוכן ה-staging לתיקיית הקומיט החדשה
        shutil.copytree(staging_dir, new_commit_path)

        # 4. שמירת המידע על הקומיט (הודעה וזמן) בקובץ טקסט בתוך התיקייה
        with open(new_commit_path / "metadata.txt", "w", encoding="utf-8") as f:
            f.write(f"Message: {message}\n")
            f.write(f"ID: {commit_id}\n")

        # 5. עדכון ה-references.txt שזהו הקומיט האחרון (HEAD)
        with open(wit_dir / "references.txt", "w", encoding="utf-8") as f:
            f.write(f"HEAD={commit_id}")

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
    # רשימת קבצים ותיקיות שנתעלם מהם תמיד
    ignored_names = {'.wit', '.venv', '.git', '.idea', 'wit.py', 'wit.bat', '.witignore'}
    return any(part in ignored_names for part in path_obj.parts)


@cli.command()
def status():
    """מציג את מצב הקבצים: Staged, Modified ו-Untracked"""
    wit_dir = Path.cwd() / ".wit"
    if not wit_dir.exists():
        click.echo("Not a wit repository.")
        return

    # 1. השגת רשימות קבצים ונרמול נתיבים (as_posix)
    # -------------------------------------------
    staged_files = {Path(f).as_posix() for f in get_staged_files()}
    last_commit_files = {Path(f).as_posix() for f in get_last_commit_files()}

    # זיהוי קבצים בתיקיית העבודה (Working Directory)
    working_dir_files = set()
    for p in Path.cwd().rglob('*'):
        if ".wit" in p.parts or p.is_dir() or is_ignored(p):
            continue
        working_dir_files.add(p.relative_to(Path.cwd()).as_posix())

    # 2. חישוב הקטגוריות (לוגיקה של קבוצות)
    # ------------------------------------

    # א. Changes to be committed: קבצים ב-Staging ששונים מהקומיט האחרון
    # זה התיקון הקריטי - אם הקובץ זהה לקומיט האחרון, הוא לא יופיע כאן
    to_be_committed = staged_files - last_commit_files

    # ב. Changes not staged for commit: קבצים עוקבים שנמחקו פיזית
    tracked_files = staged_files | last_commit_files
    deleted_files = {f for f in tracked_files if not (Path.cwd() / f).exists()}

    # ג. Untracked files: קבצים בתיקייה שלא ב-Staging ולא בקומיט
    untracked = working_dir_files - tracked_files

    # 3. הדפסה למשתמש
    # ---------------
    click.echo(f"On branch master\n")

    # הצגת קבצים להפקדה (ירוק)
    click.echo("Changes to be committed:")
    if to_be_committed:
        for f in to_be_committed:
            click.secho(f"\tnew file: {f}", fg="green")
    else:
        click.echo("\t(nothing staged)")

        # הצגת שינויים שלא נוספו (אדום)
        click.echo("\nChanges not staged for commit:")
        if deleted_files:
            for f in deleted_files:
                click.secho(f"\tdeleted: {f}", fg="red")
        else:
            click.echo("\t(use 'wit add <file>...' to update what will be committed)")

        # הצגת קבצים לא עוקבים (אדום)
        click.echo("\nUntracked files:")
        if untracked:
            for f in untracked:
                click.secho(f"\t{f}", fg="red")
        else:
            click.echo("\t(nothing untracked)")



if __name__ == "__main__":
    cli()
