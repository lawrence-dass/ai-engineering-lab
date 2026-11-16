# Problem statement: prompt changes ship without evidence

| | |
|---|---|
| **Owner** | Lawrence Dass |
| **Status** | Approved |
| **Created** | 2026-11-12 |
| **Last reviewed** | 2026-11-12 |
| **Scenario** | Fictional. Larkwell and its support team do not exist. The problem is real. |
| **Solution** | [SOLUTION.md](SOLUTION.md) for the design, [README.md](README.md) to run it |

This document describes the problem only. It does not describe the solution.

## 1. Context

Larkwell is a subscription project-tracking app. Its support team receives customer messages by email and through the app.

Every incoming message goes through one LLM call before a person sees it. The call returns four routing fields and a summary:

| Field | What the team does with it |
|---|---|
| `category` | Sends the ticket to the billing, product or accounts queue |
| `urgency` | `high` pages the on-call agent. `low` waits in the general queue |
| `refund_requested` | Adds the ticket to the refunds queue |
| `invoice_id` | Looks up the billing record and attaches it to the ticket |

The behaviour of the call is set by a system prompt, kept as a text file in the repository. Engineers edit it. So do the support lead and the product manager, through pull requests. A change is reviewed by reading the diff and trying two or three tickets by hand.

## 2. The problem

**A change to the prompt can change how tickets are classified, and the team cannot tell which tickets are affected before the change ships.**

The edits that cause this are ordinary ones: a sentence about tone, a worked example, a tidy-up for readability. Each looks safe in a diff. None produces an error when it goes wrong. The reply is still valid JSON, and the ticket still lands in a queue. It is the wrong queue.

## 3. Who is affected

| Who | How |
|---|---|
| Customers | A serious ticket waits behind routine ones, or a refund is raised that nobody asked for |
| Support agents | Tickets arrive in the wrong queue and have to be re-routed by hand |
| On-call agent | Paged for tickets that are not urgent, and not paged for ones that are |
| Engineers who own the feature | Learn about a bad edit from complaints, days later, with no record of which edit caused it |
| Anyone proposing a prompt edit | Has no way to show that their change is safe |

## 4. Impact of a wrong answer

| Field | Wrong in this direction | Consequence |
|---|---|---|
| `urgency` | Too low | A security report or a double charge sits in the general queue |
| `urgency` | Too high | The on-call agent is paged for feature requests and starts to ignore pages |
| `refund_requested` | True when not asked | A refund is queued for a customer who only asked a question |
| `refund_requested` | False when asked | The customer has to ask twice |
| `invoice_id` | Invented or misread | The wrong billing record is attached to the ticket |
| `category` | Wrong | The ticket goes to a team that cannot resolve it |

The costs are uneven. An urgency that is too low on a security report is worse than a wrong category on a feature request. A single overall score hides that.

## 5. Parts of the problem

Each part has to be dealt with before a solution can be trusted.

1. **No written definition of correct.** The rules for urgency and refunds live in people's heads. Two people would label the same ticket differently, so there is nothing fixed to measure against.
2. **No fixed set of examples.** Hand checks use whichever tickets come to mind. The hard cases that broke last time are not tried again.
3. **Valid output hides wrong output.** The reply always matches the schema. A wrong value raises no error, no alert and no failed request.
4. **Edits have effects far from where they are made.** A sentence about tone can move urgency on tickets that have nothing to do with tone. Reading the diff does not predict this.
5. **The same input can give different answers.** These models do not accept a temperature setting. One passing try proves little, and one failing try may be chance. A real regression has to be told apart from noise.
6. **Behaviour depends on the model.** An edit that is safe on one model may break another. A model upgrade is the same problem with the prompt held still.
7. **Failed calls are not wrong answers.** Timeouts, rate limits and cut-off replies happen. If they are counted as failures of the prompt, the result is wrong in a different way.
8. **The check must be cheap enough to run every time.** A check that takes an hour or costs real money per run gets skipped.
9. **A small test set limits what can be detected.** With 40 cases, one case is 2.5 points. A change smaller than the noise cannot be seen.
10. **Nobody owns the decision to ship.** There is no agreed bar a prompt change must clear, and no place where the check runs automatically.
11. **A test set goes stale.** Customers change how they write and the product changes what they write about. A prompt can also be tuned until it passes the test set and nothing else.
12. **Fields do not matter equally.** See section 4. The way results are reported has to keep the fields separate.

## 6. Scope

**In scope**

- Detecting, before release, which tickets a prompt edit classifies differently from the current prompt
- The four routing fields
- Four models from two vendors, a cheap one and a strong one from each, to see whether an edit behaves the same across model sizes and vendors
- A pass or fail signal that can block a change

**Out of scope**

- Judging the quality of the free-text summary beyond its length
- Finding the best prompt. This is about catching regressions, not tuning.
- Monitoring live traffic after release
- Multi-turn conversations, retrieval and tool use
- A labelling process with several annotators and agreement scores
- Real customer data

## 7. Constraints

- The check must call the same code that production would call. A separate test copy of the feature would drift from it.
- No customer data in the repository. Tickets are written by hand.
- A full check should finish in minutes and cost less than 10 US dollars.
- One person must be able to maintain it.
- Someone who is not an engineer must be able to add a test case without touching code.

## 8. Assumptions

- The written labelling policy is the right policy for this team.
- Hand-written tickets are close enough to real ones for the result to mean something.
- Exact match is the right standard for the four fields.

If any of these is false, the scores are measuring the wrong thing. They are restated as limits in the README.

## 9. Success criteria

A solution is good enough when:

1. Given an edited prompt, it names every ticket whose result changed against the baseline, with the field and the value.
2. It separates a ticket that broke from one that is merely inconsistent between tries.
3. A failed or interrupted run can be restarted without losing or double-counting work.
4. It runs in CI and exits with a failure when a ticket breaks.
5. Adding a test case means adding one line to a data file.
6. The cost and duration of a full run are recorded.

## 10. Open questions

| # | Question | Owner | Status |
|---|---|---|---|
| 1 | How many repetitions per case are enough to call a result stable? | Lawrence | Open. Starting with 3 |
| 2 | Should one broken case block a change, or only a drop past a threshold? | Lawrence | Open |
| 3 | A customer reports a wrong charge without asking for the money back. Is that a refund request? The policy says no. | Lawrence | Decided 2026-11-15: no. Only an explicit ask counts. t16 and t37 stay false |
| 4 | Should fields carry different weights in the gate, given section 4? | Lawrence | Open |

## 11. Change log

| Date | Change |
|---|---|
| 2026-11-12 | First version. Written on the same day as the first build of the harness, before any run against a model. |
| 2026-11-12 | Approved by the owner. Open questions carried into SOLUTION.md with the defaults in use. |
| 2026-11-15 | Scope widened from two Claude models to four models from two vendors (Anthropic and OpenAI), so a result cannot be put down to one vendor's models. Decided by the owner before any full run. |
| 2026-11-15 | Open question 3 decided after the blind labelling check: a reported wrong charge is not a refund request. The strict urgency rule was kept after the same check. |
