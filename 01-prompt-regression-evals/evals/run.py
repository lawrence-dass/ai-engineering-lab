"""Runs the triage feature over every case and writes one graded row per call.

    uv run python -m evals.run --run pilot --models haiku --versions v1_baseline --limit 5 --reps 1
    uv run python -m evals.run --run main

One job = (model, prompt version, case, repetition). Rows are written as each
job finishes, and a rerun skips jobs that already have a row, so a crash or a
rate limit never costs finished work.

Calls that fail before producing a gradable answer (API error, timeout, cut-off
reply) go to errors.jsonl instead. They are plumbing failures, not wrong answers,
and keeping them out of results.jsonl means the next run retries them.

Every invocation also updates manifest.json in the run folder: the code commit,
the model IDs asked for and the ones that answered, the settings and the prices
used for cost. It is the record of what produced the rows.
"""

import argparse
import asyncio
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import openai

from evals.cases import Case, load_all_cases
from evals.grade import grade
from triage.app import EFFORT, MAX_TOKENS, MODELS, PROMPT_CACHING, PROMPTS_DIR, PROVIDERS, load_prompt, triage_ticket

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"
CASE_TIMEOUT_S = 120

# USD per million tokens, standard (non-batch) rates for short prompts, checked
# against each vendor's pricing page on 2026-11-15. A cache write is billed at
# 1.25 times the input rate on both vendors (Anthropic's 5-minute and OpenAI's
# 30-minute retention).
PRICES = {
    "haiku": {"input": 0.10, "cache_read": 0.01, "cache_write": 0.125, "output": 0.50},
    "opus": {"input": 4.00, "cache_read": 0.20, "cache_write": 5.00, "output": 20.00},
    "luna": {"input": 0.10, "cache_read": 0.01, "cache_write": 0.125, "output": 0.50},
    "sol": {"input": 2.00, "cache_read": 0.10, "cache_write": 2.50, "output": 10.00},
}


