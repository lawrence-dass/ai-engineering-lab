"""Tests for the eval harness itself. None of them call a model."""

import asyncio
import json

import pytest

from evals.agreement import compare as compare_labels
from evals.cases import load_all_cases, load_cases, validate
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
    expected_by_ticket = {case.ticket: case.expected for case in load_all_cases()}

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
                  limit=3, runs_dir=tmp_path, triage_fn=stub_triage(set()), clients=object())
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
                    concurrency=4, limit=4, runs_dir=tmp_path, triage_fn=triage_fn, clients=object()))
    report, failures = build_report(load_rows(tmp_path / "t"))
    assert failures == ["haiku v2_keep_it_quick: 1 broken (allowed 0)"]
    assert "**broken** `t01`: urgency: high (want low)" in report


def test_api_failures_go_to_the_errors_file_not_the_results(tmp_path):
    async def failing(client, *, model, system_prompt, ticket):
        raise RuntimeError("boom")

    summary = asyncio.run(run(run_name="t", models=["haiku"], versions=["v1_baseline"], reps=1, concurrency=2,
                              limit=2, runs_dir=tmp_path, triage_fn=failing, clients=object()))
    assert summary["errors"] == 2
    assert not (tmp_path / "t" / "results.jsonl").exists()
    errors = [json.loads(line) for line in (tmp_path / "t" / "errors.jsonl").read_text().splitlines()]
    assert {e["error"] for e in errors} == {"RuntimeError"}


# --- the gate fails closed --------------------------------------------------

def run_stub(tmp_path, versions, limit=3, reps=1, **kwargs):
    return asyncio.run(run(run_name="t", models=["haiku"], versions=versions, reps=reps, concurrency=4,
                           limit=limit, runs_dir=tmp_path, triage_fn=stub_triage(set()), clients=object(), **kwargs))


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
    assert manifest["prices_usd_per_million_tokens"]["haiku"]["input"] == 0.10
    assert manifest["providers"] == {"haiku": "anthropic"}
    assert manifest["settings"]["effort"] == "low"
    assert manifest["totals"]["result_rows"] == 4
    assert [i["ran"] for i in manifest["invocations"]] == [2, 2]
    assert manifest["invocations"][1]["skipped"] == 2


# --- what the report shows beyond the headline number ----------------------

def test_report_breaks_results_down_by_kind_of_case_and_counts_wrong_answers(tmp_path):
    first_ticket = load_cases()[0].ticket
    asyncio.run(run(run_name="t", models=["haiku"], versions=["v1_baseline", "v2_keep_it_quick"], reps=3,
                    concurrency=4, limit=12, runs_dir=tmp_path,
                    triage_fn=stub_triage({("Keep it quick", first_ticket)}), clients=object()))
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


# --- the OpenAI call, with a stand-in for the API ----------------------------

from types import SimpleNamespace

from evals.run import cost_usd
from triage.app import triage_openai


def fake_openai_response(*, text="", refusal=False, status="completed", reason=None, cached=0, written=0):
    part = SimpleNamespace(type="refusal", refusal="no") if refusal else SimpleNamespace(type="output_text", text=text)
    return SimpleNamespace(
        output=[SimpleNamespace(type="reasoning"), SimpleNamespace(type="message", content=[part])],
        output_text="" if refusal else text,
        status=status,
        incomplete_details=SimpleNamespace(reason=reason) if reason else None,
        model="gpt-6-luna",
        usage=SimpleNamespace(
            input_tokens=1200,
            input_tokens_details=SimpleNamespace(cached_tokens=cached, cache_write_tokens=written),
            output_tokens=90,
            output_tokens_details=SimpleNamespace(reasoning_tokens=20),
        ),
    )


def fake_openai_client(response):
    sent = {}

    async def create(**kwargs):
        sent.update(kwargs)
        return response

    return SimpleNamespace(responses=SimpleNamespace(create=create)), sent


def call_openai(response):
    client, sent = fake_openai_client(response)
    result = asyncio.run(triage_openai(client, model="gpt-6-luna", system_prompt="rules", ticket="hi"))
    return result, sent


