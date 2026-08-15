"""
Push Notification Service
===========================
Manages Web Push subscriptions (one per installed
device/browser) and sends push notifications to all of
them. Subscriptions are stored in a plain JSON file, read
fresh on every call for the same hot-reload reasons as
announcement_service.py.

A subscription that fails with an expired/invalid error
(HTTP 404/410 from the push provider) is automatically
removed - this happens naturally over time as residents
uninstall the PWA or clear their browser data.
"""

import json
import os
from pywebpush import webpush, WebPushException

from backend.config import (
    VAPID_PRIVATE_KEY_PATH,
    VAPID_CLAIM_SUBJECT
)

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "push_subscriptions.json"
)


def _read_all():

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write_all(subscriptions):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, indent=4)


def save_subscription(subscription_info):
    """
    Stores a new push subscription (or does nothing if this
    exact endpoint is already saved, avoiding duplicates
    when a device re-subscribes).
    """

    subscriptions = _read_all()

    endpoint = subscription_info.get("endpoint")

    already_saved = any(
        s.get("endpoint") == endpoint for s in subscriptions
    )

    if not already_saved:
        subscriptions.append(subscription_info)
        _write_all(subscriptions)

    return {"status": "saved", "total_subscriptions": len(subscriptions)}


def remove_subscription(endpoint):

    subscriptions = _read_all()

    remaining = [s for s in subscriptions if s.get("endpoint") != endpoint]

    if len(remaining) != len(subscriptions):
        _write_all(remaining)


def send_push_to_all(title, body):
    """
    Sends a push notification to every saved subscription.
    Returns a summary of how many succeeded/failed, and
    prunes any subscriptions that are no longer valid.
    """

    subscriptions = _read_all()

    if not subscriptions:
        return {"sent": 0, "failed": 0, "total": 0}

    payload = json.dumps({
        "title": title,
        "body": body
    })

    sent = 0
    failed = 0
    dead_endpoints = []

    for subscription in subscriptions:

        try:
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY_PATH,
                vapid_claims={"sub": VAPID_CLAIM_SUBJECT}
            )
            sent += 1

        except WebPushException as e:

            status_code = getattr(e.response, "status_code", None)

            # 404/410 mean the subscription is gone for good
            # (uninstalled, browser data cleared, etc.) - safe
            # to prune. Other errors are left alone in case
            # they're transient (network blip, etc.).
            if status_code in (404, 410):
                dead_endpoints.append(subscription.get("endpoint"))

            failed += 1

    if dead_endpoints:

        remaining = [
            s for s in subscriptions
            if s.get("endpoint") not in dead_endpoints
        ]
        _write_all(remaining)

    return {
        "sent": sent,
        "failed": failed,
        "total": len(subscriptions)
    }