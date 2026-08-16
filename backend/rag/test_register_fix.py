"""
Live RAG answer-quality test for the "register X" fix.

This DOES call Ollama (unlike test_routing.py), so it's
slower - use it to confirm the actual ANSWER content is
correct and consistent, not just that routing is right.

Run from: backend/rag/
Command:  ..\\..\\.venv\\Scripts\\python.exe test_register_fix.py
"""

from rag_service import ask_rag


TEST_CASES = [
    {
        "question": "How can I register cricket?",
        "expect": "Should say Cricket is NOT an available competition, "
                  "and list the real ones: Drawing, Chess, Carrom, "
                  "Tambola, Musical Chairs. Should NOT invent a Cricket "
                  "registration process.",
    },
    {
        "question": "Can I register for football?",
        "expect": "Same as above - Football isn't offered, should "
                  "list real competitions instead of inventing an answer.",
    },
    {
        "question": "Is there a badminton registration?",
        "expect": "Same pattern - Badminton isn't offered.",
    },
    {
        "question": "How do I sign up for competitions?",
        "expect": "This one SHOULD get a real, helpful answer - "
                  "sign-up happens through the LVS AI Assistant, and "
                  "the real competition list should be mentioned.",
    },
    {
        "question": "What are the available competitions?",
        "expect": "Baseline check - should list Drawing, Chess, Carrom, "
                  "Tambola, Musical Chairs.",
    },
]


def run():

    print("=" * 70)
    print("Testing RAG answer quality for 'register X' style questions")
    print("(this calls Ollama - expect this to take a minute or two)")
    print("=" * 70)

    for i, case in enumerate(TEST_CASES, start=1):

        print(f"\n[{i}/{len(TEST_CASES)}] Q: {case['question']}")
        print("-" * 70)

        result = ask_rag(case["question"])

        print("A:", result["response"])
        print("\nSources:", result["sources"])
        print("\nExpected:", case["expect"])
        print("=" * 70)

    print("\nReview each answer above:")
    print("- Did it correctly say the fictional sport isn't offered?")
    print("- Did it list the REAL competitions (Drawing, Chess, Carrom,")
    print("  Tambola, Musical Chairs) instead of staying silent?")
    print("- Was it grounded/consistent, not a generic improvised answer?")


if __name__ == "__main__":
    run()