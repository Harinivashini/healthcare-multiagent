"""
data/db.py
──────────
Thin SQLite helper used by all agents.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "data/healthcare.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── User helpers ─────────────────────────────────────────────────────────────

def get_user(user_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def list_users(limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, first_name, last_name, city, dietary_preference, medical_conditions, physical_limitations FROM users LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Mood helpers ──────────────────────────────────────────────────────────────

MOOD_SCORES = {
    "happy": 5, "excited": 5,
    "content": 4, "calm": 4,
    "neutral": 3,
    "tired": 2, "anxious": 2,
    "sad": 1, "angry": 1,
}


def log_mood(user_id: int, mood: str) -> dict:
    score = MOOD_SCORES.get(mood.lower(), 3)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO mood_logs (user_id, mood, score) VALUES (?, ?, ?)",
            (user_id, mood, score),
        )
    return {"user_id": user_id, "mood": mood, "score": score}


def get_mood_history(user_id: int, limit: int = 7) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT mood, score, logged_at
               FROM mood_logs WHERE user_id = ?
               ORDER BY logged_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── CGM helpers ───────────────────────────────────────────────────────────────

def log_cgm(user_id: int, reading: float) -> dict:
    flagged = int(reading < 80 or reading > 300)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cgm_logs (user_id, reading, flagged) VALUES (?, ?, ?)",
            (user_id, reading, flagged),
        )
    return {"user_id": user_id, "reading": reading, "flagged": bool(flagged)}


def get_cgm_history(user_id: int, limit: int = 7) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT reading, flagged, logged_at
               FROM cgm_logs WHERE user_id = ?
               ORDER BY logged_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Food helpers ──────────────────────────────────────────────────────────────

def log_food(user_id: int, description: str,
             carbs: float = None, protein: float = None, fat: float = None) -> dict:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO food_logs
               (user_id, description, carbs_g, protein_g, fat_g)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, description, carbs, protein, fat),
        )
    return {"user_id": user_id, "description": description,
            "carbs": carbs, "protein": protein, "fat": fat}


def get_food_history(user_id: int, limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT description, carbs_g, protein_g, fat_g, logged_at
               FROM food_logs WHERE user_id = ?
               ORDER BY logged_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Meal plan helpers ─────────────────────────────────────────────────────────

def save_meal_plan(user_id: int, plan_json: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO meal_plans (user_id, plan_json) VALUES (?, ?)",
            (user_id, plan_json),
        )


def get_latest_meal_plan(user_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT plan_json, generated_at
               FROM meal_plans WHERE user_id = ?
               ORDER BY generated_at DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


# ── Critical Alert helpers ────────────────────────────────────────────────────

def log_critical_alert(user_id: int, reading: float, alert_type: str, message: str) -> dict:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO critical_alerts
               (user_id, reading, alert_type, message)
               VALUES (?, ?, ?, ?)""",
            (user_id, reading, alert_type, message),
        )
    return {"user_id": user_id, "reading": reading, "alert_type": alert_type}


def get_critical_alerts(user_id: int, limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT reading, alert_type, message, logged_at
               FROM critical_alerts WHERE user_id = ?
               ORDER BY logged_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def create_alerts_table():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS critical_alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                reading    REAL NOT NULL,
                alert_type TEXT NOT NULL,
                message    TEXT NOT NULL,
                logged_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()