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

    committee_keywords = [
        "committee",
        "president",
        "vice president",
        "secretary",
        "treasurer",
        "coordinator",
        "coordinators",
        "organizer",
        "organiser",
        "chairperson",
        "convenor",
        "member"
    ]

    # Committee is checked before cultural/competition/volunteer
    # since role questions like "who is the Cultural Coordinator"
    # or "who is the Volunteer Coordinator" contain a category
    # keyword (cultural, volunteer) AND a committee keyword
    # (coordinator) - the person is asking "who", which is a
    # committee_details.md lookup, not a cultural/volunteer one.
    if any(
        keyword in query_lower
        for keyword in committee_keywords
    ):
        return "committee"

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

def _build_retrieval_queries(query):
    original = query.strip()
    normalized = re.sub(r"\s+", " ", original.lower()).strip()
    cleaned = re.sub(r"\b(what|when|where|who|why|how|is|are|the|a|an|of|on|at|for|to|and|in|does|will|can|do|i|we|you|it|this|that|please|tell|me)\b", " ", normalized)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    variants = [original]
    if cleaned and cleaned != normalized:
        variants.append(cleaned)
    rules_match = re.search(r"\b(?:rules?|guidelines?)\s+(?:for\s+)?(.+)", cleaned)
    if rules_match and rules_match.group(1).strip():
        variants.append(f"{rules_match.group(1).strip()} rules")
    important_terms = ["tambola", "chess", "carrom", "drawing", "musical chairs", "committee president", "committee", "organizer", "organiser", "coordinator", "president", "secretary", "treasurer", "volunteer", "donation", "sponsor", "dance", "singing", "skit"]
    for term in important_terms:
        if term in normalized:
            variants.append(term)
    result=[]; seen=set()
    for item in variants:
        key=item.strip().lower()
        if key and key not in seen:
            seen.add(key); result.append(item.strip())
    return result[:4]

def _query_chroma(query, n_results=10):
    query_embedding = create_embedding(query)
    return collection.query(query_embeddings=[query_embedding], n_results=n_results)

