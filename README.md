# Meridian Corp — Finance & Analytics Task Force

Profitability intelligence for a recycled foodservice-products manufacturer.

## Problem statement

Finance can tell you what the company earned. It cannot quickly tell you **why
margin moved, which customers and SKUs actually make money after all deductions,
and which of those answers depend on an accounting choice rather than a fact.**

Today that analysis is a multi-day manual exercise across sales, cost and
production extracts. We are building an agent that does the diagnosis and
drafts the recommendation, while a human owns every decision that moves money.

Full scope, including what is deliberately out of scope, is in [SCOPE.md](SCOPE.md).

## Quick start

```bash
make setup     # install deps
make data      # generate the synthetic dataset into data/raw
```

## Data

**We are not using anyone's real company data.** `data/generate_data.py` produces
a synthetic dataset modelled on a real manufacturing schema — 24 months, 14 SKUs,
8 customers, 3 production lines, 2 plants. Column-level detail is in
[docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md).

CSVs are not committed. The generator with a fixed seed is the source of truth,
so everyone regenerates byte-identical files.

The generator plants a known set of findings, so we can measure whether the agent
finds them instead of arguing about whether its output "looks right". The answer
key lives in `eval/answer_key.yaml` — **do not paste it into an agent prompt.**

```bash
python eval/score.py --input runs/agent_output.md
```

## Workstreams

Pick one, claim it via an issue, work on a branch.

| # | Workstream | Deliverable |
|---|---|---|
| A | Data + semantic layer | Load CSVs, build the margin waterfall (gross → contribution → net), document metric definitions |
| B | Profitability agent | Question in, answer with evidence trail out |
| C | Variance explanation | Decompose month-over-month margin change into price / volume / mix / cost |
| D | Anomaly detection | Duplicates, returns, price-cost divergence, rebate outliers |
| E | Allocation sensitivity + human-in-loop | Side-by-side ranking under different bases; approval surface for recommended actions |
| F | Interface | Conversational front end over B–E |
| G | Eval | Score agent output against the planted findings; this is how we prove it works |

A and G unblock or validate everyone else. They start first.

## Working agreement

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: branch per workstream, PR
into `main`, one reviewer, no real company data ever, and log real decisions in
[docs/DECISIONS.md](docs/DECISIONS.md) rather than only in chat.
