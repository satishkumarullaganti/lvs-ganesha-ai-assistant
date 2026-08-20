"""
Festival Stats & Personal Lookup Service
==========================================
Deterministic - NEVER uses the LLM to generate SQL or
answers here. Same reasoning as schedule_service.py: a
small local model generating free-form SQL against a real
database (with real personal data - names, mobile numbers)
would be a genuine safety/privacy risk, and unreliable on
top of that. Every query here is pre-written and fixed;
only the parameters (name/block/flat, or which competition)
come from the resident's message.

Two categories of question, handled differently:

1. AGGREGATE stats (e.g. "how many registered for Chess?",
   "total donations so far?") - answered immediately,
   no identity check needed, since these never expose any
   individual's personal data.

2. PERSONAL lookups (e.g. "is my registration confirmed?")
   - require Name + Block + Flat Number first (the same
   identity model already used everywhere else in this app,
   since there's no login system) before looking anything
   up, and only ever return that person's OWN matching
   records.
"""

from backend.database.database import (
    get_registration_count,
    get_total_donation_amount,
    get_volunteer_count,
    get_cultural_registration_count,
    get_annaprasada_total_members,
    lookup_registration_status,
    lookup_annaprasada_status,
    lookup_volunteer_status,
    lookup_cultural_status,
)

KNOWN_COMPETITIONS = ["drawing", "chess", "carrom", "tambola", "musical chairs"]


class FestivalStatsService:

    def __init__(self):
        # session_id -> {"active": bool, "step": int, "lookup_type": str, "data": dict}
        self.sessions = {}

    def _get_session(self, session_id):

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "active": False,
                "step": 0,
                "lookup_type": None,
                "data": {}
            }

        return self.sessions[session_id]

    def is_active(self, session_id):
        return self._get_session(session_id)["active"]

    def cancel(self, session_id):
        self.sessions[session_id] = {
            "active": False,
            "step": 0,
            "lookup_type": None,
            "data": {}
        }

    # --------------------------------------------------
    # Intent detection - returns ("aggregate", answer_text)
    # or ("lookup", lookup_type) or None if this message
    # doesn't match a stats/lookup question at all.
    # --------------------------------------------------

    def detect_intent(self, message):

        lower_message = message.lower()

        # ---- Personal lookups (need "my" + a topic word) ----
        if "my" in lower_message:

            if "annaprasada" in lower_message or "coupon" in lower_message:
                return ("lookup", "annaprasada")

            if "volunteer" in lower_message:
                return ("lookup", "volunteer")

            if "cultural" in lower_message:
                return ("lookup", "cultural")

            if "registration" in lower_message or "registered" in lower_message:
                return ("lookup", "registration")

        # ---- Aggregate stats ----
        if "how many" in lower_message or "total" in lower_message or "count" in lower_message:

            for competition in KNOWN_COMPETITIONS:
                if competition in lower_message:
                    count = get_registration_count(competition)
                    return (
                        "aggregate",
                        f"📊 {count} resident(s) have registered for "
                        f"{competition.title()} so far."
                    )

            if "donat" in lower_message:
                total = get_total_donation_amount()
                return (
                    "aggregate",
                    f"📊 ₹{total:,.0f} has been raised in donations so far. "
                    "🙏 Thank you to everyone who has contributed!"
                )

            if "volunteer" in lower_message:
                count = get_volunteer_count()
                return (
                    "aggregate",
                    f"📊 {count} resident(s) have signed up to volunteer so far."
                )

            if "cultural" in lower_message:
                count = get_cultural_registration_count()
                return (
                    "aggregate",
                    f"📊 {count} cultural program registration(s) so far."
                )

            if "annaprasada" in lower_message or "coupon" in lower_message:
                total = get_annaprasada_total_members()
                return (
                    "aggregate",
                    f"📊 {total} member(s) covered by Annaprasada bookings so far."
                )

            if "registered" in lower_message or "registration" in lower_message:
                count = get_registration_count()
                return (
                    "aggregate",
                    f"📊 {count} total competition registration(s) so far."
                )

        return None

    # --------------------------------------------------
    # Start a personal lookup flow (collects Name, Block,
    # Flat Number over a few turns, then looks up records)
    # --------------------------------------------------

    def start_lookup(self, session_id, lookup_type):

        self.sessions[session_id] = {
            "active": True,
            "step": 1,
            "lookup_type": lookup_type,
            "data": {}
        }

        return (
            "🔍 To look that up, I need to confirm a few details.\n\n"
            "👤 Please enter your Full Name.\n\n"
            "(Type 'cancel' anytime to stop.)"
        )

    def process_lookup(self, session_id, message):

        session = self._get_session(session_id)

        if session["step"] == 1:

            session["data"]["name"] = message.strip()
            session["step"] = 2

            return "🏢 Please enter your Block (South/North/Terrace)."

        elif session["step"] == 2:

            session["data"]["block"] = message.strip()
            session["step"] = 3

            return "🏠 Please enter your Flat Number."

        elif session["step"] == 3:

            name = session["data"]["name"]
            block = session["data"]["block"]
            flat_number = message.strip()
            lookup_type = session["lookup_type"]

            self.cancel(session_id)

            return self._perform_lookup(lookup_type, name, block, flat_number)

    def _perform_lookup(self, lookup_type, name, block, flat_number):

        if lookup_type == "registration":

            rows = lookup_registration_status(name, block, flat_number)

            if not rows:
                return (
                    "❌ I couldn't find any competition registration matching "
                    f"that name and flat. If you believe this is a mistake, "
                    "please contact a volunteer."
                )

            lines = [f"🏆 {competition}" for competition, _ in rows]
            return "✅ Found your registration(s):\n\n" + "\n".join(lines)

        elif lookup_type == "annaprasada":

            rows = lookup_annaprasada_status(name, block, flat_number)

            if not rows:
                return (
                    "❌ I couldn't find any Annaprasada booking matching that "
                    "name and flat. If you believe this is a mistake, please "
                    "contact a volunteer."
                )

            lines = []
            for coupon_id, members, served_count, is_used, _ in rows:
                served_count = served_count or 0
                remaining = int(members) - served_count
                status = "✅ Fully redeemed" if remaining <= 0 else f"⏳ {remaining} remaining"
                lines.append(f"🎟️ {coupon_id} - {members} member(s) - {status}")

            return "Found your Annaprasada booking(s):\n\n" + "\n".join(lines)

        elif lookup_type == "volunteer":

            rows = lookup_volunteer_status(name, block, flat_number)

            if not rows:
                return (
                    "❌ I couldn't find any volunteer signup matching that "
                    "name and flat. If you believe this is a mistake, please "
                    "contact a volunteer."
                )

            lines = [f"🙋 {tasks}" for tasks, _ in rows]
            return "Found your volunteer signup(s):\n\n" + "\n".join(lines)

        elif lookup_type == "cultural":

            rows = lookup_cultural_status(name, block, flat_number)

            if not rows:
                return (
                    "❌ I couldn't find any cultural program registration "
                    "matching that name and flat. If you believe this is a "
                    "mistake, please contact a volunteer."
                )

            lines = [f"🎭 {categories}" for categories, _, _ in rows]
            return "Found your cultural registration(s):\n\n" + "\n".join(lines)

        return "❌ Something went wrong with that lookup. Please try again."


festival_stats_service = FestivalStatsService()