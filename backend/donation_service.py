from datetime import date
import random
import re
import urllib.parse

from backend.config import UPI_ID_GPAY, UPI_ID_PHONEPE
from backend.qr_service import generate_qr_code
from backend.database.database import save_donation
from backend.receipt_service import generate_receipt_pdf
from backend.validators import validate_flat_number


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

    def cancel(self, session_id):

        self.sessions[session_id] = {
            "active": False,
            "step": 0,
            "donation": {}
        }

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

(Type 'cancel' anytime to stop.)
"""

    def process_donation(self, session_id, message):

        session = self._get_session(session_id)

        # Step 1 - Name
        if session["step"] == 1:

            session["donation"]["name"] = message.strip()
            session["step"] = 2

            return (
                "🏢 Please choose your Block.\n\n"
                "1. South\n"
                "2. North\n"
                "3. Terrace"
            )

        # Step 2 - Block
        elif session["step"] == 2:

            block_input = message.strip().lower()

            if block_input in ["1", "south", "south block"]:
                session["donation"]["block"] = "South"

            elif block_input in ["2", "north", "north block"]:
                session["donation"]["block"] = "North"

            elif block_input in ["3", "terrace", "terrace block"]:
                session["donation"]["block"] = "Terrace"

            else:
                return "❌ Please enter South, North, or Terrace."

            session["step"] = 3

            return "🏠 Please enter your Flat Number (Example: 004, S004, or T1)."

        # Step 3 - Flat Number
        elif session["step"] == 3:

            original_flat = message.strip()
            block = session["donation"]["block"]

            # Allow optional prefixes such as S004/N008, mirroring
            # the same cleanup used in the main registration flow.
            flat = (
                original_flat.upper()
                    .replace("SOUTH", "")
                    .replace("NORTH", "")
                    .replace("BLOCK", "")
                    .replace("S", "")
                    .replace("N", "")
                    .replace("-", "")
                    .strip()
            )

            if not validate_flat_number(block, flat):

                if block == "Terrace":

                    return (
                        f"❌ Invalid flat number '{original_flat}' "
                        f"for {block} block.\n\n"
                        "Please enter a valid Terrace flat number.\n"
                        "Example: T1, T2, T3."
                    )

                return (
                    f"❌ Invalid flat number '{original_flat}' "
                    f"for {block} block.\n\n"
                    "Please enter a valid 3-digit flat number.\n"
                    "Example: 004, 020, 101."
                )

            session["donation"]["flat_number"] = flat
            session["step"] = 4

            return "💰 Please enter the amount you wish to donate (₹)."

        # Step 4 - Amount → show UPI details + payment proof widget
        elif session["step"] == 4:

            raw_amount = message.strip()

            # --------------------------------------------
            # Amount validation
            # --------------------------------------------
            # Without this, non-numeric input (e.g. "abc")
            # silently produces a broken UPI QR with no
            # pre-filled amount and a nonsensical "Please
            # pay ₹abc" message - and zero/negative amounts
            # would otherwise sail through untouched too.
            #
            # Reject a leading minus sign explicitly BEFORE
            # stripping non-digit characters - otherwise
            # "-500" would have its "-" silently stripped
            # and be treated as a valid positive 500.
            # --------------------------------------------

            if raw_amount.strip().startswith("-"):

                return (
                    "❌ Please enter a valid donation amount "
                    "(numbers only, greater than 0).\n\n"
                    "Example: 500"
                )

            amount_digits_only = re.sub(r"[^0-9.]", "", raw_amount)

            try:
                amount_value = float(amount_digits_only) if amount_digits_only else 0
            except ValueError:
                amount_value = 0

            if amount_value <= 0:

                return (
                    "❌ Please enter a valid donation amount "
                    "(numbers only, greater than 0).\n\n"
                    "Example: 500"
                )

            if amount_value > 1000000:

                return (
                    "❌ That amount looks unusually large - please "
                    "double-check and re-enter, or contact a volunteer "
                    "for large donations."
                )

            # Store as a clean integer/decimal string (not the raw
            # typed text) so the confirmation message and receipt
            # always show a sane, correctly formatted amount.
            if amount_value == int(amount_value):
                session["donation"]["amount"] = str(int(amount_value))
            else:
                session["donation"]["amount"] = str(amount_value)

            session["step"] = 5

            # -----------------------------------------
            # Build a real UPI payment deep link so the
            # QR actually opens a pre-filled payment
            # screen in GPay/PhonePe/any UPI app, instead
            # of encoding a meaningless tracking string.
            # -----------------------------------------

            payee_name = "LVS Excellency Ganesha Festival"
            flat_number = session["donation"]["flat_number"]

            amount_clean = session["donation"]["amount"]

            upi_params = {
                "pa": UPI_ID_PHONEPE,
                "pn": payee_name,
                "cu": "INR",
                "tn": f"Ganesh Utsav Donation - Flat {flat_number}",
            }

            if amount_clean:
                upi_params["am"] = amount_clean

            upi_link = "upi://pay?" + urllib.parse.urlencode(upi_params)

            qr_file_name = f"donation_{flat_number}_{random.randint(1000,9999)}"
            upi_qr_path = generate_qr_code(upi_link, qr_file_name)

            return f"""
