"""Writes CASES.md, a readable view of cases/tickets.jsonl for reviewing the test set.

    uv run python -m evals.render_cases
"""

from collections import Counter
from pathlib import Path

from evals.cases import load_cases

OUT = Path(__file__).resolve().parent.parent / "CASES.md"


def main() -> None:
    cases = load_cases()
    lines = [
        "# Test cases",
        "",
        f"{len(cases)} cases. Generated from `cases/tickets.jsonl`. Edit that file, not this one.",
        "Labels follow `LABELING_POLICY.md`.",
        "",
        "| id | tags | category | urgency | refund | invoice |",
        "|---|---|---|---|---|---|",
    ]
    for case in cases:
        e = case.expected
        lines.append(
            f"| {case.id} | {', '.join(case.tags)} | {e['category']} | {e['urgency']} "
            f"| {'yes' if e['refund_requested'] else 'no'} | {e['invoice_id'] or ''} |"
        )

    lines += ["", "## Counts", ""]
    for label, counter in [
        ("First tag", Counter(case.tags[0] for case in cases)),
        ("Category", Counter(case.expected["category"] for case in cases)),
        ("Urgency", Counter(case.expected["urgency"] for case in cases)),
    ]:
        lines.append(f"- {label}: " + ", ".join(f"{name} {count}" for name, count in counter.most_common()))

    lines += ["", "## Full text", ""]
    for case in cases:
        e = case.expected
        lines += [
            f"### {case.id} ({', '.join(case.tags)})",
            "",
            "````text",
            case.ticket,
            "````",
            "",
            f"Expected: `{e['category']}`, `{e['urgency']}`, refund requested "
            f"`{'yes' if e['refund_requested'] else 'no'}`, invoice `{e['invoice_id'] or 'none'}`",
            "",
        ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(cases)} cases)")


if __name__ == "__main__":
    main()
