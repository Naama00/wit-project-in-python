# Wit - Version Control System 🚀

מערכת אישית לניהול גרסאות (VCS) שנכתבה בשפת Python. הפרויקט מאפשר למשתמשים לעקוב אחר שינויים בקבצים, לשמור גרסאות היסטוריות ולשחזר מצבי פרויקט קודמים בקלות.

## 📋 תכונות עיקריות
* **ניהול גרסאות מלא**: יצירת "צילומי מצב" (Snapshots) של הפרויקט.
* **מנגנון התעלמות חכם**: תמיכה בקובץ `.witignore` לסינון קבצים שלא רוצים לגבות.
* **מעקב סטטוס**: תצוגה צבעונית של קבצים חדשים, ששונו או נמחקו.
* **חזרה בזמן**: אפשרות לשחזר את כל התיקייה לגרסה קודמת (Checkout).

---

## 🛠 פקודות המערכת
| פקודה | תיאור |
| :--- | :--- |
| `init` | מאתחל מאגר Wit חדש בתיקייה הנוכחית. |
| `add <path>` | מוסיף קובץ או תיקייה ל-Staging (אזור ההמתנה). |
| `ignore <file>` | מוסיף קובץ לרשימת ההתעלמות ב-`.witignore`. |
| `commit -m "msg"` | שומר גרסה חדשה ב-Repository עם הודעה מתארת. |
| `status` | מציג את מצב הקבצים הנוכחי מול השמירה האחרונה. |
| `checkout <id>` | משחזר את הפרויקט לגרסה ספציפית לפי מזהה הקומיט. |
| `log` | מציג את היסטוריית כל הגרסאות שנשמרו. |

---

## 📂 מבנה הנתונים
המערכת מנהלת את המידע בתיקייה נסתרת בשם `.wit`:
* **staging**: תיקיית ביניים לקבצים לפני שמירה.
* **repository**: ארכיון המכיל את כל ה-Commits (כל אחד בתיקייה נפרדת).
* **references.txt**: קובץ השומר את המזהה של הגרסה הנוכחית (HEAD).

---

## 🚀 דוגמה לשימוש מהיר
```bash
# התחלת פרויקט
python wit.py init

# הוספת קובץ והתעלמות מקבצים לא רצויים
python wit.py add main.py
python wit.py ignore secret.txt

# שמירת גרסה
python wit.py commit -m "First stable version"

# צפייה בהיסטוריה
python wit.py log