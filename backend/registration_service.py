# ============================================
# Registration Service
# ============================================
# UPDATED FLOW: mobile number is now asked right
# after choosing a competition (instead of last).
# If that number matches a previous donation/
# registration/booking anywhere in the system, we
# offer three options instead of re-asking every
# field:
#   1. Same person, same details
#   2. Different family member, same Block/Flat
#   3. Everything is different
# If the number is new, the flow continues exactly
# as before (name, block, flat, then age - mobile
# is already collected by that point).
# UPDATED AGAIN: after Age, a confirm_details step
# now shows a summary and requires "yes"/"edit"
# before anything is saved.
# UPDATED AGAIN: the competition step only accepts
# ONE valid competition (by name or menu number) -
# it used to accept any free text, so a reply like
# "Carrom Chess Tambola" saved as one garbled value
# on a single row instead of three real, countable
# registrations.
# ============================================
from backend.database.database import (
    save_registration,
    check_duplicate_competition_registration,
    find_known_resident
)
from backend.whatsapp_service import send_registration_confirmation
from backend.validators import validate_flat_number
# ============================================
# Valid Competitions
# ============================================
# Single source of truth for what a valid answer to the
# competition question looks like - matched by name
# (case/spacing-insensitive) or by its position in the
# menu (1-5), and always normalized to this exact display
# name so duplicate-checking and the Excel export stay
# consistent.
VALID_COMPETITIONS = [
    "Drawing",
    "Chess",
    "Carrom",
    "Tambola",
    "Musical Chairs",
    "Tug Of War",
]
def _match_competition(message):
    """
    Returns the canonical competition name if the message names
    exactly one valid competition (by number or by name), otherwise
    None. None covers both "matched nothing" and "matched more than
    one" - either way the caller should re-ask rather than guess.
    """
    cleaned = message.strip().lower()
    if not cleaned:
        return None
    # Numeric shortcut - "1".."5", matching the menu order.
    if cleaned.isdigit():
        index = int(cleaned) - 1
        if 0 <= index < len(VALID_COMPETITIONS):
            return VALID_COMPETITIONS[index]
        return None
    # Name match - tolerate a trailing "s" (e.g. "carroms") and
    # extra surrounding whitespace, but require the whole message
    # to be just that one competition's name, not a substring of a
    # longer message that could hide a second name in it.
    for competition in VALID_COMPETITIONS:
        canonical = competition.lower()
        if cleaned in (canonical, canonical + "s"):
            return competition
    return None
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
    # Cancel / Reset
    # ========================================
    def cancel(self, session_id):
        self.sessions[session_id] = {
            "active": False,
            "step": None,
            "data": {}
        }
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
            "🪑 Musical Chairs\n"
            "🪢 Tug Of War\n\n"
            "(Type 'cancel' anytime to stop.)"
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
            matched_competition = _match_competition(message)
            if not matched_competition:
                return (
                    "❌ Please choose just ONE competition from the "
                    "list below (type the name or its number):\n\n"
                    "1. 🎨 Drawing\n"
                    "2. ♟ Chess\n"
                    "3. 🎲 Carrom\n"
                    "4. 🎵 Tambola\n"
                    "5. 🪑 Musical Chairs\n"
                    "6. 🪢 Tug Of War\n\n"
                    "(Want more than one? Register again separately "
                    "for each competition after this one is done.)"
                )
            data["competition"] = matched_competition
            session["step"] = "mobile"
            return "📱 Please enter your Mobile Number."
        # --------------------------------------------
        # Mobile (asked right after competition now)
        # --------------------------------------------
        if step == "mobile":
            mobile_input = message.strip()
            if not mobile_input.isdigit() or len(mobile_input) != 10:
                return "❌ Please enter a valid 10-digit mobile number."
            data["mobile"] = mobile_input
            known = find_known_resident(mobile_input)
            if known:
                data["name"] = known["name"]
                data["block"] = known["block"]
                data["flat_number"] = known["flat_number"]
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
            session["step"] = "name"
            return "👤 Please enter your Full Name."
        # --------------------------------------------
        # Confirm known details
        # --------------------------------------------
        if step == "confirm_known":
            answer = message.strip().lower()
            if answer in ["1", "yes", "y", "correct", "yeah", "yep"]:
                session["step"] = "age"
                return "🎂 Enter Age."
            if answer in ["2", "different", "family", "family member"]:
                data["name"] = None
                session["step"] = "name_only"
                return (
                    f"👤 Please enter the Name for this registration "
                    f"(Block {data['block']}, Flat {data['flat_number']} "
                    f"will stay the same)."
                )
            if answer in ["3", "no", "n", "nope"]:
                data["name"] = None
                data["block"] = None
                data["flat_number"] = None
                session["step"] = "name"
                return "No problem! 👤 Please enter your Full Name."
            return "❌ Please reply 1, 2, or 3."
        # --------------------------------------------
        # Name only (Option 2 path)
        # --------------------------------------------
        if step == "name_only":
            data["name"] = message.strip()
            session["step"] = "age"
            return "🎂 Enter Age."
        # Name (only reached for new/unrecognized residents,
        # or Option 3 - everything different)
        if step == "name":
            data["name"] = message
            session["step"] = "block"
            return (
                "🏢 Please choose your Block.\n\n"
                "1. South\n"
                "2. North\n"
                "3. Terrace"
            )
        # Block
        if step == "block":
            block = message.strip().lower()
            if block in ["1", "south", "south block"]:
                data["block"] = "South"
            elif block in ["2", "north", "north block"]:
                data["block"] = "North"
            elif block in ["3", "terrace", "terrace block"]:
                data["block"] = "Terrace"
            else:
                return "❌ Please enter South, North, or Terrace."
            session["step"] = "flat"
            return "🏠 Enter Flat Number (Example: 004, S004, or T1)."
        # Flat
        if step == "flat":
            original_flat = message.strip()
            flat = message.upper()
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
            data["flat_number"] = flat
            session["step"] = "age"
            return "🎂 Enter Age."
        # Age
        if step == "age":
            try:
                age = int(message)
            except ValueError:
                return "❌ Please enter a valid age (numbers only)."
            if age < 1 or age > 100:
                return (
                    "❌ Please enter a valid age between 1 and 100.\n\n"
                    f"'{message}' doesn't look right - please re-enter."
                )
            data["age"] = age
            if check_duplicate_competition_registration(
                name=data["name"],
                block=data["block"],
                flat_number=data["flat_number"],
                competition=data["competition"]
            ):
                session["step"] = None
                session["active"] = False
                return (
                    f"❌ You've already registered for {data['competition']}.\n\n"
                    "If this is a mistake, please contact a volunteer."
                )
            session["step"] = "confirm_details"
            return f"""
📋 Please confirm your details:
🏆 Competition : {data['competition']}
👤 Name : {data['name']}
🏢 Block : {data['block']}
🏠 Flat : {data['flat_number']}
📱 Mobile : {data['mobile']}
🎂 Age : {data['age']}
Type **yes** to confirm and submit, or **edit** to re-enter your name/block/flat/age.
"""
        # --------------------------------------------
        # Confirm details before saving
        # --------------------------------------------
        if step == "confirm_details":
            answer = message.strip().lower()
            if answer in ["yes", "y", "confirm", "correct", "ok", "okay"]:
                save_registration(
                    data["name"],
                    data["block"],
                    data["flat_number"],
                    data["mobile"],
                    data["age"],
                    data["competition"]
                )
                send_registration_confirmation(
                    name=data["name"],
                    competition=data["competition"],
                    block=data["block"],
                    flat=data["flat_number"],
                    mobile_number=data["mobile"]
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
                return (summary, data['name'])
            if answer in ["edit", "no", "n", "change", "wrong"]:
                session["step"] = "name"
                return "✏️ No problem - let's redo it. 👤 Please enter your Name."
            return "❌ Please type **yes** to confirm, or **edit** to re-enter your details."
registration = RegistrationService()
