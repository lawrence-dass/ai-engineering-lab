"""Grades one model output against one expected answer.

Pure functions, no model calls. Four fields are graded by exact match.
A case passes only when all four are right, because a ticket routed with
the wrong urgency is a wrong ticket even if the category is correct.
The summary is free text, so it is checked for length only and reported separately.
"""

from triage.schema import Triage

GRADED_FIELDS = ("category", "urgency", "refund_requested", "invoice_id")
SUMMARY_MAX_WORDS = 20


def grade(expected: dict, output: Triage | None) -> dict:
    if output is None:
        return {
            "passed": False,
            "fields": {field: False for field in GRADED_FIELDS},
            "summary_ok": False,
        }
    fields = {field: getattr(output, field) == expected[field] for field in GRADED_FIELDS}
    word_count = len(output.summary.split())
    return {
        "passed": all(fields.values()),
        "fields": fields,
        "summary_ok": 0 < word_count <= SUMMARY_MAX_WORDS,
    }
