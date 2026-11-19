# ai-engineering-lab

Small experiments on how LLM systems fail in production, and what fixes them. Each one is built for an article, broken on purpose, and measured.

Every folder stands alone: its own README, dependencies and run command. Nothing is shared between folders, so you can read or run one without the others.

| # | Experiment | Question | Stack | Article |
|---|---|---|---|---|
| 01 | [prompt-regression-evals](01-prompt-regression-evals/) | How many test cases does a harmless-looking prompt edit break? | Python, Claude and OpenAI APIs | [I tidied up a prompt. It broke 7 support tickets.](https://www.lawrence-dass.com/blog/prompt_regression_evals) |

## Conventions

- Folders are numbered in publish order.
- Every experiment starts with a `PROBLEM.md`, written from [`templates/PROBLEM_TEMPLATE.md`](templates/PROBLEM_TEMPLATE.md) before any code. It describes the problem and its parts, and nothing about the solution.
- Once the problem statement is approved, a `SOLUTION.md` from [`templates/SOLUTION_TEMPLATE.md`](templates/SOLUTION_TEMPLATE.md) records the design, each decision with the alternative that was turned down, and how every part of the problem is handled. The README covers how to run it and the results.
- Both documents have one owner and a status: Draft, In review, Approved, Implemented or Superseded. Changes go through commits and are noted in the change log. When the article is published the status moves to Implemented and the documents become a record.
- Once its article is published, an experiment only gets fixes. The code stays in step with what the article says.
- Each experiment README follows [`templates/README_TEMPLATE.md`](templates/README_TEMPLATE.md): the result first, then how to run it, the setup, the evidence, the limits and the credits. The detailed design stays in `SOLUTION.md`.
- Results from the real runs are committed under `runs/<name>/`, so every number in an article can be traced to a row: `results.jsonl`, `errors.jsonl`, `report.md`, and a `manifest.json` with the code commit, model IDs, run settings and prices. The experiment README links to the published run.
- Charts and screenshots used in an article go in the experiment's `assets/` folder.
- CI workflows live in `.github/workflows/` at the repository root, one per experiment, triggered only by changes to that experiment's folder or to the workflow itself.

Written by [Lawrence Dass](https://lawrence-dass.com). MIT licence.
