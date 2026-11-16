"""Picks which prompt versions a pull request's regression check should run.

    uv run python -m evals.ci --base origin/main

A pull request that edits a prompt file is the change this suite exists to judge.
The rule:

- If the production prompt (v1_baseline) changed, the new text is compared with
  the text on the base branch, copied to prompts/main_baseline.md for the run.
- Otherwise every changed prompt file is compared with v1_baseline.

It prints the baseline and the versions to run as shell variables, for the CI
workflow to read. If no prompt changed, it prints VERSIONS= and the workflow skips
the paid run.
"""

import argparse
import subprocess
from pathlib import Path

from evals.report import BASELINE

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
MAIN_COPY = "main_baseline"


def changed_versions(changed_paths: list[str]) -> list[str]:
    """Prompt version names among the changed paths, e.g. 'prompts/v3_add_example.md' -> 'v3_add_example'."""
    names = {Path(path).stem for path in changed_paths if Path(path).parent.name == "prompts" and path.endswith(".md")}
    # A deleted prompt has nothing left to run.
    return sorted(name for name in names - {MAIN_COPY} if (PROMPTS_DIR / f"{name}.md").exists())


def plan(changed: list[str]) -> tuple[str, list[str]]:
    """(baseline, versions to run) for a set of changed prompt versions."""
    if not changed:
        return BASELINE, []
    if BASELINE in changed:
        return MAIN_COPY, [MAIN_COPY, *changed]
    return BASELINE, [BASELINE, *changed]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", required=True, help="git ref of the branch the pull request targets")
    args = parser.parse_args()

    paths = git("diff", "--name-only", f"{args.base}...HEAD", "--", "prompts").split()
    baseline, versions = plan(changed_versions(paths))
    if baseline == MAIN_COPY:
        text = git("show", f"{args.base}:{ROOT.name}/prompts/{BASELINE}.md")
        (PROMPTS_DIR / f"{MAIN_COPY}.md").write_text(text)
    print(f"BASELINE={baseline}")
    print(f"VERSIONS={' '.join(versions)}")


if __name__ == "__main__":
    main()
