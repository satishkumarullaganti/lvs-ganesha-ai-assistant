import ollama

from backend.config import OLLAMA_MODEL


SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are LVS Ganesha AI Assistant.

Developer:
Satish Kumar Ullaganti.

You help residents with:

• Competition Registration
• Festival Schedule
• Volunteer Information
• Annaprasada
• Festival Announcements

Be friendly.

Keep answers concise.
"""
}

# session_id -> list of {"role":..., "content":...} messages
# Each visitor gets their own conversation history, so one
# person's chat doesn't leak into or get mixed up with
# another visitor's conversation context.
conversation_histories = {}


def _get_history(session_id):

    if session_id not in conversation_histories:

        conversation_histories[session_id] = [SYSTEM_PROMPT]

    return conversation_histories[session_id]


def get_ai_response(session_id: str, message: str):

    history = _get_history(session_id)

    history.append(
        {
            "role": "user",
            "content": message
        }
    )

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=history
    )

    assistant_reply = response["message"]["content"]

    history.append(
        {
            "role": "assistant",
            "content": assistant_reply
        }
    )

    return assistant_reply