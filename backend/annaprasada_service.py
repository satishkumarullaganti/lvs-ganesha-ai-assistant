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
from backend.validators import validate_flat_number


class BookingStatus(Enum):
    NOT_OPEN = "NOT_OPEN"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


def generate_coupon_id():
    return "AP" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))


class AnnaprasadaService:

    def __init__(self):
        self.active = False
        self.step = 0
        self.booking = {}

    def check_booking_status(self):

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
                "response": self.start_booking()
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

    def start_booking(self):
        print(">>> start_booking() called")
        self.active = True
        self.step = 1
        self.booking = {}

        return """
🍛 Annaprasada Coupon Booking

Booking is now OPEN.

👥 How many members are you booking for?
"""

    def process_booking(self, message):

        print(">>> process_booking() called")
        print("Step:", self.step)
        print("Message:", message)

        # Step 1 - Members
        if self.step == 1:

            self.booking["members"] = message.strip()
            self.step = 2

            return "👤 Please enter your Full Name."

        # Step 2 - Name
        elif self.step == 2:

            self.booking["name"] = message.strip()
            self.step = 3

            return "🏢 Please enter your Block."

        # Step 3 - Block
        elif self.step == 3:

            block = message.strip()

            if block.upper() not in {"NORTH", "SOUTH"}:

                return "❌ Invalid block. Please enter North or South."

            self.booking["block"] = block
            self.step = 4

            return "🏠 Please enter your Flat Number (e.g. 004)."

        # Step 4 - Flat Number
        elif self.step == 4:

            flat_number = message.strip()
            block = self.booking["block"]

            if not validate_flat_number(block, flat_number):

                return (
                    f"❌ Invalid flat number '{flat_number}' "
                    f"for {block} block. "
                    "Please enter a valid 3-digit flat number."
                )

            self.booking["flat_number"] = flat_number

            self.active = False
            self.step = 0

            coupon_id = generate_coupon_id()

            save_annaprasada_booking(
                coupon_id=coupon_id,
                name=self.booking["name"],
                block=self.booking["block"],
                flat_number=self.booking["flat_number"],
                members=self.booking["members"]
            )

            verify_url = f"{PUBLIC_BASE_URL}/verify/{coupon_id}"
            qr_path = generate_qr_code(verify_url, coupon_id)

            return f"""
🎉 Hi {self.booking['name']}!

Your Annaprasada Coupon is confirmed.

━━━━━━━━━━━━━━━━━━━━━━

👤 Name : {self.booking['name']}

🏢 Block : {self.booking['block']}

🏠 Flat : {self.booking['flat_number']}

👥 Members : {self.booking['members']}

🎟️ Coupon ID : {coupon_id}

━━━━━━━━━━━━━━━━━━━━━━

📱 Show this QR code at the counter:

<img src="/{qr_path}" style="width:180px;margin-top:10px;border-radius:12px;">

🙏 Thank you!
"""


annaprasada_service = AnnaprasadaService()
