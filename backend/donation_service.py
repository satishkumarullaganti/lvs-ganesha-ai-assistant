from datetime import date
import random

from backend.config import UPI_ID_GPAY, UPI_ID_PHONEPE
from backend.qr_service import generate_qr_code
from backend.database.database import save_donation
from backend.receipt_service import generate_receipt_pdf


def generate_receipt_id():
    return "DN" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))


# ==========================================
# Donation Service
# ==========================================
# IMPORTANT: This service is now SESSION-AWARE.
# Every method takes a session_id, and donation
# state is stored per-session, not shared across
# every visitor.
# ==========================================

class DonationService:

    def __init__(self):
        # session_id -> {"active": bool, "step": int, "donation": dict}
        self.sessions = {}

    def _get_session(self, session_id):

        if session_id not in self.sessions:

            self.sessions[session_id] = {
                "active": False,
                "step": 0,
                "donation": {}
            }

        return self.sessions[session_id]

    def is_active(self, session_id):

        return self._get_session(session_id)["active"]

    def start_donation(self, session_id):

        self.sessions[session_id] = {
            "active": True,
            "step": 1,
            "donation": {}
        }

        return """
🙏 Thank you for your generous heart!

Every contribution helps make this Ganesh festival memorable for our community.

👤 Please enter your Name.
"""

    def process_donation(self, session_id, message):

        session = self._get_session(session_id)

        # Step 1 - Name
        if session["step"] == 1:

            session["donation"]["name"] = message.strip()
            session["step"] = 2

            return "🏠 Please enter your Flat Number."

        # Step 2 - Flat Number
        elif session["step"] == 2:

            session["donation"]["flat_number"] = message.strip()
            session["step"] = 3

            return "💰 Please enter the amount you wish to donate (₹)."

        # Step 3 - Amount → show UPI details
        elif session["step"] == 3:

            session["donation"]["amount"] = message.strip()
            session["step"] = 4

            upi_ref = f"upi_{session['donation']['flat_number']}_{random.randint(1000,9999)}"
            upi_qr_path = generate_qr_code(upi_ref, upi_ref)

            return f"""
💳 Please pay ₹{session['donation']['amount']} using any UPI app:

📱 GPay UPI ID : {UPI_ID_GPAY}
📱 PhonePe UPI ID : {UPI_ID_PHONEPE}

📷 Or scan the QR code below:

<img src="/{upi_qr_path}" style="width:180px;margin-top:10px;border-radius:12px;">

<br><br>

<button onclick="confirmDonationPaid()" style="background:#4CAF50;color:white;border:none;border-radius:10px;padding:12px 24px;font-size:15px;cursor:pointer;">✅ I've Paid</button>
"""

        # Step 4 - Confirm Payment
        elif session["step"] == 4:

            receipt_id = generate_receipt_id()
            donation = session["donation"]

            save_donation(
                receipt_id=receipt_id,
                name=donation["name"],
                flat_number=donation["flat_number"],
                amount=donation["amount"]
            )

            receipt_path = generate_receipt_pdf(
                receipt_id=receipt_id,
                name=donation["name"],
                flat_number=donation["flat_number"],
                amount=donation["amount"]
            )

            response = f"""
🙏 Thank you, {donation['name']}, for your generous contribution!

━━━━━━━━━━━━━━━━━━━━━━
🧾 DONATION RECEIPT
━━━━━━━━━━━━━━━━━━━━━━

👤 Name : {donation['name']}
🏠 Flat : {donation['flat_number']}
💰 Amount : ₹{donation['amount']}
🧾 Receipt ID : {receipt_id}

━━━━━━━━━━━━━━━━━━━━━━

May Lord Ganesha bless you and your family. 🙏

<br><br>

<a href="/{receipt_path}" target="_blank" style="display:inline-block;background:#ff9800;color:white;padding:10px 20px;border-radius:10px;text-decoration:none;font-size:14px;">📥 Download Receipt (PDF)</a>
"""

            self.sessions[session_id] = {
                "active": False,
                "step": 0,
                "donation": {}
            }

            return response


donation_service = DonationService()