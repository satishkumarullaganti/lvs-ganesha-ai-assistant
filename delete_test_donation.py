import sqlite3

DB = "backend/database/festival.db"

receipt_id = "DN202608076630"

connection = sqlite3.connect(DB)
cursor = connection.cursor()

cursor.execute(
    "DELETE FROM donations WHERE receipt_id = ?",
    (receipt_id,)
)

connection.commit()

print("Deleted rows:", cursor.rowcount)

connection.close()