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

            today = datetime.now().strftime("%d-%b-%Y").lower()

            for day in FESTIVAL_SCHEDULE:

                if day["date"].lower() == today:

                    return self.format_day(day)

            return "Today's festival schedule is not available."

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