from datetime import date
import random
import re
import urllib.parse

from backend.config import UPI_ID, UPI_PAYEE_NAME
from backend.qr_service import generate_qr_code
from backend.database.database import save_donation, find_known_resident
from backend.receipt_service import generate_receipt_pdf
from backend.whatsapp_service import send_donation_confirmation
from backend.validators import validate_flat_number


def generate_receipt_id():
    return "DN" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))


def generate_register_receipt_id():
    """
    Separate prefix (RG instead of DN) for donations entered
    via the security-desk register scan, so admins can tell
    at a glance in the dashboard/exports which donations came
    in online vs. were collected in-person and scanned later.
    """
    return "RG" + date.today().strftime("%Y%m%d") + str(random.randint(1000, 9999))


# ==========================================
# Donation Service
# ==========================================
# IMPORTANT: This service is SESSION-AWARE.
# Every method takes a session_id, and donation
# state is stored per-session, not shared across
# every visitor.
#
# UPDATED FLOW: mobile number is now asked FIRST
# (instead of last). If that number matches a
# previous donation/registration/booking anywhere
# in the system, we greet the resident by name and
# confirm their known block/flat instead of asking
# again - only the amount still needs to be entered.
# If the number is new, the flow continues exactly
# as before (name, block, flat, mobile already have
# it, then amount).
# ==========================================

