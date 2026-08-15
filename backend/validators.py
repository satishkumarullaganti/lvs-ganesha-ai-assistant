# ============================================
# Flat Number Validator
# ============================================

SOUTH_RANGES = [
    (1, 22),
    (101, 122),
    (201, 222),
    (301, 322),
]

NORTH_RANGES = [
    (1, 8),
    (101, 108),
    (201, 208),
    (301, 308),
]

# Terrace flats don't follow the numeric North/South pattern -
# they're an exact, small set of named units (T1, T2, T3).
TERRACE_FLATS = {
    "T1",
    "T2",
    "T3",
}

BLOCK_RANGES = {
    "SOUTH": SOUTH_RANGES,
    "NORTH": NORTH_RANGES,
}


def _normalize_flat_number(flat_number: str):
    if flat_number is None:
        return None

    cleaned = str(flat_number).strip()

    # Flat numbers must be exactly 3 digits.
    if len(cleaned) != 3:
        return None

    if not cleaned.isdigit():
        return None

    return int(cleaned)


def _is_in_ranges(flat_int: int, ranges):
    for low, high in ranges:
        if low <= flat_int <= high:
            return True

    return False


def _normalize_terrace_flat(flat_number: str):
    if flat_number is None:
        return None

    cleaned = (
        str(flat_number)
        .strip()
        .upper()
        .replace("-", "")
        .replace(" ", "")
        .replace("TERRACE", "")
        .replace("BLOCK", "")
        .strip()
    )

    return cleaned


def validate_flat_number(block: str, flat_number: str) -> bool:

    if not block:
        return False

    block_key = str(block).strip().upper()

    if block_key == "TERRACE":

        cleaned = _normalize_terrace_flat(flat_number)

        return cleaned in TERRACE_FLATS

    if block_key not in BLOCK_RANGES:
        return False

    flat_int = _normalize_flat_number(flat_number)

    if flat_int is None:
        return False

    return _is_in_ranges(
        flat_int,
        BLOCK_RANGES[block_key]
    )


def validate_flat_number_any_block(flat_number: str) -> bool:

    # Check Terrace's exact-match set first
    if _normalize_terrace_flat(flat_number) in TERRACE_FLATS:
        return True

    flat_int = _normalize_flat_number(flat_number)

    if flat_int is None:
        return False

    for ranges in BLOCK_RANGES.values():

        if _is_in_ranges(flat_int, ranges):
            return True

    return False


# ============================================
# Mobile Number Validator
# ============================================
# Shared by every registration endpoint (competition,
# cultural, volunteer) so server-side validation is
# consistent everywhere, not just relying on client-side
# JS (which can be bypassed or have gaps).

def validate_mobile_number(mobile: str) -> bool:

    if not mobile:
        return False

    cleaned = str(mobile).strip()

    return cleaned.isdigit() and len(cleaned) == 10