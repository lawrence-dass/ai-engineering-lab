# Prompt regression report

## haiku

| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice | cost | $/call | $/correct | s/call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1_baseline | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.0101 | $0.00007 | $0.00008 | 1.0 |
| v7_tidy_keep_lists | 88.0% | 78.0% to 96.0% | 97.5% | 50.0% | 98.0% | 90.0% | 98.0% | 98.0% | $0.0101 | $0.00007 | $0.00008 | 0.9 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v7_tidy_keep_lists |
|---|---|---|---|
| easy | 12 | 100% | 100% |
| injection | 2 | 50% | 50% |
| invoice-trap | 8 | 88% | 88% |
| multi-issue | 6 | 83% | 83% |
| noisy | 4 | 75% | 75% |
| refund-trap | 8 | 88% | 88% |
| tone-mismatch | 10 | 90% | 90% |

Wrong answers on v1_baseline:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

Wrong answers on v7_tidy_keep_lists:

- urgency: gave low, wanted medium (9 calls, 3 cases)
- category: gave feature_request, wanted bug (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)

### v7_tidy_keep_lists vs v1_baseline

Pass rate +0.0% (paired 95% interval +0.0% to +0.0%). Broken: 0. Fixed: 0. Flaky: 0. Missing: 0. Urgency lowered: 0.

## luna

| version | pass rate | 95% interval | visible | held-out | category | urgency | refund | invoice | cost | $/call | $/correct | s/call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1_baseline | 86.0% | 76.7% to 94.7% | 95.0% | 50.0% | 98.7% | 87.3% | 98.0% | 98.0% | $0.0061 | $0.00004 | $0.00005 | 1.7 |
| v7_tidy_keep_lists | 84.0% | 74.0% to 93.3% | 92.5% | 50.0% | 97.3% | 86.7% | 98.0% | 98.0% | $0.0062 | $0.00004 | $0.00005 | 1.4 |

Pass rate by kind of case:

| tag | cases | v1_baseline | v7_tidy_keep_lists |
|---|---|---|---|
| easy | 12 | 100% | 100% |
| injection | 2 | 50% | 50% |
| invoice-trap | 8 | 75% | 71% |
| multi-issue | 6 | 89% | 83% |
| noisy | 4 | 67% | 58% |
| refund-trap | 8 | 88% | 88% |
| tone-mismatch | 10 | 90% | 90% |

Wrong answers on v1_baseline:

- urgency: gave low, wanted medium (13 calls, 5 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave high, wanted medium (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave billing, wanted bug (1 calls, 1 cases)
- category: gave billing, wanted how_to (1 calls, 1 cases)

Wrong answers on v7_tidy_keep_lists:

- urgency: gave low, wanted medium (12 calls, 4 cases)
- urgency: gave high, wanted medium (5 calls, 2 cases)
- category: gave billing, wanted how_to (3 calls, 1 cases)
- invoice_id: gave INV-482706, wanted INV-603918 (3 calls, 1 cases)
- refund_requested: gave False, wanted True (3 calls, 1 cases)
- urgency: gave medium, wanted low (3 calls, 1 cases)
- category: gave bug, wanted billing (1 calls, 1 cases)

### v7_tidy_keep_lists vs v1_baseline

Pass rate -2.0% (paired 95% interval -5.3% to +1.3%). Broken: 0. Fixed: 0. Flaky: 4. Missing: 0. Urgency lowered: 0.

- **flaky** `t30`: category: bug (want billing)
- **flaky** `t37`
- **flaky** `t36`: category: billing (want how_to)
- **flaky** `t38`: urgency: high (want medium)

