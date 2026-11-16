# Review simulation

Answer = majority of the repeated calls. Review when the calls disagree on a graded field, a reply was unusable, or the answer is account_access. The expected answer stands in for the reviewer.

| Model | Version | Tickets | Automatic | Sent to review | Accuracy of automatic | Wrong answers | Caught by review | Slipped through | Accuracy, one call, no review |
|---|---|---|---|---|---|---|---|---|---|
| haiku | v1_baseline | 40 | 90% | 10% | 92% | 3 | 0 | 3 | 92% |
| haiku | v2_keep_it_quick | 40 | 88% | 12% | 97% | 1 | 0 | 1 | 98% |
| haiku | v3_add_example | 40 | 85% | 15% | 91% | 4 | 1 | 3 | 90% |
| haiku | v4_feel_heard | 40 | 88% | 12% | 94% | 3 | 1 | 2 | 92% |
| haiku | v5_tidy_urgency | 40 | 88% | 12% | 80% | 7 | 0 | 7 | 82% |
| luna | v1_baseline | 40 | 78% | 22% | 100% | 1 | 1 | 0 | 95% |
| luna | v2_keep_it_quick | 40 | 85% | 15% | 97% | 1 | 0 | 1 | 95% |
| luna | v3_add_example | 40 | 75% | 25% | 100% | 2 | 2 | 0 | 92% |
| luna | v4_feel_heard | 40 | 78% | 22% | 100% | 1 | 1 | 0 | 95% |
| luna | v5_tidy_urgency | 40 | 75% | 25% | 83% | 10 | 5 | 5 | 72% |

## Why tickets went to review

- haiku v1_baseline: rule:account_access 4
- haiku v2_keep_it_quick: rule:account_access 5
- haiku v3_add_example: rule:account_access 5, disagreement:urgency 2
- haiku v4_feel_heard: rule:account_access 4, disagreement:category 1
- haiku v5_tidy_urgency: rule:account_access 5, disagreement:urgency 1
- luna v1_baseline: rule:account_access 6, disagreement:category 4
- luna v2_keep_it_quick: rule:account_access 5, disagreement:category 1
- luna v3_add_example: rule:account_access 5, disagreement:category 3, disagreement:urgency 2
- luna v4_feel_heard: rule:account_access 6, disagreement:category 4
- luna v5_tidy_urgency: rule:account_access 5, disagreement:urgency 5, disagreement:category 1

## Wrong answers that slipped through (all calls agreed, and they were wrong)

- haiku v1_baseline: t29, t34, t38
- haiku v2_keep_it_quick: t29
- haiku v3_add_example: t15, t29, t34
- haiku v4_feel_heard: t29, t34
- haiku v5_tidy_urgency: t06, t16, t21, t24, t34, t35, t40
- luna v2_keep_it_quick: t36
- luna v5_tidy_urgency: t06, t15, t16, t36, t40
