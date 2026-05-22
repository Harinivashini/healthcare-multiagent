"""
data/generate_dataset.py
────────────────────────
Generates a synthetic SQLite dataset of 100 individuals.
Run once before starting the backend:
    python data/generate_dataset.py
"""

import sqlite3
import random
from faker import Faker

fake = Faker()
random.seed(42)

DB_PATH = "data/healthcare.db"

CITIES = [
    "New York", "Los Angeles", "Chicago",
    "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "Austin",
]

DIETARY_PREFERENCES = ["vegetarian", "non-vegetarian", "vegan"]

MEDICAL_CONDITIONS_POOL = [
    "Type 2 Diabetes",
    "Hypertension",
    "Celiac Disease",
    "Lactose Intolerance",
    "Chronic Kidney Disease",
    "Heart Disease",
    "Obesity",
    "None",
]

PHYSICAL_LIMITATIONS_POOL = [
    "None",
    "Mobility Issues",
    "Swallowing Difficulties",
    "Arthritis",
    "Visual Impairment",
]


def _pick_conditions() -> str:
    """Return a comma-separated list of 1–3 medical conditions."""
    k = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
    conditions = random.sample(MEDICAL_CONDITIONS_POOL, k=k)
    return ", ".join(conditions)


def _pick_limitation() -> str:
    return random.choice(PHYSICAL_LIMITATIONS_POOL)


def _cgm_range_for(conditions: str):
    """Return (low, high) CGM range.  Diabetics skew higher."""
    if "Type 2 Diabetes" in conditions:
        return (100, 300)
    return (80, 180)


def create_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name          TEXT NOT NULL,
            last_name           TEXT NOT NULL,
            city                TEXT NOT NULL,
            dietary_preference  TEXT NOT NULL,
            medical_conditions  TEXT NOT NULL,
            physical_limitations TEXT NOT NULL,
            cgm_low             INTEGER NOT NULL,
            cgm_high            INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mood_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            mood        TEXT NOT NULL,
            score       INTEGER NOT NULL,   -- 1-5 numeric
            logged_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS cgm_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            reading     REAL NOT NULL,
            flagged     INTEGER DEFAULT 0,
            logged_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS food_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            description TEXT NOT NULL,
            carbs_g     REAL,
            protein_g   REAL,
            fat_g       REAL,
            logged_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS meal_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            plan_json   TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """
    )
    conn.commit()


def seed_users(conn: sqlite3.Connection, n: int = 100):
    # Ensure ~33 of each dietary preference
    prefs = (DIETARY_PREFERENCES * 34)[:n]
    random.shuffle(prefs)

    rows = []
    for i in range(n):
        conditions = _pick_conditions()
        cgm_low, cgm_high = _cgm_range_for(conditions)
        rows.append(
            (
                fake.first_name(),
                fake.last_name(),
                random.choice(CITIES),
                prefs[i],
                conditions,
                _pick_limitation(),
                cgm_low,
                cgm_high,
            )
        )

    conn.executemany(
        """
        INSERT INTO users
            (first_name, last_name, city, dietary_preference,
             medical_conditions, physical_limitations, cgm_low, cgm_high)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    print(f"✓  Inserted {n} users into {DB_PATH}")


def main():
    import os
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    cur = conn.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count >= 100:
        print(f"Dataset already has {count} users — skipping seed.")
    else:
        seed_users(conn)

    conn.close()


if __name__ == "__main__":
    main()
