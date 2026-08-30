from datetime import date
from enum import Enum
import random

from backend.config import (
    ANNAPRASADA_DATE,
    BOOKING_OPEN_DATE,
    PUBLIC_BASE_URL
)
from backend.qr_service import generate_qr_code
from backend.database.database import save_annaprasada_booking, get_total_booked_members_for_flat
from backend.coupon_image_service import generate_annaprasada_coupon
from backend.whatsapp_service import send_annaprasada_confirmation

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

def generate_coupon_id(suffix_index=None):
    base = "AP" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))

    # When generating several coupons in the same booking
    # (one per family member), append the loop index so two
    # coupons created back-to-back in the same request can
    # never collide, even if the random part happens to match.
    if suffix_index is not None:
        base += f"-{suffix_index}"

    return base


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

    def cancel(self, session_id):

        self.sessions[session_id] = {
            "active": False,
            "step": 0,
            "booking": {}
        }

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

(Type 'cancel' anytime to stop.)
"""

    def process_booking(self, session_id, message):

        session = self._get_session(session_id)

        # Step 1 - Members (total)
        if session["step"] == 1:

            members_input = message.strip()

            if not members_input.isdigit() or int(members_input) < 1:

                return "❌ Please enter a valid number of members (e.g. 1, 2, 4)."

            if int(members_input) > 15:

                return (
                    "❌ That's a lot for one booking - please enter a "
                    "number between 1 and 15, or contact a volunteer "
                    "for larger group bookings."
                )

            session["booking"]["members"] = members_input
            session["step"] = 2

            return (
                f"👨‍👩‍👧 Of these {members_input} member(s), how many "
                f"are adults?"
            )

        # Step 2 - Adults (children is computed as the
        # remainder, not asked separately - this avoids the
        # "numbers don't add up" problem entirely, since it
        # can never happen by construction).
        elif session["step"] == 2:

            adults_input = message.strip()
            total_members = int(session["booking"]["members"])

            if not adults_input.isdigit():

                return "❌ Please enter a valid number of adults (e.g. 2)."

            adults_count = int(adults_input)

            if adults_count < 0 or adults_count > total_members:

                return (
                    f"❌ Number of adults must be between 0 and "
                    f"{total_members} (the total members you entered "
                    f"earlier). Please re-enter."
                )

            children_count = total_members - adults_count

            session["booking"]["adults"] = str(adults_count)
            session["booking"]["children"] = str(children_count)
            session["step"] = 3

            return "👤 Please enter your Full Name."

        # Step 3 - Name
        elif session["step"] == 3:

            session["booking"]["name"] = message.strip()
            session["step"] = 4

            return "🏢 Please enter your Block."

        # Step 4 - Block
        elif session["step"] == 4:

            session["booking"]["block"] = message.strip()
            session["step"] = 5

            return "🏠 Please enter your Flat Number."

        # Step 5 - Flat Number
        elif session["step"] == 5:

            session["booking"]["flat_number"] = message.strip()
            session["step"] = 6

            return (
                "📱 Please enter your Mobile Number "
                "(so we can send your coupon on WhatsApp too)."
            )

        # Step 6 - Mobile Number
        elif session["step"] == 6:

            mobile_input = message.strip()

            if not mobile_input.isdigit() or len(mobile_input) != 10:

                return "❌ Please enter a valid 10-digit mobile number."

            session["booking"]["mobile"] = mobile_input

            booking = session["booking"]

            # --------------------------------------------
            # Informational (non-blocking) note if this
            # flat has already booked Annaprasada before.
            # Checked BEFORE saving the new booking, so the
            # count reflects only prior bookings, not this
            # one being created right now.
            # --------------------------------------------

            previously_booked = get_total_booked_members_for_flat(
                block=booking["block"],
                flat_number=booking["flat_number"]
            )

            coupon_id = generate_coupon_id()

            serial_number = save_annaprasada_booking(
                coupon_id=coupon_id,
                name=booking["name"],
                block=booking["block"],
                flat_number=booking["flat_number"],
                members=booking["members"],
                mobile=booking["mobile"],
                adults=booking["adults"],
                children=booking["children"]
            )

            # -----------------------------------------------
            # IMPORTANT: this URL gets encoded INTO the QR
            # code itself, so it must be the PUBLIC ngrok/
            # production URL, not a local IP - otherwise
            # volunteer phones on different networks can't
            # reach it.
            # -----------------------------------------------
            verify_url = f"{PUBLIC_BASE_URL}/verify/{coupon_id}"

            # Coupon image is UNCHANGED - still shows the
            # TOTAL members count only, exactly as before.
            coupon_path = generate_annaprasada_coupon(
                coupon_id=coupon_id,
                serial_number=serial_number,
                name=booking["name"],
                members=booking["members"],
                verify_url=verify_url
            )

            # WhatsApp confirmation is UNCHANGED too - same
            # signature/content as before.
            send_annaprasada_confirmation(
                name=booking["name"],
                members=booking["members"],
                block=booking["block"],
                flat=booking["flat_number"],
                coupon_id=coupon_id,
                coupon_image_path=coupon_path,
                mobile_number=booking["mobile"]
            )

            if previously_booked > 0:

                prior_booking_note = (
                    f"\nℹ️ Note: This flat has already booked "
                    f"{previously_booked} Annaprasada coupon(s) "
                    f"previously. This adds {booking['members']} more "
                    f"- if that wasn't intended, please contact a "
                    f"volunteer.\n"
                )

            else:

                prior_booking_note = ""

            response = f"""
🎉 Hi {booking['name']}!

Your Annaprasada Coupon is confirmed.
{prior_booking_note}
━━━━━━━━━━━━━━━━━━━━━━

👤 Name : {booking['name']}

🏢 Block : {booking['block']}

🏠 Flat : {booking['flat_number']}

👥 Members : {booking['members']} (Adults: {booking['adults']}, Children: {booking['children']})

🎟️ Coupon ID : {coupon_id}

━━━━━━━━━━━━━━━━━━━━━━

📱 Show this QR code at the counter (covers all {booking['members']} member(s) -
if your family arrives in separate groups, the same QR can be
scanned again for whoever arrives later, until everyone's counted):

<img src="/{coupon_path}" style="width:280px;margin-top:10px;border-radius:12px;">

🙏 Thank you!
"""

            self.sessions[session_id] = {
                "active": False,
                "step": 0,
                "booking": {}
            }

            # Tuple return (unlike every other step, which returns
            # plain text) so main.py's /chat handler can detect
            # success and trigger the Ganesha thank-you popup.
            return (response, booking['name'])


annaprasada_service = AnnaprasadaService()