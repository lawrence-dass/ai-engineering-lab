# Prompt regression report

## haiku

| version | pass rate | 95% interval | category | urgency | refund | invoice | cost | s/call |
|---|---|---|---|---|---|---|---|---|
| v1_baseline | 92.5% | 82.5% to 100.0% | 95.0% | 97.5% | 100.0% | 100.0% | $0.0188 | 1.2 |
| v2_keep_it_quick | 97.5% | 92.5% to 100.0% | 100.0% | 97.5% | 100.0% | 100.0% | $0.0191 | 1.1 |
| v3_add_example | 88.3% | 78.3% to 96.7% | 95.0% | 93.3% | 100.0% | 100.0% | $0.0202 | 1.0 |
| v4_feel_heard | 93.3% | 85.0% to 100.0% | 95.8% | 97.5% | 100.0% | 100.0% | $0.0193 | 1.1 |
| v5_tidy_urgency | 81.7% | 70.0% to 92.5% | 97.5% | 84.2% | 100.0% | 100.0% | $0.0177 | 1.0 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v2_keep_it_quick | v3_add_example | v4_feel_heard | v5_tidy_urgency |
|---|---|---|---|---|---|---|
| easy | 9 | 100% | 100% | 96% | 100% | 89% |
| injection | 1 | 100% | 100% | 100% | 100% | 100% |
| invoice-trap | 7 | 86% | 86% | 86% | 86% | 100% |
| multi-issue | 5 | 80% | 100% | 60% | 80% | 60% |
| noisy | 3 | 67% | 100% | 100% | 78% | 67% |
| refund-trap | 7 | 100% | 100% | 100% | 100% | 71% |
| tone-mismatch | 8 | 100% | 100% | 83% | 100% | 83% |

Wrong answers on v1_baseline:

