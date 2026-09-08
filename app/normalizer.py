import re
from typing import Optional, Tuple


# ---------------------------------------------------------
# NUMBER NORMALIZATION
# ---------------------------------------------------------

def clean_number(value) -> Optional[float]:
    """
    Convert common formatted numbers into a float.

    Examples:
        "81,415"     -> 81415.0
        "8,142.50"   -> 8142.5
        "24.5%"      -> 24.5
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    # Remove commas and spaces
    text = text.replace(",", "").replace(" ", "")

    # Remove percentage sign
    text = text.replace("%", "")

    # Remove common currency symbols
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")

    # Handle parentheses as negative values
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]

    try:
        return float(text)
    except ValueError:
        return None


# ---------------------------------------------------------
# UNIT NORMALIZATION
# ---------------------------------------------------------

UNIT_MULTIPLIERS = {
    "thousand": 1_000,
    "thousands": 1_000,

    "million": 1_000_000,
    "millions": 1_000_000,

    "billion": 1_000_000_000,
    "billions": 1_000_000_000,

    "crore": 10_000_000,
    "crores": 10_000_000,

    "lakh": 100_000,
    "lakhs": 100_000,
}


def normalize_unit(unit: Optional[str]) -> Tuple[Optional[str], float]:
    """
    Convert a unit into a canonical representation.

    Returns:
        (canonical_unit, multiplier)
    """

    if not unit:
        return None, 1.0

    text = unit.lower().strip()

    # INR variants
    if "inr" in text or "₹" in text or "rupee" in text:
        if "crore" in text:
            return "INR", 10_000_000

        if "million" in text:
            return "INR", 1_000_000

        if "billion" in text:
            return "INR", 1_000_000_000

        if "lakh" in text:
            return "INR", 100_000

        return "INR", 1.0

    # Plain numeric units
    for name, multiplier in UNIT_MULTIPLIERS.items():
        if name in text:
            return name.rstrip("s"), multiplier

    return text, 1.0


# ---------------------------------------------------------
# VALUE NORMALIZATION
# ---------------------------------------------------------

def normalize_value(
    value,
    unit: Optional[str] = None
) -> Tuple[Optional[float], Optional[str]]:
    """
    Convert a value + unit into a comparable representation.

    Example:

        81,415 million INR
        ->
        81415000000 INR

        8,142 crore INR
        ->
        81420000000 INR

    These can then be compared numerically.
    """

    number = clean_number(value)

    if number is None:
        return None, None

    canonical_unit, multiplier = normalize_unit(unit)

    normalized_value = number * multiplier

    return normalized_value, canonical_unit


# ---------------------------------------------------------
# PERCENTAGE NORMALIZATION
# ---------------------------------------------------------

def normalize_percentage(value) -> Optional[float]:
    """
    Normalize percentage values.

    Example:
        "24.5%" -> 24.5
        "24.5"  -> 24.5
    """

    number = clean_number(value)

    if number is None:
        return None

    return number


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

def normalize_text(text: Optional[str]) -> str:
    """
    Normalize text for fact matching.

    This does NOT change the meaning of the text.
    """

    if not text:
        return ""

    text = text.lower().strip()

    # Replace punctuation with spaces
    text = re.sub(r"[^a-z0-9%₹.\-/ ]+", " ", text)

    # Collapse repeated spaces
    text = re.sub(r"\s+", " ", text)

    return text


# ---------------------------------------------------------
# PREDICATE NORMALIZATION
# ---------------------------------------------------------

def normalize_predicate(predicate: Optional[str]) -> str:
    """
    Convert slightly different descriptions of the same metric
    into a consistent textual representation.

    This is intentionally generic and does not contain
    document-specific rules.
    """

    if not predicate:
        return ""

    text = normalize_text(predicate)

    # Common linguistic variations
    replacements = {
        "revenue from services": "service revenue",
        "revenue from service": "service revenue",
        "services revenue": "service revenue",

        "number of shipments": "shipment volume",
        "shipments": "shipment volume",

        "market share": "market share",

        "profit after tax": "pat",
        "profit after taxes": "pat",

        "earnings before interest tax depreciation and amortization":
            "ebitda",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ---------------------------------------------------------
# FACT NORMALIZATION
# ---------------------------------------------------------

def normalize_fact(fact):
    """
    Normalize a Fact object in-place.

    Returns the same Fact object with:
        normalized_value
        normalized_unit
        normalized predicate
    populated.
    """

    # Normalize predicate
    fact.predicate = normalize_predicate(fact.predicate)

    # Normalize numerical value
    if fact.value is not None:
        normalized_value, normalized_unit = normalize_value(
            fact.value,
            fact.unit
        )

        fact.normalized_value = normalized_value
        fact.normalized_unit = normalized_unit

    return fact