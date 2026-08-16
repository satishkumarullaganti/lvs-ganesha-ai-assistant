"""
Routing-only test script.

This does NOT call Ollama / the RAG LLM at all - it only
classifies which branch of main.py's /chat routing logic
each test message would hit. This lets you verify routing
correctness quickly and cheaply (no CPU load), separately
from testing actual RAG answer quality.

Run from: backend/rag/
Command:  ..\\..\\.venv\\Scripts\\python.exe test_routing.py

NOTE: This mirrors the message-content-based routing rules
in main.py's /chat endpoint. It does NOT simulate session
state (donation_service.is_active, annaprasada_service.is_active,
registration.is_active) since those depend on a live session -
this only tests the stateless, message-content-based rules,
which is what determines routing for a resident's FIRST
message on a given topic.
"""

import sys
import os
import re

# Make backend importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from backend.rag.rag_service import is_festival_question


# --------------------------------------------------
# Replicated routing rules from main.py
# (keep these in sync if main.py's rules change)
# --------------------------------------------------

DONATION_QUESTION_HINTS = [
    "is there", "what is", "what are", "how much",
    "minimum", "maximum", "who", "why", "when",
    "amount", "?"
]

INFORMATIONAL_QUESTION_HINTS = [
    "when", "what time", "schedule", "timing", "day",
    "how", "what is", "what are", "is there", "does",
    "why", "who", "?"
]

SCHEDULE_TRIGGER_WORDS = [
    "schedule", "schdeule", "sched", "timing", "timings",
    "programme", "program", "events today", "what time",
    "when is", "when does", "agenda", "itinerary",
    "today's events", "what's happening", "whats happening",
    "location", "venue", "where is", "where does",
    "where will", "address", "party hall"
]


def classify_route(message):

    lower_message = message.lower().strip()

    if lower_message == "register":
        return "REGISTRATION (start)"

    looks_like_donation_question = any(
        hint in lower_message for hint in DONATION_QUESTION_HINTS
    )

    if "donation" in lower_message and not looks_like_donation_question:
        return "DONATION FLOW (start transaction)"

    looks_like_schedule_question = any(
        hint in lower_message for hint in INFORMATIONAL_QUESTION_HINTS
    )

    if "annaprasada" in lower_message and not looks_like_schedule_question:
        return "ANNAPRASADA (check booking status)"

    day_number_pattern = re.search(r"\bday\s?\d+\b", lower_message)

    if any(word in lower_message for word in SCHEDULE_TRIGGER_WORDS) or day_number_pattern:
        return "SCHEDULE_SERVICE (deterministic, no LLM)"

    if is_festival_question(message):
        return "RAG (Ollama + ChromaDB)"

    return "GENERAL AI CHAT (Ollama, no RAG context)"


TEST_MESSAGES = [
    # ---- Should reach GENERAL AI CHAT (non-festival) ----
    ("Hi", "GENERAL AI CHAT"),
    ("Hello, how are you?", "GENERAL AI CHAT"),
    ("What's the weather today?", "GENERAL AI CHAT"),
    ("Tell me a joke", "GENERAL AI CHAT"),
    ("What is the capital of France?", "GENERAL AI CHAT"),
    ("Thank you", "GENERAL AI CHAT"),

    # ---- Should reach SCHEDULE_SERVICE ----
    ("When is the Dance Competition?", "SCHEDULE_SERVICE"),
    ("full schedule", "SCHEDULE_SERVICE"),
    ("day 3", "SCHEDULE_SERVICE"),
    ("today's events", "SCHEDULE_SERVICE"),
    ("Where is the Ganesh Visarjan procession route?", "SCHEDULE_SERVICE"),

    # ---- Should reach RAG (festival, non-schedule wording) ----
    ("Who is the President of the festival committee?", "RAG"),
    ("What are the basic Chess rules?", "RAG"),
    ("Do I need to upload my performance track during registration?", "RAG"),
    ("What volunteer areas are available?", "RAG"),
    ("What events are happening on 17 September?", "RAG"),
    ("How do I redeem my Annaprasada QR coupon?", "RAG"),

    # ---- Donation: informational (should now reach RAG after fix) ----
    ("Is there a minimum donation amount?", "RAG (fixed)"),
    ("Who sponsored the Ganesh Idol?", "RAG (fixed)"),
    ("What is the donation used for?", "RAG (fixed)"),

    # ---- Register/registration keyword fix: previously fell
    # through to GENERAL AI CHAT (no grounding, inconsistent
    # answers) since neither "register" nor a real competition
    # name was recognized - now should route to RAG. ----
    ("How can I register cricket?", "RAG (fixed)"),
    ("Can I register for football?", "RAG (fixed)"),
    ("Is there a badminton registration?", "RAG (fixed)"),
    ("How do I sign up for competitions?", "RAG (fixed)"),

    # ---- Sanity check: literal "register" alone must still
    # trigger the REGISTRATION FLOW action, not RAG - this
    # confirms the new keywords didn't break the exact-match
    # trigger that starts the chat-based registration wizard. ----
    ("register", "REGISTRATION"),

    # ---- Donation: action requests (should start the flow) ----
    ("I want to make a donation", "DONATION FLOW"),
    ("donation", "DONATION FLOW"),

    # ---- Annaprasada: action vs question ----
    ("annaprasada", "ANNAPRASADA (check status)"),
    ("when is annaprasada", "SCHEDULE_SERVICE"),

    # ---- Registration ----
    ("register", "REGISTRATION"),
]


def run():

    print("=" * 70)
    print(f"{'MESSAGE':<55} {'ROUTE'}")
    print("=" * 70)

    for message, expected in TEST_MESSAGES:

        actual = classify_route(message)

        print(f"{message[:53]:<55} -> {actual}")
        print(f"{'':<55}    (expected: {expected})")
        print()


if __name__ == "__main__":
    run()