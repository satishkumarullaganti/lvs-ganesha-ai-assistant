"""
Model Comparison: llama3.2:3b vs a candidate larger model
=============================================================
Tests BOTH speed and answer quality using your ACTUAL
production pipeline (real retrieval, real guardrails, real
prompt) - not just raw chat - so the comparison reflects
what you'd actually get in production, not a synthetic
benchmark.

BEFORE RUNNING: pull the candidate model first (this is a
~4-5GB download, do this ahead of time on decent wifi):

    ollama pull qwen2.5:7b

Run from: backend/rag/
Command:  ..\\..\\.venv\\Scripts\\python.exe compare_models.py

This runs each question through BOTH models sequentially
(never loads both into memory at once, to respect your 8GB
RAM) and prints timing + answers side by side so you can
judge speed AND quality yourself.
"""

import time
import rag_service


# A representative mix pulled from the exact tests we ran
# earlier this session - covers a simple lookup, a yes/no
# question (the type that caused contradiction bugs), a
# hallucination-guard case, and a multi-fact list answer.
TEST_QUESTIONS = [
    "What are the basic Chess rules?",
    "Can I use the same Annaprasada QR code twice?",
    "Is there free parking available at the festival?",
    "What events are happening on 17 September?",
    "How can I register cricket?",
]

MODELS_TO_TEST = [
    "llama3.2:3b",
    "qwen2.5:7b",
]


def run_model(model_name):

    print("\n" + "=" * 70)
    print(f"TESTING MODEL: {model_name}")
    print("=" * 70)

    rag_service.LLM_MODEL = model_name

    total_time = 0.0

    for i, question in enumerate(TEST_QUESTIONS, start=1):

        start = time.time()
        result = rag_service.ask_rag(question)
        elapsed = time.time() - start

        total_time += elapsed

        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Q: {question}")
        print(f"({elapsed:.1f}s)")
        print("A:", result["response"])

    average = total_time / len(TEST_QUESTIONS)

    print("\n" + "-" * 70)
    print(f"{model_name} — Total: {total_time:.1f}s | Average: {average:.1f}s/question")
    print("-" * 70)

    return {"model": model_name, "total": total_time, "average": average}


def run():

    results = []

    for model_name in MODELS_TO_TEST:
        results.append(run_model(model_name))

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for r in results:
        print(f"{r['model']:<20} avg {r['average']:.1f}s/question, total {r['total']:.1f}s")

    print("\nSpeed is measured above. For QUALITY, scroll back up and")
    print("compare the actual answers side by side yourself - especially")
    print("the Chess rules (detail/completeness), the QR duplicate")
    print("question (does it stay consistent, no Yes/No contradiction),")
    print("and the Cricket question (does it correctly redirect to real")
    print("competitions instead of just refusing or hallucinating).")


if __name__ == "__main__":
    run()
    