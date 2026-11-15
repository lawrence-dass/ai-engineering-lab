"""Loads and validates the test cases.

A broken case file produces wrong scores without any error, so every load
checks the file: unique ids, known labels, well-formed invoice ids.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from triage.schema import CATEGORIES, URGENCIES

CASES_PATH = Path(__file__).resolve().parent.parent / "cases" / "tickets.jsonl"
INVOICE_RE = re.compile(r"^INV-\d{6}$")
EXPECTED_KEYS = {"category", "urgency", "refund_requested", "invoice_id"}


@dataclass(frozen=True)
class Case:
    id: str
    tags: tuple[str, ...]
    ticket: str
    expected: dict


def validate(raw: dict, line_no: int) -> None:
    where = f"line {line_no} ({raw.get('id', 'no id')})"
    for key in ("id", "tags", "ticket", "expected"):
        if key not in raw:
            raise ValueError(f"{where}: missing '{key}'")
    if not raw["tags"]:
        raise ValueError(f"{where}: needs at least one tag")
    if not raw["ticket"].strip():
        raise ValueError(f"{where}: empty ticket")
    expected = raw["expected"]
    if set(expected) != EXPECTED_KEYS:
        raise ValueError(f"{where}: expected keys must be {sorted(EXPECTED_KEYS)}")
    if expected["category"] not in CATEGORIES:
        raise ValueError(f"{where}: unknown category {expected['category']!r}")
    if expected["urgency"] not in URGENCIES:
        raise ValueError(f"{where}: unknown urgency {expected['urgency']!r}")
    if not isinstance(expected["refund_requested"], bool):
        raise ValueError(f"{where}: refund_requested must be true or false")
    invoice = expected["invoice_id"]
    if invoice is not None and not INVOICE_RE.match(invoice):
        raise ValueError(f"{where}: invoice_id must look like INV-204817 or be null")


def load_cases(path: Path = CASES_PATH) -> list[Case]:
    cases: list[Case] = []
    seen: set[str] = set()
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        validate(raw, line_no)
        if raw["id"] in seen:
            raise ValueError(f"line {line_no}: duplicate id {raw['id']!r}")
        seen.add(raw["id"])
        cases.append(Case(raw["id"], tuple(raw["tags"]), raw["ticket"], raw["expected"]))
    return cases
