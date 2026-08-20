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
    WHATSAPP_API_VERSION
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


def send_template_message(mobile_number, template_name, language_code, parameters):
    """
    Sends a WhatsApp template message. `parameters` is a
    list of plain strings mapped in order to the template's
    {{1}}, {{2}}, {{3}}... placeholders.

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

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in parameters
                    ]
                }
            ]
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