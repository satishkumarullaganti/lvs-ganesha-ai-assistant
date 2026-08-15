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

    # --------------------------------------------
    # Migration: add served_count for partial
    # redemption support (a family's coupon covers
    # N members, but they don't always arrive
    # together - this tracks how many have actually
    # been served so far, so the same coupon can be
    # scanned again for the remaining members instead
    # of the whole booking being consumed by whoever
    # arrives first).
    # --------------------------------------------

    cursor.execute("PRAGMA table_info(annaprasada_bookings)")
    annaprasada_existing_columns = [row[1] for row in cursor.fetchall()]

    if "served_count" not in annaprasada_existing_columns:
        cursor.execute(
            "ALTER TABLE annaprasada_bookings ADD COLUMN served_count INTEGER DEFAULT 0"
        )

    # --------------------------------------------
    # Migration: booking_group_id links sibling
    # coupons generated from the same original
    # booking request (e.g. a family booking for 4
    # members now gets 4 separate admit-1 coupon
    # rows, matching the physical "ADMIT ONLY - 1"
    # coupons used previously - this column lets
    # admin reporting still group them together).
    # --------------------------------------------

    if "booking_group_id" not in annaprasada_existing_columns:
        cursor.execute(
            "ALTER TABLE annaprasada_bookings ADD COLUMN booking_group_id TEXT"
        )

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS donations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        receipt_id TEXT NOT NULL UNIQUE,

        name TEXT NOT NULL,

        flat_number TEXT NOT NULL,

        amount TEXT NOT NULL,

        utr_number TEXT,

        proof_image_path TEXT,

        status TEXT DEFAULT 'pending',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # --------------------------------------------
    # Migration: add columns if this table already
    # existed before utr_number/status were added
    # --------------------------------------------

    cursor.execute("PRAGMA table_info(donations)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "utr_number" not in existing_columns:
        cursor.execute("ALTER TABLE donations ADD COLUMN utr_number TEXT")

    if "status" not in existing_columns:
        cursor.execute(
            "ALTER TABLE donations ADD COLUMN status TEXT DEFAULT 'pending'"
        )

    if "proof_image_path" not in existing_columns:
        cursor.execute(
            "ALTER TABLE donations ADD COLUMN proof_image_path TEXT"
        )

    if "block" not in existing_columns:
        cursor.execute(
            "ALTER TABLE donations ADD COLUMN block TEXT"
        )

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

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS volunteers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        block TEXT NOT NULL,

        flat_number TEXT NOT NULL,

        mobile TEXT NOT NULL,

        tasks TEXT NOT NULL,

        other_details TEXT,

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
# Duplicate Competition Registration Check
# ============================================
# Unlike cultural programs, a competition (Chess,
# Carrom, etc.) only has ONE entry per person - there's
# no equivalent of "two different performances" here, so
# registering for the same competition twice is always a
# genuine duplicate, not a legitimate second entry.
#
# Matched by name + block + flat_number, NOT mobile -
# a phone number is easy to mistype or deliberately vary
# between submissions, but a resident's flat is a much
# more reliable, harder-to-fake identifier.

def check_duplicate_competition_registration(name, block, flat_number, competition):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT id

    FROM registrations

    WHERE LOWER(name) = LOWER(?)

    AND LOWER(block) = LOWER(?)

    AND flat_number = ?

    AND LOWER(competition) = LOWER(?)

    LIMIT 1

    """, (name, block, flat_number, competition))

    row = cursor.fetchone()

    conn.close()

    return row is not None


# ============================================
# Save Annaprasada Booking
# ============================================

def save_annaprasada_booking(coupon_id, name, block, flat_number, members, booking_group_id=None):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO annaprasada_bookings(

        coupon_id,

        name,

        block,

        flat_number,

        members,

        booking_group_id

    )

    VALUES(?,?,?,?,?,?)

    """, (

        coupon_id,

        name,

        block,

        flat_number,

        members,

        booking_group_id

    ))

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return new_id


# ============================================
# Get Total Already-Booked Members for a Flat
# ============================================
# This is informational only, not a block - a flat that
# has already booked Annaprasada can still book again
# (e.g. more guests staying over, or they simply need
# more coupons), but the resident should be told how many
# they've already booked so they don't lose track and
# accidentally over-book.

def get_total_booked_members_for_flat(block, flat_number):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT members

    FROM annaprasada_bookings

    WHERE LOWER(block) = LOWER(?)

    AND flat_number = ?

    """, (block, flat_number))

    rows = cursor.fetchall()

    conn.close()

    total = 0

    for row in rows:

        try:
            total += int(row[0])
        except (TypeError, ValueError):
            pass

    return total


# ============================================
# Get Annaprasada Booking by Coupon ID
# ============================================

def get_booking_by_coupon(coupon_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT coupon_id, name, block, flat_number, members, is_used, served_count

    FROM annaprasada_bookings

    WHERE coupon_id = ?

    """, (coupon_id,))

    row = cursor.fetchone()

    conn.close()

    return row


# ============================================
# Serve N Members From an Annaprasada Coupon
# (partial redemption)
# ============================================
# A booking can cover multiple members who don't always
# arrive together. Each call here records how many are
# being served RIGHT NOW, on top of however many have
# already been served earlier for this same coupon.
# Returns (new_served_count, total_members) so the caller
# can tell the volunteer how many remain.

