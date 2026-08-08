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
        # Search Events
        # ----------------------------

        event_keywords = [

            "harathi",

            "annaprasada",

            "prasadam",

            "visarjan",

            "homam",

            "pooja",

            "bhajans",

            "dance",

            "music",

            "quiz",

            "drawing",

            "prize"

        ]

        for keyword in event_keywords:

            if keyword in message:

                result = self.search_event(keyword)

                if result:

                    return result

        # ----------------------------
        # Default
        # ----------------------------

        return self.get_schedule()


schedule_service = ScheduleService()