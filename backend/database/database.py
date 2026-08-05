import sqlite3
from pathlib import Path

# ============================================
# Database Path
# ============================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "festival.db"


# ============================================
# Database Connection
# ============================================

def get_connection():

    return sqlite3.connect(DB_PATH)


# ============================================
# Create Tables
# ============================================

def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS registrations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        block TEXT NOT NULL,

        flat_number TEXT NOT NULL,

        mobile TEXT NOT NULL,

        age INTEGER,

        competition TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    conn.commit()

    conn.close()

    print("✅ Database Initialized")


# ============================================
# Save Registration
# ============================================

def save_registration(

        name,
        block,
        flat_number,
        mobile,
        age,
        competition
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO registrations(

        name,

        block,

        flat_number,

        mobile,

        age,

        competition

    )

    VALUES(?,?,?,?,?,?)

    """, (

        name,

        block,

        flat_number,

        mobile,

        age,

        competition

    ))

    conn.commit()

    conn.close()


# ============================================
# Get Registrations
# ============================================

def get_registrations():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM registrations

    ORDER BY id DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows

