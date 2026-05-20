import json
import sqlite3
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / ".local" / "share" / "werweiss"
DB_PATH = APP_DIR / "werweiss.db"
QUESTIONS_JSON = Path(__file__).resolve().parents[1] / "data" / "questions.json"
QUESTIONS_DATA_VERSION = "1.3.0"


def connect():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL UNIQUE, category TEXT NOT NULL, difficulty TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER NOT NULL, answer TEXT NOT NULL, is_correct INTEGER NOT NULL, FOREIGN KEY(question_id) REFERENCES questions(id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, player TEXT NOT NULL, points INTEGER NOT NULL, played_at TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_answers_question_id ON answers(question_id)")
    con.commit()
    seed_questions(con)
    con.close()


def seed_questions(con):
    cur = con.cursor()
    data = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
    wanted_count = len(data)
    cur.execute("SELECT value FROM app_meta WHERE key = ?", ("questions_data_version",))
    version_row = cur.fetchone()
    cur.execute("SELECT value FROM app_meta WHERE key = ?", ("questions_json_count",))
    count_row = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM questions")
    existing_count = cur.fetchone()[0]
    if (
        version_row and version_row[0] == QUESTIONS_DATA_VERSION
        and count_row and count_row[0] == str(wanted_count)
        and existing_count >= wanted_count
    ):
        return

    # A new bundled question pack should replace older/generated packs,
    # but scores and app settings remain untouched.
    cur.execute("DELETE FROM answers")
    cur.execute("DELETE FROM questions")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('questions', 'answers')")

    question_rows = [(item["question"], item["category"], item["difficulty"]) for item in data]
    cur.executemany(
        "INSERT INTO questions(question, category, difficulty) VALUES (?, ?, ?)",
        question_rows,
    )

    cur.execute("SELECT id, question FROM questions")
    qids = {question: qid for qid, question in cur.fetchall()}
    answer_rows = []
    for item in data:
        qid = qids.get(item["question"])
        if not qid:
            continue
        for idx, answer in enumerate(item["answers"]):
            answer_rows.append((qid, answer, 1 if idx == item["correct"] else 0))
    cur.executemany(
        "INSERT INTO answers(question_id, answer, is_correct) VALUES (?, ?, ?)",
        answer_rows,
    )
    cur.execute("INSERT OR REPLACE INTO app_meta(key, value) VALUES (?, ?)", ("questions_data_version", QUESTIONS_DATA_VERSION))
    cur.execute("INSERT OR REPLACE INTO app_meta(key, value) VALUES (?, ?)", ("questions_json_count", str(wanted_count)))
    con.commit()


def get_categories():
    con = connect(); cur = con.cursor()
    cur.execute("SELECT DISTINCT category FROM questions ORDER BY category")
    rows = [row[0] for row in cur.fetchall()]
    con.close(); return rows


def get_questions(category=None, limit=10):
    con = connect(); con.row_factory = sqlite3.Row; cur = con.cursor()
    selected = []
    if category and category != "Alle Kategorien":
        cur.execute("SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT ?", (category, limit))
        selected = cur.fetchall()
    else:
        # Balanced all-category mode: rotate categories so one large category
        # cannot dominate a quiz round.
        cur.execute("SELECT DISTINCT category FROM questions ORDER BY RANDOM()")
        cats = [row[0] for row in cur.fetchall()]
        while len(selected) < limit and cats:
            for cat in cats:
                if len(selected) >= limit:
                    break
                cur.execute("SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT 1", (cat,))
                row = cur.fetchone()
                if row:
                    selected.append(row)
    questions = []
    for q in selected:
        cur.execute("SELECT answer, is_correct FROM answers WHERE question_id = ?", (q["id"],))
        answers = [{"text": a[0], "correct": bool(a[1])} for a in cur.fetchall()]
        questions.append({"id": q["id"], "question": q["question"], "category": q["category"], "difficulty": q["difficulty"], "answers": answers})
    con.close(); return questions


def save_score(player, points):
    con = connect(); cur = con.cursor()
    cur.execute("INSERT INTO scores(player, points, played_at) VALUES (?, ?, ?)", (player or "Spieler", points, datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit(); con.close()


def top_scores(limit=10):
    con = connect(); cur = con.cursor()
    cur.execute("SELECT player, points, played_at FROM scores ORDER BY points DESC, played_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall(); con.close(); return rows
