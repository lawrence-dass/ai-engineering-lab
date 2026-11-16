"""Decides, in code, whether a person should check a triage answer before it is acted on.

The model returns the routing fields. Whether a human looks at them is a business
decision, so it lives here and not in the prompt: the rules can change without a
prompt change, and every decision carries the reason it was made.
"""

# Categories a person always checks: logins, lockouts and possible security problems.
ALWAYS_REVIEW_CATEGORIES = frozenset({"account_access"})


def review_decision(status: str, output) -> tuple[bool, list[str]]:
    """Returns (needs_review, reasons) for one answer. An empty reason list means it routes automatically."""
    if status != "ok" or output is None:
        return True, [f"unusable_reply:{status}"]
    reasons = []
    if output.category in ALWAYS_REVIEW_CATEGORIES:
        reasons.append(f"rule:{output.category}")
    return bool(reasons), reasons
