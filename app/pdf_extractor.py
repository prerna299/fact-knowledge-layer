import pymupdf
from pathlib import Path


def extract_pdf_pages(pdf_path: str):
    """
    Extract text from every page while preserving page numbers.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text")

        if not text.strip():
            continue

        pages.append(
            {
                "page": page_number,
                "text": text.strip(),
            }
        )

    document.close()

    return pages


def extract_pdf_text(pdf_path: str):
    """
    Return complete PDF text with page markers.
    """

    pages = extract_pdf_pages(pdf_path)

    sections = []

    for page in pages:

        sections.append(
            f"\n--- PAGE {page['page']} ---\n"
            f"{page['text']}"
        )

    return "\n".join(sections)