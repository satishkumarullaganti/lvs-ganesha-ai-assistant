import sqlite3
from pathlib import Path
from openpyxl import Workbook


# ============================================
# Database
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "database" / "festival.db"


# ============================================
# Database Connection
# ============================================

def get_connection():

    return sqlite3.connect(DB_PATH)


# ============================================
# Dashboard Summary
# ============================================

def get_dashboard_summary():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM registrations"
    )
    registrations = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM cultural_registrations"
    )
    cultural = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM volunteers"
    )
    volunteers = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM donations"
    )
    donors = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM annaprasada_bookings"
    )
    annaprasada = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COALESCE(
            SUM(CAST(amount AS REAL)),
            0
        )
        FROM donations
        """
    )

    donation_amount = cursor.fetchone()[0]

    conn.close()

    return {
        "registrations": registrations,
        "cultural_participants": cultural,
        "volunteers": volunteers,
        "donors": donors,
        "annaprasada_bookings": annaprasada,
        "total_donation_amount": donation_amount
    }


# ============================================
# Generic Table Fetch
# ============================================

def get_table_data(table_name):

    allowed_tables = {

        "registrations":
            "registrations",

        "cultural":
            "cultural_registrations",

        "volunteers":
            "volunteers",

        "donations":
            "donations",

        "annaprasada":
            "annaprasada_bookings"
    }

    if table_name not in allowed_tables:

        raise ValueError(
            "Invalid table name"
        )

    actual_table = allowed_tables[
        table_name
    ]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT *
        FROM {actual_table}
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    columns = [
        description[0]
        for description in cursor.description
    ]

    conn.close()

    return columns, rows


# ============================================
# Excel Export
# ============================================

def create_excel_file():

    workbook = Workbook()

    # Remove default sheet
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    tables = {

        "Registrations":
            "registrations",

        "Cultural Programs":
            "cultural",

        "Volunteers":
            "volunteers",

        "Donations":
            "donations",

        "Annaprasada":
            "annaprasada"
    }

    for sheet_name, table_name in tables.items():

        columns, rows = get_table_data(
            table_name
        )

        worksheet = workbook.create_sheet(
            title=sheet_name
        )

        # Header
        for column_index, column in enumerate(
            columns,
            start=1
        ):

            cell = worksheet.cell(
                row=1,
                column=column_index
            )

            cell.value = column
            cell.font = cell.font.copy(
                bold=True
            )

        # Data
        for row_index, row in enumerate(
            rows,
            start=2
        ):

            for column_index, value in enumerate(
                row,
                start=1
            ):

                worksheet.cell(
                    row=row_index,
                    column=column_index
                ).value = value

        # Auto width
        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = (
                column_cells[0].column_letter
            )

            for cell in column_cells:

                if cell.value is not None:

                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 2,
                40
            )

    return workbook