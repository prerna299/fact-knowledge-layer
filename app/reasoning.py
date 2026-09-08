from typing import List, Tuple
from app.models import Fact, FactRelationship


# Very small differences can come from rounding in reports.
ROUNDING_TOLERANCE = 0.00001

# Differences up to 5% may be explainable by reporting precision,
# rounding, or minor contextual differences.
RELATIVE_DIFFERENCE_THRESHOLD = 0.05


def calculate_relative_difference(value_a: float, value_b: float) -> float:
    denominator = max(abs(value_a), abs(value_b), 1e-9)
    return abs(value_a - value_b) / denominator


def values_are_equal(value_a: float, value_b: float) -> bool:
    if value_a is None or value_b is None:
        return False

    difference = calculate_relative_difference(value_a, value_b)

    return difference <= ROUNDING_TOLERANCE


def values_are_similar(value_a: float, value_b: float) -> bool:
    if value_a is None or value_b is None:
        return False

    difference = calculate_relative_difference(value_a, value_b)

    return difference <= RELATIVE_DIFFERENCE_THRESHOLD


def get_time_value(fact: Fact):
    if not fact.time:
        return None

    return fact.time.value


def same_time_context(fact_a: Fact, fact_b: Fact) -> bool:
    time_a = get_time_value(fact_a)
    time_b = get_time_value(fact_b)

    if not time_a or not time_b:
        return False

    return time_a.lower().strip() == time_b.lower().strip()


def same_scope(fact_a: Fact, fact_b: Fact) -> bool:
    scope_a = (fact_a.scope or "").strip().lower()
    scope_b = (fact_b.scope or "").strip().lower()

    # If scope is missing from either fact, don't assume they are different.
    if not scope_a or not scope_b:
        return True

    return scope_a == scope_b


def classify_relationship(
    fact_a: Fact,
    fact_b: Fact
) -> Tuple[str, float, str]:

    value_a = fact_a.normalized_value
    value_b = fact_b.normalized_value

    # --------------------------------------------------
    # CASE 1: Cannot compare numerically
    # --------------------------------------------------

    if value_a is None or value_b is None:

        if same_time_context(fact_a, fact_b):
            return (
                "UNCERTAIN",
                0.50,
                "The facts refer to the same metric and period, "
                "but one or both values could not be normalized numerically."
            )

        return (
            "UNCERTAIN",
            0.40,
            "The facts could not be compared reliably because "
            "numerical values or comparable time context are missing."
        )

    # --------------------------------------------------
    # CASE 2: Values are effectively identical
    # --------------------------------------------------

    if values_are_equal(value_a, value_b):

        return (
            "CORROBORATES",
            0.98,
            "The normalized values are effectively identical. "
            "The facts therefore corroborate each other."
        )

    # --------------------------------------------------
    # CASE 3: Values are close but not identical
    # --------------------------------------------------

    if values_are_similar(value_a, value_b):

        difference = calculate_relative_difference(
            value_a,
            value_b
        )

        return (
            "RECONCILES",
            0.90,
            f"The normalized values differ by approximately "
            f"{difference * 100:.2f}%, which is small enough to be "
            f"explained by rounding or reporting precision."
        )

    # --------------------------------------------------
    # CASE 4: Different time context
    # --------------------------------------------------

    if not same_time_context(fact_a, fact_b):

        return (
            "RECONCILES",
            0.85,
            "The values differ, but the facts refer to different "
            "or incompletely specified reporting periods. "
            "The difference may therefore be explained by time context."
        )

    # --------------------------------------------------
    # CASE 5: Different scope
    # --------------------------------------------------

    if not same_scope(fact_a, fact_b):

        return (
            "RECONCILES",
            0.85,
            "The values differ, but the facts have different scopes "
            "or contexts. They should not be treated as a direct contradiction."
        )

    # --------------------------------------------------
    # CASE 6: Genuine contradiction
    # --------------------------------------------------

    difference = calculate_relative_difference(
        value_a,
        value_b
    )

    return (
        "CONTRADICTS",
        0.90,
        f"The facts describe the same metric in the same context, "
        f"but their normalized values differ substantially by "
        f"approximately {difference * 100:.2f}%."
    )


def create_relationship(
    fact_a: Fact,
    fact_b: Fact
) -> FactRelationship:

    relationship, confidence, reason = classify_relationship(
        fact_a,
        fact_b
    )

    return FactRelationship(
        id=f"relationship_{fact_a.id}_{fact_b.id}",
        fact_a=fact_a.id,
        fact_b=fact_b.id,
        relationship=relationship,
        confidence=confidence,
        reason=reason
    )


def analyze_pairs(
    pairs: List[Tuple[Fact, Fact]]
) -> List[FactRelationship]:

    relationships = []

    for fact_a, fact_b in pairs:

        relationship = create_relationship(
            fact_a,
            fact_b
        )

        relationships.append(relationship)

    return relationships