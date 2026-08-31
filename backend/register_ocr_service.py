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
Name, Block (South/North/Terrace), Flat Number, Amount.
Some rows may also include a Mobile Number column.

Extract every row you can read as a JSON array of objects
with exactly these keys:
"name", "block", "flat_number", "amount", "mobile"

Rules:
- If a value is unclear, ambiguous, or unreadable, use null
  for that specific field - do not guess.
- "block" must be exactly one of: "South", "North",
  "Terrace", or null if unclear.
- "amount" must be a plain number (no currency symbol,
  no commas), or null if unreadable.
- "mobile" should be a 10-digit number if present and
  legible, otherwise null.
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
                "amount": row.get("amount"),
                "mobile": row.get("mobile"),
            })

        return normalized

    except json.JSONDecodeError as error:
        print(f"[RegisterOCR] Could not parse Gemini response as JSON: {error}")
        return []

    except Exception as error:
        print(f"[RegisterOCR] Unexpected error during extraction: {error}")
        return []