def test_openai_reply_is_parsed_and_cached_tokens_are_split_out():
    reply = json.dumps({**EXPECTED, "summary": "Duplicate charge, refund wanted."})
    result, sent = call_openai(fake_openai_response(text=reply, cached=1024, written=0))
    assert result.status == "ok" and result.output.invoice_id == "INV-204817"
    assert (result.input_tokens, result.cache_read_tokens, result.reasoning_tokens) == (176, 1024, 20)
    assert sent["text"]["format"]["strict"] is True
    assert sent["reasoning"] == {"effort": "low"} and sent["store"] is False


def test_openai_refusal_and_cut_off_reply_are_labelled():
    assert call_openai(fake_openai_response(refusal=True))[0].status == "refusal"
    cut = call_openai(fake_openai_response(status="incomplete", reason="max_output_tokens"))[0]
    assert cut.status == "truncated" and cut.stop_reason == "incomplete:max_output_tokens"


def test_cost_prices_cache_reads_and_writes_separately():
    assert cost_usd("opus", 1_000_000, 0) == 4.0
    assert cost_usd("opus", 0, 0, cache_read=1_000_000) == 0.2
    assert cost_usd("luna", 0, 1_000_000, cache_write=1_000_000) == 0.625


# --- the review simulation ---------------------------------------------------

from evals.review import decide, simulate


def answer(**overrides):
    return {**EXPECTED, "summary": "s", **overrides}


def test_agreeing_calls_go_through_and_disagreeing_calls_go_to_review():
    assert decide([answer(), answer(), answer()])["needs_review"] is False
    split = decide([answer(), answer(urgency="low"), answer()])
    assert split["needs_review"] is True and split["reasons"] == ["disagreement:urgency"]
    assert split["answer"]["urgency"] == "high"  # the majority


def test_unusable_replies_and_the_account_access_rule_force_review():
    assert decide([answer(), None, answer()])["reasons"] == ["unusable_reply"]
    login = answer(category="account_access")
    assert decide([login, login, login])["reasons"] == ["rule:account_access"]


def test_simulation_counts_caught_and_slipped_wrong_answers():
    def rows(case_id, outputs):
        return [{"model": "haiku", "version": "v1_baseline", "case_id": case_id, "rep": i,
                 "expected": EXPECTED, "output": out, "passed": out == answer()} for i, out in enumerate(outputs)]
    data = (rows("a", [answer()] * 3)                                   # right, automatic
            + rows("b", [answer(urgency="low")] * 3)                    # wrong and consistent: slips through
            + rows("c", [answer(urgency="low"), answer(), answer(urgency="low")]))  # wrong, calls disagree: caught
    m = simulate(data)[("haiku", "v1_baseline")]
    assert (m["auto_right"], m["auto_wrong"], m["wrong_caught"], m["reviewed"]) == (1, 1, 1, 1)
    assert m["slipped"] == ["b"]


# --- the review rule inside the feature, and prompt caching -----------------

from evals.ci import MAIN_COPY, plan
from evals.import_cases import import_cases
from evals.report import urgency_downgrades
from triage.app import triage_anthropic, triage_ticket
from triage.review import review_decision


def test_review_rule_flags_account_access_and_unusable_replies_only():
    assert review_decision("ok", make_output()) == (False, [])
    assert review_decision("ok", make_output(category="account_access")) == (True, ["rule:account_access"])
    assert review_decision("invalid", None) == (True, ["unusable_reply:invalid"])


def test_the_feature_attaches_the_review_decision_to_its_answer():
    reply = json.dumps({**EXPECTED, "category": "account_access", "summary": "Locked out."})
    client, _ = fake_openai_client(fake_openai_response(text=reply))
    result = asyncio.run(triage_ticket({"openai": client}, model="gpt-6-luna", system_prompt="rules", ticket="hi"))
    assert result.needs_review is True and result.review_reasons == ("rule:account_access",)


