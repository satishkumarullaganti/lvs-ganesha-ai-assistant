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

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS annaprasada_bookings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        coupon_id TEXT NOT NULL UNIQUE,

        name TEXT NOT NULL,

        block TEXT NOT NULL,

        flat_number TEXT NOT NULL,

        members TEXT NOT NULL,

        is_used INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS donations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        receipt_id TEXT NOT NULL UNIQUE,

        name TEXT NOT NULL,

        flat_number TEXT NOT NULL,

        amount TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS cultural_registrations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        block TEXT NOT NULL,

        flat_number TEXT NOT NULL,

        mobile TEXT NOT NULL,

        categories TEXT NOT NULL,

        other_details TEXT,

        track_path TEXT,

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
# Save Annaprasada Booking
# ============================================

def save_annaprasada_booking(coupon_id, name, block, flat_number, members):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO annaprasada_bookings(

        coupon_id,

        name,

        block,

        flat_number,

        members

    )

    VALUES(?,?,?,?,?)

    """, (

        coupon_id,

        name,

        block,

        flat_number,

        members

    ))

    conn.commit()

    conn.close()


# ============================================
# Get Annaprasada Booking by Coupon ID
# ============================================

def get_booking_by_coupon(coupon_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT coupon_id, name, block, flat_number, members, is_used

    FROM annaprasada_bookings

    WHERE coupon_id = ?

    """, (coupon_id,))

    row = cursor.fetchone()

    conn.close()

    return row


# ============================================
# Mark Annaprasada Coupon as Used
# ============================================

def mark_coupon_used(coupon_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE annaprasada_bookings

    SET is_used = 1

    WHERE coupon_id = ?

    """, (coupon_id,))

    conn.commit()

    conn.close()


# ============================================
# Save Donation
# ============================================

def save_donation(receipt_id, name, flat_number, amount):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO donations(

        receipt_id,

        name,

        flat_number,

        amount

    )

    VALUES(?,?,?,?)

    """, (

        receipt_id,

        name,

        flat_number,

        amount

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


# ============================================
# Save Cultural Registration
# ============================================

def save_cultural_registration(

        name,
        block,
        flat_number,
        mobile,
        categories,
        other_details,
        track_path
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO cultural_registrations(

        name,

        block,

        flat_number,

        mobile,

        categories,

        other_details,

        track_path

    )

    VALUES(?,?,?,?,?,?,?)

    """, (

        name,

        block,

        flat_number,

        mobile,

        categories,

        other_details,

        track_path

    ))

    conn.commit()

    conn.close()


# ============================================
# Get Cultural Registrations
# ============================================

def get_cultural_registrations():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM cultural_registrations

    ORDER BY id DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows