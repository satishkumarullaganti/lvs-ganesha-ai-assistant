import os
import re
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

# Chroma returns cosine "distance" (lower = more similar).
# Anything above this is treated as too weak to be useful
# context, and gets filtered out before reaching the LLM.
MAX_RELEVANT_DISTANCE = 1.0


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
        "harathi",
        "installation",
        "annaprasada"
    ]

    location_keywords = [
        "location",
        "venue",
        "where",
        "address",
        "party hall",
        "parking",
        "directions"
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

    # Location is checked before schedule since a question
    # like "where is the annaprasada distribution" contains
    # both a schedule-ish word (annaprasada) and a location
    # word (where) - location intent should win here.
    if any(
        keyword in query_lower
        for keyword in location_keywords
    ):
        return "location"

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

        # Location / venue
        "location",
        "venue",
        "where",
        "address",
        "party hall",
        "parking",
        "directions",

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
    # Get more results initially, with distances so we
    # can filter out weakly-related chunks below.
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

    distances = results.get(
        "distances",
        [[]]
    )[0]

    # --------------------------------------------------
    # Relevance filtering
    # --------------------------------------------------
    # Drop any chunk that's too dissimilar to the query.
    # Without this, weakly-related chunks get stuffed into
    # the prompt as if they were solid context, which can
    # make the LLM's answer vague even when RAG did run.
    # --------------------------------------------------

    filtered_documents = []
    filtered_metadatas = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        if distance <= MAX_RELEVANT_DISTANCE:

            filtered_documents.append(document)
            filtered_metadatas.append(metadata)

    documents = filtered_documents
    metadatas = filtered_metadatas

    # --------------------------------------------------
    # Category-based source priority
    # --------------------------------------------------

    priority_sources = {

        "schedule": [
            "festival_schedule.md"
        ],

        "location": [
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

    # --------------------------------------------------
    # Lexical grounding check (hard guardrail)
    # --------------------------------------------------
    # Semantic similarity alone isn't reliable enough -
    # a chunk can be "close enough" in embedding space
    # without actually answering the question, and small
    # local LLMs (like llama3.2:3b) don't always follow
    # "don't invent information" instructions strictly.
    #
    # As a hard, code-level safeguard: check whether the
    # question's significant words actually appear in the
    # retrieved context. If there's no real lexical overlap,
    # treat this as "not found" WITHOUT calling the LLM at
    # all - so it can't fabricate an answer on weak context.
    # --------------------------------------------------

    GROUNDING_STOPWORDS = {
        "what", "when", "where", "who", "why", "how",
        "is", "are", "the", "a", "an", "of", "on", "at",
        "for", "to", "and", "in", "does", "will", "can",
        "do", "i", "we", "you", "it", "this", "that",
        "available", "yes", "no", "please", "need",
        "want", "get", "know", "tell", "info",
        "information", "about", "there", "any", "some"
    }

    question_words = set(
        re.findall(r"[a-z0-9]+", question.lower())
    ) - GROUNDING_STOPWORDS

    context_lower = context.lower()

    has_lexical_overlap = any(
        word in context_lower
        for word in question_words
    )

    if not has_lexical_overlap:

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

Keep the answer short, direct, and specific to what
was asked. Do not repeat unrelated details from the
knowledge base that don't answer the question.

IMPORTANT:
If the question asks about a date, time, event,
or festival schedule, prefer the official
festival schedule information over general
descriptions.

If the question asks about a location, venue, or
address, answer with the specific place name only
(e.g. "Party Hall") rather than describing the
whole event.

IMPORTANT RULES:

1. Answer ONLY what is directly supported by the
   festival knowledge base.

2. NEVER assume, infer, guess, or invent information.

3. If the user's question is not directly answered
   by the provided festival knowledge, say:
   "I don't have that information in the LVS Ganesha
   Festival knowledge base."

4. Do NOT use general world knowledge to answer
   festival-related questions.

5. Do NOT treat the absence of information as evidence
   that something is available or allowed.

6. Do NOT invent facilities such as parking, accommodation,
   transport, food, security, or other arrangements unless
   they are explicitly mentioned in the knowledge base.

7. Answer only the specific question asked. Do not reproduce
   the entire retrieved document unless the user explicitly
   asks for the complete information or schedule.

   8. If the user asks about a specific event, program,
   competition, dance, singing, or cultural activity,
   answer using information specifically related
   to that event or activity.

9. If the user asks "when" about a specific event,
   provide the specific date and time of that event
   if it is available in the knowledge base.

10. Do NOT answer a specific event question with
    only the overall festival start and end dates.

11. If the specific event or activity is not found
    in the knowledge base, say:
    "I don't have that information in the LVS Ganesha
    Festival knowledge base."
   

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