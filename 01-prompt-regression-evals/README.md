# 01 · prompt-regression-evals

A small eval suite that catches regressions when a prompt changes.

The feature under test is one model call that triages a customer support message into JSON: category, urgency, whether a refund was requested, and the invoice number. The suite runs 40 hand-labelled tickets through it, repeats each one, and compares every edited prompt against the baseline.

The problem it addresses is set out in [PROBLEM.md](PROBLEM.md). The design is in [SOLUTION.md](SOLUTION.md).

## Result

Pending the first full run. This section will hold the main finding and a link to the run it came from.

## Run it

You need Python 3.11 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/lawrence-dass/ai-engineering-lab.git
cd ai-engineering-lab/01-prompt-regression-evals
uv sync --locked
```

### Free: the harness tests

No API key, no model calls, no cost. They use a stand-in for the model and take about a second.

```bash
uv run pytest
```

### Paid: runs against the models

These call the Claude API and cost money. Set a key first, either with `export ANTHROPIC_API_KEY=...` or by copying `.env.example` to `.env` and adding `--env-file .env` after `uv run`.

Start with the pilot. It makes 5 calls on the cheaper model and prints what they cost.

```bash
uv run python -m evals.run --run pilot --models haiku --versions v1_baseline --limit 5 --reps 1
```

The full run is 1,200 calls: 2 models, 5 prompt versions, 40 cases, 3 repetitions.

```bash
uv run python -m evals.run --run main
```

A rerun of the same command skips finished calls and retries failed ones.

The report reads the saved rows and makes no model calls.

```bash
uv run python -m evals.report --run main
uv run python -m evals.report --run main --gate   # exits 1 if a case broke or evidence is missing
```

## Evidence

Every run writes four files to `runs/<name>/`:

| File | What it holds |
|---|---|
| `results.jsonl` | One graded row per finished call |
| `errors.jsonl` | Calls that failed before giving a gradable answer |
| `report.md` | The comparison against the baseline, written by `evals.report` |
| `manifest.json` | The code commit, the model IDs requested and the ones that answered, run settings, the prices used for cost, and a history of every invocation |

Pilot runs are ignored by git. The run behind the article is committed, and will be linked here.

## How it works

| File | What it does |
|---|---|
| `PROBLEM.md` | The problem this experiment addresses, its parts, scope and success criteria |
| `SOLUTION.md` | How the suite works, each design decision and what was turned down |
| `prompts/v1_baseline.md` | The system prompt. Each other file in `prompts/` is the baseline with one edit |
| `triage/schema.py` | The output contract: a JSON Schema sent to the API and a Pydantic model for checking the reply |
| `triage/app.py` | The feature: one call to the model, returns a `Triage` record |
| `cases/tickets.jsonl` | 40 tickets with expected answers. `CASES.md` is the readable view |
| `LABELING_POLICY.md` | The rules every expected answer follows |
| `evals/grade.py` | Exact-match grading of four fields. A case passes only if all four are right |
| `evals/run.py` | Runs model × prompt version × case × repetition, writes one row per call, resumable. Writes `manifest.json` |
| `evals/report.py` | Pass rates overall and per tag, per-field accuracy, wrong answers counted by pattern, and the cases each edit broke |
| `evals/agreement.py` | Checks a second person's blind labels against the expected answers |
| `PREDICTIONS.md` | What I expected, written before the run |
| `.env.example` | The one setting a paid run needs |

## Design

The design, the alternatives that were turned down, and how each part of the problem is handled are in [SOLUTION.md](SOLUTION.md).

## Limits

- 40 cases is a small set. One case is 2.5 points of pass rate. The suite is built to show which cases changed. Its pass rates are rough.
- The tickets are written by hand, not sampled from a real support queue.
- The expected answers follow one written policy. A different policy would give different scores.

## Credits

The design is guided by the `prompt-regression-tester` project and the evaluation lesson in [ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch), and by the evaluation chapter and the eval-gated CI/CD case study in the [AI System Design Guide](https://github.com/ombharatiya/ai-system-design-guide). [SOLUTION.md](SOLUTION.md) lists what each one contributed. The code and cases here are my own.
