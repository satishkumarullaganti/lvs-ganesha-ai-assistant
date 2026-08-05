import ollama

from backend.config import OLLAMA_MODEL


conversation_history = [
    {
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
]


def get_ai_response(message: str):

    conversation_history.append(
        {
            "role": "user",
            "content": message
        }
    )

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=conversation_history
    )

    assistant_reply = response["message"]["content"]

    conversation_history.append(
        {
            "role": "assistant",
            "content": assistant_reply
        }
    )

    return assistant_reply



