import os
import json
import uuid
import re

from dotenv import load_dotenv
from google import genai

from app.models import Fact


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini is kept as an optional extractor.
# Our current pipeline uses the local extractor so that
# development does not consume Gemini quota.
client = None

if API_KEY:
    client = genai.Client(api_key=API_KEY)


# ============================================================
# GEMINI FACT EXTRACTION PROMPT
# ============================================================

FACT_EXTRACTION_PROMPT = """
You are a fact extraction system.

Extract meaningful factual statements from the provided document page.

Focus especially on:

- numerical facts
- financial metrics
- operational metrics
- percentages
- counts
- dates
- growth rates
- volumes
- market/share information
- company/business facts that can be compared across documents

Do NOT invent information.

Every extracted fact MUST be directly supported by text in the
provided document.

For every fact return:

subject:
The entity the fact is about.

predicate:
A normalized description of what is being measured.

value:
Numerical value if one exists. Otherwise null.

value_text:
Original textual representation of the value.

unit:
The original unit, if applicable.

time_type:
Examples: fiscal_year, calendar_year, quarter, date, period,
or null.

time_value:
The corresponding period, for example FY2024, Q4 FY2024, etc.

scope:
Any important scope/context such as geography, business segment,
customer category, consolidated/standalone, etc.

evidence:
An exact or near-exact excerpt from the supplied text that supports
the fact.

confidence:
A number between 0 and 1.

IMPORTANT:

- Never fabricate evidence.
- Do not combine unrelated numbers.
- Preserve the meaning and scope of the source.
- If a table contains multiple metrics, make sure each value is
  associated with the correct metric.
- If the page is ambiguous, lower the confidence.
- Return ONLY valid JSON.
- Return an empty array if there are no meaningful facts.

JSON format:

[
  {
    "subject": "...",
    "predicate": "...",
    "value": 123.45,
    "value_text": "...",
    "unit": "...",
    "time_type": "...",
    "time_value": "...",
    "scope": "...",
    "evidence": "...",
    "confidence": 0.95
  }
]
"""


# ============================================================
# GEMINI EXTRACTION
# ============================================================

def extract_facts_from_page(
    text: str,
    document_name: str,
    page_number: int
):
    """
    Extract structured facts from one PDF page using Gemini.

    This function is optional. The current development pipeline
    uses extract_facts_locally() so that Gemini quota is not consumed.
    """

    if not text or len(text.strip()) < 100:
        print(
            f"→ Skipping {document_name} | "
            f"page {page_number} | insufficient text"
        )
        return []

    if client is None:
        print(
            "⚠ Gemini API key is not configured. "
            "Using local extraction instead."
        )

        return extract_facts_locally(
            text=text,
            document_name=document_name,
            page_number=page_number
        )

    prompt = f"""
{FACT_EXTRACTION_PROMPT}

DOCUMENT:
{document_name}

PAGE NUMBER:
{page_number}

PAGE TEXT:
{text}
"""

    print(
        f"Processing {document_name} | "
        f"page {page_number}"
    )

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if not response.text:
            print(
                f"⚠ Empty Gemini response on "
                f"page {page_number}"
            )

            return []

        raw_output = response.text.strip()

        # Remove markdown code fences if Gemini returns them.
        if raw_output.startswith("```"):

            raw_output = raw_output.replace(
                "```json",
                ""
            )

            raw_output = raw_output.replace(
                "```",
                ""
            )

            raw_output = raw_output.strip()

        try:

            extracted = json.loads(
                raw_output
            )

        except json.JSONDecodeError:

            print(
                f"⚠ Gemini returned invalid JSON "
                f"for page {page_number}"
            )

            return []

        if not isinstance(extracted, list):

            print(
                f"⚠ Unexpected Gemini response format "
                f"on page {page_number}"
            )

            return []

        facts = []

        for item in extracted:

            try:

                fact = Fact(
                    id=f"fact_{uuid.uuid4().hex[:10]}",

                    subject=item.get(
                        "subject",
                        "Unknown"
                    ),

                    predicate=item.get(
                        "predicate",
                        "Unknown"
                    ),

                    value=item.get(
                        "value"
                    ),

                    value_text=item.get(
                        "value_text"
                    ),

                    unit=item.get(
                        "unit"
                    ),

                    time={
                        "type": item.get(
                            "time_type"
                        ),
                        "value": item.get(
                            "time_value"
                        )
                    },

                    scope=item.get(
                        "scope"
                    ),

                    source={
                        "document": document_name,
                        "page": page_number,
                        "text": item.get(
                            "evidence",
                            ""
                        )
                    },

                    confidence=float(
                        item.get(
                            "confidence",
                            0.5
                        )
                    )
                )

                facts.append(fact)

            except Exception as error:

                print(
                    f"⚠ Could not validate "
                    f"fact on page {page_number}: "
                    f"{error}"
                )

        print(
            f"✓ Page {page_number}: "
            f"{len(facts)} facts extracted"
        )

        return facts

    except Exception as error:

        print(
            f"✗ Gemini request failed on "
            f"{document_name} | "
            f"page {page_number}"
        )

        print(
            f"  Error: {error}"
        )

        return []


# ============================================================
# LOCAL FACT EXTRACTION
# ============================================================