def serve_annaprasada_members(coupon_id, count_to_serve):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT members, served_count

    FROM annaprasada_bookings

    WHERE coupon_id = ?

    """, (coupon_id,))

    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    total_members = int(row[0])
    already_served = row[1] or 0

    remaining = total_members - already_served

    # Never allow serving more than what's actually left,
    # regardless of what the volunteer typed in.
    actual_serve_count = min(count_to_serve, remaining)

    new_served_count = already_served + actual_serve_count

    is_now_fully_used = 1 if new_served_count >= total_members else 0

    cursor.execute("""

    UPDATE annaprasada_bookings

    SET served_count = ?, is_used = ?

    WHERE coupon_id = ?

    """, (new_served_count, is_now_fully_used, coupon_id))

    conn.commit()
    conn.close()

    return {
        "served_now": actual_serve_count,
        "new_served_count": new_served_count,
        "total_members": total_members,
        "remaining": total_members - new_served_count
    }

    conn.commit()

    conn.close()


# ============================================
# Save Donation
# ============================================

def save_donation(receipt_id, name, flat_number, amount, utr_number=None, proof_image_path=None, status="pending", block=None):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO donations(

        receipt_id,

        name,

        flat_number,

        amount,

        utr_number,

        proof_image_path,

        status,

        block

    )

    VALUES(?,?,?,?,?,?,?,?)

    """, (

        receipt_id,

        name,

        flat_number,

        amount,

        utr_number,

        proof_image_path,

        status,

        block

    ))

    conn.commit()

    conn.close()


# ============================================
# Get Donations
# ============================================

def get_donations():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM donations

    ORDER BY id DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# ============================================
# Mark Donation Verified
# (for admin dashboard use, once a volunteer
# has checked the UTR against the bank statement)
# ============================================

def mark_donation_verified(receipt_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE donations

    SET status = 'verified'

    WHERE receipt_id = ?

    """, (receipt_id,))

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


# ============================================
# Duplicate Cultural Registration Check
# (accidental double-submit guard)
# ============================================
# A participant CAN legitimately register for the same
# category more than once (e.g. two different Solo Dance
# performances - different people, or the same person
# with two separate entries). What this catches is an
# accidental duplicate: the exact same name, category
# set, and other_details text submitted again within a
# few minutes - almost certainly a double-click or form
# resubmission, not a genuine second performance.
#
# Note: track_path isn't used for comparison here - it
# stores a randomly generated server-side filename, not
# the original upload name, so it can't reliably indicate
# whether two submissions are "the same" performance.

DUPLICATE_WINDOW_MINUTES = 5


def check_recent_duplicate_cultural_registration(
    name,
    categories,
    other_details
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT id

    FROM cultural_registrations

    WHERE LOWER(name) = LOWER(?)

    AND categories = ?

    AND COALESCE(other_details, '') = COALESCE(?, '')

    AND created_at >= datetime('now', ?)

    LIMIT 1

    """, (
        name,
        categories,
        other_details,
        f"-{DUPLICATE_WINDOW_MINUTES} minutes"
    ))

    row = cursor.fetchone()

    conn.close()

    return row is not None


# ============================================
# Get Previously Registered Cultural Categories
# (for a person, EVER - not time-limited)
# ============================================
# Used to decide whether "Performance Details" should be
# required for this submission. A person's FIRST time
# registering for a given category can leave details
# optional (as before) - but if they're registering for a
# category they've already registered for at any point in
# the past, details become required, so there's always
# something distinguishing repeat entries from each other
# instead of relying purely on the accidental-resubmit
# time-window guard above.

def get_previously_registered_categories(name, block, flat_number):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT categories

    FROM cultural_registrations

    WHERE LOWER(name) = LOWER(?)

    AND LOWER(block) = LOWER(?)

    AND flat_number = ?

    """, (name, block, flat_number))

    rows = cursor.fetchall()

    conn.close()

    previously_registered = set()

    for row in rows:

        categories_string = row[0] or ""

        for category in categories_string.split(","):

            cleaned = category.strip()

            if cleaned:
                previously_registered.add(cleaned.lower())

    return previously_registered


# ============================================
# Save Volunteer Registration
# ============================================

def save_volunteer_registration(

        name,
        block,
        flat_number,
        mobile,
        tasks,
        other_details
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO volunteers(

        name,

        block,

        flat_number,

        mobile,

        tasks,

        other_details

    )

    VALUES(?,?,?,?,?,?)

    """, (

        name,

        block,

        flat_number,

        mobile,

        tasks,

        other_details

    ))

    conn.commit()

    conn.close()


# ============================================
# Get Already-Registered Volunteer Tasks
# ============================================
# Unlike cultural categories, a volunteer task (e.g.
# "Registration Desk") has no equivalent of "two
# different performances" - there's no legitimate reason
# to be signed up for the exact same task twice, so this
# blocks re-adding a task the person already has, while
# still allowing them to add OTHER, not-yet-registered
# tasks in the same or a later submission.
#
# Matched by name + block + flat_number, NOT mobile -
# a phone number is easy to mistype or deliberately vary
# between submissions, but a resident's flat is a much
# more reliable, harder-to-fake identifier.

def get_registered_tasks_for_person(name, block, flat_number):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT tasks

    FROM volunteers

    WHERE LOWER(name) = LOWER(?)

    AND LOWER(block) = LOWER(?)

    AND flat_number = ?

    """, (name, block, flat_number))

    rows = cursor.fetchall()

    conn.close()

    already_registered = set()

    for row in rows:

        tasks_string = row[0] or ""

        for task in tasks_string.split(","):

            cleaned = task.strip()

            if cleaned:
                already_registered.add(cleaned.lower())

    return already_registered


# ============================================
# Get Volunteer Registrations
# ============================================

def get_volunteer_registrations():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM volunteers

    ORDER BY id DESC

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows