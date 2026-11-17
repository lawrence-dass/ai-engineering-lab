# Predictions

Each round is written before its run and not edited afterwards.

## Round 2: the rebuilt prompts (2026-11-16)

For each edit, how many of the 50 cases (40 visible, 10 held-out) do I expect it to break on each model? "Break" means the case passed every repetition on the baseline and failed most repetitions on the edited prompt.

| Edit               | What changed                                                                                        | Haiku 5.5 | Opus 5.5 | GPT-6 Luna | GPT-6.1 Sol |
| ------------------ | --------------------------------------------------------------------------------------------------- | --------- | -------- | ---------- | ----------- |
| `v2_keep_it_quick` | One line at the end: go with the obvious reading, don't overanalyse                                 | 2         | 1        | 1          | 0           |
| `v3_add_example`   | One more worked example: a double charge with an invoice ID                                         | 0         | 0        | 1          | 0           |
| `v4_feel_heard`    | Two sentences near the top: upset customers should get the attention they deserve                   | 3         | 2        | 2          | 1           |
| `v5_tidy_urgency`  | The urgency definitions and the tone rule shortened for readability                                 | 2         | 1        | 2          | 1           |
| `v6_bundled_pr`    | Three changes at once: a shorter refund rule, a vaguer multi-issue rule, "if unsure, choose medium" | 3         | 2        | 4          | 2           |

Baseline pass rate I expect, out of 50: Haiku 38, Opus 39, Luna 37, Sol 39

Date: 16/11/2026

## Round 1: the first prompts (2026-11-15)

Written for the first version of the prompts, which had no sections and no worked examples. Superseded on 2026-11-16 when the prompts were rebuilt. Kept as written. The stage 1 run against these prompts is in `runs/round1/`.

For each prompt edit, how many of the 40 cases do I expect it to break on each model? "Break" means the case passed every repetition on the baseline and failed most repetitions on the edited prompt.

| Edit               | What changed                                                                            | Haiku 5.5 | Opus 5.5 | GPT-6 Luna | GPT-6.1 Sol |
| ------------------ | --------------------------------------------------------------------------------------- | --------- | -------- | ---------- | ----------- |
| `v2_keep_it_quick` | One line added at the end: go with the obvious reading, don't overanalyse               | 4         | 6        | 7          | 6           |
| `v3_add_example`   | One worked example added: a double charge with an invoice ID                            | 5         | 3        | 6          | 5           |
| `v4_feel_heard`    | Two sentences added near the top: upset customers should get the attention they deserve | 6         | 4        | 8          | 6           |
| `v5_tidy_urgency`  | The urgency definitions shortened for readability                                       | 4         | 5        | 8          | 5           |

Baseline pass rate I expect, out of 40: Haiku 38, Opus 37, Luna ?, Sol ?

Date: 15/11/2026
