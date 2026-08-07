OLLAMA_MODEL = "llama3.2:3b"

APP_NAME = "LVS Ganesha AI Assistant"

VERSION = "2.0"

from datetime import date, timedelta

# ===========================================
# Festival Configuration
# ===========================================

ANNAPRASADA_DATE = date(2026, 8, 8)

# Booking opens 2 days before the event
BOOKING_OPEN_DATE = ANNAPRASADA_DATE - timedelta(days=2)    

# ==========================================
# Donation UPI Details (TESTING - dummy IDs)
# ==========================================

UPI_ID_GPAY = "lvsganesha@okaxis"
UPI_ID_PHONEPE = "lvsganesha@ybl"