def test_claude_call_marks_the_system_prompt_for_caching_and_reads_cache_tokens():
    sent = {}

    async def create(**kwargs):
        sent.update(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps({**EXPECTED, "summary": "s"}))],
            stop_reason="end_turn", model="claude-haiku-5-5",
            usage=SimpleNamespace(input_tokens=50, output_tokens=70, cache_read_input_tokens=1400,
                                  cache_creation_input_tokens=0, output_tokens_details=SimpleNamespace(thinking_tokens=3)),
        )

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    result = asyncio.run(triage_anthropic(client, model="claude-haiku-5-5", system_prompt="rules", ticket="hi"))
    assert sent["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert (result.cache_read_tokens, result.reasoning_tokens, result.status) == (1400, 3, "ok")


# --- held-out cases and the spreadsheet importer ------------------------------

def write_lines(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return path


def test_heldout_cases_load_with_their_own_split_and_ids_must_not_clash(tmp_path):
    row = {"id": "h01", "tags": ["easy"], "ticket": "hi", "expected": {**EXPECTED}}
    visible = write_lines(tmp_path / "v.jsonl", [{**row, "id": "t01"}])
    heldout = write_lines(tmp_path / "h.jsonl", [row])
    cases = load_all_cases(visible, heldout)
    assert [(c.id, c.split) for c in cases] == [("t01", "visible"), ("h01", "heldout")]
    with pytest.raises(ValueError, match="both files"):
        load_all_cases(visible, write_lines(tmp_path / "h2.jsonl", [{**row, "id": "t01"}]))


def test_spreadsheet_import_checks_every_row_and_skips_empty_ones(tmp_path):
    sheet = tmp_path / "cases.csv"
    sheet.write_text(
        "id,tags,ticket,category,urgency,refund_requested,invoice_id\n"
        "h01,refund-trap,Refund the duplicate on inv-204817 please,Billing,High,TRUE,inv-204817\n"
        "h02,,,,,,\n"
        "h03,easy,Where is the export button?,how_to,urgent,FALSE,\n"
    )
    cases, problems = import_cases(sheet)
    assert [c["id"] for c in cases] == ["h01"]
    assert cases[0]["expected"]["category"] == "billing" and cases[0]["expected"]["refund_requested"] is True
    assert len(problems) == 1 and "urgency" in problems[0]


# --- the gate's urgency rule, cost limit and CI plan --------------------------

def test_lowering_urgency_fails_the_gate_even_when_broken_cases_are_allowed(tmp_path):
    high = next(case for case in load_cases() if case.expected["urgency"] == "high")
    asyncio.run(run(run_name="t", models=["haiku"], versions=["v1_baseline", "v2_keep_it_quick"], reps=3,
                    concurrency=4, limit=10, runs_dir=tmp_path, triage_fn=stub_triage({("Keep it quick", high.ticket)}),
                    clients=object()))
    rows = load_rows(tmp_path / "t")
    base = [r for r in rows if r["version"] == "v1_baseline"]
    cand = [r for r in rows if r["version"] == "v2_keep_it_quick"]
    assert urgency_downgrades(base, cand) == [high.id]
    _, failures = build_report(rows, max_broken=5)
    assert any("urgency lowered" in reason for reason in failures)
    assert not any("broken" in reason for reason in failures)


def test_gate_can_cap_the_cost_per_call(tmp_path):
    run_stub(tmp_path, ["v1_baseline", "v2_keep_it_quick"])
    rows = load_rows(tmp_path / "t")
    assert not build_report(rows)[1]
    assert any("per call" in reason for reason in build_report(rows, max_cost_per_call=0.000001)[1])


def test_ci_plan_compares_a_changed_production_prompt_with_the_base_branch_copy():
    assert plan([]) == ("v1_baseline", [])
    assert plan(["v3_add_example"]) == ("v1_baseline", ["v1_baseline", "v3_add_example"])
    assert plan(["v1_baseline"]) == (MAIN_COPY, [MAIN_COPY, "v1_baseline"])
