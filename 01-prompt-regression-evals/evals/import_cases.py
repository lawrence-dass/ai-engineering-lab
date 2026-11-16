"""Turns a spreadsheet of test cases into the JSON Lines file the suite reads.

    uv run python -m evals.import_cases cases/heldout.csv cases/heldout.jsonl

Someone who does not write code adds cases in a spreadsheet with the columns
id, tags, ticket, category, urgency, refund_requested, invoice_id. This checks
every row against the same rules the suite uses and writes nothing unless all
rows pass, so a typo cannot slip into the test set.
"""

import argparse
import csv
import json
import re
from pathlib import Path

from evals.cases import validate

COLUMNS = ["id", "tags", "ticket", "category", "urgency", "refund_requested", "invoice_id"]


def parse_bool(value: str, where: str) -> bool:
    cleaned = value.strip().lower()
    if cleaned in {"true", "yes", "1"}:
        return True
    if cleaned in {"false", "no", "0"}:
        return False
    raise ValueError(f"{where}: refund_requested must be TRUE or FALSE, got {value!r}")


def row_to_case(row: dict, line_no: int) -> dict:
    where = f"row {line_no} ({row.get('id') or 'no id'})"
    case = {
        "id": row["id"].strip(),
        "tags": [tag.strip() for tag in re.split(r"[;,]", row["tags"]) if tag.strip()],
        "ticket": row["ticket"].strip(),
        "expected": {
            "category": row["category"].strip().lower(),
            "urgency": row["urgency"].strip().lower(),
            "refund_requested": parse_bool(row["refund_requested"], where),
            "invoice_id": row["invoice_id"].strip().upper() or None,
        },
    }
    validate(case, line_no)
    return case


def import_cases(source: Path) -> tuple[list[dict], list[str]]:
    """Returns (cases, problems). Rows with only an id are skipped as unfilled."""
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [], [f"missing columns: {', '.join(missing)}"]
        cases, problems = [], []
        for line_no, row in enumerate(reader, start=2):
            if not any((row.get(column) or "").strip() for column in COLUMNS[1:]):
                continue
            try:
                cases.append(row_to_case({k: row.get(k) or "" for k in COLUMNS}, line_no))
            except ValueError as exc:
                problems.append(str(exc))
    ids = [case["id"] for case in cases]
    problems += [f"duplicate id {case_id!r}" for case_id in sorted({i for i in ids if ids.count(i) > 1})]
    return cases, problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    cases, problems = import_cases(args.source)
    if problems:
        raise SystemExit("Nothing written. Fix these rows first:\n  " + "\n  ".join(problems))
    args.target.write_text("".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases))
    print(f"wrote {len(cases)} cases to {args.target}")


if __name__ == "__main__":
    main()
