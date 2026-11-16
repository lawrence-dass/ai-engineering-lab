"""Compares every prompt version against the baseline and names the cases that changed.

    uv run python -m evals.report --run main
    uv run python -m evals.report --run main --gate     # exit 1 if the gate fails

A model can answer the same ticket differently on two calls, so each case is
repeated. A case is only called BROKEN when it passed every repetition on the
baseline and failed most of them on the new version. Anything in between is
reported as flaky, not as a regression.

Urgency gets its own rule. A ticket rated less urgent than it is waits in the
general queue when it should page someone, which is the costliest mistake this
feature can make, so any case whose urgency an edit lowers fails the gate on its
own, whatever --max-broken allows.

The gate fails closed. No results, no baseline, a case with no answer on the new
version, or cases edited between versions all fail it, because a decision made
on missing evidence is not the same as a decision made on zero failures.
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from evals.grade import GRADED_FIELDS
from evals.run import RUNS_DIR

BASELINE = "v1_baseline"
URGENCY_RANK = {"low": 0, "medium": 1, "high": 2}


def load_rows(run_dir: Path) -> list[dict]:
    path = run_dir / "results.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def pass_fractions(rows: list[dict]) -> dict[str, float]:
    """case_id -> share of repetitions that passed."""
    by_case: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        by_case[row["case_id"]].append(row["passed"])
    return {case_id: sum(results) / len(results) for case_id, results in by_case.items()}


def bootstrap_ci(values: list[float], *, samples: int = 2000, seed: int = 7) -> tuple[float, float]:
    """95% interval for the mean, resampling cases. Shows how much the score could move by chance."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(samples))
    return (means[int(0.025 * samples)], means[int(0.975 * samples) - 1])


def classify(baseline: float, candidate: float) -> str:
    """Labels how one case moved between the baseline and a candidate version."""
    if baseline == 1.0 and candidate < 0.5:
        return "broken"
    if baseline == 0.0 and candidate > 0.5:
        return "fixed"
    if baseline == candidate:
        return "same"
    return "flaky"


def split_pass_rate(rows: list[dict], split: str) -> float | None:
    fractions = pass_fractions([row for row in rows if row.get("split", "visible") == split])
    return sum(fractions.values()) / len(fractions) if fractions else None


def summarise(rows: list[dict]) -> dict:
    fractions = pass_fractions(rows)
    values = list(fractions.values())
    low, high = bootstrap_ci(values)
    correct_calls = sum(r["passed"] for r in rows)
    return {
        "visible_pass_rate": split_pass_rate(rows, "visible"),
        "heldout_pass_rate": split_pass_rate(rows, "heldout"),
        "cost_per_call": sum(r["cost_usd"] for r in rows) / len(rows),
        "cost_per_correct": sum(r["cost_usd"] for r in rows) / correct_calls if correct_calls else None,
        "cases": len(values),
        "calls": len(rows),
        "pass_rate": sum(values) / len(values),
        "ci": (low, high),
        "fields": {f: sum(r["fields"][f] for r in rows) / len(rows) for f in GRADED_FIELDS},
        "summary_ok": sum(r["summary_ok"] for r in rows) / len(rows),
        "not_ok": sum(r["status"] != "ok" for r in rows),
        "cost_usd": sum(r["cost_usd"] for r in rows),
        "latency_s": sum(r["latency_s"] for r in rows) / len(rows),
        "fractions": fractions,
    }


def compare(baseline: dict, candidate: dict) -> dict[str, list[str]]:
    moved: dict[str, list[str]] = {"broken": [], "fixed": [], "flaky": [], "missing": []}
    for case_id, base_fraction in baseline["fractions"].items():
        if case_id not in candidate["fractions"]:
            moved["missing"].append(case_id)  # every call failed or was never run: no evidence
            continue
        label = classify(base_fraction, candidate["fractions"][case_id])
        if label != "same":
            moved[label].append(case_id)
    return moved


def urgency_downgrades(baseline_rows: list[dict], candidate_rows: list[dict]) -> list[str]:
    """Cases whose urgency was right on every baseline call and rated lower than expected on most candidate calls."""
    def by_case(rows):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["case_id"]].append(row)
        return grouped

    base, cand = by_case(baseline_rows), by_case(candidate_rows)
    lowered = []
    for case_id, calls in base.items():
        if not all(row["fields"]["urgency"] for row in calls) or case_id not in cand:
            continue
        expected = URGENCY_RANK[calls[0]["expected"]["urgency"]]
        lower = [r for r in cand[case_id] if r["output"] and URGENCY_RANK[r["output"]["urgency"]] < expected]
        if len(lower) > len(cand[case_id]) / 2:
            lowered.append(case_id)
    return sorted(lowered)


