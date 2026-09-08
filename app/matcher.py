from typing import List, Tuple

from app.models import Fact
from app.normalizer import normalize_text


def same_subject(fact_a: Fact, fact_b: Fact) -> bool:
    """
    Check whether two facts refer to the same subject.

    Example:
        Delhivery and Delhivery -> True
        Delhivery and Amazon -> False
    """

    subject_a = normalize_text(fact_a.subject)
    subject_b = normalize_text(fact_b.subject)

    if not subject_a or not subject_b:
        return False

    return subject_a == subject_b


def same_predicate(fact_a: Fact, fact_b: Fact) -> bool:
    """
    Check whether two facts measure the same metric.
    """

    predicate_a = normalize_text(fact_a.predicate)
    predicate_b = normalize_text(fact_b.predicate)

    if not predicate_a or not predicate_b:
        return False

    return predicate_a == predicate_b


def same_time(fact_a: Fact, fact_b: Fact) -> bool:
    """
    Check whether two facts refer to the same reporting period.

    If time information is missing, we do not reject the pair.
    Missing context will be handled later by the reasoning layer.
    """

    if not fact_a.time or not fact_b.time:
        return True

    time_a = fact_a.time.value
    time_b = fact_b.time.value

    if not time_a or not time_b:
        return True

    return normalize_text(time_a) == normalize_text(time_b)


def compatible_facts(fact_a: Fact, fact_b: Fact) -> bool:
    """
    Determine whether two facts are suitable candidates
    for comparison.

    This is intentionally generic:
    no document names, filenames, or fixed metrics are used.
    """

    if fact_a.id == fact_b.id:
        return False

    if not same_subject(fact_a, fact_b):
        return False

    if not same_predicate(fact_a, fact_b):
        return False

    if not same_time(fact_a, fact_b):
        return False

    return True


def find_candidate_pairs(
    facts: List[Fact]
) -> List[Tuple[Fact, Fact]]:
    """
    Find all pairs of facts that may describe the same thing.

    Each pair is returned only once.
    """

    pairs = []

    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):
            fact_a = facts[i]
            fact_b = facts[j]

            if compatible_facts(fact_a, fact_b):
                pairs.append((fact_a, fact_b))

    return pairs