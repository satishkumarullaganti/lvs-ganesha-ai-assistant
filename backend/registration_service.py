# ============================================
# Registration Service
# ============================================

from backend.database.database import save_registration
from backend.validators import validate_flat_number


class RegistrationService:

    def __init__(self):
        self.active = False
        self.step = None
        self.data = {}

    # ========================================
    # Start Registration
    # ========================================

    def start(self):
        self.active = True
        self.step = "competition"
        self.data = {}

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

    def process(self, message):

        # Competition
        if self.step == "competition":

            self.data["competition"] = message.title()
            self.step = "name"

            return "👤 Please enter your Full Name."

        # Name
        if self.step == "name":

            self.data["name"] = message
            self.step = "block"

            return (
                "🏢 Please choose your Block.\n\n"
                "1. South\n"
                "2. North"
            )

        # Block
        if self.step == "block":

            block = message.strip().lower()

            if block in ["1", "south", "south block"]:
                self.data["block"] = "South"

            elif block in ["2", "north", "north block"]:
                self.data["block"] = "North"

            else:
                return "❌ Please enter South or North."

            self.step = "flat"

            return "🏠 Enter Flat Number (Example: 004 or S004)."

        # Flat
        if self.step == "flat":

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

            block = self.data["block"]

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

            self.data["flat_number"] = flat
            self.step = "mobile"

            return "📱 Enter Mobile Number."

        # Mobile
        if self.step == "mobile":

            message = message.strip()

            if not message.isdigit() or len(message) != 10:
                return "❌ Please enter a valid 10-digit mobile number."

            self.data["mobile"] = message
            self.step = "age"

            return "🎂 Enter Age."

        # Age
        if self.step == "age":

            try:
                age = int(message)

            except ValueError:
                return "❌ Please enter a valid age."

            self.data["age"] = age

            save_registration(
                self.data["name"],
                self.data["block"],
                self.data["flat_number"],
                self.data["mobile"],
                self.data["age"],
                self.data["competition"]
            )

            summary = f"""
🎉 Registration Successful!

🏆 Competition : {self.data['competition']}

👤 Name : {self.data['name']}

🏢 Block : {self.data['block']}

🏠 Flat : {self.data['flat_number']}

📱 Mobile : {self.data['mobile']}

🎂 Age : {self.data['age']}

Thank you for registering.
"""

            self.active = False
            self.step = None
            self.data = {}

            return summary


registration = RegistrationService()
