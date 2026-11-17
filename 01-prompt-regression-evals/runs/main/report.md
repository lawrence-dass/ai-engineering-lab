# Prompt regression report

## haiku

| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice | cost | $/call | $/correct | s/call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1_baseline | 87.3% | 77.3% to 96.0% | 96.7% | 50.0% | 98.0% | 89.3% | 98.0% | 98.0% | $0.0101 | $0.00007 | $0.00008 | 1.0 |
| v2_keep_it_quick | 89.3% | 80.0% to 97.3% | 99.2% | 50.0% | 100.0% | 89.3% | 98.0% | 98.0% | $0.0099 | $0.00007 | $0.00007 | 1.1 |
| v3_add_example | 84.0% | 74.0% to 94.0% | 92.5% | 50.0% | 98.0% | 86.0% | 98.0% | 98.0% | $0.0098 | $0.00007 | $0.00008 | 1.0 |
| v4_feel_heard | 86.0% | 76.0% to 94.0% | 95.0% | 50.0% | 98.0% | 88.0% | 98.0% | 98.0% | $0.0096 | $0.00006 | $0.00007 | 1.5 |
| v5_tidy_urgency | 76.0% | 64.0% to 88.0% | 82.5% | 50.0% | 98.0% | 76.0% | 98.0% | 98.0% | $0.0099 | $0.00007 | $0.00009 | 1.0 |
| v6_bundled_pr | 87.3% | 78.0% to 96.0% | 96.7% | 50.0% | 97.3% | 88.0% | 98.0% | 98.0% | $0.0099 | $0.00007 | $0.00008 | 1.0 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v2_keep_it_quick | v3_add_example | v4_feel_heard | v5_tidy_urgency | v6_bundled_pr |
|---|---|---|---|---|---|---|---|
| easy | 12 | 100% | 100% | 100% | 100% | 92% | 100% |
| injection | 2 | 50% | 50% | 50% | 50% | 50% | 50% |
| invoice-trap | 8 | 83% | 88% | 75% | 88% | 88% | 88% |
| multi-issue | 6 | 83% | 94% | 67% | 67% | 67% | 83% |
| noisy | 4 | 75% | 75% | 75% | 75% | 50% | 75% |
| refund-trap | 8 | 88% | 88% | 88% | 88% | 62% | 88% |
| tone-mismatch | 10 | 90% | 90% | 90% | 90% | 80% | 87% |

Wrong answers on v1_baseline:

