"""The output contract for the triage feature.

Two views of the same contract:
- TRIAGE_JSON_SCHEMA is sent to the API, which then guarantees the reply is JSON of this shape.
- Triage is the Pydantic model we validate the reply against on our side.

A schema guarantees shape. It says nothing about whether the values are right.
That gap is what the eval suite measures.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Category = Literal["billing", "bug", "account_access", "how_to", "feature_request", "other"]
Urgency = Literal["high", "medium", "low"]

CATEGORIES: tuple[str, ...] = ("billing", "bug", "account_access", "how_to", "feature_request", "other")
URGENCIES: tuple[str, ...] = ("high", "medium", "low")


class Triage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Category
    urgency: Urgency
    refund_requested: bool
    invoice_id: str | None
    summary: str


TRIAGE_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "urgency": {"type": "string", "enum": list(URGENCIES)},
        "refund_requested": {"type": "boolean"},
        "invoice_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "summary": {"type": "string"},
    },
    "required": ["category", "urgency", "refund_requested", "invoice_id", "summary"],
    "additionalProperties": False,
}
