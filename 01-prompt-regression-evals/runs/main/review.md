# Review

## 1. The rule as shipped: one call per ticket, business rules only

| Model | Version | Calls | Sent to review | Wrong answers | Caught by review | Slipped through | Reasons |
|---|---|---|---|---|---|---|---|
| haiku | v1_baseline | 150 | 12% | 19 | 0 | 19 | rule:account_access 18 |
| haiku | v2_keep_it_quick | 150 | 12% | 16 | 1 | 15 | rule:account_access 18 |
| haiku | v3_add_example | 150 | 12% | 24 | 3 | 21 | rule:account_access 18 |
| haiku | v4_feel_heard | 150 | 12% | 21 | 3 | 18 | rule:account_access 18 |
| haiku | v5_tidy_urgency | 150 | 12% | 36 | 0 | 36 | rule:account_access 18 |
| haiku | v6_bundled_pr | 150 | 12% | 19 | 0 | 19 | rule:account_access 18 |
| luna | v1_baseline | 150 | 12% | 21 | 0 | 21 | rule:account_access 18 |
| luna | v2_keep_it_quick | 150 | 12% | 25 | 3 | 22 | rule:account_access 18 |
| luna | v3_add_example | 150 | 12% | 23 | 0 | 23 | rule:account_access 18 |
| luna | v4_feel_heard | 150 | 12% | 21 | 0 | 21 | rule:account_access 18 |
| luna | v5_tidy_urgency | 150 | 12% | 42 | 2 | 40 | rule:account_access 18 |
| luna | v6_bundled_pr | 150 | 12% | 25 | 2 | 23 | rule:account_access 18 |
| opus | v1_baseline | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| opus | v2_keep_it_quick | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| opus | v3_add_example | 150 | 12% | 15 | 0 | 15 | rule:account_access 18 |
| opus | v4_feel_heard | 150 | 12% | 16 | 0 | 16 | rule:account_access 18 |
| opus | v5_tidy_urgency | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| opus | v6_bundled_pr | 150 | 12% | 15 | 0 | 15 | rule:account_access 18 |
| sol | v1_baseline | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| sol | v2_keep_it_quick | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| sol | v3_add_example | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| sol | v4_feel_heard | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |
| sol | v5_tidy_urgency | 150 | 12% | 16 | 0 | 16 | rule:account_access 18 |
| sol | v6_bundled_pr | 150 | 12% | 18 | 0 | 18 | rule:account_access 18 |

## 2. Simulated: three calls per ticket, plus review when the calls disagree

Answer = majority of the repeated calls. Review when the calls disagree on a graded field, a reply was unusable, or the answer is account_access. The expected answer stands in for the reviewer. No majority = the calls split with no majority on a field, so there is no answer to call right or wrong; those tickets go to review and are not counted as wrong answers.

| Model | Version | Tickets | Automatic | Sent to review | Accuracy of automatic | Wrong answers | Caught by review | Slipped through | No majority | Accuracy, one call, no review |
|---|---|---|---|---|---|---|---|---|---|---|
| haiku | v1_baseline | 50 | 86% | 14% | 86% | 6 | 0 | 6 | 0 | 88% |
| haiku | v2_keep_it_quick | 50 | 88% | 12% | 89% | 5 | 0 | 5 | 0 | 90% |
| haiku | v3_add_example | 50 | 88% | 12% | 84% | 8 | 1 | 7 | 0 | 84% |
| haiku | v4_feel_heard | 50 | 88% | 12% | 86% | 7 | 1 | 6 | 0 | 86% |
| haiku | v5_tidy_urgency | 50 | 88% | 12% | 73% | 12 | 0 | 12 | 0 | 76% |
| haiku | v6_bundled_pr | 50 | 86% | 14% | 86% | 6 | 0 | 6 | 0 | 88% |
| luna | v1_baseline | 50 | 84% | 16% | 86% | 7 | 1 | 6 | 0 | 86% |
| luna | v2_keep_it_quick | 50 | 86% | 14% | 84% | 8 | 1 | 7 | 0 | 84% |
| luna | v3_add_example | 50 | 86% | 14% | 84% | 8 | 1 | 7 | 0 | 86% |
| luna | v4_feel_heard | 50 | 84% | 16% | 86% | 7 | 1 | 6 | 0 | 84% |
| luna | v5_tidy_urgency | 50 | 78% | 22% | 77% | 14 | 5 | 9 | 1 | 72% |
| luna | v6_bundled_pr | 50 | 84% | 16% | 83% | 8 | 1 | 7 | 0 | 84% |
| opus | v1_baseline | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| opus | v2_keep_it_quick | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| opus | v3_add_example | 50 | 88% | 12% | 89% | 5 | 0 | 5 | 0 | 90% |
| opus | v4_feel_heard | 50 | 86% | 14% | 88% | 5 | 0 | 5 | 0 | 90% |
| opus | v5_tidy_urgency | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| opus | v6_bundled_pr | 50 | 88% | 12% | 89% | 5 | 0 | 5 | 0 | 90% |
| sol | v1_baseline | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| sol | v2_keep_it_quick | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| sol | v3_add_example | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| sol | v4_feel_heard | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |
| sol | v5_tidy_urgency | 50 | 86% | 14% | 88% | 5 | 0 | 5 | 0 | 90% |
| sol | v6_bundled_pr | 50 | 88% | 12% | 86% | 6 | 0 | 6 | 0 | 88% |

