import click
from wit_implementation import WitImplementation

# יצירת אובייקט של המימוש
wit_app = WitImplementation()

@click.group()
def cli():
    """Wit - מערכת ניהול גרסאות אישית"""
    pass

@cli.command()
def init():
    """מאתחל מאגר wit חדש בתיקייה הנוכחית"""
    result = wit_app.init()
    click.echo(result)

@cli.command()
@click.argument('filename')
def ignore(filename):
    """מוסיף קובץ לרשימת ההתעלמות"""
    result = wit_app.add_to_ignore(filename)
    click.echo(result)

@cli.command()
@click.argument('path')
def add(path):
    """מוסיף קובץ או תיקייה ל-staging עם תמיכה בסינון חכם"""
    result = wit_app.add(path)
    click.echo(result)

@cli.command()
@click.option('--message', '-m', required=True, help='הודעה המתארת את השינויים')
def commit(message):
    """יוצר צילום מצב (Snapshot) של ה-staging ומעביר ל-repository"""
    result = wit_app.commit(message)
    click.echo(result)

@cli.command()
def status():
    """מציג את סטטוס הפרויקט בדומה ל-git status"""
    result = wit_app.status()
    # כאן אפשר להוסיף לוגיקה לצביעת הטקסט אם רוצים
    click.echo(result)

@cli.command()
@click.argument('commit_id')
def checkout(commit_id):
    """משחזר את מצב הפרויקט לקומיט המצוין"""
    result = wit_app.checkout(commit_id)
    click.echo(result)

@cli.command()
def log():
    """מציג את היסטוריית הקומיטים במאגר"""
    result = wit_app.log()
    click.echo(result)

if __name__ == "__main__":
    cli()