"""Tests for the eval harness itself. None of them call a model."""

import asyncio
import json

import pytest

from evals.agreement import compare as compare_labels
from evals.cases import load_cases, validate
from evals.grade import grade
from evals.report import build_report, classify, load_rows
from evals.run import StaleRun, run
from triage.app import PROMPTS_DIR, TriageResult
from triage.schema import Triage

EXPECTED = {"category": "billing", "urgency": "high", "refund_requested": True, "invoice_id": "INV-204817"}


def make_output(**overrides) -> Triage:
    return Triage(**{**EXPECTED, "summary": "Customer wants a duplicate charge refunded.", **overrides})


# --- cases -----------------------------------------------------------------

def test_case_file_is_valid_and_not_empty():
    cases = load_cases()
    assert len(cases) >= 40
    assert len({case.id for case in cases}) == len(cases)


def test_validate_rejects_a_badly_formed_invoice_id():
    raw = {"id": "x", "tags": ["easy"], "ticket": "hi", "expected": {**EXPECTED, "invoice_id": "204817"}}
    with pytest.raises(ValueError, match="invoice_id"):
        validate(raw, 1)


def test_every_prompt_version_keeps_the_ticket_tag_instruction():
    for path in PROMPTS_DIR.glob("*.md"):
        assert "<ticket>" in path.read_text(), path.name


# --- grading ---------------------------------------------------------------

def test_all_fields_right_passes():
    assert grade(EXPECTED, make_output())["passed"] is True


def test_one_wrong_field_fails_and_is_named():
    graded = grade(EXPECTED, make_output(urgency="low"))
    assert graded["passed"] is False
    assert graded["fields"] == {"category": True, "urgency": False, "refund_requested": True, "invoice_id": True}


def test_invented_invoice_id_fails_when_none_expected():
    graded = grade({**EXPECTED, "invoice_id": None}, make_output())
    assert graded["fields"]["invoice_id"] is False


def test_unusable_reply_fails_every_field():
    graded = grade(EXPECTED, None)
    assert graded["passed"] is False
    assert not any(graded["fields"].values())


def test_long_summary_is_flagged_but_does_not_fail_the_case():
    graded = grade(EXPECTED, make_output(summary=" ".join(["word"] * 30)))
    assert graded["passed"] is True
    assert graded["summary_ok"] is False


# --- comparing versions ----------------------------------------------------

@pytest.mark.parametrize(
    "baseline, candidate, label",
    [
        (1.0, 0.0, "broken"),
        (1.0, 1 / 3, "broken"),
        (1.0, 2 / 3, "flaky"),
        (0.0, 1.0, "fixed"),
        (2 / 3, 1 / 3, "flaky"),
        (1.0, 1.0, "same"),
    ],
)
def test_classify(baseline, candidate, label):
    assert classify(baseline, candidate) == label


# --- runner, with a stand-in for the model ---------------------------------

def stub_triage(wrong_on: set[tuple[str, str]]):
    """Returns the expected answer, except urgency is flipped for (version marker, ticket) pairs in wrong_on."""
    expected_by_ticket = {case.ticket: case.expected for case in load_cases()}

    async def triage_fn(client, *, model, system_prompt, ticket):
        answer = dict(expected_by_ticket[ticket])
        if any(marker in system_prompt and ticket == bad for marker, bad in wrong_on):
            answer["urgency"] = "low" if answer["urgency"] != "low" else "high"
        return TriageResult(
            output=Triage(**answer, summary="A short summary."), raw_text="", status="ok",
            stop_reason="end_turn", served_model=model, input_tokens=500, output_tokens=60, latency_s=0.1,
        )

    return triage_fn


def test_run_writes_one_row_per_job_and_resumes_without_duplicates(tmp_path):
    kwargs = dict(run_name="t", models=["haiku"], versions=["v1_baseline"], reps=2, concurrency=4,
                  limit=3, runs_dir=tmp_path, triage_fn=stub_triage(set()), client=object())
    first = asyncio.run(run(**kwargs))
    second = asyncio.run(run(**kwargs))
    rows = load_rows(tmp_path / "t")
    assert first["ran"] == 6 and second["ran"] == 0
    assert len(rows) == 6
    assert all(row["passed"] for row in rows)


def test_report_names_the_case_a_prompt_edit_broke(tmp_path):
    first_ticket = load_cases()[0].ticket
    # "Keep it quick" only appears in the v2 prompt, so only v2 gets the wrong answer.
    triage_fn = stub_triage({("Keep it quick", first_ticket)})
    asyncio.run(run(run_name="t", models=["haiku"], versions=["v1_baseline", "v2_keep_it_quick"], reps=3,
                    concurrency=4, limit=4, runs_dir=tmp_path, triage_fn=triage_fn, client=object()))
    report, failures = build_report(load_rows(tmp_path / "t"))
    assert failures == ["haiku v2_keep_it_quick: 1 broken (allowed 0)"]
    assert "**broken** `t01`: urgency: high (want low)" in report


def test_api_failures_go_to_the_errors_file_not_the_results(tmp_path):
    async def failing(client, *, model, system_prompt, ticket):
        raise RuntimeError("boom")

    summary = asyncio.run(run(run_name="t", models=["haiku"], versions=["v1_baseline"], reps=1, concurrency=2,
                              limit=2, runs_dir=tmp_path, triage_fn=failing, client=object()))
    assert summary["errors"] == 2
    assert not (tmp_path / "t" / "results.jsonl").exists()
    errors = [json.loads(line) for line in (tmp_path / "t" / "errors.jsonl").read_text().splitlines()]
    assert {e["error"] for e in errors} == {"RuntimeError"}


