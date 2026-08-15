# Scope — v1

Locked. Changes go through a PR to this file, not a chat message.

## Problem

Finance can report what the company earned. It cannot quickly say **why margin
moved, which customers and SKUs actually make money after all deductions, and
which of those answers depend on an accounting choice rather than a fact.**

We are building an agent that does that diagnosis and drafts the recommendation.
A human owns every decision that moves money.

## In scope

1. **Profitability model** — SKU and customer level, gross margin down to net:
   discounts, off-invoice rebates, freight, scrap, allocated overhead.
2. **Variance explanation** — month over month margin change decomposed into
   price, volume, mix, input cost, cost-to-serve.
3. **Allocation sensitivity** — how the profitability ranking changes under
   different overhead allocation bases, surfaced as a human decision.
4. **Anomaly detection** — duplicates, unflagged returns, price/cost divergence,
   rebate outliers.

## Out of scope for v1

**Demand forecasting.** Deferred to v2 on the same schema.

Rationale: the original statement covered forecasting *and* profitability. Those
are two projects. Forecasting on a simulated dataset learns the seasonality curve
we ourselves wrote into the generator — it cannot produce a real finding, only a
plausible-looking chart. Profitability is a reasoning problem, which is what an
agent is actually good at, and it is the one that maps to the department charter.
If we land v1 early, forecasting is the first v2 item.

## Charter mapping

| Asha's question | Our answer |
|---|---|
| Which reports could write themselves? | The monthly profitability pack and the margin-variance commentary. Numbers are deterministic; the narrative is the labour. |
| Where does AI speed the close? | Variance investigation — today that is analysts chasing "why did SKU-2003 drop four points" across three extracts. |
| Where must a human stay in the loop when money moves? | **Allocation basis** — it reorders which SKUs look unprofitable, so a human owns the method rather than inheriting it from the agent. **Actions** — reprice, renegotiate a rebate, discontinue a SKU: the agent recommends with evidence, a human approves. Nothing writes back to a pricing or billing system. |

## Non-negotiable

No real company data. Ours or anyone's. The dataset is synthetic and generated
by `data/generate_data.py`.
