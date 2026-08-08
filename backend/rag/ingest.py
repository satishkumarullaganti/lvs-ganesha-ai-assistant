import os
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
    name=COLLECTION_NAME
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
# Split document into chunks
# --------------------------------------------------

def split_text(text, chunk_size=1000):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start = end

    return chunks


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