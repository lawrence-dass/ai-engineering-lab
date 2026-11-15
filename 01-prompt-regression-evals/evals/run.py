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

from evals.cases import Case, load_cases
from evals.grade import grade
from triage.app import EFFORT, MAX_TOKENS, MODELS, PROMPTS_DIR, load_prompt, triage_ticket

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"
CASE_TIMEOUT_S = 120

# USD per million tokens (input, output), prompts under 100K tokens.
PRICES = {
    "haiku": (0.10, 0.50),
    "opus": (4.00, 20.00),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES[model]
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


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
            "sdk_version": anthropic.__version__,
        },
        "prices_usd_per_million_tokens": {
            name: {"input": PRICES[name][0], "output": PRICES[name][1]} for name in used
        },
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


def classify_error(exc: Exception) -> str:
    if isinstance(exc, asyncio.TimeoutError):
        return "timeout"
    if isinstance(exc, anthropic.RateLimitError):
        return "rate_limit"
    if isinstance(exc, anthropic.APIStatusError):
        return f"api_{exc.status_code}"
    if isinstance(exc, anthropic.APIConnectionError):
        return "connection"
    return type(exc).__name__


async def run_job(
    *, client, triage_fn, semaphore, run_dir: Path, model: str, version: str, prompt: str, case: Case, rep: int
) -> dict:
    """Runs one job and returns {"cost": float, "error": bool}."""
    base = {"model": model, "version": version, "case_id": case.id, "rep": rep}
    provenance = {
        "case_sha": case_fingerprint(case),
        "prompt_sha": fingerprint(prompt),
        "effort": EFFORT,
        "sdk_version": anthropic.__version__,
        "ran_at": now(),
    }
    async with semaphore:
        try:
            result = await asyncio.wait_for(
                triage_fn(client, model=MODELS[model], system_prompt=prompt, ticket=case.ticket),
                timeout=CASE_TIMEOUT_S,
            )
        except anthropic.AuthenticationError:
            raise
        except Exception as exc:  # recorded and retried on the next run
            if "authentication method" in str(exc):  # the SDK found no credentials at all
                raise MissingCredentials from exc
            append(run_dir / "errors.jsonl", {**base, "error": classify_error(exc), "detail": str(exc)[:300]})
            return {"cost": 0.0, "error": True}

    cost = cost_usd(model, result.input_tokens, result.output_tokens)
    usage = {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens, "cost_usd": cost}

    # A cut-off reply, or a reply from a different model than the one asked for, is not a fair test.
    wrong_model = not result.served_model.startswith(MODELS[model])
    if result.status == "truncated" or wrong_model:
        error = "served_model_mismatch" if wrong_model else "truncated"
        append(run_dir / "errors.jsonl", {**base, "error": error, "served_model": result.served_model, **usage})
        return {"cost": cost, "error": True}

    graded = grade(case.expected, result.output)
    append(
        run_dir / "results.jsonl",
        {
            **base,
            **provenance,
            "tags": list(case.tags),
            "status": result.status,
            "passed": graded["passed"],
            "fields": graded["fields"],
            "summary_ok": graded["summary_ok"],
            "expected": case.expected,
            "output": result.output.model_dump() if result.output else None,
            "raw_text": None if result.output else result.raw_text,
            "stop_reason": result.stop_reason,
            "served_model": result.served_model,
            "latency_s": result.latency_s,
            **usage,
        },
    )
    return {"cost": cost, "error": False}


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
    client=None,
) -> dict:
    run_dir = runs_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    started_at = now()
    code = code_state()  # read before any output is written
    cases = load_cases()[:limit]
    done = load_done(run_dir / "results.jsonl")
    client = client or anthropic.AsyncAnthropic(max_retries=4)
    semaphore = asyncio.Semaphore(concurrency)

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
                            client=client, triage_fn=triage_fn, semaphore=semaphore, run_dir=run_dir,
                            model=model, version=version, prompt=prompt, case=case, rep=rep,
                        )
                    )

    outcomes = await asyncio.gather(*jobs)
    counts = {
        "skipped": len(done),
        "ran": len(outcomes),
        "errors": sum(o["error"] for o in outcomes),
        "cost_usd": round(sum(o["cost"] for o in outcomes), 4),
    }
    write_manifest(
        run_dir,
        {
            "started_at": started_at, "finished_at": now(), **code,
            "models": models, "versions": versions, "reps": reps, "concurrency": concurrency,
            "limit": limit, "cases": len(cases), **counts,
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
    args = parser.parse_args()

    try:
        summary = asyncio.run(
            run(run_name=args.run, models=args.models, versions=args.versions, reps=args.reps,
                concurrency=args.concurrency, limit=args.limit)
        )
    except (anthropic.AuthenticationError, MissingCredentials):
        raise SystemExit("No valid API key. Set ANTHROPIC_API_KEY and run again.")
    except StaleRun as exc:
        raise SystemExit(str(exc))

    print(
        f"ran {summary['ran']} calls, skipped {summary['skipped']} already done, "
        f"{summary['errors']} errors, cost ${summary['cost_usd']:.4f}"
    )
    print(f"results in {summary['run_dir']}")
    if summary["errors"]:
        print("some calls failed. Run the same command again to retry them.")


if __name__ == "__main__":
    main()
