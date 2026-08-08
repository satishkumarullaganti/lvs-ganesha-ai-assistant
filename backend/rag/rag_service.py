import os
import chromadb
import ollama


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHROMA_DIR = os.path.join(
    BASE_DIR,
    "chroma_db"
)

EMBEDDING_MODEL = "nomic-embed-text"

LLM_MODEL = "llama3.2:3b"

COLLECTION_NAME = "lvs_festival"


# --------------------------------------------------
# Connect to ChromaDB
# --------------------------------------------------

client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


# --------------------------------------------------
# Create embedding
# --------------------------------------------------

def create_embedding(text):
    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=text
    )

    return response["embedding"]


# --------------------------------------------------
# Detect question category
# --------------------------------------------------

def detect_category(query):

    query_lower = query.lower()

    schedule_keywords = [
        "schedule",
        "when",
        "what time",
        "time",
        "date",
        "today",
        "tomorrow",
        "sep",
        "september",
        "event",
        "events",
        "visarjan",
        "pooja",
        "pooja",
        "harathi",
        "installation",
        "annaprasada"
    ]

    competition_keywords = [
        "rules",
        "rule",
        "chess",
        "carrom",
        "tambola",
        "drawing",
        "musical chairs",
        "competition"
    ]

    cultural_keywords = [
        "cultural",
        "dance",
        "singing",
        "song",
        "skit",
        "instrument",
        "performance",
        "track",
        "karaoke"
    ]

    volunteer_keywords = [
        "volunteer",
        "volunteering",
        "registration desk",
        "cleanup",
        "decoration",
        "visarjan support",
        "photography"
    ]

    donation_keywords = [
        "donation",
        "donate",
        "donor",
        "sponsor",
        "ganesh idol sponsor"
    ]

    if any(
        keyword in query_lower
        for keyword in schedule_keywords
    ):
        return "schedule"

    if any(
        keyword in query_lower
        for keyword in competition_keywords
    ):
        return "competition"

    if any(
        keyword in query_lower
        for keyword in cultural_keywords
    ):
        return "cultural"

    if any(
        keyword in query_lower
        for keyword in volunteer_keywords
    ):
        return "volunteer"

    if any(
        keyword in query_lower
        for keyword in donation_keywords
    ):
        return "donation"

    return "general"

# --------------------------------------------------
# Detect whether question is festival-related
# --------------------------------------------------

def is_festival_question(query):

    query_lower = query.lower()

    festival_keywords = [

        # Festival
        "ganesh",
        "ganesha",
        "vinayaka",
        "festival",
        "lvs",
        "excellency",

        # Religious / festival activities
        "pooja",
        "puja",
        "harathi",
        "aarti",
        "archana",
        "homam",
        "bhajan",
        "visarjan",
        "immersion",
        "idol",
        "prasadam",
        "annaprasada",

        # Schedule
        "schedule",
        "event",
        "events",
        "festival timing",
        "festival date",
        "today's event",
        "event today",

        # Competitions
        "competition",
        "chess",
        "carrom",
        "tambola",
        "drawing",
        "musical chairs",
        "quiz",

        # Cultural
        "cultural",
        "dance",
        "singing",
        "song",
        "skit",
        "instrument",
        "performance",
        "karaoke",
        "track",

        # Volunteer
        "volunteer",
        "volunteering",
        "registration desk",
        "cleanup",
        "cleanup crew",
        "decoration",
        "visarjan support",
        "photography",

        # Donation
        "donation",
        "donate",
        "donor",
        "sponsor",

        # Festival information
        "committee",
        "committee member",
        "organizer",
        "organiser",
        "festival rules",
        "festival faq"
    ]

    return any(
        keyword in query_lower
        for keyword in festival_keywords
    )
# --------------------------------------------------
# Search knowledge base
# --------------------------------------------------

def search_knowledge(
    query,
    number_of_results=5
):

    query_embedding = create_embedding(
        query
    )

    category = detect_category(
        query
    )

    # --------------------------------------------------
    # Get more results initially
    # --------------------------------------------------

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=10
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    # --------------------------------------------------
    # Category-based source priority
    # --------------------------------------------------

    priority_sources = {

        "schedule": [
            "festival_schedule.md"
        ],

        "competition": [
            "competition_rules.md"
        ],

        "cultural": [
            "cultural_programs.md"
        ],

        "volunteer": [
            "volunteer_rules.md"
        ],

        "donation": [
            "donation_information.md"
        ],

        "general": []
    }

    preferred_sources = priority_sources.get(
        category,
        []
    )

    # --------------------------------------------------
    # Reorder results
    # --------------------------------------------------

    prioritized = []
    normal = []

    for document, metadata in zip(
        documents,
        metadatas
    ):

        source = ""

        if metadata:

            source = metadata.get(
                "source",
                ""
            )

        if source in preferred_sources:

            prioritized.append(
                {
                    "document": document,
                    "source": source
                }
            )

        else:

            normal.append(
                {
                    "document": document,
                    "source": source
                }
            )

    ordered_results = (
        prioritized +
        normal
    )

    ordered_results = ordered_results[
        :number_of_results
    ]

    final_documents = [
        item["document"]
        for item in ordered_results
    ]

    final_sources = [
        item["source"]
        for item in ordered_results
        if item["source"]
    ]

    return {
        "documents": final_documents,
        "sources": final_sources
    }


# --------------------------------------------------
# Build context
# --------------------------------------------------

def build_context(
    documents
):

    if not documents:
        return ""

    context_parts = []

    for index, document in enumerate(
        documents,
        start=1
    ):

        context_parts.append(
            f"Source {index}:\n{document}"
        )

    return "\n\n".join(
        context_parts
    )


# --------------------------------------------------
# Generate RAG response
# --------------------------------------------------

def ask_rag(
    question
):

    search_results = search_knowledge(
        question
    )

    documents = search_results[
        "documents"
    ]

    sources = search_results[
        "sources"
    ]

    context = build_context(
        documents
    )

    if not context:

        return {
            "response": (
                "I couldn't find this information "
                "in the festival knowledge base."
            ),
            "sources": []
        }

    prompt = f"""
You are the LVS Excellency Ganesha Festival AI Assistant.

Answer the resident's question using ONLY the
information provided in the festival knowledge base.

Do not invent information.

If the answer is not available in the knowledge
base, clearly say that the information is currently
not available.

Keep the answer clear, concise, and helpful.

IMPORTANT:
If the question asks about a date, time, event,
or festival schedule, prefer the official
festival schedule information over general
descriptions.

Festival Knowledge Base:
------------------------

{context}

------------------------

Resident Question:
{question}

Answer:
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response[
        "message"
    ][
        "content"
    ]

    return {
        "response": answer,
        "sources": list(
            dict.fromkeys(sources)
        )
    }