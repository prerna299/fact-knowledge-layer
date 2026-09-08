from pathlib import Path
from typing import List, Dict, Any

from app.pdf_extractor import extract_pdf_pages
from app.fact_extractor import extract_facts_locally
from app.normalizer import normalize_fact
from app.matcher import find_candidate_pairs
from app.reasoning import analyze_pairs


# Words that strongly suggest a page contains useful facts.
# These are generic document concepts, NOT document-specific rules.
FACT_KEYWORDS = {
    "revenue",
    "income",
    "profit",
    "loss",
    "ebitda",
    "margin",
    "growth",
    "volume",
    "shipment",
    "shipments",
    "tonnes",
    "tons",
    "customers",
    "customer",
    "market share",
    "market",
    "pin codes",
    "facilities",
    "employees",
    "team members",
    "countries",
    "million",
    "billion",
    "crore",
    "lakh",
    "%",
    "fy20",
    "fy21",
    "fy22",
    "fy23",
    "fy24",
    "fy2020",
    "fy2021",
    "fy2022",
    "fy2023",
    "fy2024",
}


def is_relevant_page(text: str) -> bool:
    """
    Determine whether a PDF page is likely to contain
    meaningful comparable facts.

    This is a generic heuristic used only to reduce
    unnecessary LLM calls.
    """

    if not text:
        return False

    text_lower = text.lower()

    # Require at least one number.
    contains_number = any(
        character.isdigit()
        for character in text
    )

    if not contains_number:
        return False

    # Check for meaningful fact-related terminology.
    keyword_matches = sum(
        1
        for keyword in FACT_KEYWORDS
        if keyword in text_lower
    )

    return keyword_matches >= 1


def process_pdf(pdf_path: str) -> Dict[str, Any]:

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    document_name = pdf_path.name

    pages = extract_pdf_pages(
        str(pdf_path)
    )

    all_facts = []

    pages_considered = 0
    pages_sent_to_llm = 0

    for page in pages:

        pages_considered += 1

        page_number = page["page"]
        page_text = page["text"]

        # Local filtering BEFORE Gemini.
        if not is_relevant_page(page_text):

            print(
                f"→ Skipping page {page_number}: "
                f"not fact-relevant"
            )

            continue

        pages_sent_to_llm += 1

        page_facts = extract_facts_locally(
            text=page_text,
            document_name=document_name,
            page_number=page_number
        )

        for fact in page_facts:

            fact = normalize_fact(fact)

            all_facts.append(fact)

    return {
        "document": document_name,
        "pages_processed": pages_considered,
        "pages_sent_to_llm": pages_sent_to_llm,
        "facts": all_facts
    }


def process_documents(
    pdf_paths: List[str]
) -> Dict[str, Any]:

    all_facts = []
    document_results = []

    for pdf_path in pdf_paths:

        result = process_pdf(pdf_path)

        document_results.append(result)

        all_facts.extend(
            result["facts"]
        )

    # Find potentially related facts.
    candidate_pairs = find_candidate_pairs(
        all_facts
    )

    # Determine whether each pair corroborates,
    # contradicts, reconciles, or remains uncertain.
    relationships = analyze_pairs(
        candidate_pairs
    )

    return {
        "documents": document_results,
        "facts": all_facts,
        "candidate_pairs": candidate_pairs,
        "relationships": relationships
    }