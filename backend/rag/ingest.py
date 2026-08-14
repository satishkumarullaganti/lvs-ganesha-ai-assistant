import os
import re
import chromadb
import ollama


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")

CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

EMBEDDING_MODEL = "nomic-embed-text"

COLLECTION_NAME = "lvs_festival"


# --------------------------------------------------
# Create ChromaDB client
# --------------------------------------------------

client = chromadb.PersistentClient(
    path=CHROMA_DIR
)


# --------------------------------------------------
# Create / get collection
# --------------------------------------------------

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# Read documents
# --------------------------------------------------

def load_documents():

    documents = []

    for filename in os.listdir(DOCUMENTS_DIR):

        if filename.endswith(".md"):

            filepath = os.path.join(
                DOCUMENTS_DIR,
                filename
            )

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                content = file.read()

            documents.append(
                {
                    "filename": filename,
                    "content": content
                }
            )

    return documents


# --------------------------------------------------
# Strip embedded AI meta-instructions
# --------------------------------------------------
#
# The source documents contain sentences written as
# guidance for the AI assistant itself (e.g. "The AI
# assistant should not invent a minimum donation
# amount."). These are already duplicated as explicit
# rules in rag_service.py's system prompt, so leaving
# them in the retrievable knowledge base only adds risk:
# a small local LLM can end up quoting or paraphrasing
# these meta-instructions back to the resident as if they
# were an answer (e.g. "the minimum donation amount is
# available... the AI assistant should not invent one").
#
# This strips any paragraph that reads as an instruction
# to the AI, so only real factual content gets embedded
# and retrieved.
# --------------------------------------------------

def strip_ai_instructions(text):

    paragraphs = text.split("\n\n")

    kept = []

    for paragraph in paragraphs:

        stripped = paragraph.strip()

        # Always keep section separators and headers untouched
        if not stripped or re.fullmatch(r"-{3,}", stripped):
            kept.append(paragraph)
            continue

        if "ai assistant" in stripped.lower():
            continue

        kept.append(paragraph)

    return "\n\n".join(kept)


# --------------------------------------------------
# Split document into chunks
# --------------------------------------------------
#
# Markdown-section-aware chunking instead of blind
# character slicing. Every doc in backend/rag/documents
# already uses "---" as a section separator, so we split
# on that first - this keeps FAQ entries, schedule
# day-blocks, and rule sections intact as single chunks
# instead of getting sliced mid-table or mid-sentence.
#
# Small adjacent sections get merged together (so we don't
# end up with tiny near-empty chunks), and any section that
# is still too large gets a secondary split on paragraph
# boundaries (double newline) as a fallback.
# --------------------------------------------------

MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 1500


def _split_large_section(section, max_size):

    paragraphs = section.split("\n\n")

    chunks = []
    buffer = ""

    for paragraph in paragraphs:

        candidate = f"{buffer}\n\n{paragraph}" if buffer else paragraph

        if len(candidate) <= max_size:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
            buffer = paragraph

    if buffer:
        chunks.append(buffer)

    return chunks


def split_text(text, min_chunk_size=MIN_CHUNK_SIZE, max_chunk_size=MAX_CHUNK_SIZE):

    # Split on markdown horizontal-rule separators ("---" on its own line)
    raw_sections = re.split(r"\n-{3,}\n", text)
    sections = [s.strip() for s in raw_sections if s.strip()]

    # Merge small/adjacent sections so we don't produce
    # tiny fragments that carry little standalone meaning
    merged = []
    buffer = ""

    for section in sections:

        candidate = f"{buffer}\n\n---\n\n{section}" if buffer else section

        if len(candidate) <= max_chunk_size:
            buffer = candidate
        else:
            if buffer:
                merged.append(buffer)
            buffer = section

    if buffer:
        merged.append(buffer)

    # Any merged chunk still over max_chunk_size gets a
    # secondary split on paragraph boundaries
    final_chunks = []

    for chunk in merged:

        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            final_chunks.extend(
                _split_large_section(chunk, max_chunk_size)
            )

    return final_chunks


# --------------------------------------------------
# Create embeddings
# --------------------------------------------------

def create_embedding(text):

    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=text
    )

    return response["embedding"]


# --------------------------------------------------
# Ingest documents
# --------------------------------------------------

def ingest_documents():

    documents = load_documents()

    print(
        f"Found {len(documents)} documents."
    )

    document_id = 0

    for document in documents:

        filename = document["filename"]

        content = document["content"]

        print(
            f"\nProcessing: {filename}"
        )

        content = strip_ai_instructions(content)

        chunks = split_text(content)

        print(
            f"Created {len(chunks)} chunks."
        )

        for chunk in chunks:

            embedding = create_embedding(
                chunk
            )

            collection.add(

                ids=[
                    f"chunk_{document_id}"
                ],

                embeddings=[
                    embedding
                ],

                documents=[
                    chunk
                ],

                metadatas=[
                    {
                        "source": filename
                    }
                ]
            )

            document_id += 1

            print(
                f"Added chunk {document_id}"
            )

    print(
        "\n================================="
    )

    print(
        "RAG ingestion completed successfully!"
    )

    print(
        f"Total chunks: {document_id}"
    )

    print(
        f"ChromaDB location: {CHROMA_DIR}"
    )

    print(
        "================================="
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    ingest_documents()