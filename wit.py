import click
import shutil
from pathlib import Path

@click.group()
def cli():
    """Wit - מערכת ניהול גרסאות אישית"""
    pass

@cli.command()
def init():
    """מאתחל מאגר wit חדש בתיקייה הנוכחית"""
    # 1. מגדירים את הנתיב של תיקיית .wit בתיקייה שבה המשתמש נמצא
    wit_dir = Path.cwd() / ".wit"

    # 2. בודקים אם התיקייה כבר קיימת כדי לא לדרוס מידע
    if wit_dir.exists():
        click.echo("Error: .wit directory already exists in this folder.")
        return

    try:
        # 3. יצירת התיקייה הראשית ותתי-התיקיות
        # התיקייה הראשית
        wit_dir.mkdir()

        # תתי-התיקיות (staging ו-repository)
        (wit_dir / "staging").mkdir()
        (wit_dir / "repository").mkdir()

        # 4. יצירת קובץ ה-references (אפשר לקרוא לו HEAD או references)
        # כרגע הוא יהיה ריק כי אין עדיין קומיטים
        (wit_dir / "references.txt").touch()

        click.echo("Initialized empty Wit repository in .wit/")
    except Exception as e:
        click.echo(f"An error occurred during initialization: {e}")

@cli.command()
@click.argument('path')
def add(path):
    """מוסיף קובץ או תיקייה ל-staging"""
    # הפיכת הנתיב לאובייקט שאפשר לעבוד איתו
    source = Path(path)
    staging_dir = Path.cwd() / ".wit" / "staging"

    # שלב א: בדיקה אם ה-init בוצע
    if not (Path.cwd() / ".wit").exists():
        click.echo("Error: Please run 'init' first.")
        return

    # שלב ב: האם הקובץ קיים?
    if not source.exists():
        click.echo(f"Error: Path '{path}' does not exist.")
        return

    # שלב ג: בדיקת .witignore (נדמה שזה קובץ טקסט פשוט)
    ignored_files = []
    ignore_file_path = Path.cwd() / ".witignore"
    if ignore_file_path.exists():
        ignored_files = ignore_file_path.read_text().splitlines()

    if source.name in ignored_files:
        click.echo(f"Ignoring {source.name} (found in .witignore)")
        return

    # שלב ד: העתקה
    try:
        if source.is_file():
            # מעתיקים קובץ בודד
            shutil.copy(source, staging_dir / source.name)
            click.echo(f"Successfully added {source.name} to staging.")
        elif source.is_dir():
            # מעתיקים תיקייה שלמה
            dest_dir = staging_dir / source.name
            if dest_dir.exists():
                shutil.rmtree(dest_dir) # מנקים גרסה קודמת אם הייתה
            shutil.copytree(source, dest_dir)
            click.echo(f"Successfully added directory {source.name} to staging.")
    except Exception as e:
        click.echo(f"Failed to add: {e}")

if __name__ == "__main__":
    cli()