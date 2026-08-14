OLLAMA_MODEL = "llama3.2:3b"

APP_NAME = "LVS Ganesha AI Assistant"

VERSION = "2.0"

from datetime import date, timedelta

# ===========================================
# Festival Configuration
# ===========================================

ANNAPRASADA_DATE = date(2026, 8, 14)

# Booking opens 2 days before the event
BOOKING_OPEN_DATE = ANNAPRASADA_DATE - timedelta(days=2)    

# ==========================================
# Donation UPI Details (TESTING - dummy IDs)
# ==========================================

UPI_ID_GPAY = "satishkumarullaganti@okhdfcbank"
UPI_ID_PHONEPE = "9866406054-2@ybl"

# ==========================================
# Public Base URL
# ==========================================
# This MUST be your current public ngrok URL, not a local
# IP or 127.0.0.1 - it gets encoded directly into QR codes,
# so volunteer/attendee phones on any network can reach it.
# If your ngrok URL ever changes, update it here only.

PUBLIC_BASE_URL = "https://agency-unwrapped-judicial.ngrok-free.dev"

