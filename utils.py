import shutil
import uuid
import hashlib
from pathlib import Path

class WitUtils:
    """
    מחלקה סטטית לריכוז פונקציות עזר טכניות.
    מאפשרת שינוי קל של תשתיות (כמו החלפת ספריות העתקה או יצירת מזהים) במקום אחד.
    """

    @staticmethod
    def generate_id() -> str:
        """מייצר מזהה ייחודי קצר עבור ה-Commits."""
        return str(uuid.uuid4())[:8]

    @staticmethod
    def copy_file(source: Path, destination: Path):
        """מעתיק קובץ בודד תוך שמירה על מטא-דאטה (זמני יצירה וכו')."""
        shutil.copy2(source, destination)

    @staticmethod
    def copy_directory(source: Path, destination: Path):
        """מעתיק תיקייה שלמה. אם תיקיית היעד קיימת - היא תימחק ותיווצר מחדש."""
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)

    @staticmethod
    def get_file_hash(filepath: Path) -> str:
        """מחשב MD5 Hash של קובץ כדי לזהות אם הוא השתנה."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            # קריאת הקובץ בבלוקים כדי לא להעמיס על הזיכרון בקבצים גדולים
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def delete_directory_contents(directory: Path):
        """מנקה את כל התוכן של תיקייה מסוימת בלי למחוק את התיקייה עצמה."""
        for item in directory.iterdir():
            if item.is_file():
                item.unlink()