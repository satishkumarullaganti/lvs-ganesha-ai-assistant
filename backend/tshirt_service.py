"""
T-shirt / Kurti pre-booking price setting.
JSON-file backed, same lightweight pattern as announcement_service.py -
lets the committee change either price from the admin panel, without
touching any code or restarting the server.

Kurti price starts as None ("yet to get" / to be announced) until
the committee sets it - orders can still be placed, the amount is
simply confirmed later.
"""
import json
import os

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tshirt_settings.json")

DEFAULT_TSHIRT_PRICE = 380
DEFAULT_KURTI_PRICE = None


def _read_settings():

    if not os.path.exists(_SETTINGS_PATH):
        return {}

    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError, TypeError):
        return {}


def _write_settings(data):

    os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)

    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_price():
    """T-shirt price - kept as the original function name/behaviour
    other modules already import."""

    data = _read_settings()

    # Older settings files only ever had a single "price" key for
    # the T-shirt - treat that as the T-shirt price if present.
    if "tshirt_price" in data:
        try:
            return float(data["tshirt_price"])
        except (ValueError, TypeError):
            return DEFAULT_TSHIRT_PRICE

    if "price" in data:
        try:
            return float(data["price"])
        except (ValueError, TypeError):
            return DEFAULT_TSHIRT_PRICE

    return DEFAULT_TSHIRT_PRICE


def set_price(new_price):

    data = _read_settings()
    data["tshirt_price"] = float(new_price)
    data.pop("price", None)
    _write_settings(data)

    return float(new_price)


def get_kurti_price():
    """Returns None if the committee hasn't set a Kurti price yet."""

    data = _read_settings()

    if "kurti_price" not in data or data["kurti_price"] is None:
        return DEFAULT_KURTI_PRICE

    try:
        return float(data["kurti_price"])
    except (ValueError, TypeError):
        return DEFAULT_KURTI_PRICE


def set_kurti_price(new_price):

    data = _read_settings()
    data["kurti_price"] = float(new_price)
    _write_settings(data)

    return float(new_price)
