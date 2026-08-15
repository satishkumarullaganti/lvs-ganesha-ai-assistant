"""
Announcement Service
=====================
Announcements are stored in a plain JSON file
(backend/data/announcements.json) and read fresh on every
call - there is deliberately NO in-memory caching here, so
adding or removing an announcement (via the admin panel,
or by directly editing the JSON file) takes effect
immediately, without restarting uvicorn or redeploying.
"""

import json
import os
import uuid
from datetime import datetime, timezone

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "announcements.json"
)


def _read_all():

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    return data.get("announcements", [])


def _write_all(announcements):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"announcements": announcements}, f, indent=4)


def get_active_announcements():
    """
    Returns only active announcements, newest first.
    Called by the public /api/announcements endpoint that
    the frontend polls - always reads the file fresh.
    """

    all_announcements = _read_all()

    active = [a for a in all_announcements if a.get("active", True)]

    active.sort(key=lambda a: a.get("created_at", ""), reverse=True)

    return active


def get_all_announcements():
    """
    Returns every announcement (active and inactive), for
    the admin panel's management view.
    """

    all_announcements = _read_all()

    all_announcements.sort(key=lambda a: a.get("created_at", ""), reverse=True)

    return all_announcements


def add_announcement(message, announcement_type="info"):

    announcements = _read_all()

    new_announcement = {
        "id": uuid.uuid4().hex[:10],
        "message": message.strip(),
        "type": announcement_type if announcement_type in ("info", "urgent", "reminder") else "info",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    announcements.append(new_announcement)

    _write_all(announcements)

    return new_announcement


def deactivate_announcement(announcement_id):

    announcements = _read_all()

    found = False

    for announcement in announcements:

        if announcement.get("id") == announcement_id:
            announcement["active"] = False
            found = True
            break

    if found:
        _write_all(announcements)

    return found