- urgency: gave low, wanted medium (10 calls, 4 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v2_keep_it_quick:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- urgency: gave medium, wanted high (1 calls, 1 cases)

Wrong answers on v3_add_example:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted high (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v4_feel_heard:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted high (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v5_tidy_urgency:

- urgency: gave medium, wanted high (18 calls, 6 cases)
- urgency: gave low, wanted medium (12 calls, 4 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v6_bundled_pr:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave how_to, wanted billing (1 calls, 1 cases)

### v2_keep_it_quick vs v1_baseline

Pass rate +2.0%. Broken: 0. Fixed: 1. Flaky: 2. Missing: 0. Urgency lowered: 0.

- **fixed** `t34`
- **flaky** `t29`
- **flaky** `t33`: urgency: medium (want high)

### v3_add_example vs v1_baseline

Pass rate -3.3%. Broken: 1. Fixed: 0. Flaky: 1. Missing: 0. Urgency lowered: 1.

- **broken** `t33`: urgency: medium (want high)
- **flaky** `t29`: urgency: low (want medium)

### v4_feel_heard vs v1_baseline

Pass rate -1.3%. Broken: 1. Fixed: 0. Flaky: 1. Missing: 0. Urgency lowered: 1.

- **broken** `t33`: urgency: medium (want high)
- **flaky** `t29`

### v5_tidy_urgency vs v1_baseline

Pass rate -11.3%. Broken: 6. Fixed: 0. Flaky: 1. Missing: 0. Urgency lowered: 7.

- **broken** `t06`: urgency: medium (want high)
- **broken** `t16`: urgency: medium (want high)
- **broken** `t21`: urgency: medium (want high)
- **broken** `t24`: urgency: medium (want high)
- **broken** `t35`: urgency: medium (want high)
- **broken** `t40`: urgency: medium (want high)
- **flaky** `t29`

### v6_bundled_pr vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 2. Missing: 0. Urgency lowered: 1.

- **flaky** `t15`: category: how_to (want billing)
- **flaky** `t29`

## luna

| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice | cost | $/call | $/correct | s/call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1_baseline | 86.0% | 76.0% to 94.7% | 95.0% | 50.0% | 98.0% | 88.0% | 98.0% | 98.0% | $0.0063 | $0.00004 | $0.00005 | 1.5 |
| v2_keep_it_quick | 83.3% | 73.3% to 93.3% | 91.7% | 50.0% | 97.3% | 86.0% | 98.0% | 98.0% | $0.0061 | $0.00004 | $0.00005 | 1.6 |
| v3_add_example | 84.7% | 74.0% to 94.0% | 93.3% | 50.0% | 96.7% | 88.0% | 98.0% | 98.0% | $0.0063 | $0.00004 | $0.00005 | 1.5 |
| v4_feel_heard | 86.0% | 76.0% to 94.7% | 95.0% | 50.0% | 98.0% | 88.0% | 98.0% | 98.0% | $0.0066 | $0.00004 | $0.00005 | 1.4 |
| v5_tidy_urgency | 72.0% | 59.3% to 84.0% | 77.5% | 50.0% | 96.7% | 75.3% | 98.0% | 98.0% | $0.0165 | $0.00011 | $0.00015 | 1.2 |
| v6_bundled_pr | 83.3% | 73.3% to 92.7% | 91.7% | 50.0% | 96.7% | 86.0% | 98.0% | 98.0% | $0.0121 | $0.00008 | $0.00010 | 1.4 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v2_keep_it_quick | v3_add_example | v4_feel_heard | v5_tidy_urgency | v6_bundled_pr |
|---|---|---|---|---|---|---|---|
| easy | 12 | 100% | 100% | 100% | 100% | 92% | 100% |
| injection | 2 | 50% | 50% | 50% | 50% | 50% | 50% |
| invoice-trap | 8 | 71% | 71% | 67% | 71% | 67% | 75% |
| multi-issue | 6 | 89% | 83% | 83% | 89% | 72% | 78% |
| noisy | 4 | 75% | 50% | 75% | 75% | 33% | 58% |
| refund-trap | 8 | 88% | 88% | 88% | 88% | 62% | 88% |
| tone-mismatch | 10 | 90% | 90% | 90% | 90% | 80% | 87% |

Wrong answers on v1_baseline:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave billing, wanted how_to (2 calls, 1 cases)
- category: gave bug, wanted billing (1 calls, 1 cases)

Wrong answers on v2_keep_it_quick:

- urgency: gave low, wanted medium (15 calls, 5 cases)
- category: gave billing, wanted how_to (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave bug, wanted billing (1 calls, 1 cases)

Wrong answers on v3_add_example:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- category: gave billing, wanted how_to (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave bug, wanted billing (2 calls, 1 cases)

Wrong answers on v4_feel_heard:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave billing, wanted how_to (2 calls, 1 cases)
- category: gave bug, wanted billing (1 calls, 1 cases)

Wrong answers on v5_tidy_urgency:

- urgency: gave low, wanted medium (14 calls, 5 cases)
- urgency: gave medium, wanted high (11 calls, 6 cases)
- urgency: gave low, wanted high (6 calls, 4 cases)
- category: gave billing, wanted how_to (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave bug, wanted billing (2 calls, 1 cases)

Wrong answers on v6_bundled_pr:

- urgency: gave low, wanted medium (15 calls, 6 cases)
- category: gave billing, wanted how_to (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave feature_request, wanted bug (1 calls, 1 cases)
- category: gave how_to, wanted billing (1 calls, 1 cases)

### v2_keep_it_quick vs v1_baseline

Pass rate -2.7%. Broken: 1. Fixed: 0. Flaky: 1. Missing: 0. Urgency lowered: 1.

- **broken** `t38`: urgency: low (want medium)
- **flaky** `t36`: category: billing (want how_to)

### v3_add_example vs v1_baseline

Pass rate -1.3%. Broken: 0. Fixed: 0. Flaky: 2. Missing: 0. Urgency lowered: 0.

- **flaky** `t30`: category: bug (want billing)
- **flaky** `t36`: category: billing (want how_to)

### v4_feel_heard vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

### v5_tidy_urgency vs v1_baseline

Pass rate -14.0%. Broken: 7. Fixed: 0. Flaky: 2. Missing: 0. Urgency lowered: 7.

- **broken** `t06`: urgency: medium (want high)
- **broken** `t16`: urgency: low (want high), medium (want high)
- **broken** `t21`: urgency: low (want high), medium (want high)
- **broken** `t24`: urgency: low (want high), medium (want high)
- **broken** `t35`: urgency: low (want high), medium (want high)
- **broken** `t38`: urgency: low (want medium)
- **broken** `t40`: urgency: medium (want high)
- **flaky** `t30`: category: bug (want billing)
- **flaky** `t36`: category: billing (want how_to)

### v6_bundled_pr vs v1_baseline

Pass rate -2.7%. Broken: 1. Fixed: 0. Flaky: 4. Missing: 0. Urgency lowered: 1.

- **broken** `t38`: urgency: low (want medium)
- **flaky** `t15`: category: how_to (want billing)
- **flaky** `t30`
- **flaky** `t34`: category: feature_request (want bug); urgency: low (want medium)
- **flaky** `t36`: category: billing (want how_to)

## opus

| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice | cost | $/call | $/correct | s/call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1_baseline | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 100.0% | 88.0% | 98.0% | 98.0% | $0.3434 | $0.00229 | $0.00260 | 1.9 |
| v2_keep_it_quick | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 100.0% | 88.0% | 98.0% | 98.0% | $0.3361 | $0.00224 | $0.00255 | 1.6 |
| v3_add_example | 90.0% | 80.0% to 98.0% | 100.0% | 50.0% | 100.0% | 90.0% | 98.0% | 98.0% | $0.3494 | $0.00233 | $0.00259 | 1.7 |
| v4_feel_heard | 89.3% | 80.0% to 97.3% | 99.2% | 50.0% | 100.0% | 89.3% | 98.0% | 98.0% | $0.3187 | $0.00212 | $0.00238 | 1.7 |
| v5_tidy_urgency | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 100.0% | 88.0% | 98.0% | 98.0% | $0.3440 | $0.00229 | $0.00261 | 1.7 |
| v6_bundled_pr | 90.0% | 80.0% to 98.0% | 100.0% | 50.0% | 100.0% | 90.0% | 98.0% | 98.0% | $0.3266 | $0.00218 | $0.00242 | 1.8 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v2_keep_it_quick | v3_add_example | v4_feel_heard | v5_tidy_urgency | v6_bundled_pr |
|---|---|---|---|---|---|---|---|
| easy | 12 | 100% | 100% | 100% | 100% | 100% | 100% |
| injection | 2 | 50% | 50% | 50% | 50% | 50% | 50% |
| invoice-trap | 8 | 75% | 75% | 88% | 83% | 88% | 88% |
| multi-issue | 6 | 100% | 100% | 100% | 100% | 100% | 100% |
| noisy | 4 | 75% | 75% | 75% | 75% | 50% | 75% |
| refund-trap | 8 | 88% | 88% | 88% | 88% | 88% | 88% |
| tone-mismatch | 10 | 90% | 90% | 90% | 90% | 90% | 90% |

Wrong answers on v1_baseline:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v2_keep_it_quick:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v3_add_example:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v4_feel_heard:

- urgency: gave low, wanted medium (10 calls, 4 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v5_tidy_urgency:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted high (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v6_bundled_pr:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

### v2_keep_it_quick vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

### v3_add_example vs v1_baseline

Pass rate +2.0%. Broken: 0. Fixed: 1. Flaky: 0. Missing: 0. Urgency lowered: 0.

- **fixed** `t29`

### v4_feel_heard vs v1_baseline

Pass rate +1.3%. Broken: 0. Fixed: 1. Flaky: 0. Missing: 0. Urgency lowered: 0.

- **fixed** `t29`: urgency: low (want medium)

### v5_tidy_urgency vs v1_baseline

Pass rate +0.0%. Broken: 1. Fixed: 1. Flaky: 0. Missing: 0. Urgency lowered: 1.

- **broken** `t40`: urgency: medium (want high)
- **fixed** `t29`

### v6_bundled_pr vs v1_baseline

Pass rate +2.0%. Broken: 0. Fixed: 1. Flaky: 0. Missing: 0. Urgency lowered: 0.

- **fixed** `t29`

## sol

| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice | cost | $/call | $/correct | s/call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1_baseline | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.1020 | $0.00068 | $0.00077 | 2.1 |
| v2_keep_it_quick | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.0984 | $0.00066 | $0.00075 | 2.1 |
| v3_add_example | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.1003 | $0.00067 | $0.00076 | 2.1 |
| v4_feel_heard | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.1002 | $0.00067 | $0.00076 | 2.0 |
| v5_tidy_urgency | 89.3% | 80.0% to 97.3% | 99.2% | 50.0% | 100.0% | 89.3% | 98.0% | 98.0% | $0.3179 | $0.00212 | $0.00237 | 2.3 |
| v6_bundled_pr | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.2238 | $0.00149 | $0.00170 | 2.0 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v2_keep_it_quick | v3_add_example | v4_feel_heard | v5_tidy_urgency | v6_bundled_pr |
|---|---|---|---|---|---|---|---|
| easy | 12 | 100% | 100% | 100% | 100% | 100% | 100% |
| injection | 2 | 50% | 50% | 50% | 50% | 50% | 50% |
| invoice-trap | 8 | 75% | 75% | 75% | 75% | 88% | 75% |
| multi-issue | 6 | 100% | 100% | 100% | 100% | 100% | 100% |
| noisy | 4 | 75% | 75% | 75% | 75% | 75% | 75% |
| refund-trap | 8 | 88% | 88% | 88% | 88% | 83% | 88% |
| tone-mismatch | 10 | 90% | 90% | 90% | 90% | 90% | 90% |

Wrong answers on v1_baseline:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave bug, wanted billing (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v2_keep_it_quick:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave bug, wanted billing (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v3_add_example:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave bug, wanted billing (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v4_feel_heard:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave bug, wanted billing (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v5_tidy_urgency:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- urgency: gave medium, wanted high (1 calls, 1 cases)

Wrong answers on v6_bundled_pr:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave bug, wanted billing (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

### v2_keep_it_quick vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

### v3_add_example vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

### v4_feel_heard vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

### v5_tidy_urgency vs v1_baseline

Pass rate +1.3%. Broken: 0. Fixed: 1. Flaky: 1. Missing: 0. Urgency lowered: 0.

- **fixed** `t30`
- **flaky** `t24`: urgency: medium (want high)

### v6_bundled_pr vs v1_baseline

Pass rate +0.0%. Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

