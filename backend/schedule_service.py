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

                    response += f"📆 {day['date']} ({day['day']})\n"
                    response += f"🕒 {event['time']}\n"
                    response += f"🎉 {event['event']}\n"
                    response += f"📍 {event['location']}"

                    return response

        return None

    # ==========================================
    # Search Event By Word Overlap
    # ==========================================
    # Instead of relying on a fixed, hand-picked
    # keyword list (which can never cover every
    # event name), this checks the user's message
    # against the ACTUAL event titles in the
    # schedule, matching when most of an event's
    # significant words appear in the message.
    # e.g. "What time is Ganapathi Idol
    # Installation?" matches the event named
    # "Ganapathi Idol Installation" directly.
    # ==========================================

    STOPWORDS = {
        "what", "time", "is", "the", "when", "does",
        "will", "are", "a", "an", "of", "on", "at",
        "for", "to", "and", "in"
    }

    def search_event_by_words(self, message):

        # Extract only word characters, so trailing
        # punctuation like "Harathi?" or "Harathi!"
        # doesn't fail to match "Harathi".
        message_lower = message.lower()

        message_words = set(
            re.findall(r"[a-z0-9]+", message_lower)
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

                overlap = event_words & message_words

                if not overlap:
                    continue

                score = len(overlap) / len(event_words)

                # Require most of the event name's
                # significant words to be present,
                # to avoid weak/coincidental matches.
                if score >= 0.6 and score > best_score:

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
        response += f"📆 {day['date']} ({day['day']})\n"
        response += f"🕒 {event['time']}\n"
        response += f"🎉 {event['event']}\n"
        response += f"📍 {event['location']}"

        return response
    # ==========================================
    # Get Schedule By Sequential Day Number
    # ==========================================
    # "Day 1" = FESTIVAL_SCHEDULE[0] (14-Sep-2026)
    # "Day 2" = FESTIVAL_SCHEDULE[1] (15-Sep-2026)
    # ...and so on, based on list order.
    # ==========================================
    def get_day_by_number(self, day_number: int):

        index = day_number - 1

        if index < 0 or index >= len(FESTIVAL_SCHEDULE):
            return None

        return self.format_day(FESTIVAL_SCHEDULE[index])

    # ==========================================
    # Handle User Query
    # ==========================================
    def handle_query(self, message):

        original_message = message
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

            today = datetime.now().strftime("%d-%b-%Y").lower()

            for day in FESTIVAL_SCHEDULE:

                if day["date"].lower() == today:

                    return self.format_day(day)

            return "Today's festival schedule is not available."

        # ----------------------------
        # Search By Sequential Day Number
        # (e.g. "day 2", "day2", "Day 5")
        # ----------------------------

        day_number_match = re.search(r"\bday\s?(\d+)\b", message)

        if day_number_match:

            day_number = int(day_number_match.group(1))

            result = self.get_day_by_number(day_number)

            if result:
                return result

            return (
                f"I couldn't find Day {day_number} in the schedule. "
                f"The festival runs for {len(FESTIVAL_SCHEDULE)} days "
                f"(Day 1 to Day {len(FESTIVAL_SCHEDULE)})."
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
        # Search Events (dynamic match
        # against actual event titles,
        # not a fixed keyword list)
        # ----------------------------

        word_match_result = self.search_event_by_words(message)

        if word_match_result:

            return word_match_result

        # ----------------------------
        # Default - short summary instead
        # of dumping the entire schedule
        # ----------------------------

        return self.get_festival_summary()

    # ==========================================
    # Short Festival Summary
    # ==========================================
    # Used as the default answer for general
    # questions ("when is the festival?") that
    # don't match a specific day/date/event, so
    # we don't dump the whole schedule for every
    # vague question.
    # ==========================================
    def get_festival_summary(self):

        if not FESTIVAL_SCHEDULE:
            return "Festival schedule is not available yet."

        first_day = FESTIVAL_SCHEDULE[0]
        last_day = FESTIVAL_SCHEDULE[-1]

        response = "🪔 LVS Excellency Ganesha Festival\n\n"

        response += (
            f"The festival runs from {first_day['date']} "
            f"({first_day['title']}) to {last_day['date']} "
            f"({last_day['title']}).\n\n"
        )

        response += (
            "Ask me about a specific day (e.g. \"day 2\"), "
            "today's schedule, or say \"full schedule\" to "
            "see every event."
        )

        return response


schedule_service = ScheduleService()