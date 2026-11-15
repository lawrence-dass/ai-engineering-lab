# <NN> · <experiment-name>

<!--
Copy this file to <NN-experiment-name>/README.md.
The README covers the result and how to run it. The design and its reasons belong in SOLUTION.md.
Keep the failure and the fix on the first screen. Delete these comments as you fill each section in.
-->

<One sentence: what this is and the question it answers.>

Article: <link, or "coming DD Mon YYYY">

## Result

<!--
The failure and the fix, with the numbers, in three to five lines. Lead with the verdict.
Every number comes from the run linked under Evidence. Until that run exists, write "Pending the first full run." and nothing else.
-->

## Run it

You need <language and version> and <tools, with install links>.

```bash
git clone https://github.com/lawrence-dass/ai-engineering-lab.git
cd ai-engineering-lab/<NN-experiment-name>
<install command, locked to the lock file>
```

### Free: <tests or offline mode>

<!-- What runs with no API key and no cost, and how long it takes. -->

```bash
<command>
```

### Paid: <runs against a model or service>

<!-- Which key is needed (point to .env.example), a small pilot command first, then the full run with its call count and measured cost. -->

```bash
<pilot command>
<full run command>
```

## Setup

<!--
What was tested, in a short table or list: the system under test, the data, the conditions compared, the models and settings.
One paragraph on what was broken on purpose. Link to PROBLEM.md and SOLUTION.md for the rest.
-->

## Evidence

<!-- Link the committed run directly. Keep these four files for every published run. -->

Published run: [`runs/<name>/`](runs/<name>/), from commit `<short sha>`.

| File | What it holds |
|---|---|
| `results.jsonl` | One row per finished call or trial |
| `errors.jsonl` | Calls that failed before giving a usable result |
| `report.md` | The generated comparison the article quotes |
| `manifest.json` | Code commit, resolved model IDs, run settings and the prices used for cost |

<!-- Charts and screenshots used in the article go in assets/ and are shown or linked here. -->

## Limits

<!-- What this does not show. Sample size, synthetic data, one model family, one run. Restate the assumptions from PROBLEM.md that could be false. -->

## Article and credits

<!-- Link to the article. Name each resource that guided the design, with a link and what it contributed. State that the code is your own. -->
