# ============================================
# Registration Service
# ============================================

from backend.database.database import save_registration
from backend.validators import validate_flat_number


class RegistrationService:

    def __init__(self):
        # Per-session state, keyed by session_id.
        # Each entry: {"active": bool, "step": str|None, "data": dict}
        self.sessions = {}

    # ========================================
    # Internal helper
    # ========================================

    def _get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "active": False,
                "step": None,
                "data": {}
            }
        return self.sessions[session_id]

    # ========================================
    # Status Check
    # ========================================

    def is_active(self, session_id):
        return self._get_session(session_id)["active"]

    # ========================================
    # Start Registration
    # ========================================

    def start(self, session_id):
        session = self._get_session(session_id)
        session["active"] = True
        session["step"] = "competition"
        session["data"] = {}

        return (
            "🙏 Competition Registration\n\n"
            "Please choose a competition:\n\n"
            "🎨 Drawing\n"
            "♟ Chess\n"
            "🎲 Carrom\n"
            "🎵 Tambola\n"
            "🪑 Musical Chairs"
        )

    # ========================================
    # Handle Registration Steps
    # ========================================

    def process(self, session_id, message):

        session = self._get_session(session_id)
        step = session["step"]
        data = session["data"]

        # Competition
        if step == "competition":

            data["competition"] = message.title()
            session["step"] = "name"

            return "👤 Please enter your Full Name."

        # Name
        if step == "name":

            data["name"] = message
            session["step"] = "block"

            return (
                "🏢 Please choose your Block.\n\n"
                "1. South\n"
                "2. North"
            )

        # Block
        if step == "block":

            block = message.strip().lower()

            if block in ["1", "south", "south block"]:
                data["block"] = "South"

            elif block in ["2", "north", "north block"]:
                data["block"] = "North"

            else:
                return "❌ Please enter South or North."

            session["step"] = "flat"

            return "🏠 Enter Flat Number (Example: 004 or S004)."

        # Flat
        if step == "flat":

            original_flat = message.strip()
            flat = message.upper()

            # Allow optional prefixes such as S004/N008.
            flat = (
                flat.replace("SOUTH", "")
                    .replace("NORTH", "")
                    .replace("BLOCK", "")
                    .replace("S", "")
                    .replace("N", "")
                    .replace("-", "")
                    .strip()
            )

            block = data["block"]

            # Central validator:
            # - exactly 3 digits
            # - valid range for the selected block
            if not validate_flat_number(block, flat):

                return (
                    f"❌ Invalid flat number '{original_flat}' "
                    f"for {block} block.\n\n"
                    "Please enter a valid 3-digit flat number.\n"
                    "Example: 004, 020, 101."
                )

            data["flat_number"] = flat
            session["step"] = "mobile"

            return "📱 Enter Mobile Number."

        # Mobile
        if step == "mobile":

            message = message.strip()

            if not message.isdigit() or len(message) != 10:
                return "❌ Please enter a valid 10-digit mobile number."

            data["mobile"] = message
            session["step"] = "age"

            return "🎂 Enter Age."

        # Age
        if step == "age":

            try:
                age = int(message)

            except ValueError:
                return "❌ Please enter a valid age."

            data["age"] = age

            save_registration(
                data["name"],
                data["block"],
                data["flat_number"],
                data["mobile"],
                data["age"],
                data["competition"]
            )

            summary = f"""
🎉 Registration Successful!

🏆 Competition : {data['competition']}

👤 Name : {data['name']}

🏢 Block : {data['block']}

🏠 Flat : {data['flat_number']}

📱 Mobile : {data['mobile']}

🎂 Age : {data['age']}

Thank you for registering.
"""

            session["active"] = False
            session["step"] = None
            session["data"] = {}

            return summary


registration = RegistrationService()