## Why tickets went to review

- haiku v1_baseline: rule:account_access 6, disagreement:urgency 1
- haiku v2_keep_it_quick: rule:account_access 6, disagreement:urgency 1
- haiku v3_add_example: rule:account_access 6
- haiku v4_feel_heard: rule:account_access 6
- haiku v5_tidy_urgency: rule:account_access 6
- haiku v6_bundled_pr: rule:account_access 6, disagreement:category 1
- luna v1_baseline: rule:account_access 6, disagreement:category 2
- luna v2_keep_it_quick: rule:account_access 6, disagreement:category 1
- luna v3_add_example: rule:account_access 6, disagreement:category 1
- luna v4_feel_heard: rule:account_access 6, disagreement:category 2
- luna v5_tidy_urgency: rule:account_access 6, disagreement:urgency 5, disagreement:category 1
- luna v6_bundled_pr: rule:account_access 6, disagreement:category 2, disagreement:urgency 2
- opus v1_baseline: rule:account_access 6
- opus v2_keep_it_quick: rule:account_access 6
- opus v3_add_example: rule:account_access 6
- opus v4_feel_heard: rule:account_access 6, disagreement:urgency 1
- opus v5_tidy_urgency: rule:account_access 6
- opus v6_bundled_pr: rule:account_access 6
- sol v1_baseline: rule:account_access 6
- sol v2_keep_it_quick: rule:account_access 6
- sol v3_add_example: rule:account_access 6
- sol v4_feel_heard: rule:account_access 6
- sol v5_tidy_urgency: rule:account_access 6, disagreement:urgency 1
- sol v6_bundled_pr: rule:account_access 6

## Wrong answers that slipped through (all calls agreed, and they were wrong)

- haiku v1_baseline: h02, h04, h05, h07, h08, t34
- haiku v2_keep_it_quick: h02, h04, h05, h07, h08
- haiku v3_add_example: h02, h04, h05, h07, h08, t29, t34
- haiku v4_feel_heard: h02, h04, h05, h07, h08, t34
- haiku v5_tidy_urgency: h02, h04, h05, h07, h08, t06, t16, t21, t24, t34, t35, t40
- haiku v6_bundled_pr: h02, h04, h05, h07, h08, t34
- luna v1_baseline: h02, h04, h05, h07, h08, t29
- luna v2_keep_it_quick: h02, h04, h05, h07, h08, t29, t36
- luna v3_add_example: h02, h04, h05, h07, h08, t29, t36
- luna v4_feel_heard: h02, h04, h05, h07, h08, t29
- luna v5_tidy_urgency: h02, h04, h05, h07, h08, t06, t29, t36, t40
- luna v6_bundled_pr: h02, h04, h05, h07, h08, t29, t36
- opus v1_baseline: h02, h04, h05, h07, h08, t29
- opus v2_keep_it_quick: h02, h04, h05, h07, h08, t29
- opus v3_add_example: h02, h04, h05, h07, h08
- opus v4_feel_heard: h02, h04, h05, h07, h08
- opus v5_tidy_urgency: h02, h04, h05, h07, h08, t40
- opus v6_bundled_pr: h02, h04, h05, h07, h08
- sol v1_baseline: h02, h04, h05, h07, h08, t30
- sol v2_keep_it_quick: h02, h04, h05, h07, h08, t30
- sol v3_add_example: h02, h04, h05, h07, h08, t30
- sol v4_feel_heard: h02, h04, h05, h07, h08, t30
- sol v5_tidy_urgency: h02, h04, h05, h07, h08
- sol v6_bundled_pr: h02, h04, h05, h07, h08, t30
