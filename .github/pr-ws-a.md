Adopts Srinivas's star schema as the target model, with two structural changes,
and replaces the sample values with data that ties.

## Schema changes

- Overhead moves out of `Fact_COGS` into `Fact_Overhead_Pool` (plant x month, **unallocated**).
  Allocation is applied in the reporting layer so the basis stays a visible, switchable choice.
- Freight moves out of `Fact_COGS` into `Fact_Freight` at order grain. Outbound freight is a
  delivery cost, not a production cost, and cost-to-serve analysis needs it per shipment.

Everything else keeps Srinivas's table and column names.

## Data

`data/generate_data.py` — 24 months, 120 customers, 80 SKUs, 4 plants. Costs derive from real
drivers (kg x material price, machine hours x plant labour rate) rather than being independent
random values. Net Sales ties to its components on every row. Customer revenue is
Pareto-distributed, so "top customer" means something.

CSVs are not committed. Fixed seed, so everyone regenerates identical files.

## Semantic layer

`src/semantic/views.sql` — 8 views. Every metric is defined once, and nothing outside this file
computes a metric. This is the structural fix for Net Sales differing between two dashboard tabs
by $36,647: both calculations were reasonable, there was just no single definition.

## Load assertions

`src/load.py` — 10 assertions, each covering a defect that previously reached a chart: net sales
tying to its components, no future-dated rows, orders belonging to one customer, referential
integrity, opex under 40% of revenue, budget within 2x of actuals. A failure exits non-zero.

Two planted defects (9 duplicate lines, 14 unflagged returns) report as notes rather than
failures — detecting those is workstream D.

## What this makes visible

Overhead margin by product category, same data, two defensible allocation bases:

| Category | Units basis | Machine-hours basis |
|---|---|---|
| Paper Plates | 39.6% | 41.9% |
| Bowls | 27.2% | 23.3% |
| Food Containers | 26.8% | 22.0% |
| Paper Cups | 14.8% | 19.3% |
| **Cutlery** | **-13.2%** | **+6.4%** |

Cutlery is loss-making or profitable depending entirely on an accounting convention nobody
voted on. That is the human-in-the-loop moment in the charter, and it is workstream E.

## Verify

    rm -f data/raw/*.csv finance.db
    python data/generate_data.py --out data/raw
    python src/load.py

## Note for @svijetaj

The dashboard's Overhead and Freight bars read from `Fact_COGS`; those two columns moved
deliberately. Repointing both at `vw_margin_waterfall` should be the only change needed —
everything else binds unchanged, and freight becomes cube-allocated rather than estimated.
