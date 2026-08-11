from datetime import date
import random

from backend.config import UPI_ID_GPAY, UPI_ID_PHONEPE
from backend.qr_service import generate_qr_code
from backend.database.database import save_donation
from backend.receipt_service import generate_receipt_pdf
from backend.validators import validate_flat_number_any_block


def generate_receipt_id():
    return "DN" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))


class DonationService:

    def __init__(self):
        self.active = False
        self.step = 0
        self.donation = {}

    def start_donation(self):

        self.active = True
        self.step = 1
        self.donation = {}

        return """
🙏 Thank you for your generous heart!

Every contribution helps make this Ganesh festival memorable for our community.

👤 Please enter your Name.
"""

    def process_donation(self, message):

        # Step 1 - Name
        if self.step == 1:

            self.donation["name"] = message.strip()
            self.step = 2

            return "🏠 Please enter your Flat Number (e.g. 004)."

        # Step 2 - Flat Number
        elif self.step == 2:

            flat_number = message.strip()

            if not validate_flat_number_any_block(flat_number):

                return (
                    f"❌ Invalid flat number '{flat_number}'. "
                    "Please enter a valid 3-digit flat number."
                )

            self.donation["flat_number"] = flat_number
            self.step = 3

            return "💰 Please enter the amount you wish to donate (₹)."

        # Step 3 - Amount → show UPI details
        elif self.step == 3:

            self.donation["amount"] = message.strip()
            self.step = 4

            upi_ref = (
                f"upi_{self.donation['flat_number']}_"
                f"{random.randint(1000,9999)}"
            )
            upi_qr_path = generate_qr_code(upi_ref, upi_ref)

            return f"""
💳 Please pay ₹{self.donation['amount']} using any UPI app:

📱 GPay UPI ID : {UPI_ID_GPAY}
📱 PhonePe UPI ID : {UPI_ID_PHONEPE}

📷 Or scan the QR code below:

<img src="/{upi_qr_path}" style="width:180px;margin-top:10px;border-radius:12px;">

<br><br>

<button onclick="confirmDonationPaid()" style="background:#4CAF50;color:white;border:none;border-radius:10px;padding:12px 24px;font-size:15px;cursor:pointer;">✅ I've Paid</button>
"""

        # Step 4 - Confirm Payment
        elif self.step == 4:

            self.active = False
            self.step = 0

            receipt_id = generate_receipt_id()

            save_donation(
                receipt_id=receipt_id,
                name=self.donation["name"],
                flat_number=self.donation["flat_number"],
                amount=self.donation["amount"]
            )

            receipt_path = generate_receipt_pdf(
                receipt_id=receipt_id,
                name=self.donation["name"],
                flat_number=self.donation["flat_number"],
                amount=self.donation["amount"]
            )

            return f"""
🙏 Thank you, {self.donation['name']}, for your generous contribution!

━━━━━━━━━━━━━━━━━━━━━━
🧾 DONATION RECEIPT
━━━━━━━━━━━━━━━━━━━━━━

👤 Name : {self.donation['name']}
🏠 Flat : {self.donation['flat_number']}
💰 Amount : ₹{self.donation['amount']}
🧾 Receipt ID : {receipt_id}

━━━━━━━━━━━━━━━━━━━━━━

May Lord Ganesha bless you and your family. 🙏

<br><br>

<a href="/{receipt_path}" target="_blank" style="display:inline-block;background:#ff9800;color:white;padding:10px 20px;border-radius:10px;text-decoration:none;font-size:14px;">📥 Download Receipt (PDF)</a>
"""


donation_service = DonationService()
