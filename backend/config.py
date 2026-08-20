OLLAMA_MODEL = "llama3.2:3b"

APP_NAME = "LVS Ganesha AI Assistant"

VERSION = "2.0"

from datetime import date, timedelta
import os as _os

# --------------------------------------------------
# Load .env HERE, at the very top of config.py, rather
# than relying on main.py to have done it first. Some of
# main.py's OWN imports (e.g. whatsapp_service) import
# this config module before main.py's own load_dotenv()
# call runs - without this line, env vars read below
# would get "" permanently locked in at import time,
# regardless of what's actually in .env.
#
# Uses an EXPLICIT path (computed from this file's own
# location) rather than relying on load_dotenv()'s
# automatic directory-searching - that auto-search proved
# unreliable under uvicorn's --reload worker process in
# testing, even though the .env file itself was confirmed
# correct via a standalone diagnostic.
# --------------------------------------------------
from dotenv import load_dotenv

_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_ENV_PATH = _os.path.join(_PROJECT_ROOT, ".env")

load_dotenv(_ENV_PATH)

# ===========================================
# Festival Configuration
# ===========================================

ANNAPRASADA_DATE = date(2026, 8, 16)

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
VAPID_CLAIM_SUBJECT = f"mailto:admin@example.com"

# ==========================================
# WhatsApp Business API (Meta Cloud API)
# ==========================================
# Phone Number ID is not secret (safe to hardcode) - the
# Access Token IS secret and must come from a local .env
# file (never commit it to git). Add this line to your
# .env file at the project root:
#
#   WHATSAPP_ACCESS_TOKEN=your_real_token_here
#
# If WHATSAPP_ACCESS_TOKEN is missing, whatsapp_service.py
# will skip sending gracefully (registration itself still
# succeeds either way - WhatsApp is a nice-to-have, not a
# blocker) rather than crashing anything.

WHATSAPP_PHONE_NUMBER_ID = "1272269172637594"
WHATSAPP_ACCESS_TOKEN = _os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_API_VERSION = "v20.0"