"""
Payment Screenshot Verification (OCR-based sanity check)
"""

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SUCCESS_KEYWORDS = [
    "payment successful",
    "successfully paid",
    "payment sent",
    "money sent",
    "transaction successful",
    "payment complete",
    "paid successfully",
    "sent successfully",
    "success",
    "completed",
]


def screenshot_looks_like_payment_proof(image_path):

    try:

        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image).lower()

    except Exception as error:

        print(f"[OCR Check] Could not run OCR, allowing through: {error}")
        return True, ""

    has_success_keyword = any(
        keyword in extracted_text for keyword in SUCCESS_KEYWORDS
    )

    has_rupee_amount = "₹" in extracted_text or "rs." in extracted_text or "inr" in extracted_text

    looks_valid = has_success_keyword or has_rupee_amount

    return looks_valid, extracted_text
