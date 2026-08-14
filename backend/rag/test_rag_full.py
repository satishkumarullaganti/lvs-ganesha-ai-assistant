"""
Comprehensive RAG test suite covering every document in the knowledge base.
Run from: backend/rag/
Command:  ..\\..\\.venv\\Scripts\\python.exe test_rag_full.py

Each test case has an 'expect' hint (not automated pass/fail - your local
LLM's exact wording will vary) so you can eyeball whether the answer is
in the right ballpark. Cases marked should_refuse are testing the
hallucination guardrail - the correct behavior is for the assistant to
say the info isn't available, NOT to invent an answer.
"""

from rag_service import ask_rag


TEST_CASES = [
    # ---------------- festival_schedule.md ----------------
    {
        "category": "Schedule",
        "question": "When is the Dance Competition?",
        "expect": "16 September 2026, 05:30 PM, Party Hall",
    },
    {
        "category": "Schedule",
        "question": "When is the Ganapathi Idol Installation?",
        "expect": "14 September 2026, 08:00 AM, Party Hall",
    },
    {
        "category": "Schedule",
        "question": "What time is Ganesh Visarjan?",
        "expect": "19 September 2026, 05:00 PM, Immersion Route",
    },
    {
        "category": "Schedule",
        "question": "What events are happening on 17 September?",
        "expect": "Morning Pooja, Sahasranama Archana, Annaprasada Distribution, Singing Competition, Maha Harathi, Quiz Competition, Community Meet",
    },

    # ---------------- festival_faq.md / location ----------------
    {
        "category": "Location",
        "question": "Where is the Ganesh Visarjan procession route?",
        "expect": "Immersion Route (procession begins at Main Entrance, 3:00 PM)",
    },
    {
        "category": "Location",
        "question": "Where are most festival activities held?",
        "expect": "Party Hall",
    },

    # ---------------- competition_rules.md ----------------
    {
        "category": "Competition",
        "question": "What are the basic rules of the Chess Competition?",
        "expect": "Standard chess rules, checkmate objective, sportsmanship, final format confirmed by committee",
    },
    {
        "category": "Competition",
        "question": "What competitions are available at the festival?",
        "expect": "Drawing, Chess, Carrom, Tambola, Musical Chairs",
    },

    # ---------------- cultural_programs.md ----------------
    {
        "category": "Cultural",
        "question": "Do I need to upload my performance track during registration?",
        "expect": "No, track upload is optional and can be provided later",
    },
    {
        "category": "Cultural",
        "question": "Can a group participate in cultural programs?",
        "expect": "Yes, Group Dance and Group Singing are supported",
    },

    # ---------------- volunteer_rules.md ----------------
    {
        "category": "Volunteer",
        "question": "What volunteer areas are available?",
        "expect": "Drawing/Chess/Carrom/Tambola/Musical Chairs competitions, Annaprasada, Registration Desk, Decoration, Pooja Support, Cultural Coordination, Donations Desk, Visarjan Support, Photography, Cleanup Crew, Other",
    },
    {
        "category": "Volunteer",
        "question": "What information is collected during volunteer registration?",
        "expect": "Name, Block, Flat Number, Mobile Number, Preferred Area, Time Slot, Available Days",
    },

    # ---------------- donation_information.md ----------------
    {
        "category": "Donation",
        "question": "How can I make a donation?",
        "expect": "Use the Donation feature in the application",
    },
    {
        "category": "Donation",
        "question": "Is there a minimum donation amount?",
        "expect": "should say not officially specified / not invent a number",
    },

    # ---------------- committee_details.md ----------------
    {
        "category": "Committee",
        "question": "Who is the President of the festival committee?",
        "expect": "K V Uma Shankar",
    },
    {
        "category": "Committee",
        "question": "Who is the Cultural Coordinator?",
        "expect": "Reshma Binu Prasad",
    },
    {
        "category": "Committee",
        "question": "What does the Vice President do?",
        "expect": "GAP CHECK: no responsibility text exists in the doc for this role - answer should say info not available, not invent duties",
    },

    # ---------------- annaprasada_information.md ----------------
    {
        "category": "Annaprasada",
        "question": "How do I redeem my Annaprasada QR coupon?",
        "expect": "Present QR to volunteer, volunteer scans it, system verifies, redeemed if valid and unused",
    },
    {
        "category": "Annaprasada",
        "question": "Can I use the same Annaprasada QR code twice?",
        "expect": "No, a redeemed coupon cannot be redeemed again",
    },

    # ---------------- Hallucination guardrail checks ----------------
    {
        "category": "Should Refuse",
        "question": "Who sponsored the Ganesh Idol?",
        "expect": "SHOULD REFUSE / say not yet confirmed - doc has literal placeholder '[ENTER APPROVED NAME]', must NOT be repeated verbatim",
    },
    {
        "category": "Should Refuse",
        "question": "Is there free parking available at the festival?",
        "expect": "SHOULD REFUSE - parking is not mentioned anywhere in the knowledge base",
    },
    {
        "category": "Should Refuse",
        "question": "What is the entry fee for the Chess Competition?",
        "expect": "SHOULD REFUSE - no fee information exists in competition_rules.md",
    },
    {
        "category": "Should Refuse",
        "question": "What is the capital of France?",
        "expect": "SHOULD REFUSE - not a festival question at all",
    },
]


def run():
    passed_visually = 0

    for i, case in enumerate(TEST_CASES, start=1):
        print("\n" + "=" * 60)
        print(f"[{i}/{len(TEST_CASES)}] Category: {case['category']}")
        print("=" * 60)
        print(f"Q: {case['question']}")

        result = ask_rag(case["question"])

        print(f"\nA: {result['response']}")
        print(f"\nSources: {result['sources']}")
        print(f"\nExpected: {case['expect']}")

    print("\n" + "=" * 60)
    print(f"Ran {len(TEST_CASES)} test cases across all 8 knowledge base docs.")
    print("Review each answer against its 'Expected' line above.")
    print("For 'Should Refuse' cases, the correct behavior is a refusal")
    print("or 'not available' response - NOT a confident invented answer.")
    print("=" * 60)


if __name__ == "__main__":
    run()