class DonationService:

    def __init__(self):
        # session_id -> {"active": bool, "step": int|str, "donation": dict}
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
            "step": "mobile",
            "donation": {}
        }

        return """
🙏 Thank you for your generous heart!

Every contribution helps make this Ganesh festival memorable for our community.

📱 Please enter your Mobile Number to get started.

(Type 'cancel' anytime to stop.)
"""

    def process_donation(self, session_id, message):

        session = self._get_session(session_id)

        # --------------------------------------------
        # Step: Mobile (asked FIRST now)
        # --------------------------------------------
        if session["step"] == "mobile":

            mobile_input = message.strip()

            if not mobile_input.isdigit() or len(mobile_input) != 10:
                return "❌ Please enter a valid 10-digit mobile number."

            session["donation"]["mobile"] = mobile_input

            known = find_known_resident(mobile_input)

            if known:

                session["donation"]["name"] = known["name"]
                session["donation"]["block"] = known["block"]
                session["donation"]["flat_number"] = known["flat_number"]
                session["step"] = "confirm_known"

                return (
                    f"👋 Welcome back!\n\n"
                    f"This number is linked to:\n"
                    f"👤 {known['name']}\n"
                    f"🏢 Block: {known['block']}\n"
                    f"🏠 Flat: {known['flat_number']}\n\n"
                    "Please choose:\n\n"
                    "1️⃣ Yes, same details\n"
                    "2️⃣ Different family member, same Block/Flat\n"
                    "3️⃣ No, everything is different"
                )

            session["step"] = 1

            return "👤 Please enter your Name."

        # --------------------------------------------
        # Step: Confirm known details
        # --------------------------------------------
        if session["step"] == "confirm_known":

            answer = message.strip().lower()

            # Option 1 - same person, same everything
            if answer in ["1", "yes", "y", "correct", "yeah", "yep"]:

                session["step"] = 5

                return "💰 Please enter the amount you wish to donate (₹)."

            # Option 2 - different family member, same address -
            # keep block/flat, only ask for the new name
            if answer in ["2", "different", "family", "family member"]:

                session["donation"]["name"] = None
                session["step"] = "name_only"

                return (
                    f"👤 Please enter the Name for this donation "
                    f"(Block {session['donation']['block']}, "
                    f"Flat {session['donation']['flat_number']} will stay the same)."
                )

            # Option 3 - nothing matches, start completely fresh
            if answer in ["3", "no", "n", "nope"]:

                session["donation"]["name"] = None
                session["donation"]["block"] = None
                session["donation"]["flat_number"] = None
                session["step"] = 1

                return "No problem! 👤 Please enter your Name."

            return "❌ Please reply 1, 2, or 3."

        # --------------------------------------------
        # Step: Name only (Option 2 path - block/flat
        # already known, just need the new name before
        # jumping straight to the amount)
        # --------------------------------------------
        if session["step"] == "name_only":

            session["donation"]["name"] = message.strip()
            session["step"] = 5

            return "💰 Please enter the amount you wish to donate (₹)."

        # Step 1 - Name (only reached for new/unrecognized residents)
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
            session["step"] = 5

            return "💰 Please enter the amount you wish to donate (₹)."

        # Step 5 - Amount → show UPI details + payment proof widget
        elif session["step"] == 5:

            raw_amount = message.strip()

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

            if amount_value == int(amount_value):
                session["donation"]["amount"] = str(int(amount_value))
            else:
                session["donation"]["amount"] = str(amount_value)

            session["step"] = 6

            payee_name = "LVS Excellency Ganesha Festival"
            flat_number = session["donation"]["flat_number"]

            amount_clean = session["donation"]["amount"]

            upi_params = {
                "pa": UPI_ID,
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

<br><br>

<a href="{upi_link}" style="display:inline-block;background:#ff9800;color:white;padding:14px 28px;border-radius:12px;text-decoration:none;font-size:16px;font-weight:bold;">💳 Pay ₹{session['donation']['amount']} Now</a>

<p style="font-size:13px;color:#888;margin-top:8px;">Tap above to pay directly with GPay, PhonePe, or any UPI app on this phone.</p>

<br>

📱 UPI ID ({UPI_PAYEE_NAME}) : {UPI_ID}

<p style="font-size:13px;color:#888;margin-top:16px;">On a computer? Scan this QR code with your phone's UPI app instead:</p>

<img src="/{upi_qr_path}" style="width:160px;margin-top:6px;border-radius:12px;">

<br><br>

<a href="{upi_link}" style="display:inline-block;background:#ff9800;color:white;padding:14px 28px;border-radius:12px;text-decoration:none;font-size:16px;font-weight:bold;">💳 Pay ₹{session['donation']['amount']} Now</a>

<br><br>

🔎 To verify your payment, attach a screenshot of the
payment success screen. The button below will unlock
once a screenshot is attached.

<br><br>

<input type="file" id="donation-proof-input" class="donation-proof-input" accept="image/*" onchange="enableDonationSubmit(this)" style="margin-bottom:10px;">

<br>

<button id="donation-submit-btn" class="donation-submit-btn" onclick="submitDonationProof(this)" disabled style="background:#ccc;color:white;border:none;border-radius:10px;padding:12px 24px;font-size:15px;cursor:not-allowed;">✅ I've Paid</button>

<p style="font-size:13px;color:#888;margin-top:12px;">Prefer not to upload? Type your UPI Transaction Reference Number (UTR) below instead.</p>
"""

        # Step 6 - Validate typed UTR, save as pending, issue provisional receipt
        elif session["step"] == 6:

            utr_number = message.strip().replace(" ", "")

            digit_count = sum(ch.isdigit() for ch in utr_number)

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
    # ========================================

    def finalize_with_screenshot(self, session_id, proof_image_path):

        session = self._get_session(session_id)

        if not session["active"] or session["step"] != 6:
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
            block=donation.get("block"),
            mobile=donation.get("mobile")
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

        send_donation_confirmation(
            name=donation["name"],
            amount=donation["amount"],
            receipt_id=receipt_id,
            receipt_pdf_path=receipt_path,
            mobile_number=donation.get("mobile")
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

        return (response, donation['name'])

    # ========================================
    # Save a donation collected in-person at the
    # security desk register (not via chat flow)
    # ========================================

    def save_register_donation(self, name, block, flat_number, amount, mobile=None):

        receipt_id = generate_register_receipt_id()

        save_donation(
            receipt_id=receipt_id,
            name=name,
            flat_number=flat_number,
            amount=str(amount),
            utr_number=None,
            proof_image_path=None,
            status="pending",
            block=block,
            mobile=mobile
        )

        receipt_path = generate_receipt_pdf(
            receipt_id=receipt_id,
            name=name,
            flat_number=flat_number,
            amount=str(amount),
            utr_number=None,
            proof_uploaded=False,
            status="pending",
            block=block
        )

        whatsapp_sent = False

        if mobile:
            whatsapp_sent = send_donation_confirmation(
                name=name,
                amount=str(amount),
                receipt_id=receipt_id,
                receipt_pdf_path=receipt_path,
                mobile_number=mobile
            )

        return {
            "receipt_id": receipt_id,
            "receipt_path": receipt_path,
            "whatsapp_sent": whatsapp_sent
        }


donation_service = DonationService()