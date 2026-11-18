# Review

## 1. The rule as shipped: one call per ticket, business rules only

| Model | Version | Calls | Sent to review | Wrong answers | Caught by review | Slipped through | Reasons |
|---|---|---|---|---|---|---|---|
| haiku | v1_baseline | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| haiku | v7_tidy_keep_lists | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| luna | v1_baseline | 150 | 12% | 21 | 1 | 20 | rule:account_access 18 |
| luna | v7_tidy_keep_lists | 150 | 12% | 24 | 2 | 22 | rule:account_access 18 |

## 2. Simulated: three calls per ticket, plus review when the calls disagree

Answer = majority of the repeated calls. Review when the calls disagree on a graded field, a reply was unusable, or the answer is account_access. The expected answer stands in for the reviewer. No majority = the calls split with no majority on a field, so there is no answer to call right or wrong; those tickets go to review and are not counted as wrong answers.

| Model | Version | Tickets | Automatic | Sent to review | Accuracy of automatic | Wrong answers | Caught by review | Slipped through | No majority | Accuracy, one call, no review |
|---|---|---|---|---|---|---|---|---|---|---|
| haiku | v1_baseline | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| haiku | v7_tidy_keep_lists | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| luna | v1_baseline | 50 | 84% | 16% | 86% | 6 | 0 | 6 | 0 | 88% |
| luna | v7_tidy_keep_lists | 50 | 86% | 14% | 84% | 8 | 1 | 7 | 0 | 86% |

## Why tickets went to review

- haiku v1_baseline: rule:account_access 6
- haiku v7_tidy_keep_lists: rule:account_access 6
- luna v1_baseline: rule:account_access 6, disagreement:category 2, disagreement:urgency 1
- luna v7_tidy_keep_lists: rule:account_access 6, disagreement:category 1, disagreement:urgency 1

## Wrong answers that slipped through (all calls agreed, and they were wrong)

- haiku v1_baseline: h02, h04, h05, h07, h08, t34
- haiku v7_tidy_keep_lists: h02, h04, h05, h07, h08, t34
- luna v1_baseline: h02, h04, h05, h07, h08, t29
- luna v7_tidy_keep_lists: h02, h04, h05, h07, h08, t29, t36
