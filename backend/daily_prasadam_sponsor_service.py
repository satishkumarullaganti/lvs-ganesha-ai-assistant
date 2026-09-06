"""
Daily Prasadam Sponsor Request Service
=======================================
Residents can submit a request to sponsor a day's prasadam
from the home page. Requests are stored in a plain JSON file
(backend/data/daily_prasadam_sponsors.json), same pattern as
daily_prasadam_service.py, and reviewed by the coordinator in
the admin panel before being turned into a published
Daily Prasadam entry.

Status values: "pending" (default), "handled" (coordinator
used it to create/update a schedule entry), "rejected".
"""

import json
import os
import uuid
from datetime import datetime, timezone

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "daily_prasadam_sponsors.json"
)


def _read_all():

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    return data.get("requests", [])


def _write_all(requests):

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"requests": requests}, f, indent=4)


def get_all_sponsor_requests():
    """
    Returns every sponsor request, most recently submitted
    first - used by the admin panel's pending requests list.
    """

    requests = _read_all()

    requests.sort(key=lambda r: r.get("created_at", ""), reverse=True)

    return requests


def add_sponsor_request(name, mobile, block, flat_number, preferred_date, slot="", item="", notes=""):

    requests = _read_all()

    new_request = {
        "id": uuid.uuid4().hex[:10],
        "name": name.strip(),
        "mobile": mobile.strip(),
        "block": block.strip(),
        "flat_number": str(flat_number).strip(),
        "preferred_date": preferred_date.strip(),
        "slot": slot.strip() if slot else "",
        "item": item.strip() if item else "",
        "notes": notes.strip() if notes else "",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    requests.append(new_request)

    _write_all(requests)

    return new_request


def update_sponsor_request_status(request_id, status):

    requests = _read_all()

    found_request = None

    for req in requests:

        if req.get("id") == request_id:

            req["status"] = status
            req["updated_at"] = datetime.now(timezone.utc).isoformat()

            found_request = req
            break

    if found_request:
        _write_all(requests)

    return found_request


def delete_sponsor_request(request_id):

    requests = _read_all()

    remaining_requests = [r for r in requests if r.get("id") != request_id]

    found = len(remaining_requests) != len(requests)

    if found:
        _write_all(remaining_requests)

    return found