def extract_facts_locally(
    text: str,
    document_name: str,
    page_number: int
):
    """
    Lightweight local fact extraction fallback.

    Extracts numerical statements directly from PDF text
    without requiring an LLM/API call.

    This is intentionally generic and does not contain
    document-specific facts.
    """

    facts = []

    if not text:
        return facts

    # --------------------------------------------------------
    # Split PDF text into meaningful lines
    # --------------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # --------------------------------------------------------
    # Generic numerical pattern
    # --------------------------------------------------------

    number_pattern = re.compile(
        r"""
        (?<!\w)
        \(?
        -?
        \d[\d,]*(?:\.\d+)?
        %?
        \)?
        (?:\s*
            (?:million|millions|
               billion|billions|
               thousand|thousands|
               crore|crores|
               lakh|lakhs|
               tonnes|tons|
               km|bn|mn)
        )?
        """,
        re.IGNORECASE | re.VERBOSE
    )

    # --------------------------------------------------------
    # Generic metric vocabulary
    # --------------------------------------------------------

    metric_patterns = [

        ("profit after tax", "pat"),

        ("profit after taxes", "pat"),

        ("pat", "pat"),

        ("revenue from services", "service revenue"),

        ("revenue from service", "service revenue"),

        ("revenue", "revenue"),

        ("income", "income"),

        ("ebitda margin", "ebitda margin"),

        ("ebitda", "ebitda"),

        ("market share", "market share"),

        ("shipments", "shipment volume"),

        ("shipment", "shipment volume"),

        ("tonnes", "volume"),

        ("tons", "volume"),

        ("customers", "customer count"),

        ("customer", "customer count"),

        ("pin codes", "pin code coverage"),

        ("facilities", "facility count"),

        ("countries", "country coverage"),

        ("employees", "employee count"),

        ("team members", "employee count"),

        ("growth", "growth"),

        ("margin", "margin"),

        ("volume", "volume"),
    ]

    # --------------------------------------------------------
    # Process each line
    # --------------------------------------------------------

    for line in lines:

        line_lower = line.lower()

        predicate = None

        # Find the first relevant metric.
        for keyword, normalized_predicate in metric_patterns:

            if keyword in line_lower:

                predicate = normalized_predicate

                break

        if predicate is None:
            continue

        # Find numbers associated with this line.
        matches = list(
            number_pattern.finditer(line)
        )

        if not matches:
            continue

        # ----------------------------------------------------
        # Extract every number from the metric line
        # ----------------------------------------------------

        for match in matches:

            raw_value = match.group(0).strip()

            cleaned_number = (
                raw_value
                .replace(",", "")
                .replace("%", "")
                .replace("(", "")
                .replace(")", "")
            )

            number_match = re.search(
                r"-?\d+(?:\.\d+)?",
                cleaned_number
            )

            if not number_match:
                continue

            try:

                value = float(
                    number_match.group()
                )

            except ValueError:

                continue

            # ------------------------------------------------
            # Detect unit
            # ------------------------------------------------

            unit = None

            unit_match = re.search(
                r"""
                (million|millions|
                 billion|billions|
                 thousand|thousands|
                 crore|crores|
                 lakh|lakhs|
                 tonnes|tons|
                 km|bn|mn)
                """,
                raw_value,
                re.IGNORECASE | re.VERBOSE
            )

            if unit_match:

                unit = unit_match.group(1)

            if "%" in raw_value:

                unit = "%"

            # ------------------------------------------------
            # Determine subject
            # ------------------------------------------------

            subject = "Document metric"

            if "delhivery" in line_lower:

                subject = "Delhivery"

            # ------------------------------------------------
            # Detect fiscal year
            # ------------------------------------------------

            time_value = None
            time_type = None

            time_match = re.search(
                r"\bFY\s?20\d{2}\b",
                line,
                re.IGNORECASE
            )

            if time_match:

                time_value = (
                    time_match
                    .group(0)
                    .upper()
                    .replace(" ", "")
                )

                time_type = "fiscal_year"

            # ------------------------------------------------
            # Detect short FY notation
            # Example: FY24
            # ------------------------------------------------

            short_fy_match = re.search(
                r"\bFY\s?(\d{2})\b",
                line,
                re.IGNORECASE
            )

            if (
                short_fy_match
                and time_value is None
            ):

                year = short_fy_match.group(1)

                time_value = (
                    "FY20" + year
                )

                time_type = "fiscal_year"

            # ------------------------------------------------
            # Detect quarter
            # ------------------------------------------------

            quarter_match = re.search(
                r"\bQ[1-4]\s*(?:FY\s*)?20\d{2}\b",
                line,
                re.IGNORECASE
            )

            if quarter_match:

                time_value = (
                    quarter_match
                    .group(0)
                    .upper()
                    .replace(" ", "")
                )

                time_type = "quarter"

            # ------------------------------------------------
            # Create structured Fact
            # ------------------------------------------------

            fact = Fact(

                id=(
                    f"fact_"
                    f"{uuid.uuid4().hex[:10]}"
                ),

                subject=subject,

                predicate=predicate,

                value=value,

                value_text=raw_value,

                unit=unit,

                time={
                    "type": time_type,
                    "value": time_value
                },

                scope=None,

                source={
                    "document": document_name,
                    "page": page_number,
                    "text": line
                },

                # Local extraction has lower confidence
                # than LLM-based extraction.
                confidence=0.60
            )

            facts.append(fact)

    print(
        f"✓ Local extraction | "
        f"page {page_number}: "
        f"{len(facts)} facts"
    )

    return facts