def search_knowledge(query, number_of_results=5):
    category = detect_category(query)
    # Schedule and donation questions can have their answer
    # split across multiple related sections (donation info is
    # spread across About/Amount/Sponsor/FAQ sections in the
    # same doc), so give them a bit more retrieval headroom to
    # reduce the odds of the right chunk being crowded out.
    if category == "schedule":
        number_of_results = 8
    elif category == "donation":
        number_of_results = 7
    candidates=[]
    for retrieval_query in _build_retrieval_queries(query):
        try:
            results=_query_chroma(retrieval_query, n_results=10)
            documents=results.get("documents", [[]])[0]
            metadatas=results.get("metadatas", [[]])[0]
            distances=results.get("distances", [[]])[0]
            for document, metadata, distance in zip(documents, metadatas, distances):
                candidates.append({"document":document, "metadata":metadata or {}, "distance":distance})
        except Exception as error:
            print(f"RAG retrieval failed for query '{retrieval_query}': {error}")
    unique=[]; seen=set()
    for candidate in candidates:
        key=candidate["document"].strip()
        if not key or key in seen:
            continue
        seen.add(key); unique.append(candidate)
    filtered=[c for c in unique if c["distance"] <= MAX_RELEVANT_DISTANCE]
    priority_sources={"schedule":["festival_schedule.md"],"location":["festival_schedule.md"],"competition":["competition_rules.md"],"cultural":["cultural_programs.md"],"volunteer":["volunteer_rules.md"],"donation":["donation_information.md"],"committee":["committee_details.md"],"general":[]}
    preferred_sources=priority_sources.get(category, [])
    filtered.sort(key=lambda item:(0 if item["metadata"].get("source", "") in preferred_sources else 1, item["distance"]))
    ordered=filtered[:number_of_results]
    return {"documents":[x["document"] for x in ordered], "sources":list(dict.fromkeys(x["metadata"].get("source", "") for x in ordered if x["metadata"].get("source", "")))}


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
            document
        )

    return "\n\n---\n\n".join(
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

If the question asks what events or activities are
happening on a specific date (rather than asking
about one named event), list EVERY event scheduled
for that date with its time, using the full day's
schedule information. Do not answer with only one
event when the question is asking for the whole day.

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

12. Never reference "Source 1", "Source 2", document
    names, or any internal labels in your answer - the
    resident should never see how the knowledge base is
    structured internally.

13. Do not quote the knowledge base text verbatim or
    wrap phrases in quotation marks. Always paraphrase
    in your own plain words.

14. Give exactly one clear, direct answer. Do not say
    "yes" and then contradict it with "however" or "but"
    in the same answer - decide the correct answer first,
    then state only that.

15. If a specific number, amount, name, or detail asked
    about is not directly stated in the Festival
    Knowledge Base above, respond with exactly:
    "I don't have that information in the LVS Ganesha
    Festival knowledge base." Do not explain what
    conditions would need to be met for that detail to
    exist, and do not describe your own answering rules
    or policy - just give the one-sentence response above.

16. For yes/no questions, work out the correct answer
    FIRST, then make sure your opening word matches it.
    Do not begin with "Yes." if the fact you go on to
    state actually means no (or the reverse). For example,
    if a resident asks whether something can be reused and
    the knowledge base says it cannot be reused, the answer
    must begin with "No," not "Yes."
   

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

    # --------------------------------------------------
    # Numeric-amount guardrail (hard code-level check)
    # --------------------------------------------------
    # Some source documents describe amount-type policies
    # in many different phrasings ("should be provided only
    # when officially confirmed", "should not invent a
    # minimum...", etc.) - trying to strip every paraphrase
    # at ingest time is unreliable, since new wording can
    # always slip through.
    #
    # Instead, validate the LLM's actual answer: if the
    # resident asked about a minimum/maximum/cost/fee/price
    # and the generated answer contains no digits at all,
    # the model is very likely hedging around missing data
    # instead of giving a real number - force the standard
    # "not available" response instead of letting a vague,
    # policy-sounding non-answer through.
    # --------------------------------------------------

    AMOUNT_QUESTION_WORDS = {
        "minimum", "maximum", "amount", "cost", "fee",
        "fees", "price", "how much"
    }

    question_lower_for_amount = question.lower()

    asks_about_amount = any(
        term in question_lower_for_amount
        for term in AMOUNT_QUESTION_WORDS
    )

    has_digit_in_answer = any(
        character.isdigit()
        for character in answer
    )

    # A correct answer can legitimately have no digits at all -
    # e.g. "donations are purely voluntary, there is no minimum."
    # Only treat a no-digit answer as a hedge/non-answer if it
    # also doesn't contain a clear explicit statement either way.
    answer_lower_for_amount = answer.lower()

    has_clear_negation = any(
        phrase in answer_lower_for_amount
        for phrase in [
            "no minimum", "no maximum", "not required",
            "voluntary", "any amount", "not fixed",
            "no fixed amount", "no specific amount"
        ]
    )

    if asks_about_amount and not has_digit_in_answer and not has_clear_negation:

        answer = (
            "I don't have that information in the LVS Ganesha "
            "Festival knowledge base."
        )

        sources = []

    # --------------------------------------------------
    # Committee role-responsibility guardrail
    # --------------------------------------------------
    # committee_details.md lists every role's NAME once, and
    # separately lists RESPONSIBILITIES only for roles that
    # actually have documented duties. Roles like Vice
    # President and Joint Secretary appear only once (the name
    # entry) with no matching entry in the Responsibilities
    # section.
    #
    # A small local LLM can still generate a plausible-sounding
    # answer by blending a nearby role's real responsibilities
    # onto the one actually asked about (e.g. attributing the
    # Secretary's duties to the Vice President because both
    # appear close together in the same retrieved chunk).
    #
    # Hard check: if the question asks what a specific role
    # does, and that role's name appears in context only once
    # (no separate Responsibilities entry), refuse instead of
    # letting the LLM guess.
    # --------------------------------------------------

    COMMITTEE_ROLES = [
        "vice president", "president", "joint secretary",
        "secretary", "treasurer", "cultural coordinator",
        "volunteer coordinator", "food coordinator",
        "annaprasada coordinator", "decoration coordinator",
        "event coordinator"
    ]

    DUTY_QUESTION_WORDS = {
        "do", "does", "role", "responsibility",
        "responsibilities", "duty", "duties", "job"
    }

    question_lower_for_role = question.lower()

    asks_about_role_duty = any(
        word in question_lower_for_role.split()
        or word in question_lower_for_role
        for word in DUTY_QUESTION_WORDS
    )

    # Match the longest role name first so "vice president"
    # isn't mistakenly matched as just "president"
    matched_role = None

    for role in sorted(COMMITTEE_ROLES, key=len, reverse=True):
        if role in question_lower_for_role:
            matched_role = role
            break

    if asks_about_role_duty and matched_role:

        role_occurrences = context_lower.count(matched_role)

        if role_occurrences < 2:

            answer = (
                "I don't have that information in the LVS Ganesha "
                "Festival knowledge base."
            )

            sources = []

    # --------------------------------------------------
    # "Yes, but actually no" contradiction guardrail
    # --------------------------------------------------
    # A small local LLM can answer a yes/no question by
    # leading with "Yes." and then immediately stating a
    # fact that actually means "no" (e.g. "Yes. A redeemed
    # coupon cannot be redeemed again." in answer to "Can I
    # use it twice?"). The information itself isn't wrong,
    # but the leading word directly contradicts it and would
    # mislead a resident skimming the answer.
    #
    # If the answer opens with "Yes" but contains a clear
    # negation shortly after, strip the misleading opener
    # so the answer isn't self-contradictory.
    # --------------------------------------------------

    answer_stripped = answer.strip()

    starts_with_yes = re.match(
        r"^yes[\.,!]?\s",
        answer_stripped,
        re.IGNORECASE
    )

    NEGATION_PHRASES = [
        "cannot", "can not", "can't", "won't", "will not",
        "should not", "shouldn't", "must not", "mustn't",
        "is not", "isn't", "are not", "aren't", "not be"
    ]

    contains_negation = any(
        phrase in answer_stripped.lower()
        for phrase in NEGATION_PHRASES
    )

    if starts_with_yes and contains_negation:

        answer = re.sub(
            r"^yes[\.,!]?\s*",
            "",
            answer_stripped,
            flags=re.IGNORECASE
        )

    return {
        "response": answer,
        "sources": list(
            dict.fromkeys(sources)
        )
    }