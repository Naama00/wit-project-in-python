import click
import shutil
import uuid
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












if __name__ == "__main__":
    cli()
