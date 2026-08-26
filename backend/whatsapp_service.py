"""
WhatsApp Service (Meta Cloud API)
===================================
Sends WhatsApp confirmation messages using pre-approved
message templates - never free-form text (Meta requires an
approved template for any business-initiated message
outside a 24-hour customer-service window).

This is designed to NEVER break the calling registration
flow if anything goes wrong - a failed/misconfigured
WhatsApp send should never prevent someone from completing
their actual registration. Every failure is caught and
logged, not raised.
"""

import requests

from backend.config import (
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_VERSION,
    PUBLIC_BASE_URL
)

GRAPH_API_URL = (
    f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/"
    f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

# India-only for now, matching the app's existing 10-digit
# mobile number validation everywhere else.
COUNTRY_CODE = "91"


def _format_recipient_number(mobile_number):
    """
    Converts a plain 10-digit Indian mobile number (as
    stored/validated everywhere else in this app) into the
    international format Meta's API requires (country code,
    no leading +, no spaces/dashes).
    """

    cleaned = "".join(ch for ch in str(mobile_number) if ch.isdigit())

    if len(cleaned) == 10:
        return COUNTRY_CODE + cleaned

    if len(cleaned) == 12 and cleaned.startswith(COUNTRY_CODE):
        return cleaned

    return None


def send_template_message(
    mobile_number,
    template_name,
    language_code,
    parameters,
    header_type=None,
    header_link=None,
    header_filename=None
):
    """
    Sends a WhatsApp template message. `parameters` is a
    list of plain strings mapped in order to the template's
    {{1}}, {{2}}, {{3}}... placeholders.

    header_type/header_link are optional - set these when
    the template has an Image or Document header (e.g. the
    Annaprasada coupon or donation receipt). header_link
    must be a real, publicly reachable HTTPS URL - WhatsApp
    fetches the file from that link at send-time, it isn't
    uploaded directly. header_filename is only used for
    Document headers (shown as the attachment's file name).

    Returns True if the message was accepted by Meta's API,
    False otherwise (including if WhatsApp isn't configured
    at all yet) - never raises, so this is always safe to
    call from any registration flow without extra try/except
    at the call site.
    """

    if not WHATSAPP_ACCESS_TOKEN:
        print(
            "[WhatsApp] Skipped sending - WHATSAPP_ACCESS_TOKEN "
            "is not set in .env yet."
        )
        return False

    recipient = _format_recipient_number(mobile_number)

    if not recipient:
        print(f"[WhatsApp] Skipped sending - invalid mobile number: {mobile_number}")
        return False

    components = []

    if header_type and header_link:

        if header_type == "image":

            components.append({
                "type": "header",
                "parameters": [
                    {"type": "image", "image": {"link": header_link}}
                ]
            })

        elif header_type == "document":

            document_param = {"link": header_link}

            if header_filename:
                document_param["filename"] = header_filename

            components.append({
                "type": "header",
                "parameters": [
                    {"type": "document", "document": document_param}
                ]
            })

    components.append({
        "type": "body",
        "parameters": [
            {"type": "text", "text": str(p)} for p in parameters
        ]
    })

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": components
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            GRAPH_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            response_data = response.json()
            print(f"[WhatsApp] Sent '{template_name}' to {recipient} - Meta response: {response_data}")
            return True

        # Common early cause: template still "In review" or
        # not yet approved - Meta returns a 4xx error here.
        print(
            f"[WhatsApp] Failed to send '{template_name}' to {recipient}: "
            f"{response.status_code} {response.text}"
        )
        return False

    except requests.RequestException as error:

        print(f"[WhatsApp] Network error sending to {recipient}: {error}")
        return False


def send_registration_confirmation(name, competition, block, flat, mobile_number):
    """
    Sends the registration_confirmation template. Matches
    the exact variable order submitted for Meta approval:
    {{1}}=Name, {{2}}=Competition, {{3}}=Block, {{4}}=Flat.

    Tries "en" first (confirmed as the correct code Meta
    approved this template under), then falls back to
    "en_US" just in case that ever changes.
    """

    parameters = [name, competition, block, flat]

    sent = send_template_message(
        mobile_number=mobile_number,
        template_name="registration_confirmation",
        language_code="en",
        parameters=parameters
    )

    if not sent:

        print("[WhatsApp] Retrying with language code 'en_US' instead of 'en'...")

        sent = send_template_message(
            mobile_number=mobile_number,
            template_name="registration_confirmation",
            language_code="en_US",
            parameters=parameters
        )

    return sent


def _build_public_file_url(relative_path):
    """
    Converts a relative file path (e.g. "static/coupons/x.png",
    the same format used everywhere else in this app) into a
    full public URL WhatsApp can actually fetch the file from.
    """

    cleaned_path = relative_path.replace("\\", "/").lstrip("/")

    return f"{PUBLIC_BASE_URL}/{cleaned_path}"


def send_annaprasada_confirmation(name, members, block, flat, coupon_id, coupon_image_path, mobile_number):
    """
    Sends the annaprasada_confirmation template, with the
    resident's actual coupon QR image attached as the
    template's Image header.

    Variable order matches what was submitted for Meta
    approval: {{1}}=Name, {{2}}=Members, {{3}}=Block,
    {{4}}=Flat, {{5}}=Coupon ID.
    """

    parameters = [name, members, block, flat, coupon_id]
    image_url = _build_public_file_url(coupon_image_path)

    sent = send_template_message(
        mobile_number=mobile_number,
        template_name="annaprasada_confirmation",
        language_code="en",
        parameters=parameters,
        header_type="image",
        header_link=image_url
    )

    if not sent:

        print("[WhatsApp] Retrying Annaprasada confirmation with language code 'en_US'...")

        sent = send_template_message(
            mobile_number=mobile_number,
            template_name="annaprasada_confirmation",
            language_code="en_US",
            parameters=parameters,
            header_type="image",
            header_link=image_url
        )

    return sent


def send_donation_confirmation(name, amount, receipt_id, receipt_pdf_path, mobile_number):
    """
    Sends the donation_confirmation template, with the
    resident's actual receipt PDF attached as the template's
    Document header.

    Variable order matches what was submitted for Meta
    approval: {{1}}=Name, {{2}}=Amount, {{3}}=Receipt ID.
    """

    parameters = [name, amount, receipt_id]
    document_url = _build_public_file_url(receipt_pdf_path)

    sent = send_template_message(
        mobile_number=mobile_number,
        template_name="donation_confirmation",
        language_code="en",
        parameters=parameters,
        header_type="document",
        header_link=document_url,
        header_filename=f"Receipt_{receipt_id}.pdf"
    )

    if not sent:

        print("[WhatsApp] Retrying Donation confirmation with language code 'en_US'...")

        sent = send_template_message(
            mobile_number=mobile_number,
            template_name="donation_confirmation",
            language_code="en_US",
            parameters=parameters,
            header_type="document",
            header_link=document_url,
            header_filename=f"Receipt_{receipt_id}.pdf"
        )

    return sent