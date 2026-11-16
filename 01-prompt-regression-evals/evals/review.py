"""Simulates a human review rule over a finished run. Makes no model calls.

    uv run python -m evals.review --run main

In production, code decides per ticket whether a person should check the model's
answer. This script asks what such a rule would have done on the saved results:

- The answer for a ticket is the majority of its repeated calls, field by field.
- The ticket goes to review when the calls disagree on a graded field, when a
  reply was unusable, or when a business rule fires (any account_access ticket).
- The expected answer stands in for a reviewer who always corrects the ticket.

The question it answers: of the tickets the model got wrong, how many would a
person have seen, and how many would have slipped through to the wrong queue?
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from evals.grade import GRADED_FIELDS
from evals.run import RUNS_DIR

ALWAYS_REVIEW_CATEGORIES = {"account_access"}  # logins and possible security problems


def load_rows(run_dir: Path) -> list[dict]:
    path = run_dir / "results.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def majority(values: list):
    """Most common value. On a tie, the value seen first wins."""
    counts = Counter(json.dumps(value) for value in values)
    best = max(counts.values())
    return next(value for value in values if counts[json.dumps(value)] == best)


def decide(outputs: list[dict | None]) -> dict:
    """The answer and the review decision for one ticket, from its repeated calls."""
    if not outputs or any(output is None for output in outputs):
        return {"answer": None, "needs_review": True, "reasons": ["unusable_reply"]}

    answer = {field: majority([output[field] for output in outputs]) for field in GRADED_FIELDS}
    reasons = [
        f"disagreement:{field}"
        for field in GRADED_FIELDS
        if len({json.dumps(output[field]) for output in outputs}) > 1
    ]
    if answer["category"] in ALWAYS_REVIEW_CATEGORIES:
        reasons.append(f"rule:{answer['category']}")
    return {"answer": answer, "needs_review": bool(reasons), "reasons": reasons}


def is_correct(answer: dict | None, expected: dict) -> bool:
    return answer is not None and all(answer[field] == expected[field] for field in GRADED_FIELDS)


def simulate(rows: list[dict]) -> dict[tuple[str, str], dict]:
    """(model, version) -> review metrics."""
    tickets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        tickets[(row["model"], row["version"], row["case_id"])].append(row)

    results: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"tickets": 0, "reviewed": 0, "auto_right": 0, "auto_wrong": 0,
                 "wrong_caught": 0, "reviewed_right": 0, "single_call_right": 0, "reasons": Counter(),
                 "slipped": []}
    )
    for (model, version, case_id), calls in sorted(tickets.items()):
        calls.sort(key=lambda row: row["rep"])
        expected = calls[0]["expected"]
        decision = decide([row["output"] for row in calls])
        right = is_correct(decision["answer"], expected)
        m = results[(model, version)]
        m["tickets"] += 1
        m["single_call_right"] += calls[0]["passed"]
        if decision["needs_review"]:
            m["reviewed"] += 1
            m["reasons"].update(decision["reasons"])
            m["wrong_caught" if not right else "reviewed_right"] += 1
        else:
            m["auto_right" if right else "auto_wrong"] += 1
            if not right:
                m["slipped"].append(case_id)
    return dict(results)


def pct(part: int, whole: int) -> str:
    return f"{part / whole:.0%}" if whole else "n/a"


def build_review_report(rows: list[dict]) -> str:
    results = simulate(rows)
    if not results:
        return "# Review simulation\n\nNo results.\n"

    lines = [
        "# Review simulation",
        "",
        "Answer = majority of the repeated calls. Review when the calls disagree on a graded field, "
        "a reply was unusable, or the answer is account_access. The expected answer stands in for the reviewer.",
        "",
        "| Model | Version | Tickets | Automatic | Sent to review | Accuracy of automatic | Wrong answers | "
        "Caught by review | Slipped through | Accuracy, one call, no review |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for (model, version), m in sorted(results.items()):
        auto = m["auto_right"] + m["auto_wrong"]
        wrong = m["wrong_caught"] + m["auto_wrong"]
        lines.append(
            f"| {model} | {version} | {m['tickets']} | {pct(auto, m['tickets'])} | {pct(m['reviewed'], m['tickets'])} | "
            f"{pct(m['auto_right'], auto)} | {wrong} | {m['wrong_caught']} | {m['auto_wrong']} | "
            f"{pct(m['single_call_right'], m['tickets'])} |"
        )

    lines += ["", "## Why tickets went to review", ""]
    for (model, version), m in sorted(results.items()):
        reasons = ", ".join(f"{reason} {count}" for reason, count in m["reasons"].most_common()) or "none"
        lines.append(f"- {model} {version}: {reasons}")

    lines += ["", "## Wrong answers that slipped through (all calls agreed, and they were wrong)", ""]
    for (model, version), m in sorted(results.items()):
        if m["slipped"]:
            lines.append(f"- {model} {version}: {', '.join(m['slipped'])}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    run_dir = RUNS_DIR / args.run
    report = build_review_report(load_rows(run_dir))
    (run_dir / "review.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