def cost_usd(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> float:
    """input_tokens is the part billed at the full rate. Cache reads and writes are priced separately."""
    price = PRICES[model]
    total = (
        input_tokens * price["input"]
        + cache_read * price["cache_read"]
        + cache_write * price["cache_write"]
        + output_tokens * price["output"]
    )
    return round(total / 1_000_000, 6)


def job_key(row: dict) -> tuple:
    return (row["model"], row["version"], row["case_id"], row["rep"])


def fingerprint(text: str) -> str:
    """A short hash. Stored on every row so a result can be tied to the exact case and prompt text."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def case_fingerprint(case: Case) -> str:
    return fingerprint(json.dumps({"ticket": case.ticket, "expected": case.expected}, sort_keys=True))


def load_done(results_path: Path) -> dict[tuple, tuple]:
    """Finished jobs, mapped to the (case, prompt) fingerprints they ran against."""
    if not results_path.exists():
        return {}
    rows = [json.loads(line) for line in results_path.read_text().splitlines() if line.strip()]
    return {job_key(row): (row.get("case_sha"), row.get("prompt_sha")) for row in rows}


def append(path: Path, row: dict) -> None:
    with path.open("a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def code_state() -> dict:
    """The commit the harness is running from, and whether this folder has uncommitted changes.

    Run outputs are left out of the check, since writing them is the point of the run.
    Both values are None outside a git checkout.
    """
    def git(*args: str) -> str | None:
        try:
            done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return done.stdout.strip() if done.returncode == 0 else None

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--", ".", ":(exclude)runs") if commit else None
    return {"commit": commit, "dirty": None if status is None else bool(status)}


def write_manifest(run_dir: Path, invocation: dict) -> None:
    """Rewrites manifest.json from the files in the run folder and adds this invocation to its history."""
    path = run_dir / "manifest.json"
    history = json.loads(path.read_text())["invocations"] if path.exists() else []
    results = read_jsonl(run_dir / "results.jsonl")
    errors = read_jsonl(run_dir / "errors.jsonl")
    used = sorted({row["model"] for row in results} | set(invocation["models"]))
    manifest = {
        "run": run_dir.name,
        "code": {"commit": invocation["commit"], "dirty": invocation["dirty"]},
        "models": {
            name: {
                "requested": MODELS[name],
                "served": sorted({r["served_model"] for r in results if r["model"] == name and r.get("served_model")}),
            }
            for name in used
        },
        "settings": {
            "effort": EFFORT,
            "max_tokens": MAX_TOKENS,
            "call_timeout_s": CASE_TIMEOUT_S,
            "prompt_caching": PROMPT_CACHING,
            "sdk_version": anthropic.__version__,
            "openai_sdk_version": openai.__version__,
        },
        "providers": {name: PROVIDERS[name] for name in used},
        "prices_usd_per_million_tokens": {name: PRICES[name] for name in used},
        "totals": {
            "result_rows": len(results),
            "error_rows": len(errors),
            "cost_usd": round(sum(row.get("cost_usd", 0.0) for row in results + errors), 4),
        },
        "invocations": history + [invocation],
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n")


class MissingCredentials(Exception):
    """No API key or login was found, so no call can succeed."""


class StaleRun(Exception):
    """A case or prompt was edited after this run started, so old and new rows would not be comparable."""


AUTH_ERRORS = (anthropic.AuthenticationError, openai.AuthenticationError)


def classify_error(exc: Exception) -> str:
    if isinstance(exc, asyncio.TimeoutError):
        return "timeout"
    if isinstance(exc, (anthropic.RateLimitError, openai.RateLimitError)):
        return "rate_limit"
    if isinstance(exc, (anthropic.APIStatusError, openai.APIStatusError)):
        return f"api_{exc.status_code}"
    if isinstance(exc, (anthropic.APIConnectionError, openai.APIConnectionError)):
        return "connection"
    return type(exc).__name__


def make_clients(models: list[str]) -> dict:
    """One client per provider in use, so a run on Claude models alone needs no OpenAI key."""
    providers = {PROVIDERS[name] for name in models}
    clients = {}
    if "anthropic" in providers:
        clients["anthropic"] = anthropic.AsyncAnthropic(max_retries=4)
    if "openai" in providers:
        try:
            clients["openai"] = openai.AsyncOpenAI(max_retries=4)
        except openai.OpenAIError as exc:  # raised at construction when no key is set
            raise MissingCredentials("OPENAI_API_KEY") from exc
    return clients


async def run_job(
    *, clients, triage_fn, semaphore, run_dir: Path, model: str, version: str, prompt: str, case: Case, rep: int,
    budget: dict | None = None,
) -> dict:
    """Runs one job and returns {"cost": float, "error": bool, "over_budget": bool}.

    budget is shared by every job in the run: {"limit": float or None, "spent": float}.
    Once spending reaches the limit, jobs that have not started are skipped and
    left without a row, so a rerun with a higher limit picks them up.
    """
    budget = budget if budget is not None else {"limit": None, "spent": 0.0}
    base = {"model": model, "version": version, "case_id": case.id, "rep": rep}
    provenance = {
        "case_sha": case_fingerprint(case),
        "prompt_sha": fingerprint(prompt),
        "effort": EFFORT,
        "sdk_version": anthropic.__version__ if PROVIDERS[model] == "anthropic" else openai.__version__,
        "ran_at": now(),
    }
    async with semaphore:
        if budget["limit"] is not None and budget["spent"] >= budget["limit"]:
            return {"cost": 0.0, "error": False, "over_budget": True}
        try:
            result = await asyncio.wait_for(
                triage_fn(clients, model=MODELS[model], system_prompt=prompt, ticket=case.ticket),
                timeout=CASE_TIMEOUT_S,
            )
        except AUTH_ERRORS:
            raise
        except Exception as exc:  # recorded and retried on the next run
            if "authentication method" in str(exc):  # the Anthropic SDK found no credentials at all
                raise MissingCredentials("ANTHROPIC_API_KEY") from exc
            append(run_dir / "errors.jsonl", {**base, "error": classify_error(exc), "detail": str(exc)[:300]})
            return {"cost": 0.0, "error": True, "over_budget": False}

    cost = cost_usd(model, result.input_tokens, result.output_tokens, result.cache_read_tokens, result.cache_write_tokens)
    budget["spent"] += cost
    usage = {
        "input_tokens": result.input_tokens,
        "cache_read_tokens": result.cache_read_tokens,
        "cache_write_tokens": result.cache_write_tokens,
        "output_tokens": result.output_tokens,
        "reasoning_tokens": result.reasoning_tokens,
        "cost_usd": cost,
    }

    # A cut-off reply, or a reply from a different model than the one asked for, is not a fair test.
    wrong_model = not result.served_model.startswith(MODELS[model])
    if result.status == "truncated" or wrong_model:
        error = "served_model_mismatch" if wrong_model else "truncated"
        append(run_dir / "errors.jsonl", {**base, "error": error, "served_model": result.served_model, **usage})
        return {"cost": cost, "error": True, "over_budget": False}

    graded = grade(case.expected, result.output)
    append(
        run_dir / "results.jsonl",
        {
            **base,
            **provenance,
            "tags": list(case.tags),
            "split": case.split,
            "status": result.status,
            "passed": graded["passed"],
            "fields": graded["fields"],
            "summary_ok": graded["summary_ok"],
            "expected": case.expected,
            "output": result.output.model_dump() if result.output else None,
            "raw_text": None if result.output else result.raw_text,
            "stop_reason": result.stop_reason,
            "served_model": result.served_model,
            "needs_review": result.needs_review,
            "review_reasons": list(result.review_reasons),
            "latency_s": result.latency_s,
            **usage,
        },
    )
    return {"cost": cost, "error": False, "over_budget": False}


async def run(
    *,
    run_name: str,
    models: list[str],
    versions: list[str],
    reps: int,
    concurrency: int,
    limit: int | None = None,
    runs_dir: Path = RUNS_DIR,
    triage_fn=triage_ticket,
    clients=None,
    budget_usd: float | None = None,
) -> dict:
    run_dir = runs_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    started_at = now()
    code = code_state()  # read before any output is written
    cases = load_all_cases()[:limit]
    done = load_done(run_dir / "results.jsonl")
    clients = clients if clients is not None else make_clients(models)
    semaphore = asyncio.Semaphore(concurrency)
    budget = {"limit": budget_usd, "spent": 0.0}

    jobs = []
    for model in models:
        for version in versions:
            prompt = load_prompt(version)
            for case in cases:
                for rep in range(reps):
                    key = (model, version, case.id, rep)
                    if key in done:
                        if done[key] != (case_fingerprint(case), fingerprint(prompt)):
                            raise StaleRun(
                                f"{case.id} or {version} was edited after run '{run_name}' started. "
                                "Start a new run with a different --run name."
                            )
                        continue
                    jobs.append(
                        run_job(
                            clients=clients, triage_fn=triage_fn, semaphore=semaphore, run_dir=run_dir,
                            model=model, version=version, prompt=prompt, case=case, rep=rep, budget=budget,
                        )
                    )

    outcomes = await asyncio.gather(*jobs)
    over_budget = sum(o["over_budget"] for o in outcomes)
    counts = {
        "skipped": len(done),
        "ran": len(outcomes) - over_budget,
        "over_budget": over_budget,
        "errors": sum(o["error"] for o in outcomes),
        "cost_usd": round(sum(o["cost"] for o in outcomes), 4),
    }
    write_manifest(
        run_dir,
        {
            "started_at": started_at, "finished_at": now(), **code,
            "models": models, "versions": versions, "reps": reps, "concurrency": concurrency, "budget_usd": budget_usd,
            "limit": limit, "cases": len(cases), "heldout_cases": sum(c.split == "heldout" for c in cases), **counts,
        },
    )
    return {"run_dir": run_dir, **counts}


def all_versions() -> list[str]:
    return sorted(path.stem for path in PROMPTS_DIR.glob("*.md"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="name of the run folder under runs/")
    parser.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    parser.add_argument("--versions", nargs="+", default=all_versions(), help="prompt files in prompts/, without .md")
    parser.add_argument("--reps", type=int, default=3, help="times each case is repeated")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None, help="only the first N cases")
    parser.add_argument("--budget-usd", type=float, default=None,
                        help="stop starting new calls once this run has spent this much")
    args = parser.parse_args()

    try:
        summary = asyncio.run(
            run(run_name=args.run, models=args.models, versions=args.versions, reps=args.reps,
                concurrency=args.concurrency, limit=args.limit, budget_usd=args.budget_usd)
        )
    except MissingCredentials as exc:
        raise SystemExit(f"No API key found. Set {exc} and run again.")
    except AUTH_ERRORS as exc:
        raise SystemExit(f"An API key was rejected ({type(exc).__module__.split('.')[0]}). Check it and run again.")
    except StaleRun as exc:
        raise SystemExit(str(exc))

    print(
        f"ran {summary['ran']} calls, skipped {summary['skipped']} already done, "
        f"{summary['errors']} errors, cost ${summary['cost_usd']:.4f}"
    )
    print(f"results in {summary['run_dir']}")
    if summary["errors"]:
        print("some calls failed. Run the same command again to retry them.")
    if summary["over_budget"]:
        print(f"{summary['over_budget']} calls not made: the ${args.budget_usd:.2f} budget was reached. "
              "Rerun with a higher --budget-usd to finish them.")


if __name__ == "__main__":
    main()
