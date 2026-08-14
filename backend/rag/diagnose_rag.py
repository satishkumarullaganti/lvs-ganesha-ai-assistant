"""
Standalone RAG diagnostic script.
Run from: C:\\Projects\\lvs-ganesha-ai-assistant\\backend\\rag
Command:  ..\\..\\.venv\\Scripts\\python.exe ..\\..\\..\\diagnose_rag.py
(or just copy this file into backend/rag/ and run it from there)
"""

import os
import sys
import chromadb
import ollama

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2:3b"
COLLECTION_NAME = "lvs_festival"

print("=" * 50)
print("STEP 1: Is Ollama reachable?")
print("=" * 50)
try:
    models = ollama.list()
    names = [m.get("model", m.get("name", "?")) for m in models.get("models", [])]
    print("Ollama reachable. Installed models:")
    for n in names:
        print(" -", n)
    if not any(EMBEDDING_MODEL in n for n in names):
        print(f"\n⚠️  '{EMBEDDING_MODEL}' NOT found in installed models.")
        print(f"   Fix: ollama pull {EMBEDDING_MODEL}")
    if not any(LLM_MODEL.split(":")[0] in n for n in names):
        print(f"\n⚠️  '{LLM_MODEL}' NOT found in installed models.")
        print(f"   Fix: ollama pull {LLM_MODEL}")
except Exception as e:
    print("❌ Could not reach Ollama:", e)
    print("   Fix: make sure 'ollama serve' is running (or the Ollama app is open).")
    sys.exit(1)

print("\n" + "=" * 50)
print("STEP 2: Can we create an embedding?")
print("=" * 50)
try:
    resp = ollama.embeddings(model=EMBEDDING_MODEL, prompt="dance competition")
    emb = resp["embedding"]
    print(f"✅ Embedding created. Length: {len(emb)}")
except Exception as e:
    print("❌ Embedding creation failed:", e)
    sys.exit(1)

print("\n" + "=" * 50)
print("STEP 3: Is the ChromaDB collection populated?")
print("=" * 50)
try:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)
    count = collection.count()
    print(f"Collection '{COLLECTION_NAME}' chunk count: {count}")
    if count == 0:
        print("⚠️  Collection is empty. Run ingest.py first.")
        sys.exit(1)
except Exception as e:
    print("❌ Could not open collection:", e)
    sys.exit(1)

print("\n" + "=" * 50)
print("STEP 4: Raw query against Chroma (no filtering)")
print("=" * 50)
test_query = "When is the Dance Competition?"
results = collection.query(query_embeddings=[emb], n_results=5)
docs = results.get("documents", [[]])[0]
metas = results.get("metadatas", [[]])[0]
dists = results.get("distances", [[]])[0]

print(f"Query: '{test_query}'")
print(f"Results returned: {len(docs)}\n")
for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
    print(f"--- Result {i+1} ---")
    print(f"Source: {meta.get('source')}")
    print(f"Distance: {dist:.4f}  (threshold is 1.0 — lower is better)")
    print(f"Snippet: {doc[:120].strip()}...")
    print()

if dists and min(dists) > 1.0:
    print("⚠️  ALL distances are above 1.0 — this is why rag_service.py filters everything out.")
    print("   MAX_RELEVANT_DISTANCE in rag_service.py may need to be raised (try 1.3-1.5),")
    print("   OR the embedding model used here doesn't match what ingest.py used.")
elif not dists:
    print("⚠️  Query returned zero results — collection may be corrupted or query embedding shape mismatch.")
else:
    print("✅ At least one result is under the 1.0 threshold — retrieval itself is working.")
    print("   If test_rag.py still says 'not found', the issue is the lexical grounding")
    print("   check in ask_rag() — add a print(question_words, context_lower[:200]) there to confirm.")