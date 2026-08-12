import re
from datetime import datetime

from backend.festival_schedule import FESTIVAL_SCHEDULE


class ScheduleService:

    # ==========================================
    # Full Festival Schedule
    # ==========================================
    def get_schedule(self):

        response = "🪔 LVS Excellency Ganesha Festival\n\n"
        response += "📅 FESTIVAL SCHEDULE\n\n"

        for day in FESTIVAL_SCHEDULE:

            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"📆 {day['date']} ({day['day']})\n"
            response += f"{day['title']}\n\n"

            for event in day["events"]:

                response += f"🕒 {event['time']}\n"
                response += f"{event['event']}\n"
                response += f"📍 {event['location']}\n\n"

        response += "🙏 Ganapathi Bappa Morya!"

        return response

    # ==========================================
    # Format One Day
    # ==========================================
    def format_day(self, day):

        response = ""

        response += f"📆 {day['date']} ({day['day']})\n"
        response += f"{day['title']}\n\n"

        for event in day["events"]:

            response += f"🕒 {event['time']}\n"
            response += f"{event['event']}\n"
            response += f"📍 {event['location']}\n\n"

        return response

    # ==========================================
    # Search Event
    # ==========================================
    def search_event(self, keyword):

        keyword = keyword.lower()

        for day in FESTIVAL_SCHEDULE:

            for event in day["events"]:

                if keyword in event["event"].lower():

                    response = "🔍 Event Found\n\n"
                    response += (
                        f"📆 {day['date']} ({day['day']})\n"
                    )
                    response += f"🕒 {event['time']}\n"
                    response += f"🎉 {event['event']}\n"
                    response += f"📍 {event['location']}"

                    return response

        return None

    # ==========================================
    # Search Event By Word Overlap
    # ==========================================
    STOPWORDS = {
        "what", "time", "is", "the", "when", "does",
        "will", "are", "a", "an", "of", "on", "at",
        "for", "to", "and", "in"
    }

    def search_event_by_words(self, message):

        message_lower = message.lower()

        message_words = set(
            re.findall(
                r"[a-z0-9]+",
                message_lower
            )
        )

        significant_message_words = (
            message_words - self.STOPWORDS
        )

        best_match = None
        best_score = 0

        for day in FESTIVAL_SCHEDULE:

            for event in day["events"]:

                event_words = set(
                    re.findall(
                        r"[a-z0-9]+",
                        event["event"].lower()
                    )
                ) - self.STOPWORDS

                if not event_words:
                    continue

                overlap = (
                    event_words
                    & significant_message_words
                )

                if not overlap:
                    continue

                score = (
                    len(overlap)
                    / len(event_words)
                )

                is_single_keyword_match = (
                    len(significant_message_words) == 1
                    and len(overlap) == 1
                )

                if (
                    (
                        score >= 0.6
                        or is_single_keyword_match
                    )
                    and score > best_score
                ):

                    best_score = score

                    best_match = {
                        "day": day,
                        "event": event
                    }

        if not best_match:
            return None

        day = best_match["day"]
        event = best_match["event"]

        response = "🔍 Event Found\n\n"
        response += (
            f"📆 {day['date']} ({day['day']})\n"
        )
        response += f"🕒 {event['time']}\n"
        response += f"🎉 {event['event']}\n"
        response += f"📍 {event['location']}"

        return response

    # ==========================================
    # Get Schedule By Sequential Day Number
    # ==========================================
    def get_day_by_number(self, day_number: int):

        index = day_number - 1

        if (
            index < 0
            or index >= len(FESTIVAL_SCHEDULE)
        ):
            return None

        return self.format_day(
            FESTIVAL_SCHEDULE[index]
        )

    # ==========================================
    # Handle User Query
    # ==========================================
    def handle_query(self, message):

        message = message.lower()

        # ----------------------------
        # Full Schedule
        # ----------------------------
        if "full" in message:
            return self.get_schedule()

        # ----------------------------
        # Today's Schedule
        # ----------------------------
        if "today" in message:
            return self.get_todays_schedule()

        # ----------------------------
        # Search By Sequential Day Number
        # ----------------------------
        day_number_match = re.search(
            r"\bday\s?(\d+)\b",
            message
        )

        if day_number_match:

            day_number = int(
                day_number_match.group(1)
            )

            result = self.get_day_by_number(
                day_number
            )

            if result:
                return result

            return (
                f"I couldn't find Day {day_number} "
                f"in the schedule. "
                f"The festival runs for "
                f"{len(FESTIVAL_SCHEDULE)} days "
                f"(Day 1 to Day "
                f"{len(FESTIVAL_SCHEDULE)})."
            )

        # ----------------------------
        # Search By Date
        # ----------------------------
        date_keywords = {
            "14": "14-Sep-2026",
            "15": "15-Sep-2026",
            "16": "16-Sep-2026",
            "17": "17-Sep-2026",
            "18": "18-Sep-2026",
            "19": "19-Sep-2026"
        }

        for key, value in date_keywords.items():

            if key in message:

                for day in FESTIVAL_SCHEDULE:

                    if day["date"] == value:
                        return self.format_day(day)

        # ----------------------------
        # Search By Day Name
        # ----------------------------
        for day in FESTIVAL_SCHEDULE:

            if day["day"].lower() in message:
                return self.format_day(day)

        # ----------------------------
        # Search Events
        # ----------------------------
        word_match_result = (
            self.search_event_by_words(message)
        )

        if word_match_result:
            return word_match_result

        # ----------------------------
        # Default - Short Festival Summary
        # ----------------------------
        return self.get_festival_summary()

    # ==========================================
    # Today's Schedule (with pre/post-festival handling)
    # ==========================================
    def get_todays_schedule(self):

        if not FESTIVAL_SCHEDULE:
            return "Festival schedule is not available yet."

        now = datetime.now()
        today = now.strftime("%d-%b-%Y").lower()

        # Exact match - today is a festival day
        for day in FESTIVAL_SCHEDULE:

            if day["date"].lower() == today:
                return self.format_day(day)

        first_day = FESTIVAL_SCHEDULE[0]
        last_day = FESTIVAL_SCHEDULE[-1]

        first_date = datetime.strptime(
            first_day["date"], "%d-%b-%Y"
        )
        last_date = datetime.strptime(
            last_day["date"], "%d-%b-%Y"
        )

        # Before the festival starts
        if now < first_date:

            days_left = (first_date - now).days

            return (
                f"🪔 The festival hasn't started yet — "
                f"it begins on {first_day['date']} "
                f"({first_day['title']}), "
                f"{days_left} day(s) from today.\n\n"
                "Say \"full schedule\" to see all the events!"
            )

        # After the festival has ended
        if now > last_date:
            return "🙏 The festival has concluded. Ganapathi Bappa Morya!"

        # Fallback (shouldn't normally hit this)
        return "Today's festival schedule is not available."

    # ==========================================
    # Short Festival Summary
    # ==========================================
    def get_festival_summary(self):

        if not FESTIVAL_SCHEDULE:
            return (
                "Festival schedule is "
                "not available yet."
            )

        first_day = FESTIVAL_SCHEDULE[0]
        last_day = FESTIVAL_SCHEDULE[-1]

        response = (
            "🪔 LVS Excellency Ganesha Festival\n\n"
        )

        response += (
            f"The festival runs from "
            f"{first_day['date']} "
            f"({first_day['title']}) to "
            f"{last_day['date']} "
            f"({last_day['title']}).\n\n"
        )

        response += (
            "Ask me about a specific day "
            "(e.g. \"day 2\"), today's schedule, "
            "or say \"full schedule\" to see "
            "every event."
        )

        return response


schedule_service = ScheduleService()