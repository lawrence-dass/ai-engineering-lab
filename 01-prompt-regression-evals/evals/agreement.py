"""Measures how often a second person's labels match the expected answers.

    uv run python -m evals.agreement --template        # writes labels/blind.jsonl with the answers blanked
    uv run python -m evals.agreement                   # compares the filled-in file with the expected answers

If two people label the same ticket differently, the labelling policy is not
clear enough, and the suite would be grading models against an unclear target.
Below about 80% agreement on a field, fix the policy before trusting scores for it.
"""

import argparse
import json
from pathlib import Path

from evals.cases import load_cases
from evals.grade import GRADED_FIELDS

BLIND_PATH = Path(__file__).resolve().parent.parent / "labels" / "blind.jsonl"
BLANK = {"category": "", "urgency": "", "refund_requested": None, "invoice_id": ""}


def write_template(path: Path = BLIND_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    rows = [{"id": case.id, "ticket": case.ticket, "label": BLANK} for case in load_cases()]
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    print(f"wrote {path}. Fill in each label without looking at cases/tickets.jsonl or CASES.md.")
    print('invoice_id: use null when the ticket has no invoice number, e.g. "invoice_id": null')


def compare(labels: dict[str, dict]) -> dict:
    """labels maps case id to a filled-in label. Returns agreement per field and the disagreements."""
    agree = {field: 0 for field in GRADED_FIELDS}
    disagreements, counted = [], 0
    for case in load_cases():
        label = labels.get(case.id)
        if label is None:
            continue
        counted += 1
        for field in GRADED_FIELDS:
            if label[field] == case.expected[field]:
                agree[field] += 1
            else:
                disagreements.append((case.id, field, label[field], case.expected[field]))
    return {
        "counted": counted,
        "agreement": {field: agree[field] / counted for field in GRADED_FIELDS} if counted else {},
        "disagreements": disagreements,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--template", action="store_true", help="write the blank labelling file")
    args = parser.parse_args()
    if args.template:
        write_template()
        return

    rows = [json.loads(line) for line in BLIND_PATH.read_text().splitlines() if line.strip()]
    filled = {row["id"]: row["label"] for row in rows if row["label"]["category"]}
    result = compare(filled)
    print(f"{result['counted']} cases labelled")
    for field, share in result["agreement"].items():
        print(f"  {field}: {share:.0%} agreement")
    for case_id, field, mine, expected in result["disagreements"]:
        print(f"  {case_id} {field}: you said {mine!r}, expected answer is {expected!r}")


if __name__ == "__main__":
    main()
