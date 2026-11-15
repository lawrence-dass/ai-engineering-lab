# Labelling policy

Every expected answer in `cases/tickets.jsonl` follows these rules. If a label cannot be defended from this page, the label is wrong and the case gets fixed or removed.

The product is fictional: Larkwell, a subscription project-tracking app with web and mobile clients and Free, Team and Business plans.

## category

| Value | Use when |
|---|---|
| `billing` | Charges, invoices, refunds, payment methods, cancelling or changing a subscription, plan prices and what a plan includes |
| `bug` | Something in the product is broken, erroring or behaving wrongly |
| `account_access` | The customer cannot sign in, is locked out, or reports a possible security problem. Applies even when a defect is the cause |
| `how_to` | The customer asks how to do something, or whether something is possible |
| `feature_request` | The customer asks us to add or change a capability |
| `other` | Praise, spam, sales pitches, anything else |

## urgency

| Value | Use when |
|---|---|
| `high` | The customer cannot do their work at all, has lost data, reports a possible security problem, or has had money taken wrongly (charged twice, charged after cancelling, charged the wrong amount) |
| `medium` | Something is wrong or degraded, but the customer can keep working |
| `low` | Questions, requests and feedback with nothing broken |

Urgency follows what happened. Tone does not count in either direction.

## refund_requested

`true` only when the customer explicitly asks for money back, in any wording or language. "Reverse the charge" and "I want my money back" count.

`false` for: asking about refund policy, cancelling, reporting a wrong charge without asking for the money, and saying they might ask later.

## invoice_id

The Larkwell invoice number, normalised to `INV-` plus six digits. `null` when the customer gives none. Ticket numbers, order confirmations, error IDs, PO numbers and card digits are not invoice numbers.

## More than one issue

Category and urgency follow the most urgent issue. On a tie, the issue mentioned first wins. `refund_requested` and `invoice_id` apply to the whole message.

## summary

One sentence, at most 20 words. Checked for length only. It does not decide pass or fail.

## Case tags

The first tag is the reason the case exists.

| Tag | What it tests |
|---|---|
| `easy` | A clear single-issue message |
| `tone-mismatch` | Tone points one way, the facts point the other |
| `refund-trap` | Refund language that is or is not an explicit request |
| `invoice-trap` | Numbers that look like invoice IDs, and loosely written real ones |
| `multi-issue` | Two issues in one message |
| `noisy` | Typos, forwarded threads, another language |
| `injection` | Text in the ticket that tries to instruct the model |
