# Data dictionary

All tables are synthetic, produced by `data/generate_data.py`. Default run is
24 months from 2024-08, seed 42. Regenerate with `make data`.

Grain is stated for every table — read it before joining.

## dim_sku — one row per SKU (14)
| column | type | notes |
|---|---|---|
| sku_id | str | PK |
| family | str | plate, bowl, cup, lid, cutlery |
| material | str | FK to ref_material_costs.material |
| size | str | descriptive |
| unit_weight_g | float | drives material consumption |
| list_price_usd | float | before customer discount |
| units_per_case | int | order quantities are case-rounded |
| line | str | production line: FORM-A, FORM-B, CONV-1, CONV-2, INJ-1 |

## dim_customer — one row per customer (8)
| column | type | notes |
|---|---|---|
| customer_id | str | PK |
| customer_name | str | |
| channel | str | national_retail, foodservice, distributor, private_label |
| payment_terms_days | int | not costed in v1; available for working-capital analysis |
| base_discount_pct | float | on-invoice, already reflected in unit_price_usd |
| rebate_pct | float | **off-invoice** — NOT in unit_price_usd, must be subtracted separately |
| freight_terms | str | prepaid (we pay) or collect (customer pays) |

> The rebate column is the single most common modelling mistake here. Gross
> margin computed from `unit_price_usd` alone will look healthy on customers
> whose net margin is the worst in the book.

## fact_order_lines — grain: order_id + line_no
| column | type | notes |
|---|---|---|
| order_id | str | |
| line_no | int | `99` marks a return line |
| order_date | date | |
| customer_id | str | FK |
| sku_id | str | FK |
| qty_units | int | **negative on returns** |
| unit_price_usd | float | net of on-invoice discount only |
| freight_terms | str | denormalised from customer |

Contains deliberate defects: exact duplicate rows, and returns that are not
flagged by any column other than sign. Reconcile row counts before trusting
revenue.

## fact_freight — grain: order_id + sku_id
| column | type | notes |
|---|---|---|
| freight_cost_usd | float | cube-driven, not weight-driven |

## fact_production — grain: month + sku_id
| column | type | notes |
|---|---|---|
| month | date | month start |
| plant | str | PLANT-EAST, PLANT-WEST |
| line | str | |
| units_produced | int | gross of scrap, i.e. > units sold |
| material_kg | float | |
| machine_hours | float | allocation basis option A |
| labor_hours | float | |
| labor_cost_usd | float | |
| scrap_rate | float | by line |

## ref_material_costs — grain: month + material
| column | type | notes |
|---|---|---|
| cost_per_kg | float | monthly; contains a permanent step change mid-series |

## ref_overhead_pools — grain: month + plant
| column | type | notes |
|---|---|---|
| overhead_pool_usd | float | **unallocated.** How you push this to SKUs is the project's central judgement call — units produced and machine hours give different rankings. |

## Suggested margin waterfall

```
gross revenue        = qty_units * unit_price_usd
- rebates            = gross revenue * rebate_pct        (off-invoice)
= net revenue
- material cost      = units_produced * unit_weight_g/1000 * cost_per_kg
- labour cost        = labor_cost_usd
= contribution margin
- freight            = freight_cost_usd (prepaid terms only)
= contribution after cost-to-serve
- allocated overhead = overhead_pool_usd * <chosen basis>
= net margin
```

Every line above the overhead row is a fact. The overhead row is a choice.
