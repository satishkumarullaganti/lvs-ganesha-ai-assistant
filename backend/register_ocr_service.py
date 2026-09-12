"""
Register OCR Service
======================
Uses Gemini's vision model to extract donation entries
from a photo of the handwritten security-desk register,
so an admin doesn't have to type each row manually.

This is intentionally kept separate from the existing
Tesseract-based payment_verification.py - that OCR is
tuned for clean, machine-rendered UPI screenshots, while
this handles messy, multi-writer handwriting, which
needs a vision-LLM approach instead of classic OCR.

The extracted rows are NEVER saved directly - they are
always shown to an admin for review/correction first,
since handwriting misreads (especially on amounts and
flat numbers) carry real financial risk if trusted blindly.
"""

import os
import json
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

EXTRACTION_PROMPT = """
This is a photo of a handwritten donation register page
from a residential community's Ganesh festival.

The register has columns (order may vary slightly):
Date, Name, Flat No, Amount. Some pages also have a running
"Value" (cumulative total) column and a "Receipt No" column -
ignore "Value" entirely (it is not this row's amount), but do
capture "Receipt No" if present.

IMPORTANT - how flat numbers are actually written in this
register: the block letter and flat number are usually written
TOGETHER in one cell, e.g. "S001" (South, flat 001), "N104"
(North, flat 104), "S-306" (South, flat 306), "T2" (Terrace).
There is no separate "Block" column - you must split this
yourself:
- Starts with "S" -> block is "South", flat_number is the
  digits only (zero-padded to 3 digits if the register wrote
  fewer, e.g. "S1" -> flat_number "001").
- Starts with "N" -> block is "North", same digit rule.
- Starts with "T" followed by a single digit (T1/T2/T3) ->
  block is "Terrace", flat_number is exactly "T1", "T2", or
  "T3" (do not zero-pad these).

Some entries are NOT a resident flat at all - e.g. "Security",
"Watchman", "Office", or a vendor name written in that column.
Some entries are illegible, crossed out, or show two different
flat numbers on one line (e.g. "N006/S012") because of a
correction - never guess which one is correct.

In every one of these non-standard or ambiguous cases: set
"block" and "flat_number" to null, but always copy exactly
what was written in that column, character for character, into
"raw_flat_text" - this lets a human resolve it correctly instead
of a wrong guess being silently saved.

Extract every row you can read as a JSON array of objects
with exactly these keys:
"name", "block", "flat_number", "raw_flat_text", "amount", "mobile", "receipt_no"

Rules:
- If a value is unclear, ambiguous, or unreadable, use null
  for that specific field - do not guess.
- "raw_flat_text" should always be filled in with the flat
  column's exact original text, even when block/flat_number
  were successfully split out - never leave it null if that
  cell has any writing in it.
- "amount" must be a plain number (no currency symbol,
  no commas, no trailing "/-"), or null if unreadable. Take
  this from the "Amount" column specifically, never the
  "Value" column.
- "mobile" - this register does not have a mobile number
  column at all. Always return null for this field - never
  interpret any other number (flat, amount, receipt no,
  date) as a mobile number.
- "receipt_no" is the register's own handwritten receipt
  number if that column exists and is filled in, otherwise
  null.
- Skip entirely blank rows.
- Return ONLY the JSON array - no markdown formatting,
  no explanation, no extra text before or after it.
"""


def extract_register_rows(image_path: str) -> list[dict]:
    """
    Sends the register photo to Gemini and returns a list
    of extracted row dicts. Never raises on a bad/partial
    response from the model - returns an empty list instead,
    so the admin UI can show a clear "nothing extracted,
    try a clearer photo" message rather than a crash.
    """

    if not GEMINI_API_KEY:
        print("[RegisterOCR] GEMINI_API_KEY not set in .env - cannot scan.")
        return []

    try:

        model = genai.GenerativeModel("gemini-3.6-flash")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        response = model.generate_content([
            {"mime_type": mime_type, "data": image_bytes},
            EXTRACTION_PROMPT
        ])

        raw_text = (response.text or "").strip()

        # Strip markdown code fences if the model added them
        # despite being told not to - happens occasionally.
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:].strip()

        rows = json.loads(raw_text)

        if not isinstance(rows, list):
            print(f"[RegisterOCR] Unexpected response shape: {raw_text[:200]}")
            return []

        # Normalize every row so the frontend always gets the
        # same five keys, even if the model omitted one.
        normalized = []

        for row in rows:

            if not isinstance(row, dict):
                continue

            normalized.append({
                "name": row.get("name"),
                "block": row.get("block"),
                "flat_number": row.get("flat_number"),
                "raw_flat_text": row.get("raw_flat_text"),
                "amount": row.get("amount"),
                "mobile": row.get("mobile"),
                "receipt_no": row.get("receipt_no"),
            })

        return normalized

    except json.JSONDecodeError as error:
        print(f"[RegisterOCR] Could not parse Gemini response as JSON: {error}")
        return []

    except Exception as error:
        print(f"[RegisterOCR] Unexpected error during extraction: {error}")
        return []

