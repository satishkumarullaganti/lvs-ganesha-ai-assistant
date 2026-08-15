OLLAMA_MODEL = "llama3.2:3b"

APP_NAME = "LVS Ganesha AI Assistant"

VERSION = "2.0"

from datetime import date, timedelta

# ===========================================
# Festival Configuration
# ===========================================

ANNAPRASADA_DATE = date(2026, 8, 15)

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

# ==========================================
# Web Push Notifications (VAPID)
# ==========================================
# The public key is sent to the browser so it can create a
# push subscription; the private key signs outgoing push
# messages so browsers know they genuinely came from this
# server. Generated once with py_vapid - regenerating these
# would invalidate every existing subscription (residents
# would need to re-enable notifications), so treat this
# private key file as something to keep, not regenerate.

VAPID_PRIVATE_KEY_PATH = "backend/data/vapid_private_key.pem"
VAPID_PUBLIC_KEY = "BGeaCcva9dd6nOOye7UiVyxuLc5QDIxiqeTpfDN2SNqwjeOIB8fqPHWFJ1Yu3NxHEIKYs1dX3zFf-p4lxKVnsrE"

# VAPID requires a contact URL/email in case a push provider
# needs to reach the sender (e.g. about abuse) - any real
# contactable URL for this project works here.
VAPID_CLAIM_SUBJECT = f"mailto:satishkumar.ullaganti@gmail.com"