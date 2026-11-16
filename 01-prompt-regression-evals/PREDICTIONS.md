# Predictions

Written before the first full run. Not edited afterwards.

For each prompt edit, how many of the 40 cases do I expect it to break on each model? "Break" means the case passed every repetition on the baseline and failed most repetitions on the edited prompt.

| Edit               | What changed                                                                            | Haiku 5.5 | Opus 5.5 |
| ------------------ | --------------------------------------------------------------------------------------- | --------- | -------- |
| `v2_keep_it_quick` | One line added at the end: go with the obvious reading, don't overanalyse               | 36        | 34       |
| `v3_add_example`   | One worked example added: a double charge with an invoice ID                            | 35        | 37       |
| `v4_feel_heard`    | Two sentences added near the top: upset customers should get the attention they deserve | 34        | 36       |
| `v5_tidy_urgency`  | The urgency definitions shortened for readability                                       | 36        | 35       |

Baseline pass rate I expect, out of 40: Haiku 38, Opus 37

Date: 15/11/2026
