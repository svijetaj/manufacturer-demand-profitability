# Workstreams

Status as of Aug 15. Claim one by opening an issue or saying so on the floor.

Sequence: **scope → schema → data → agent → eval**. The dashboard already exists and
mostly does not need changing; it will start showing correct numbers once the data
underneath it is regenerated on an agreed schema.

## Where we actually are

| Layer | State |
|---|---|
| Interface | **Built** — Vijay's Streamlit app, 4 subject areas, DuckDB backend |
| Semantic layer | **Partially built** — waterfall + customer matrix join 4 fact tables; metrics defined per-chart rather than once |
| Schema | **Built** — Srinivas's star schema; 2 structural changes needed (see A) |
| Data | **Blocked** — values incoherent and contain no signal; regeneration needed |
| Reasoning layer | **Not started** — this is the AI part of an AI task force |
| Evaluation | **Not started** |

---

## A — Schema + semantic layer

Owner: unclaimed. Blocks C, D, E.

Adopt Srinivas's star schema with two structural changes:

1. **Split overhead out of `Fact_COGS`** into `Fact_Overhead_Pool` at plant x period,
   unallocated. Allocation is applied in the reporting layer, not baked into the data.
   Without this there is no allocation-choice story, which is our answer to the
   human-in-the-loop question.
2. **Move `Freight_Cost`** from `Fact_COGS` (production grain) to order/shipment grain.
   Outbound freight is a delivery cost, not a production cost, and cost-to-serve
   analysis needs it per shipment.

Minor: `Dim_Customer.Account_Manager` becomes a `Sales_Rep_ID` FK; `Expense_Type` /
`Expense_Category` made properly hierarchical; drop `Currency_Code` (single currency);
cap all dates at today.

Then define every metric **once** as a SQL view — `vw_margin_waterfall`,
`vw_customer_profitability`, `vw_sku_profitability`. Today Net Sales is computed
independently on two tabs and they disagree by $36,647. One definition fixes that
class of bug permanently.

Deliverable: `src/semantic/*.sql` + a metric dictionary in `docs/`.

## B — Profitability agent

Owner: unclaimed. Depends on A.

Question in, answer out, with the evidence trail. Not seven agents by business
dimension — those are one query with a different GROUP BY. Three components:

- retrieval (natural language to SQL over the views)
- analysis (run it, interpret the result)
- narrative (state the finding, cite the rows)

Must refuse to answer where the data cannot support it, and must flag when an answer
depends on an accounting choice rather than a fact.

## C — Variance explanation

Owner: unclaimed. Depends on A.

Decompose month-over-month margin change into price / volume / mix / input cost /
cost-to-serve. This is the "why did margin drop" engine. Deterministic maths, not LLM
work — the agent narrates the output.

## D — Anomaly detection

Owner: unclaimed. Depends on A.

Duplicates, unflagged returns, price-vs-cost divergence, rebate outliers, and
referential/arithmetic integrity checks that run **at load time** so bad data cannot
silently reach a chart again.

## E — Allocation sensitivity + human approval

Owner: unclaimed. Depends on A.

Show the SKU profitability ranking side by side under different overhead bases (units
produced vs machine hours) and surface the difference as a decision a human makes.
Then an approval surface for any recommended action — reprice, renegotiate a rebate,
discontinue a SKU. The agent recommends with evidence; a human approves; nothing
writes back to a pricing or billing system.

**This is the workstream that answers the capitalised part of the charter.** If only
one thing lands beyond the dashboard, make it this.

## F — Interface

Owner: Vijay. Largely built.

Remaining: add a question box wired to B, and surface B's evidence trail by linking
into the existing waterfall and customer matrix views. The dashboard becomes the
evidence layer behind the agent's answers rather than the deliverable itself.

## G — Eval

Owner: unclaimed. Independent of A — can start now.

Score agent output against the findings planted in the regenerated data. This is how
we say "the agent found 4 of 5" instead of "the output looks right". Current scorer is
keyword coverage; upgrading it to a model-as-judge is the obvious improvement.

---

## Deferred

**Demand forecasting.** A model trained on synthetic data learns the seasonality curve
we wrote into the generator — it produces a plausible chart and no real finding. The
existing Demand Analytics tab stays as descriptive history. Revisit as v2 on the same
schema if v1 lands early.