# --- the gate fails closed --------------------------------------------------

def run_stub(tmp_path, versions, limit=3, reps=1, **kwargs):
    return asyncio.run(run(run_name="t", models=["haiku"], versions=versions, reps=reps, concurrency=4,
                           limit=limit, runs_dir=tmp_path, triage_fn=stub_triage(set()), client=object(), **kwargs))


def test_gate_fails_when_there_are_no_results(tmp_path):
    _, failures = build_report(load_rows(tmp_path / "nothing-here"))
    assert failures == ["no results to judge"]


def test_gate_fails_when_the_baseline_was_never_run(tmp_path):
    run_stub(tmp_path, ["v2_keep_it_quick"])
    _, failures = build_report(load_rows(tmp_path / "t"))
    assert failures == ["haiku: no v1_baseline results"]


def test_gate_fails_when_a_case_has_no_answer_on_the_new_version(tmp_path):
    run_stub(tmp_path, ["v1_baseline", "v2_keep_it_quick"])
    rows = [r for r in load_rows(tmp_path / "t") if not (r["version"] == "v2_keep_it_quick" and r["case_id"] == "t02")]
    report, failures = build_report(rows)
    assert failures == ["haiku v2_keep_it_quick: no results for t02"]
    assert "**missing** `t02`" in report


def test_gate_fails_when_a_case_was_edited_between_versions(tmp_path):
    run_stub(tmp_path, ["v1_baseline", "v2_keep_it_quick"])
    rows = load_rows(tmp_path / "t")
    for row in rows:
        if row["version"] == "v2_keep_it_quick" and row["case_id"] == "t01":
            row["case_sha"] = "different"
    _, failures = build_report(rows)
    assert failures == ["haiku v2_keep_it_quick: cases edited since the baseline ran: t01"]


def test_gate_can_require_a_minimum_pass_rate_and_rejects_bad_thresholds(tmp_path):
    run_stub(tmp_path, ["v1_baseline", "v2_keep_it_quick"])
    rows = load_rows(tmp_path / "t")
    assert build_report(rows, min_pass_rate=1.0)[1] == []
    with pytest.raises(ValueError):
        build_report(rows, min_pass_rate=float("nan"))


def test_resuming_after_a_prompt_was_edited_is_refused(tmp_path):
    run_stub(tmp_path, ["v1_baseline"])
    results = tmp_path / "t" / "results.jsonl"
    edited = [json.dumps({**json.loads(line), "prompt_sha": "older"}) for line in results.read_text().splitlines()]
    results.write_text("\n".join(edited) + "\n")
    with pytest.raises(StaleRun):
        run_stub(tmp_path, ["v1_baseline"])


def test_every_row_records_what_it_ran_against(tmp_path):
    run_stub(tmp_path, ["v1_baseline"], limit=1)
    row = load_rows(tmp_path / "t")[0]
    assert {"case_sha", "prompt_sha", "effort", "sdk_version", "ran_at", "served_model"} <= set(row)


def test_manifest_records_what_produced_the_run_and_keeps_a_history(tmp_path):
    run_stub(tmp_path, ["v1_baseline"], limit=2)
    run_stub(tmp_path, ["v1_baseline", "v2_keep_it_quick"], limit=2)
    manifest = json.loads((tmp_path / "t" / "manifest.json").read_text())
    assert {"commit", "dirty"} <= set(manifest["code"])
    assert manifest["models"]["haiku"]["requested"] == "claude-haiku-5-5"
    assert manifest["models"]["haiku"]["served"]
    assert manifest["prices_usd_per_million_tokens"]["haiku"] == {"input": 0.10, "output": 0.50}
    assert manifest["settings"]["effort"] == "low"
    assert manifest["totals"]["result_rows"] == 4
    assert [i["ran"] for i in manifest["invocations"]] == [2, 2]
    assert manifest["invocations"][1]["skipped"] == 2


# --- what the report shows beyond the headline number ----------------------

def test_report_breaks_results_down_by_kind_of_case_and_counts_wrong_answers(tmp_path):
    first_ticket = load_cases()[0].ticket
    asyncio.run(run(run_name="t", models=["haiku"], versions=["v1_baseline", "v2_keep_it_quick"], reps=3,
                    concurrency=4, limit=12, runs_dir=tmp_path,
                    triage_fn=stub_triage({("Keep it quick", first_ticket)}), client=object()))
    report, _ = build_report(load_rows(tmp_path / "t"))
    assert "| tag | cases | v1_baseline | v2_keep_it_quick |" in report
    assert "| easy | 9 | 100% | 89% |" in report
    assert "- urgency: gave high, wanted low (3 calls, 1 cases)" in report


# --- label agreement --------------------------------------------------------

def test_label_agreement_reports_each_disagreement():
    cases = load_cases()[:4]
    labels = {case.id: dict(case.expected) for case in cases}
    labels[cases[0].id]["urgency"] = "high"
    result = compare_labels(labels)
    assert result["counted"] == 4
    assert result["agreement"]["urgency"] == 0.75
    assert result["agreement"]["category"] == 1.0
    assert result["disagreements"] == [(cases[0].id, "urgency", "high", "low")]