# ============================================
# Cultural Program Sign-up Notebook Scan
# ============================================
# A separate notebook from the donation register - residents
# who want to sign up for cultural program performances (often
# children) are noted here by hand: Name, Mobile, Age, and
# Flat. It doesn't record which category they want to perform
# in - that gets chosen by the admin during review, since it
# was never captured on paper.
# ============================================

CULTURAL_SIGNUP_EXTRACTION_PROMPT = """
This is a photo of a handwritten sign-up notebook page for
cultural program performances at a residential community's
Ganesh festival. Entries are often for children being signed
up by a parent.

Each numbered line typically has, in some order: Name, a
10-digit Mobile Number, an Age (sometimes with "yrs"), and a
Flat (block letter + number combined, e.g. "S108", "N303",
or just "NT" for a non-tower/guest entry). The exact left-to-
right order of Age and Flat varies line to line - read
carefully rather than assuming a fixed column order.

Some entries have a corrected mobile number - the first
number may be crossed out or marked with an "X", with the
correct number written below or beside it (often with an
arrow). Always use the corrected/final number, never the
crossed-out one.

It is normal and expected for two entries to share the same
mobile number - these are usually siblings signed up by the
same parent. Do not treat this as an error.

Extract every numbered row you can read as a JSON array of
objects with exactly these keys:
"name", "mobile", "age", "block", "flat_number", "raw_flat_text"

Rules:
- "mobile" must be a 10-digit number, using the corrected
  value if one was written, or null if genuinely illegible.
- "age" should be the age exactly as written (e.g. "12",
  "2.5", "9 yrs" -> just capture the number part as a string,
  e.g. "12", "2.5", "9"), or null if not given.
- For the flat: if it's written as a block letter + number
  together (e.g. "S108" -> block "South", flat_number "108";
  "N303" -> block "North", flat_number "303"; a bare "S" or
  "N" with no number, or "NT"/blank, means it's unclear or a
  non-resident entry) split it the same way as described
  below, otherwise set block and flat_number to null.
  - Starts with "S" + digits -> block "South", flat_number is
    the digits (zero-padded to 3 if needed).
  - Starts with "N" + digits -> block "North", flat_number is
    the digits (zero-padded to 3 if needed).
  - "T" followed by a single digit (T1/T2/T3) -> block
    "Terrace", flat_number exactly "T1"/"T2"/"T3".
  - Anything else (unclear, missing, "NT", just a block
    letter with no number) -> block and flat_number both
    null.
- "raw_flat_text" must always contain exactly what was
  written in that part of the line, even if block/flat_number
  were successfully split out, so a human can double check.
- If a value is unclear or unreadable, use null for that
  specific field - do not guess.
- Skip entirely blank lines, but do not skip a row just
  because one field (like flat) is missing - still extract
  the name and mobile you can read.
- Return ONLY the JSON array - no markdown formatting, no
  explanation, no extra text before or after it.
"""


def extract_cultural_signup_rows(image_path: str) -> list[dict]:
    """
    Sends the cultural sign-up notebook photo to Gemini and
    returns a list of extracted row dicts. Same never-raises
    contract as extract_register_rows - an empty list means
    "nothing extracted, try a clearer photo", not a crash.
    """

    if not GEMINI_API_KEY:
        print("[RegisterOCR] GEMINI_API_KEY not set in .env - cannot scan.")
        return []

    try:

        model = genai.GenerativeModel("gemini-3.6-flash")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        response = model.generate_content([
            {"mime_type": mime_type, "data": image_bytes},
            CULTURAL_SIGNUP_EXTRACTION_PROMPT
        ])

        raw_text = (response.text or "").strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:].strip()

        rows = json.loads(raw_text)

        if not isinstance(rows, list):
            print(f"[RegisterOCR] Unexpected response shape: {raw_text[:200]}")
            return []

        normalized = []

        for row in rows:

            if not isinstance(row, dict):
                continue

            normalized.append({
                "name": row.get("name"),
                "mobile": row.get("mobile"),
                "age": row.get("age"),
                "block": row.get("block"),
                "flat_number": row.get("flat_number"),
                "raw_flat_text": row.get("raw_flat_text"),
            })

        return normalized

    except json.JSONDecodeError as error:
        print(f"[RegisterOCR] Could not parse Gemini response as JSON: {error}")
        return []

    except Exception as error:
        print(f"[RegisterOCR] Unexpected error during extraction: {error}")
        return []