def money(value: float | None) -> str:
    return f"${value:.5f}" if value is not None else "n/a"


def share(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "n/a"


def wrong_fields(rows: list[dict], case_id: str) -> str:
    """Which fields a case got wrong, with the values seen, e.g. 'urgency: high (want low)'."""
    seen: dict[str, set] = defaultdict(set)
    for row in rows:
        if row["case_id"] != case_id or row["passed"] or not row["output"]:
            continue
        for field in GRADED_FIELDS:
            if not row["fields"][field]:
                seen[field].add(f"{row['output'][field]} (want {row['expected'][field]})")
    return "; ".join(f"{field}: {', '.join(sorted(values))}" for field, values in seen.items())


def edited_cases(baseline_rows: list[dict], candidate_rows: list[dict]) -> list[str]:
    """Cases whose text or expected answer differs between the two sets of rows."""
    shas = {row["case_id"]: row.get("case_sha") for row in baseline_rows}
    return sorted({r["case_id"] for r in candidate_rows if r["case_id"] in shas and r.get("case_sha") != shas[r["case_id"]]})


def tag_table(versions: dict[str, list[dict]]) -> list[str]:
    """Pass rate per first tag and version. An overall score can hold steady while one kind of case gets worse."""
    names = sorted(versions)
    tags = sorted({row["tags"][0] for rows in versions.values() for row in rows})
    lines = ["Pass rate by kind of case:", "", "| tag | cases | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for tag in tags:
        cells, case_count = [], 0
        for name in names:
            tagged = [row for row in versions[name] if row["tags"][0] == tag]
            fractions = pass_fractions(tagged)
            case_count = max(case_count, len(fractions))
            cells.append(f"{sum(fractions.values()) / len(fractions):.0%}" if fractions else "")
        lines.append(f"| {tag} | {case_count} | " + " | ".join(cells) + " |")
    return lines + [""]


def failure_patterns(rows: list[dict]) -> list[str]:
    """Counts each kind of wrong answer, e.g. 'urgency: gave high, wanted low', most frequent first."""
    calls: dict[str, int] = defaultdict(int)
    cases: dict[str, set] = defaultdict(set)
    for row in rows:
        if row["passed"] or not row["output"]:
            continue
        for field in GRADED_FIELDS:
            if not row["fields"][field]:
                pattern = f"{field}: gave {row['output'][field]}, wanted {row['expected'][field]}"
                calls[pattern] += 1
                cases[pattern].add(row["case_id"])
    ordered = sorted(calls, key=lambda pattern: (-calls[pattern], pattern))
    return [f"- {pattern} ({calls[pattern]} calls, {len(cases[pattern])} cases)" for pattern in ordered]


def build_report(
    rows: list[dict],
    *,
    max_broken: int = 0,
    min_pass_rate: float = 0.0,
    max_urgency_downgrades: int = 0,
    max_cost_per_call: float | None = None,
    baseline: str = BASELINE,
) -> tuple[str, list[str]]:
    """Returns (markdown, reasons the gate fails). An empty list of reasons means the gate passes."""
    if not 0.0 <= min_pass_rate <= 1.0 or max_broken < 0 or max_urgency_downgrades < 0:
        raise ValueError("min_pass_rate must be between 0 and 1, and the allowed counts must not be negative")
    if max_cost_per_call is not None and max_cost_per_call <= 0:
        raise ValueError("max_cost_per_call must be positive")

    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["model"]][row["version"]].append(row)

    lines: list[str] = ["# Prompt regression report", ""]
    failures: list[str] = []
    if not rows:
        failures.append("no results to judge")

    for model, versions in sorted(grouped.items()):
        summaries = {version: summarise(version_rows) for version, version_rows in sorted(versions.items())}
        lines += [f"## {model}", ""]
        lines += [
            "| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice "
            "| cost | $/call | $/correct | s/call |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for version, s in summaries.items():
            f = s["fields"]
            lines.append(
                f"| {version} | {s['pass_rate']:.1%} | {s['ci'][0]:.1%} to {s['ci'][1]:.1%} "
                f"| {share(s['visible_pass_rate'])} | {share(s['heldout_pass_rate'])} "
                f"| {f['category']:.1%} | {f['urgency']:.1%} | {f['refund_requested']:.1%} | {f['invoice_id']:.1%} "
                f"| ${s['cost_usd']:.4f} | {money(s['cost_per_call'])} | {money(s['cost_per_correct'])} | {s['latency_s']:.1f} |"
            )
            if max_cost_per_call is not None and s["cost_per_call"] > max_cost_per_call:
                failures.append(f"{model} {version}: ${s['cost_per_call']:.5f} per call is above ${max_cost_per_call:.5f}")
        lines.append("")
        lines += tag_table(versions)
        for version in sorted(versions):
            patterns = failure_patterns(versions[version])
            if patterns:
                lines += [f"Wrong answers on {version}:", ""] + patterns + [""]

        if baseline not in summaries:
            lines += [f"No {baseline} rows for this model, so nothing to compare against.", ""]
            failures.append(f"{model}: no {baseline} results")
            continue

        for version, s in summaries.items():
            if version == baseline:
                continue
            moved = compare(summaries[baseline], s)
            edited = edited_cases(versions[baseline], versions[version])
            lowered = urgency_downgrades(versions[baseline], versions[version])
            if len(lowered) > max_urgency_downgrades:
                failures.append(
                    f"{model} {version}: urgency lowered on {len(lowered)} cases ({', '.join(lowered)}), "
                    f"allowed {max_urgency_downgrades}"
                )
            if len(moved["broken"]) > max_broken:
                failures.append(f"{model} {version}: {len(moved['broken'])} broken (allowed {max_broken})")
            if moved["missing"]:
                failures.append(f"{model} {version}: no results for {', '.join(moved['missing'])}")
            if edited:
                failures.append(f"{model} {version}: cases edited since the baseline ran: {', '.join(edited)}")
            if s["pass_rate"] < min_pass_rate:
                failures.append(f"{model} {version}: pass rate {s['pass_rate']:.1%} is below {min_pass_rate:.1%}")
            delta = s["pass_rate"] - summaries[baseline]["pass_rate"]
            lines += [
                f"### {version} vs {baseline}",
                "",
                f"Pass rate {delta:+.1%}. Broken: {len(moved['broken'])}. "
                f"Fixed: {len(moved['fixed'])}. Flaky: {len(moved['flaky'])}. Missing: {len(moved['missing'])}. "
                f"Urgency lowered: {len(lowered)}.",
                "",
            ]
            for label in ("broken", "fixed", "flaky", "missing"):
                for case_id in moved[label]:
                    detail = wrong_fields(versions[version], case_id)
                    lines.append(f"- **{label}** `{case_id}`" + (f": {detail}" if detail else ""))
            if any(moved.values()):
                lines.append("")

    return "\n".join(lines) + "\n", failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    parser.add_argument("--gate", action="store_true", help="exit 1 if the gate fails")
    parser.add_argument("--max-broken", type=int, default=0, help="broken cases allowed per prompt version")
    parser.add_argument("--min-pass-rate", type=float, default=0.0, help="lowest pass rate allowed, 0 to 1")
    parser.add_argument("--max-urgency-downgrades", type=int, default=0,
                        help="cases an edit may rate less urgent than they are (default 0)")
    parser.add_argument("--max-cost-per-call", type=float, default=None, help="highest average cost per call, in USD")
    parser.add_argument("--baseline", default=BASELINE, help="prompt version the others are compared against")
    args = parser.parse_args()

    run_dir = RUNS_DIR / args.run
    report, failures = build_report(
        load_rows(run_dir), max_broken=args.max_broken, min_pass_rate=args.min_pass_rate,
        max_urgency_downgrades=args.max_urgency_downgrades, max_cost_per_call=args.max_cost_per_call,
        baseline=args.baseline,
    )
    (run_dir / "report.md").write_text(report)
    print(report)

    errors_path = run_dir / "errors.jsonl"
    if errors_path.exists():
        print(f"note: {len(errors_path.read_text().splitlines())} failed calls logged in {errors_path}")
    if args.gate and failures:
        print("GATE FAILED")
        for reason in failures:
            print(f"  - {reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