💳 Please pay ₹{session['donation']['amount']} using any UPI app:

📱 GPay UPI ID : {UPI_ID_GPAY}
📱 PhonePe UPI ID : {UPI_ID_PHONEPE}

📷 Or scan the QR code below:

<img src="/{upi_qr_path}" style="width:180px;margin-top:10px;border-radius:12px;">

<br><br>

🔎 To verify your payment, attach a screenshot of the
payment success screen. The button below will unlock
once a screenshot is attached.

<br><br>

<input type="file" id="donation-proof-input" accept="image/*" onchange="enableDonationSubmit(this)" style="margin-bottom:10px;">

<br>

<button id="donation-submit-btn" onclick="submitDonationProof()" disabled style="background:#ccc;color:white;border:none;border-radius:10px;padding:12px 24px;font-size:15px;cursor:not-allowed;">✅ I've Paid</button>

<p style="font-size:13px;color:#888;margin-top:12px;">Prefer not to upload? Type your UPI Transaction Reference Number (UTR) below instead.</p>
"""

        # Step 5 - Validate typed UTR, save as pending, issue provisional receipt
        elif session["step"] == 5:

            utr_number = message.strip().replace(" ", "")

            digit_count = sum(ch.isdigit() for ch in utr_number)

            # Real UPI UTR/RRN numbers are almost entirely digits
            # (typically 12 digits, sometimes with a couple of
            # letters for certain bank formats). Require the
            # string to be mostly numeric so plain words like
            # "donation" or "paid" can't slip through as a fake
            # reference number.
            is_valid_utr = (
                utr_number.isalnum()
                and 9 <= len(utr_number) <= 25
                and digit_count >= 9
            )

            if not is_valid_utr:

                return (
                    "❌ That doesn't look like a valid transaction "
                    "reference number. A UTR is usually a 9-12 digit "
                    "number shown on your payment success screen. "
                    "Please check your UPI app and enter it again, "
                    "or use the 📷 Upload Screenshot button above."
                )

            return self._finalize_donation(
                session_id,
                utr_number=utr_number,
                proof_image_path=None
            )

    # ========================================
    # Finalize with an uploaded screenshot
    # (called from the /donation/upload-proof
    # route instead of the normal chat flow)
    # ========================================

    def finalize_with_screenshot(self, session_id, proof_image_path):

        session = self._get_session(session_id)

        if not session["active"] or session["step"] != 5:
            return None

        return self._finalize_donation(
            session_id,
            utr_number=None,
            proof_image_path=proof_image_path
        )

    # ========================================
    # Shared finalize logic (UTR or screenshot)
    # ========================================

    def _finalize_donation(self, session_id, utr_number=None, proof_image_path=None):

        session = self._get_session(session_id)
        donation = session["donation"]

        receipt_id = generate_receipt_id()

        save_donation(
            receipt_id=receipt_id,
            name=donation["name"],
            flat_number=donation["flat_number"],
            amount=donation["amount"],
            utr_number=utr_number,
            proof_image_path=proof_image_path,
            status="pending",
            block=donation.get("block")
        )

        receipt_path = generate_receipt_pdf(
            receipt_id=receipt_id,
            name=donation["name"],
            flat_number=donation["flat_number"],
            amount=donation["amount"],
            utr_number=utr_number,
            proof_uploaded=bool(proof_image_path),
            status="pending",
            block=donation.get("block")
        )

        if utr_number:
            proof_line = f"🔎 UTR / Ref No. : {utr_number}"
        else:
            proof_line = "📷 Payment Proof : Screenshot Uploaded"

        response = f"""
🙏 Thank you, {donation['name']}, for your generous contribution!

Your payment proof has been recorded and will be
verified by our volunteers against the bank statement
shortly.

━━━━━━━━━━━━━━━━━━━━━━
🧾 PROVISIONAL DONATION RECEIPT
━━━━━━━━━━━━━━━━━━━━━━

👤 Name : {donation['name']}
🏢 Block : {donation.get('block', '-')}
🏠 Flat : {donation['flat_number']}
💰 Amount : ₹{donation['amount']}
{proof_line}
🧾 Receipt ID : {receipt_id}
⏳ Status : Pending Verification

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

        # Tuple return so main.py can detect success and
        # trigger the Ganesha thank-you popup - covers BOTH
        # completion paths (typed UTR via chat, and screenshot
        # upload via the separate /donation/upload-proof
        # route), since both call this shared function.
        return (response, donation['name'])


donation_service = DonationService()