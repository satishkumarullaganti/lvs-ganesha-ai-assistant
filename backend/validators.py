# ============================================
# Flat Number Validator
# ============================================
# Validates that a given block + flat number
# combination is a real unit in LVS Excellency.
#
# South Block: 001-022, 101-122, 201-222, 301-322
# North Block: 001-008, 101-108, 201-208, 301-308
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

BLOCK_RANGES = {
    "SOUTH": SOUTH_RANGES,
    "NORTH": NORTH_RANGES,
}


def _normalize_flat_number(flat_number: str):
    """
    Converts input like '5', '05', ' 105 ' into an integer.
    Returns None if it isn't a valid number at all.
    """
    if flat_number is None:
        return None

    cleaned = flat_number.strip()

    if not cleaned.isdigit():
        return None

    return int(cleaned)


def _is_in_ranges(flat_int: int, ranges):
    for low, high in ranges:
        if low <= flat_int <= high:
            return True
    return False


def validate_flat_number(block: str, flat_number: str) -> bool:
    """
    Validates a flat number against a specific block's known ranges.
    block: "South" or "North" (case-insensitive)
    flat_number: raw string input from user, e.g. "105", "5", "022"
    Returns True if valid, False otherwise.
    """

    if not block:
        return False

    block_key = block.strip().upper()

    if block_key not in BLOCK_RANGES:
        return False

    flat_int = _normalize_flat_number(flat_number)

    if flat_int is None:
        return False

    return _is_in_ranges(flat_int, BLOCK_RANGES[block_key])


def validate_flat_number_any_block(flat_number: str) -> bool:
    """
    Looser check used where block isn't collected (e.g. donation flow).
    Returns True if the flat number is valid in ANY block's ranges.
    """

    flat_int = _normalize_flat_number(flat_number)

    if flat_int is None:
        return False

    for ranges in BLOCK_RANGES.values():
        if _is_in_ranges(flat_int, ranges):
            return True

    return False    