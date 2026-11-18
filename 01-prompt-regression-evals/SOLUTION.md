# Solution design: a regression suite for prompt changes

| | |
|---|---|
| **Owner** | Lawrence Dass |
| **Status** | In review |
| **Created** | 2026-11-12 |
| **Last reviewed** | 2026-11-18 |
| **Problem** | [PROBLEM.md](PROBLEM.md) (Approved) |
| **How to run** | [README.md](README.md) |

This document explains how the solution works and why it is built this way. Results are not in it. They are in the README, from the run in `runs/main/`.

## 1. Summary

Run a fixed set of labelled tickets through the real triage code, once for the current prompt and once for each edited prompt, several times each. Part of the set is held out: drafted by a second author, an AI model, and added after the prompts were finished. Grade every answer field by field. Report which tickets changed, and fail the check if any ticket that used to pass now fails, if an edit lowers the urgency of a ticket the baseline always got right, or if the evidence doesn't match the run's plan. Run the same check in CI on every pull request that changes a prompt.

## 2. Goals and non-goals

**Goals.** The six success criteria in [PROBLEM.md, section 9](PROBLEM.md#9-success-criteria).

**Non-goals.** Everything listed as out of scope in [PROBLEM.md, section 6](PROBLEM.md#6-scope). The suite catches regressions. It does not search for a better prompt, grade summary quality, or watch live traffic.

## 3. How it works

```mermaid
flowchart LR
    C[cases/tickets.jsonl + heldout.jsonl<br/>40 visible + 10 held-out] --> R
    P[prompts/*.md<br/>baseline + edits] --> R
    R[evals/run.py<br/>model x prompt x case x repetition] --> A[triage/app.py<br/>one model call, cached prompt]
    A --> RV[triage/review.py<br/>needs a person?]
    RV --> G[evals/grade.py<br/>exact match per field]
    G --> RES[(runs/NAME/results.jsonl)]
    R -. failed calls .-> ERR[(runs/NAME/errors.jsonl)]
    RES --> REP[evals/report.py<br/>compare to baseline]
    REP --> MD[report.md]
    REP --> EXIT{case broken, urgency lowered,<br/>or cost over limit?}
    EXIT -- yes, or evidence missing --> F[exit 1]
    EXIT -- no --> OK[exit 0]
```

One **job** is a single model call, identified by four values: model, prompt version, case and repetition number. A default full run is 4 models × 6 prompt versions × 50 cases × 3 repetitions, which is 3,600 jobs.

## 4. Components

| Component | File | Responsibility |
|---|---|---|
| Labelling policy | `LABELING_POLICY.md` | The written rules that define a correct answer |
| Test cases | `cases/tickets.jsonl`, `cases/heldout.jsonl` | One JSON line per ticket: id, tags, text, expected values. The held-out file has a second author and is not read while editing prompts |
| Case importer | `evals/import_cases.py` | Turns a spreadsheet of cases into JSON Lines, checking every row first |
| Case loader | `evals/cases.py` | Loads the cases and rejects a malformed file before any call is made |
| Prompts | `prompts/*.md` | `v1_baseline.md`, four single-change edits and one bundled edit |
| Output contract | `triage/schema.py` | The JSON Schema sent to the API, and the Pydantic model used to check the reply |
| The feature | `triage/app.py` | `triage_ticket()`: the single model call a product would ship, with one implementation per provider and the system prompt cached |
| Review rule | `triage/review.py` | Business rules that decide whether a person checks an answer, with the reason |
| Grader | `evals/grade.py` | Compares one output with one expected answer. No model calls |
| Runner | `evals/run.py` | Schedules jobs, writes one row per finished job, logs failed calls separately, writes the run manifest |
| Report | `evals/report.py` | Pass rates overall and per tag, per-field accuracy, wrong answers counted by pattern, cases that changed, and the gate |
| Review measurement | `evals/review.py` | How many wrong answers the shipped rule caught, and a simulation of adding agreement across three calls. No model calls |
| CI planner | `evals/ci.py` | Picks which prompt versions a pull request's check runs |
| Agreement check | `evals/agreement.py` | Compares a second person's blind labels with the expected answers |
| Case viewer | `evals/render_cases.py` | Generates `CASES.md` so the test set can be reviewed without reading JSON |

## 5. Design decisions

Each decision lists what was chosen, why, and what was turned down.

### 5.1 The suite calls the production function

`evals/run.py` calls `triage_ticket()` from `triage/app.py` and nothing else.

*Why:* a test copy of the prompt or the call would drift from the real one, and the suite would then be measuring something that does not ship.

*Turned down:* comparing recorded outputs only, as the reference project this draws on does. That is cheaper and deterministic, but it cannot test a prompt nobody has run yet.

### 5.2 A JSON Schema on the request, then our own validation

The request carries a JSON Schema, so the API returns JSON of the right shape. The reply is still validated with Pydantic on our side.

*Why:* the schema removes a whole class of failure (unparseable replies), which leaves the suite measuring one thing: whether the values are right. Validating again costs nothing and means a contract mismatch is recorded as `invalid`, not as a crash.

*Turned down:* asking for JSON in the prompt and parsing free text. That mixes formatting failures with judgement failures in the same score.

Both vendors support this. Anthropic takes the schema in `output_config.format`, OpenAI in the Responses API's `text.format` with `strict: true`. OpenAI's strict mode writes a nullable field as a type list, so `triage/schema.py` keeps a second copy of the schema that differs only in how `invoice_id` allows null. The Pydantic check on our side is the same for both.

### 5.3 Exact match on four fields, and all four must be right

`category`, `urgency`, `refund_requested` and `invoice_id` are compared for equality. A case passes only when all four match.

*Why:* each field has a small closed set of valid answers, so equality measures the answer and not the wording. A ticket with the right category and the wrong urgency still reaches the wrong person, so partial credit would overstate how well a prompt works.

*Turned down:* an LLM judge. It adds cost, a second source of variation, and a grader that itself needs checking. Nothing in these four fields needs judgement to grade.

The per-field results are kept, so the report can show which field went wrong.

### 5.4 The summary is checked for length only

*Why:* a summary has many valid wordings. Grading it properly needs a judge, which section 5.3 rules out. Length is the one property that can be checked exactly. It is reported in its own column and does not affect pass or fail.

### 5.5 Every case runs three times

*Why:* these models reject a temperature setting, so the same ticket can be answered differently on two calls. One run cannot tell a regression from chance.

*Turned down:* one run per case. It is three times cheaper and its results cannot be trusted.

Three is a starting point, not a derived number. See open question 1.

### 5.6 What counts as broken

For each case, the report computes the share of repetitions that passed, on the baseline and on the edited prompt.

| Baseline | Edited prompt | Label |
|---|---|---|
| Passed every time | Passed fewer than half | **broken** |
| Failed every time | Passed more than half | **fixed** |
| Same share | Same share | same |
| Anything else | | **flaky** |

*Why:* "broken" should mean something a reviewer can act on. Requiring a clean baseline and a majority of failures keeps single unlucky calls out of that list. Flaky cases are still listed, because a case that became unreliable is worth a look.

### 5.7 Failed calls go to a separate file

A timeout, an API error, a reply cut off at the token limit, or a reply served by a different model than the one requested is written to `errors.jsonl`. It never gets a row in `results.jsonl`.

*Why:* these are failures of plumbing, not of the prompt. Scoring them as wrong answers would blame an edit for a rate limit. Keeping them out of the results file also means the next run retries them automatically.

A refusal is different. It is the model's answer to the ticket, so it is recorded in the results as a failed case.

### 5.8 Resumable by job key

Before starting, the runner reads `results.jsonl` and skips every job that already has a row. Rows are appended as each job finishes.

*Why:* a crash or a rate limit part-way through 1,200 calls should cost nothing already paid for, and a rerun must not create two rows for the same job.

### 5.9 No model fallback

The request does not enable server-side fallback to another model.

*Why:* a fallback would let a different model answer silently. The suite compares prompts on a named model, so the model has to stay fixed. The runner also checks the model named in each reply, for both vendors, and treats a mismatch as an error.

### 5.10 Four models, two vendors, low effort

The suite runs on a cheap model and a strong model from each of two vendors:

| Tier | Anthropic | OpenAI |
|---|---|---|
| Cheap, high volume | Claude Haiku 5.5 | GPT-6 Luna |
| Strong, a step below the flagship | Claude Opus 5.5 | GPT-6.1 Sol |

All four run at `low` effort, the lowest level all four accept, and all four reason before answering.

*Why:* triage is a short classification task and would run at high volume, where low effort is the realistic setting. Two tiers show whether a stronger model resists an edit that breaks a cheap one. Two vendors show whether a result is about the prompt or about one vendor's models: Haiku and Opus may fail in similar ways, and a second vendor answers that objection. Each tier is matched by position in its vendor's lineup. Prices differ: Luna and Haiku cost the same, Sol costs half what Opus does.

*Turned down:* the two flagships, Claude Fable 5.2 and GPT-6 Astra. They roughly double the cost of the run, and a company would not route support tickets through a flagship model. Neither vendor's top model is tested, and the results say nothing about them. Also turned down: a local model, whose JSON output is less reliable and would mix format failures into the results.

### 5.11 An interval next to every pass rate

The report shows a 95% interval for each pass rate, from 2,000 bootstrap resamples of the cases with a fixed seed.

*Why:* with 40 cases, a two-point difference between prompts may be nothing. The interval makes that visible beside the number.

*Turned down:* a standard binomial interval. Repetitions of the same case are not independent, so it would look narrower than it should. Resampling whole cases avoids that.

### 5.12 Plain files, no eval framework

Cases, prompts and results are JSON Lines and Markdown. The harness is about 650 lines of Python with two dependencies.

*Why:* the constraints ask for something one person can maintain and a non-engineer can add a case to. Every result row can be read and checked by hand.

*Turned down:* an eval platform. Reasonable for a team, more than this needs, and it would hide the mechanism the article is about.

### 5.13 The gate fails closed, with explicit tolerances

The gate takes two settings: the number of broken cases allowed per prompt version (default 0) and a minimum pass rate (default none). It also fails when there are no results, when the baseline was never run, when a case has no answer on the new version, and when a threshold is not a valid number.

With `--gate`, the run's `manifest.json` gives the plan: every model, version, case and repetition its invocations asked for. The gate fails on any planned call with no result, any call recorded twice, any result the plan didn't ask for, and a run with no manifest. It also fails when a model has only baseline results, because there is no edit to judge.

The first version inferred the expected repetitions from the data itself, so a run that was short everywhere, or a baseline-only run, passed. An independent review (Codex, 2026-11-18) found this; the plan check replaced it.

*Why:* a decision made on missing evidence is not the same as a decision made on zero failures. The first version of this harness skipped a case silently when every call for it had failed, which would have let a bad edit through.

*Source:* stage 4 of the `prompt-regression-tester` project ("An empty suite fails closed", "missing responses are failures").

### 5.14 Every row records what it ran against

Each result row carries a fingerprint of the case text and expected answer, a fingerprint of the prompt, the effort level, the SDK version and the time of the call. Resuming a run after a case or prompt was edited is refused. The report fails the gate if a case differs between the baseline rows and the edited-prompt rows.

*Why:* comparing two prompt versions only means something if both ran against the same cases. Without a fingerprint, editing a ticket halfway through would mix old and new rows with no warning. Recording effort and SDK version matters because both can change model behaviour with no change to the prompt.

*Source:* stages 1 and 3 of the same project (hash the case list, keep model and settings beside the responses), and "Drift You Did Not Ship" in the AI System Design Guide's evaluation chapter.

### 5.15 Results are broken down by kind of case

The report shows the pass rate for each tag (tone mismatch, refund trap, invoice trap and so on) under every prompt version, beside the overall number.

*Why:* an edit can leave the overall pass rate flat while one kind of case gets worse. The tag table shows where.

*Source:* exercise 3 of the evaluation lesson in ai-engineering-from-scratch ("A system can improve overall while regressing on a specific category").

### 5.16 Wrong answers are counted by pattern

For each prompt version the report lists every kind of wrong answer with its frequency, for example "urgency: gave high, wanted low (9 calls, 4 cases)".

*Why:* a list of failed case ids says which tickets broke. It does not say what the prompt edit did. Counting the patterns turns scattered failures into a named failure mode that can be fixed and prioritised.

*Source:* the error analysis chapter of the evals study guide in the AI System Design Guide, which treats categorising and counting failures as the most important step and the one teams skip.

### 5.17 A second person can label the cases blind

`evals/agreement.py` writes a copy of the tickets with the answers blanked. Someone fills it in without seeing the expected answers, and the script reports agreement per field and lists each disagreement.

*Why:* if two people label the same ticket differently, the policy is unclear and the suite is grading against an unclear target. The study guide puts the bar at about 80% agreement before trusting a label.

*Source:* the human annotation chapter of the same study guide.

### 5.18 The review decision is part of the feature, made by code

`triage/review.py` decides whether a person checks each answer before it is acted on. Today it sends a ticket to review when the reply was unusable, or when the answer is `account_access`, which covers logins and possible security problems. Every result carries `needs_review` and the reasons.

*Why:* whether a human looks is a business decision. Kept in code, a rule can change without a prompt change, it can differ per field, business rules can sit beside it, and every decision records why it was made.

*Turned down:* asking the model for a confidence score or a needs-review flag. It changes the prompt and the output schema, which is itself a prompt edit, and self-reported confidence tends to be overconfident.

`evals/review.py` measures how many wrong answers the rule caught. It also simulates a stronger signal: three calls per ticket, with review whenever they disagree.

*Limits:* the account_access rule is one example rule, not a tuned policy. Three calls per ticket would triple the production cost. Fifty tickets can show the method but cannot set a threshold.

### 5.19 The baseline is written the way a production prompt is

`v1_baseline.md` has labelled sections:
- the role, including what each field is used for;
- how to treat the input, with an injection defence that also covers text claiming to come from staff or a system;
- the field definitions;
- the decision rules;
- five worked examples.

The examples are new tickets, none of them taken from the test set.

*Why:* definitions alone leave gaps on the hard edges, and production classifier prompts show the model how those go. An example that matches a test case would make that case a test of copying, so examples and test cases are kept apart.

*Turned down:* the first baseline, used for the run kept in `runs/round1/`. It had the same definitions and rules but no sections and no examples.

### 5.20 Single-change edits, and one bundled edit

`v2` to `v5` each change one thing, so a break can be traced to its cause:

| Edit | The change |
|---|---|
| `v2` | An instruction to keep it quick |
| `v3` | One more worked example, a double charge, as added after a bug report |
| `v4` | A request to give upset customers attention |
| `v5` | The urgency definitions shortened for readability |

`v6_bundled_pr` makes three plausible changes at once, as a real pull request often does:
- a shorter refund rule;
- a vaguer multi-issue rule;
- "if unsure about urgency, choose medium".

*Why:* single changes show cause, and the bundle shows how much harder a regression is to trace when several changes arrive together.

`v3`'s added example is close to test case t06. That is deliberate. Adding the failing ticket as an example is a common fix, and it can make that one case pass for the wrong reason.

### 5.21 A held-out set from a second author

`cases/heldout.jsonl` holds 10 tickets. The ticket text was drafted by Codex, an OpenAI coding agent, given `LABELING_POLICY.md` to write from. Codex later disclosed that the same session had earlier seen parts of this experiment, including one visible ticket, so the drafting was not fully isolated. The owner reviewed every ticket and wrote all the expected answers from the policy. The prompts were committed before the held-out file was added, and the report gives their pass rate in a column of its own.

*After the run:* all four models gave the same graded answer on 5 of the 10 tickets, on every call, and a policy review finds those answers closer to the policy than the labels. The labels are kept as written. The held-out pass rate is therefore agreement with the original labels, not model accuracy.

*Why:* the prompt, the edits and the 40 visible tickets have one author, and a prompt can be tuned to the cases its author can see. A second author and a set that stays unread while editing are the resources' answer to both.

*Turned down:* moving 10 of the existing tickets into a held-out file. They would still have the prompt's author.

*Limit:* the ticket text comes from an OpenAI model, and two of the four models under test are OpenAI's. Tickets in a style GPT models write may be easier for GPT models to read, which could favour Luna and Sol on the held-out set. The expected answers are human-written.

### 5.22 The system prompt is cached

The Claude call marks the system prompt with `cache_control`, and OpenAI caches automatically once a prompt reaches 1,024 tokens. Every row records cache reads and writes, and cost prices them separately.

*Why:* the same instructions start every call, and caching them is standard practice in production. Caching changes cost and speed, never the answer.

### 5.23 Urgency gets its own gate rule, and cost has a limit

A case whose urgency was right on every baseline call, and which the edit rates lower than expected on most calls, fails the gate, whatever `--max-broken` allows (`--max-urgency-downgrades`, default 0). A single lower call, or a case whose baseline urgency was already wrong, is not caught by this rule; it shows up as flaky. The report shows cost per call and cost per correct ticket, and `--max-cost-per-call` can fail the gate on cost.

*Why:* a ticket rated less urgent than it is waits when it should page someone. The eval-gated CI case study gates each quality axis on its own, because one combined score hides the axis that matters most. This answers open question 4.

Cost per correct ticket is the useful unit, because list prices per token cannot be compared across vendors that count tokens differently.

### 5.24 The gate runs in CI on prompt changes

The `prompt-gate` job runs on every pull request:
1. `evals/ci.py` lists the prompt files the pull request changed.
2. The job runs those versions and the baseline on Haiku and Luna.
3. It applies the gate. A failure blocks the merge.

If the production prompt itself changed, the new text is compared with the copy on the base branch. The report goes into the job summary.

*Why:* a gate only protects the product if it runs automatically, before the merge. The cheap models keep it at about $0.15 a run, which makes running it on every pull request reasonable.

*Limits:* the job needs both API keys as repository secrets, so pull requests from forks cannot run it. It checks two of the four models; the strong models are run by hand before a release.

### 5.25 Two spending limits

1. Each vendor account has a monthly spend limit, set in its console.
2. The runner takes `--budget-usd`. Once a run has spent that much, it starts no new calls. Calls not made get no row, so the gate fails closed on the missing evidence, and a rerun with a higher budget finishes them.

*Why:* a loop or a wrong flag can multiply calls far past the plan. The vendor limit caps the account, and the runner budget caps the run, which is what a person setting off a run actually intends to spend.

*Limit:* calls already in flight when the budget is reached still finish, so a run can overshoot by up to the cost of a few calls.

## 6. Data formats

**A case** (`cases/tickets.jsonl`):

```json
{"id": "t12", "tags": ["tone-mismatch"], "ticket": "Hello, hope you're well. Small thing, no rush at all: I got an email saying someone signed into my account from a device in a country I've never been to. Probably nothing? Thanks so much!", "expected": {"category": "account_access", "urgency": "high", "refund_requested": false, "invoice_id": null}}
```

**A result row** (`runs/<name>/results.jsonl`) holds the job key, the case and prompt fingerprints, effort, SDK version, timestamp, the model that served the call, the review decision and its reasons, the tags, the split (visible or held-out), the status, `passed`, a true or false per field, the expected answer, the model's output, token counts (full-rate input, cache reads, cache writes, output, and the reasoning part of output), cost and latency.

**The manifest** (`runs/<name>/manifest.json`) is rewritten at the end of every invocation. It holds the code commit and whether the folder had uncommitted changes, the model IDs requested and the ones that answered, effort, token limit, timeout and SDK version, the prices used for cost, totals across the run, and one entry per invocation with its arguments, start and finish times, call counts and cost.

**An error row** (`runs/<name>/errors.jsonl`) holds the job key, an error class (`timeout`, `rate_limit`, `api_<status>`, `connection`, `truncated`, `served_model_mismatch`) and, where the call completed, its token counts and cost.

## 7. How each part of the problem is handled

The numbers match [PROBLEM.md, section 5](PROBLEM.md#5-parts-of-the-problem).

| # | Part of the problem | Handled by | Status |
|---|---|---|---|
| 1 | No written definition of correct | `LABELING_POLICY.md`. Every expected answer must follow it | Handled |
| 2 | No fixed set of examples | 40 tagged visible cases including the hard kinds, plus 10 held-out cases (5.21) | Handled |
| 3 | Valid output hides wrong output | Exact-match grading of values (5.3) | Handled |
| 4 | Edits have distant effects | Every edit is run against every case, not only related ones | Handled |
| 5 | Same input, different answers | Three repetitions and the broken/flaky rule (5.5, 5.6) | Handled. Number of repetitions unproven |
| 6 | Behaviour depends on the model | Four models, two vendors, reported separately (5.10) | Handled for four models |
| 7 | Failed calls are not wrong answers | Separate errors file (5.7) | Handled |
| 8 | Cheap enough to run every time | Concurrent calls, resumable runs, cost recorded per call | Measured: all 6 versions on both cheap models cost $0.11 in `runs/main` |
| 9 | A small test set limits detection | Interval beside each pass rate (5.11) | Shown, not solved |
| 10 | Nobody owns the decision to ship | `--gate` with explicit tolerances, failing closed (5.13), run in CI on every prompt change (5.24) | Handled |
| 11 | A test set goes stale | Fingerprints catch edits within a run (5.14). A spreadsheet importer makes adding cases easy. Nothing rotates or refreshes cases | Partly |
| 12 | Fields do not matter equally | Per-field columns in the report, and a separate gate rule for lowered urgency (5.23) | Handled for urgency |

## 8. Success criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Names every changed ticket, with field and value | Met | `test_report_names_the_case_a_prompt_edit_broke` |
| 2 | Separates broken from inconsistent | Met | `test_classify` |
| 3 | Restartable without loss or double-counting | Met | `test_run_writes_one_row_per_job_and_resumes_without_duplicates` |
| 4 | Runs in CI and fails when a ticket breaks | Met. Pull request #1 (the v5 edit on the production prompt) failed `prompt-gate`: 6 broken on Haiku, 6 on Luna, $0.04; merge blocked by the required check | `prompt-gate` job (5.24), `test_ci_plan_compares_a_changed_production_prompt_with_the_base_branch_copy` |
| 5 | Adding a case is one line in a data file | Met | `cases/tickets.jsonl`, or a spreadsheet row through `evals/import_cases.py` |
| 6 | Cost and duration recorded | Met | `runs/main/manifest.json`: $3.07 for 3,600 calls, with start and finish times per invocation |

The tests use a stand-in for the model. The full run is `runs/main/`; a first run on the first prompts is kept in `runs/round1/`.

## 9. Known gaps

- **The required check and path filters.** `prompt-gate` is required on `main`, but the workflow only runs when this experiment's folder changes. A pull request that touches only another experiment will wait for a check that never starts. When experiment 02 arrives, the workflow should run on every pull request and skip its own work when nothing here changed.
- **Nothing keeps the test set current.** There is no process for adding cases from real failures or retiring old ones.
- **Only urgency has its own gate rule.** The other fields are covered by the broken-case rule.
- **40 cases is below what the resources recommend for a pass rate.** The evaluation lesson in ai-engineering-from-scratch says 50 cases cannot detect a 5-point change and recommends 200 or more for release decisions. This suite is built to find which individual cases changed, which works at 40. Its pass rates should be read as rough.
- **The held-out set is small.** Ten cases from one second author. It checks the prompt author's blind spots, but cannot give a pass rate of its own with any precision.
- **No cases from real traffic.** The resources describe three sources for a test set: curated cases, adversarial cases and production samples. This set has the first two.
- **The labels have been checked by one second person, once.** The blind check (5.17) on 2026-11-15 gave 80% agreement on category, 68% on urgency, 88% on refund and 95% on invoice. Every urgency disagreement rated higher than the policy. The owner kept the strict urgency rule. The round 1 file is kept unedited in `labels/blind_round1.*`; later corrections are not blind.

## 10. Testing

50 tests in `tests/test_evals.py`, none of which call a model. They cover case validation, grading, the broken/flaky/fixed rule, resuming a run, the errors file, the report naming the right case, the per-tag and wrong-answer tables, label agreement, the run manifest, the OpenAI call (parsing, refusals, cut-off replies, cached tokens), the cost formula, the review rule in the feature and its measurement, prompt caching on the Claude call, held-out loading, the spreadsheet importer, the urgency gate rule, the cost limit, the CI plan, the run budget, the paired change interval, ties in the review simulation, and each way the gate fails closed, including runs that don't match their plan. The runner accepts the triage function as an argument, which is how the tests substitute a stand-in.

## 11. Cost

Prices used for cost tracking, in US dollars per million tokens, checked against each vendor's pricing page on 2026-11-15:

| Model | Input | Cache read | Cache write | Output |
|---|---|---|---|---|
| Claude Haiku 5.5 | 0.10 | 0.01 | 0.125 | 0.50 |
| Claude Opus 5.5 | 4.00 | 0.20 | 5.00 | 20.00 |
| GPT-6 Luna | 0.10 | 0.01 | 0.125 | 0.50 |
| GPT-6.1 Sol | 2.00 | 0.10 | 2.50 | 10.00 |

OpenAI caches prompts of 1,024 tokens or more automatically. Anthropic caches when the request asks for it, which the feature now does (5.22). Cached tokens are recorded and priced on every row.

A ten-call pilot on the two Claude models on 2026-11-15 cost $0.0318. The full run in `runs/main/` cost $3.07 for 3,600 calls: $0.11 for both cheap models across all six prompt versions, and $2.96 for the strong models. Per 1,000 calls on the baseline: Haiku $0.07, Luna $0.04, Sol $0.68, Opus $2.29.

## 12. Open questions

Carried over from [PROBLEM.md, section 10](PROBLEM.md#10-open-questions). The design currently uses the default shown.

| # | Question | Default in use |
|---|---|---|
| 1 | How many repetitions are enough? | 3 |
| 2 | Does one broken case block a change? | Yes. Now a setting (`--max-broken`), default 0 |
| 3 | Is reporting a wrong charge a refund request? | No. Decided by the owner on 2026-11-15 |
| 4 | Should fields carry different weights in the gate? | Urgency set too low fails the gate on its own (5.23) |

## 13. What came from the resources

The three resource repos are the study material for this experiment. This table records what each contributed, so the credit is exact.

| Source | What it contributed |
|---|---|
| `prompt-regression-tester` project, ai-engineering-from-scratch | Pair results by case, because an average can stay flat while a required behaviour is lost. Validate cases before scoring. Fingerprint cases. Gate on explicit tolerances and fail closed |
| Evaluation lesson (phase 11, lesson 10), ai-engineering-from-scratch | The before-and-after regression workflow. An interval on every score. The warning that small sets cannot detect small changes |
| Eval-gated CI/CD case study, AI System Design Guide | Use code checks where the answer is deterministic and keep judges for subjective quality. Gate per axis, not on one combined score. Pin effort. Keep cases and results in files you own |
| LLM evaluation chapter, AI System Design Guide | Record model, effort and SDK version on every run, because behaviour can change with no change on your side |
| Evals study guide, AI System Design Guide (chapters 1, 3, 5 and 11 to 15) | Categorise and count failures before anything else. Have a second person label blind and measure agreement. Test the grader itself with known good and bad cases |
| Evaluation lesson exercises, ai-engineering-from-scratch | Break results down by category, because an overall score can hide a regression in one kind of case |

What this experiment does that the reference project does not: it calls a live model, repeats each case to separate regressions from chance, and keeps failed calls apart from wrong answers.

## 14. Change log

| Date | Change |
|---|---|
| 2026-11-12 | First version, describing the harness as built. No run against a model yet. |
| 2026-11-12 | Revised after reading the article 1 resources in full, which the first version was not based on. Added a fail-closed gate with tolerances (5.13) and fingerprints on every row (5.14). Added four known gaps and the table of what came from each resource. |
| 2026-11-12 | Second revision after finishing the remaining resources. Added the per-tag breakdown (5.15), wrong-answer patterns (5.16) and the blind-label agreement check (5.17). |
| 2026-11-14 | Added the run manifest (section 6) and the served model on every result row. |
| 2026-11-16 | Added the run budget and spending limits (5.25), and gate checks for missing cases and repetitions (5.13). Recorded who wrote the held-out cases (5.21). |
| 2026-11-16 | Rebuilt to production practice: a sectioned baseline with worked examples (5.19), a bundled edit (5.20), a held-out set (5.21), prompt caching (5.22), the review decision in the feature (5.18), an urgency gate rule and cost limit (5.23), and the gate in CI (5.24). The first run is kept in `runs/round1/`. |
| 2026-11-16 | Added the review simulation (5.18). |
| 2026-11-18 | After the full run and an independent review: the gate now checks results against the run's plan (5.13), the urgency rule is described as built (5.23), the report gives a paired interval for each edit's change, and the review simulation counts a three-way split as no majority. Status and cost updated from `runs/main/`. |
| 2026-11-15 | Added two OpenAI models (5.2, 5.10, section 11). Cache reads, cache writes and reasoning tokens are recorded on every row and priced separately. |
| 2026-11-15 | Recorded the blind labelling result and the decision on open question 3 (section 9, section 12). |
