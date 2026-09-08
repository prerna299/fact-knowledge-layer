from app.pipeline import process_documents


if __name__ == "__main__":

    pdf_paths = [
        "data/01-delhivery-prospectus-2022-excerpt.pdf",
        "data/02-delhivery-annual-report-fy24-excerpt.pdf",
    ]

    result = process_documents(pdf_paths)

    print("\n========================================")
    print("DOCUMENT PROCESSING")
    print("========================================")

    for document in result["documents"]:
        print(
            f"{document['document']} "
            f"→ {document['pages_processed']} pages "
            f"→ {len(document['facts'])} facts"
        )

    print("\n========================================")
    print("EXTRACTED FACTS")
    print("========================================")

    for fact in result["facts"]:

        print("\n----------------------------------------")

        print("ID:", fact.id)
        print("Subject:", fact.subject)
        print("Predicate:", fact.predicate)
        print("Value:", fact.value)
        print("Unit:", fact.unit)
        print("Normalized Value:", fact.normalized_value)
        print("Normalized Unit:", fact.normalized_unit)

        if fact.time:
            print("Time:", fact.time.value)

        print("Scope:", fact.scope)

        print("Evidence:", fact.source.text)

        print("Confidence:", fact.confidence)

    print("\n========================================")
    print("RELATIONSHIPS")
    print("========================================")

    for relationship in result["relationships"]:

        print("\n----------------------------------------")

        print("Relationship:", relationship.relationship)
        print("Confidence:", relationship.confidence)
        print("Reason:", relationship.reason)
        print("Fact A:", relationship.fact_a)
        print("Fact B:", relationship.fact_b)