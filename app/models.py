from pydantic import BaseModel, Field
from typing import Optional, Literal


class TimeContext(BaseModel):
    type: Optional[str] = None
    value: Optional[str] = None


class SourceEvidence(BaseModel):
    document: str
    page: int
    text: str


class Fact(BaseModel):
    id: str

    subject: str
    predicate: str

    value: Optional[float] = None
    value_text: Optional[str] = None

    unit: Optional[str] = None

    normalized_value: Optional[float] = None
    normalized_unit: Optional[str] = None

    time: Optional[TimeContext] = None

    scope: Optional[str] = None

    source: SourceEvidence

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )


class FactRelationship(BaseModel):
    id: str

    fact_a: str
    fact_b: str

    relationship: Literal[
        "CORROBORATES",
        "CONTRADICTS",
        "RECONCILES",
        "UNCERTAIN"
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    reason: str