# ============================================
# Annaprasada Coupon Register Scan
# ============================================
# A separate offline register from the two above - used when a
# resident collects an Annaprasada coupon in person (at a desk,
# rather than through the app) and is noted by hand: Name, Flat,
# and how many members the coupon covers. Adults/Children and
# Mobile are usually NOT recorded on paper (this register is
# about handing out a coupon, not identity/contact info), so
# those normally come back null - the admin fills them in during
# review, same as how the cultural sign-up scan leaves Category
# for the admin to pick since paper never records it either.
# ============================================

ANNAPRASADA_EXTRACTION_PROMPT = """
This is a photo of a handwritten register page used to note down
Annaprasada (prasadam meal) coupons handed out in person at a
residential community's Ganesh festival.

Each numbered line typically has, in some order: Name, a Flat
(block letter + number combined, e.g. "S104", "N020", "T2"), and
a count of how many members/persons the coupon is for (this may
be labeled "Members", "Persons", "Count", "No.", or similar - it
is always a small whole number, usually 1-15). Some registers may
also separately note how many of those members are adults versus
children, and occasionally a mobile number - capture these if
present, but most registers will NOT have them, which is normal.

For the flat, split it the same way as always:
- Starts with "S" + digits -> block "South", flat_number is the
  digits (zero-padded to 3 if needed, e.g. "S1" -> "001").
- Starts with "N" + digits -> block "North", same digit rule.
- "T" followed by a single digit (T1/T2/T3) -> block "Terrace",
  flat_number exactly "T1"/"T2"/"T3" (do not zero-pad these).
- Anything else (unclear, missing, just a block letter with no
  number, "Security"/"Office"/a name with no flat at all) -> set
  block and flat_number both to null, but still copy exactly what
  was written into "raw_flat_text".

Extract every numbered row you can read as a JSON array of
objects with exactly these keys:
"name", "block", "flat_number", "raw_flat_text", "members", "adults", "children", "mobile"

Rules:
- "members" must be a plain whole number as a string (e.g. "3"),
  taken from whichever column records the total count for this
  coupon, or null if genuinely unreadable/missing.
- "adults" and "children" should only be filled in if the
  register actually has separate columns for them and the numbers
  add up to "members" - otherwise leave both null rather than
  guessing a split.
- "mobile" must be a 10-digit number if one is written for this
  row, otherwise null - do not confuse a flat number, a serial
  number, or a members count with a mobile number.
- "raw_flat_text" must always contain exactly what was written in
  the flat column, even when block/flat_number were successfully
  split out, so a human can double check.
- If a value is unclear or unreadable, use null for that specific
  field - do not guess.
- Skip entirely blank lines, but do not skip a row just because
  one field is missing - still extract what you can read.
- Return ONLY the JSON array - no markdown formatting, no
  explanation, no extra text before or after it.
"""


def extract_annaprasada_rows(image_path: str) -> list[dict]:
    """
    Sends the Annaprasada coupon register photo to Gemini and
    returns a list of extracted row dicts. Same never-raises
    contract as the two extractors above - an empty list means
    "nothing extracted, try a clearer photo", not a crash.
    """

    if not GEMINI_API_KEY:
        print("[RegisterOCR] GEMINI_API_KEY not set in .env - cannot scan.")
        return []

    try:

        model = genai.GenerativeModel("gemini-3.6-flash")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        response = model.generate_content([
            {"mime_type": mime_type, "data": image_bytes},
            ANNAPRASADA_EXTRACTION_PROMPT
        ])

        raw_text = (response.text or "").strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:].strip()

        rows = json.loads(raw_text)

        if not isinstance(rows, list):
            print(f"[RegisterOCR] Unexpected response shape: {raw_text[:200]}")
            return []

        normalized = []

        for row in rows:

            if not isinstance(row, dict):
                continue

            normalized.append({
                "name": row.get("name"),
                "block": row.get("block"),
                "flat_number": row.get("flat_number"),
                "raw_flat_text": row.get("raw_flat_text"),
                "members": row.get("members"),
                "adults": row.get("adults"),
                "children": row.get("children"),
                "mobile": row.get("mobile"),
            })

        return normalized

    except json.JSONDecodeError as error:
        print(f"[RegisterOCR] Could not parse Gemini response as JSON: {error}")
        return []

    except Exception as error:
        print(f"[RegisterOCR] Unexpected error during extraction: {error}")
        return []