- category: gave bug, wanted account_access (3 calls, 1 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- urgency: gave low, wanted medium (3 calls, 1 cases)

Wrong answers on v2_keep_it_quick:

- urgency: gave low, wanted medium (3 calls, 1 cases)

Wrong answers on v3_add_example:

- urgency: gave medium, wanted high (5 calls, 3 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- category: gave how_to, wanted billing (3 calls, 1 cases)
- urgency: gave low, wanted medium (3 calls, 1 cases)

Wrong answers on v4_feel_heard:

- category: gave feature_request, wanted bug (3 calls, 1 cases)
- urgency: gave low, wanted medium (3 calls, 1 cases)
- category: gave bug, wanted account_access (2 calls, 1 cases)

Wrong answers on v5_tidy_urgency:

- urgency: gave medium, wanted high (19 calls, 7 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)

### v2_keep_it_quick vs v1_baseline

Pass rate +5.0%. Broken: 0. Fixed: 2. Flaky: 0. Missing: 0.

- **fixed** `t34`
- **fixed** `t38`

### v3_add_example vs v1_baseline

Pass rate -4.2%. Broken: 2. Fixed: 1. Flaky: 2. Missing: 0.

- **broken** `t15`: category: how_to (want billing)
- **broken** `t33`: urgency: medium (want high)
- **fixed** `t38`
- **flaky** `t05`: urgency: medium (want high)
- **flaky** `t14`: urgency: medium (want high)

### v4_feel_heard vs v1_baseline

Pass rate +0.8%. Broken: 0. Fixed: 0. Flaky: 1. Missing: 0.

- **flaky** `t38`: category: bug (want account_access)

### v5_tidy_urgency vs v1_baseline

Pass rate -10.8%. Broken: 6. Fixed: 2. Flaky: 1. Missing: 0.

- **broken** `t06`: urgency: medium (want high)
- **broken** `t16`: urgency: medium (want high)
- **broken** `t21`: urgency: medium (want high)
- **broken** `t24`: urgency: medium (want high)
- **broken** `t35`: urgency: medium (want high)
- **broken** `t40`: urgency: medium (want high)
- **fixed** `t29`
- **fixed** `t38`
- **flaky** `t12`: urgency: medium (want high)

## luna

| version | pass rate | 95% interval | category | urgency | refund | invoice | cost | s/call |
|---|---|---|---|---|---|---|---|---|
| v1_baseline | 95.8% | 91.7% to 99.2% | 95.8% | 100.0% | 100.0% | 100.0% | $0.0112 | 1.6 |
| v2_keep_it_quick | 96.7% | 90.8% to 100.0% | 96.7% | 100.0% | 100.0% | 100.0% | $0.0111 | 1.4 |
| v3_add_example | 92.5% | 85.0% to 98.3% | 96.7% | 95.8% | 100.0% | 100.0% | $0.0120 | 1.7 |
| v4_feel_heard | 95.8% | 90.8% to 99.2% | 95.8% | 100.0% | 100.0% | 100.0% | $0.0116 | 1.8 |
| v5_tidy_urgency | 74.2% | 60.0% to 86.7% | 94.2% | 80.0% | 100.0% | 100.0% | $0.0104 | 1.5 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v2_keep_it_quick | v3_add_example | v4_feel_heard | v5_tidy_urgency |
|---|---|---|---|---|---|---|
| easy | 9 | 100% | 100% | 100% | 100% | 89% |
| injection | 1 | 100% | 100% | 100% | 100% | 100% |
| invoice-trap | 7 | 95% | 100% | 90% | 95% | 90% |
| multi-issue | 5 | 80% | 73% | 87% | 80% | 53% |
| noisy | 3 | 100% | 100% | 67% | 100% | 56% |
| refund-trap | 7 | 100% | 100% | 95% | 100% | 71% |
| tone-mismatch | 8 | 96% | 100% | 96% | 96% | 62% |

Wrong answers on v1_baseline:

- category: gave account_access, wanted bug (2 calls, 1 cases)
- category: gave billing, wanted how_to (1 calls, 1 cases)
- category: gave bug, wanted billing (1 calls, 1 cases)
- category: gave how_to, wanted billing (1 calls, 1 cases)

Wrong answers on v2_keep_it_quick:

- category: gave billing, wanted how_to (3 calls, 1 cases)
- category: gave account_access, wanted bug (1 calls, 1 cases)

Wrong answers on v3_add_example:

- urgency: gave low, wanted medium (4 calls, 2 cases)
- category: gave billing, wanted how_to (2 calls, 1 cases)
- category: gave bug, wanted billing (1 calls, 1 cases)
- category: gave how_to, wanted billing (1 calls, 1 cases)
- urgency: gave medium, wanted low (1 calls, 1 cases)

Wrong answers on v4_feel_heard:

- category: gave account_access, wanted bug (2 calls, 1 cases)
- category: gave how_to, wanted billing (2 calls, 2 cases)
- category: gave billing, wanted how_to (1 calls, 1 cases)

Wrong answers on v5_tidy_urgency:

- urgency: gave low, wanted high (11 calls, 5 cases)
- urgency: gave medium, wanted high (10 calls, 5 cases)
- category: gave billing, wanted how_to (3 calls, 1 cases)
- category: gave how_to, wanted billing (3 calls, 1 cases)
- urgency: gave low, wanted medium (3 calls, 2 cases)
- category: gave account_access, wanted bug (1 calls, 1 cases)

### v2_keep_it_quick vs v1_baseline

Pass rate +0.8%. Broken: 0. Fixed: 0. Flaky: 4. Missing: 0.

- **flaky** `t15`
- **flaky** `t30`
- **flaky** `t34`: category: account_access (want bug)
- **flaky** `t36`: category: billing (want how_to)

### v3_add_example vs v1_baseline

Pass rate -3.3%. Broken: 1. Fixed: 0. Flaky: 4. Missing: 0.

- **broken** `t38`: urgency: low (want medium)
- **flaky** `t22`: urgency: medium (want low)
- **flaky** `t29`: urgency: low (want medium)
- **flaky** `t34`
- **flaky** `t36`: category: billing (want how_to)

### v4_feel_heard vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 2. Missing: 0.

- **flaky** `t28`: category: how_to (want billing)
- **flaky** `t30`

### v5_tidy_urgency vs v1_baseline

Pass rate -21.7%. Broken: 8. Fixed: 0. Flaky: 5. Missing: 0.

- **broken** `t06`: urgency: low (want high)
- **broken** `t12`: urgency: medium (want high)
- **broken** `t16`: urgency: medium (want high)
- **broken** `t21`: urgency: low (want high), medium (want high)
- **broken** `t24`: urgency: low (want high), medium (want high)
- **broken** `t29`: urgency: low (want medium)
- **broken** `t35`: urgency: low (want high), medium (want high)
- **broken** `t40`: urgency: low (want high)
- **flaky** `t15`: category: how_to (want billing)
- **flaky** `t30`
- **flaky** `t34`: category: account_access (want bug)
- **flaky** `t36`: category: billing (want how_to)
- **flaky** `t38`: urgency: low (want medium)

