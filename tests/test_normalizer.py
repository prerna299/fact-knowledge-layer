from app.normalizer import (
    clean_number,
    normalize_value,
    normalize_percentage,
    normalize_text,
    normalize_predicate,
)


def test_clean_number():
    assert clean_number("81,415") == 81415.0
    assert clean_number("8,142.50") == 8142.5
    assert clean_number("24.5%") == 24.5


def test_percentage():
    assert normalize_percentage("24.5%") == 24.5


def test_text_normalization():
    assert normalize_text("Revenue From Services") == "revenue from services"


def test_predicate_normalization():
    assert normalize_predicate("Revenue from services") == "service revenue"


def test_crore_conversion():
    value, unit = normalize_value(
        8142,
        "INR crore"
    )

    assert value == 8142 * 10_000_000
    assert unit == "INR"


def test_million_conversion():
    value, unit = normalize_value(
        81415,
        "INR million"
    )

    assert value == 81415 * 1_000_000
    assert unit == "INR"
from app.matcher import (
    same_subject,
    same_predicate,
    same_time,
    compatible_facts,
    find_candidate_pairs,
)

from app.models import Fact


def create_test_fact(
    fact_id,
    subject,
    predicate,
    value,
    unit,
    year
):
    return Fact(
        id=fact_id,
        subject=subject,
        predicate=predicate,
        value=value,
        unit=unit,
        time={
            "type": "fiscal_year",
            "value": year
        },
        source={
            "document": "test.pdf",
            "page": 1,
            "text": "Test evidence"
        },
        confidence=0.9
    )


def test_same_subject():
    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "service revenue",
        100,
        "INR million",
        "FY2024"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "service revenue",
        200,
        "INR million",
        "FY2024"
    )

    assert same_subject(fact_a, fact_b)


def test_same_predicate():
    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "service revenue",
        100,
        "INR million",
        "FY2024"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "service revenue",
        200,
        "INR crore",
        "FY2024"
    )

    assert same_predicate(fact_a, fact_b)


def test_different_years_are_not_compatible():
    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "service revenue",
        100,
        "INR million",
        "FY2023"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "service revenue",
        200,
        "INR million",
        "FY2024"
    )

    assert not compatible_facts(fact_a, fact_b)


def test_candidate_pairs():
    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "service revenue",
        100,
        "INR million",
        "FY2024"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "service revenue",
        200,
        "INR crore",
        "FY2024"
    )

    fact_c = create_test_fact(
        "c",
        "Amazon",
        "service revenue",
        300,
        "INR million",
        "FY2024"
    )

    pairs = find_candidate_pairs([fact_a, fact_b, fact_c])

    assert len(pairs) == 1
    assert pairs[0][0].id == "a"
    assert pairs[0][1].id == "b"   

from app.reasoning import (
    calculate_relative_difference,
    values_are_equal,
    values_are_similar,
    classify_relationship,
)


def test_relative_difference():

    difference = calculate_relative_difference(
        100,
        110
    )

    assert round(difference, 2) == 0.09


def test_equal_values():

    assert values_are_equal(
        100,
        100
    )


def test_similar_values():

    assert values_are_similar(
        100,
        103
    )


def test_corrobating_facts():

    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "service revenue",
        81415,
        "INR million",
        "FY2024"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "service revenue",
        81415,
        "INR million",
        "FY2024"
    )

    # Normalize values before reasoning
    from app.normalizer import normalize_fact

    fact_a = normalize_fact(fact_a)
    fact_b = normalize_fact(fact_b)

    relationship, confidence, reason = classify_relationship(
        fact_a,
        fact_b
    )

    assert relationship == "CORROBORATES"


def test_contradicting_facts():

    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "service revenue",
        100,
        "INR million",
        "FY2024"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "service revenue",
        200,
        "INR million",
        "FY2024"
    )

    from app.normalizer import normalize_fact

    fact_a = normalize_fact(fact_a)
    fact_b = normalize_fact(fact_b)

    relationship, confidence, reason = classify_relationship(
        fact_a,
        fact_b
    )

    assert relationship == "CONTRADICTS"


def test_rounding_difference():

    fact_a = create_test_fact(
        "a",
        "Delhivery",
        "shipment volume",
        374000,
        "tonnes",
        "FY2021"
    )

    fact_b = create_test_fact(
        "b",
        "Delhivery",
        "shipment volume",
        373854,
        "tonnes",
        "FY2021"
    )

    from app.normalizer import normalize_fact

    fact_a = normalize_fact(fact_a)
    fact_b = normalize_fact(fact_b)

    relationship, confidence, reason = classify_relationship(
        fact_a,
        fact_b
    )

    assert relationship == "RECONCILES"     