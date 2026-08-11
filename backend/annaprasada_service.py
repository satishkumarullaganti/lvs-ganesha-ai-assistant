from datetime import date
from enum import Enum
import random

from backend.config import (
    ANNAPRASADA_DATE,
    BOOKING_OPEN_DATE,
    PUBLIC_BASE_URL
)
from backend.qr_service import generate_qr_code
from backend.database.database import save_annaprasada_booking

# ==========================================
# Booking Status
# ==========================================

class BookingStatus(Enum):
    NOT_OPEN = "NOT_OPEN"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


# ==========================================
# Coupon ID Generator
# ==========================================

def generate_coupon_id():
    return "AP" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))


# ==========================================
# Annaprasada Service
# ==========================================
# IMPORTANT: This service is now SESSION-AWARE.
# Every method takes a session_id, and booking
# state is stored per-session, not shared across
# every visitor.
# ==========================================

class AnnaprasadaService:

    def __init__(self):
        # session_id -> {"active": bool, "step": int, "booking": dict}
        self.sessions = {}

    def _get_session(self, session_id):

        if session_id not in self.sessions:

            self.sessions[session_id] = {
                "active": False,
                "step": 0,
                "booking": {}
            }

        return self.sessions[session_id]

    def is_active(self, session_id):

        return self._get_session(session_id)["active"]

    def check_booking_status(self, session_id):

        today = date.today()

        if today < BOOKING_OPEN_DATE:

            return {
                "status": BookingStatus.NOT_OPEN,
                "response": f"""
🍛 Annaprasada Coupon Booking

🙏 Thank you for your interest.

Coupon booking has not opened yet.

📅 Annaprasada Date
{ANNAPRASADA_DATE.strftime("%d-%b-%Y")}

📅 Coupon Booking Opens
{BOOKING_OPEN_DATE.strftime("%d-%b-%Y")}

Please visit again on or after the booking opening date.

🙏 Thank you.
"""
            }

        elif today <= ANNAPRASADA_DATE:

            return {
                "status": BookingStatus.OPEN,
                "response": self.start_booking(session_id)
            }

        else:

            return {
                "status": BookingStatus.CLOSED,
                "response": """
🍛 Annaprasada Coupon Booking

The Annaprasada event has been completed.

Coupon booking is now closed.

🙏 Thank you.
"""
            }

    def start_booking(self, session_id):

        self.sessions[session_id] = {
            "active": True,
            "step": 1,
            "booking": {}
        }

        return """
🍛 Annaprasada Coupon Booking

Booking is now OPEN.

👥 How many members are you booking for?
"""

    def process_booking(self, session_id, message):

        session = self._get_session(session_id)

        # Step 1 - Members
        if session["step"] == 1:

            session["booking"]["members"] = message.strip()
            session["step"] = 2

            return "👤 Please enter your Full Name."

        # Step 2 - Name
        elif session["step"] == 2:

            session["booking"]["name"] = message.strip()
            session["step"] = 3

            return "🏢 Please enter your Block."

        # Step 3 - Block
        elif session["step"] == 3:

            session["booking"]["block"] = message.strip()
            session["step"] = 4

            return "🏠 Please enter your Flat Number."

        # Step 4 - Flat Number
        elif session["step"] == 4:

            session["booking"]["flat_number"] = message.strip()

            coupon_id = generate_coupon_id()

            save_annaprasada_booking(
                coupon_id=coupon_id,
                name=session["booking"]["name"],
                block=session["booking"]["block"],
                flat_number=session["booking"]["flat_number"],
                members=session["booking"]["members"]
            )

            # -----------------------------------------------
            # IMPORTANT: this URL gets encoded INTO the QR
            # code itself, so it must be the PUBLIC ngrok/
            # production URL, not a local IP - otherwise
            # volunteer phones on different networks can't
            # reach it.
            # -----------------------------------------------
            verify_url = f"{PUBLIC_BASE_URL}/verify/{coupon_id}"
            qr_path = generate_qr_code(verify_url, coupon_id)

            booking = session["booking"]

            response = f"""
🎉 Hi {booking['name']}!

Your Annaprasada Coupon is confirmed.

━━━━━━━━━━━━━━━━━━━━━━

👤 Name : {booking['name']}

🏢 Block : {booking['block']}

🏠 Flat : {booking['flat_number']}

👥 Members : {booking['members']}

🎟️ Coupon ID : {coupon_id}

━━━━━━━━━━━━━━━━━━━━━━

📱 Show this QR code at the counter:

<img src="/{qr_path}" style="width:180px;margin-top:10px;border-radius:12px;">

🙏 Thank you!
"""

            self.sessions[session_id] = {
                "active": False,
                "step": 0,
                "booking": {}
            }

            return response


annaprasada_service = AnnaprasadaService()