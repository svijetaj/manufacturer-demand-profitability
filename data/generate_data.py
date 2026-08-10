"""
Synthetic dataset generator - Meridian Corp Finance & Analytics task force.

Models a manufacturer of recycled foodservice products (plates, cups, bowls,
lids, cutlery) selling to national retail, foodservice and private-label
customers. Structure mirrors a real manufacturing P&L; all values are generated.

Deliberately plants five findings a good profitability agent should surface.
See FINDINGS at the bottom of this file (spoilers - don't read before demo prep).

Usage:  python generate_data.py [--out ../data/raw] [--months 24] [--seed 42]
"""

import argparse
import os
import numpy as np
import pandas as pd

MATERIALS = {
    "bagasse":      {"base_cost_per_kg": 1.85, "vol": 0.05},
    "molded_fiber": {"base_cost_per_kg": 2.10, "vol": 0.06},
    "rpet":         {"base_cost_per_kg": 3.40, "vol": 0.14},   # volatile - resin linked
    "pla_paper":    {"base_cost_per_kg": 3.95, "vol": 0.11},
}

# sku_id, family, material, size, unit_weight_g, list_price, units_per_case, line
SKUS = [
    ("SKU-1001", "plate",   "bagasse",      '9in',   14.0, 0.085, 1000, "FORM-A"),
    ("SKU-1002", "plate",   "bagasse",      '10.25in', 18.5, 0.104, 1000, "FORM-A"),
    ("SKU-1003", "plate",   "molded_fiber", '6in',    8.0, 0.061,  1200, "FORM-A"),
    ("SKU-1004", "bowl",    "bagasse",      '12oz',  12.0, 0.098,  1000, "FORM-B"),
    ("SKU-1005", "bowl",    "molded_fiber", '32oz',  26.0, 0.187,   600, "FORM-B"),
    ("SKU-2001", "cup",     "pla_paper",    '12oz',   9.5, 0.121,  1000, "CONV-1"),
    ("SKU-2002", "cup",     "pla_paper",    '16oz',  11.5, 0.139,  1000, "CONV-1"),
    ("SKU-2003", "cup",     "rpet",         '24oz',  15.0, 0.164,   600, "CONV-2"),  # cold cup
    ("SKU-2004", "cup",     "rpet",         '32oz',  19.0, 0.198,   600, "CONV-2"),
    ("SKU-3001", "lid",     "rpet",         'flat',   4.5, 0.052,  2000, "CONV-2"),
    ("SKU-3002", "lid",     "pla_paper",    'dome',   6.0, 0.071,  1500, "CONV-2"),
    ("SKU-4001", "cutlery", "pla_paper",    'fork',   5.5, 0.038,  2500, "INJ-1"),
    ("SKU-4002", "cutlery", "pla_paper",    'spoon',  5.2, 0.038,  2500, "INJ-1"),
    ("SKU-4003", "cutlery", "bagasse",      'knife',  5.8, 0.041,  2500, "INJ-1"),
]

# customer_id, name, channel, terms_days, base_discount, rebate_pct, freight_terms
CUSTOMERS = [
    ("CUST-100", "Northbrook Coffee Co",   "foodservice",    45, 0.18, 0.030, "prepaid"),
    ("CUST-101", "Vantage Wholesale Club", "national_retail",60, 0.29, 0.125, "prepaid"),  # rebate trap
    ("CUST-102", "Harbor Grocers",         "national_retail",45, 0.22, 0.040, "prepaid"),
    ("CUST-103", "Cedar Foodservice Dist", "distributor",    30, 0.31, 0.010, "collect"),
    ("CUST-104", "Lakeside Cafeterias",    "foodservice",    30, 0.14, 0.000, "prepaid"),
    ("CUST-105", "Meridian Private Label", "private_label",  60, 0.34, 0.005, "prepaid"),
    ("CUST-106", "Summit Stadium Group",   "foodservice",    30, 0.16, 0.000, "prepaid"),
    ("CUST-107", "Pinecrest Markets",      "national_retail",45, 0.20, 0.025, "prepaid"),
]

# seasonality: month index 1-12 multipliers by family
SEASONALITY = {
    "plate":   [0.85, 0.82, 0.92, 1.05, 1.22, 1.35, 1.40, 1.28, 1.05, 0.95, 1.10, 1.15],
    "bowl":    [1.05, 1.02, 0.98, 0.95, 0.94, 0.96, 0.98, 1.00, 1.06, 1.12, 1.18, 1.16],
    "cup":     [0.78, 0.80, 0.95, 1.12, 1.30, 1.48, 1.52, 1.42, 1.10, 0.92, 0.82, 0.85],
    "lid":     [0.80, 0.82, 0.96, 1.10, 1.28, 1.44, 1.48, 1.38, 1.08, 0.94, 0.84, 0.88],
    "cutlery": [0.90, 0.88, 0.96, 1.04, 1.16, 1.26, 1.30, 1.22, 1.04, 0.98, 1.02, 1.04],
}

LINES = {
    "FORM-A": {"plant": "PLANT-EAST", "units_per_machine_hr": 42000, "labor_hr_per_mh": 1.6},
    "FORM-B": {"plant": "PLANT-EAST", "units_per_machine_hr": 26000, "labor_hr_per_mh": 1.8},
    "CONV-1": {"plant": "PLANT-WEST", "units_per_machine_hr": 61000, "labor_hr_per_mh": 1.2},
    "CONV-2": {"plant": "PLANT-WEST", "units_per_machine_hr": 55000, "labor_hr_per_mh": 1.3},
    "INJ-1":  {"plant": "PLANT-EAST", "units_per_machine_hr": 96000, "labor_hr_per_mh": 0.9},
}

LABOR_RATE = {"PLANT-EAST": 24.50, "PLANT-WEST": 27.80}
SCRAP_RATE = {"FORM-A": 0.031, "FORM-B": 0.048, "CONV-1": 0.022, "CONV-2": 0.036, "INJ-1": 0.017}

# freight: cost driven by volume (cube), not weight - cups/bowls are bulky and cheap
CUBE_FACTOR = {"plate": 1.0, "bowl": 2.4, "cup": 3.1, "lid": 1.4, "cutlery": 0.7}


def month_range(start, months):
    return pd.date_range(start=start, periods=months, freq="MS")


def build_material_costs(months_idx, rng):
    rows = []
    for m, cfg in MATERIALS.items():
        cost = cfg["base_cost_per_kg"]
        for i, dt in enumerate(months_idx):
            drift = rng.normal(0.002, cfg["vol"] / 4)
            cost = cost * (1 + drift)
            # planted: resin spike from month 13, permanent step change
            if m == "rpet" and i == 12:
                cost *= 1.34
            if m == "pla_paper" and i == 12:
                cost *= 1.11
            rows.append({"month": dt.date(), "material": m,
                         "cost_per_kg": round(cost, 4)})
    return pd.DataFrame(rows)


def build_overhead(months_idx, rng):
    rows = []
    pools = {"PLANT-EAST": 655000, "PLANT-WEST": 528000}
    for plant, base in pools.items():
        for dt in months_idx:
            amt = base * (1 + rng.normal(0, 0.04))
            rows.append({"month": dt.date(), "plant": plant,
                         "overhead_pool_usd": round(amt, 2)})
    return pd.DataFrame(rows)


def build_orders(months_idx, sku_df, rng):
    lines, order_seq = [], 1
    for dt in months_idx:
        mi = dt.month - 1
        for cid, cname, channel, terms, disc, rebate, freight_terms in CUSTOMERS:
            n_orders = rng.integers(2, 6)
            for _ in range(n_orders):
                order_id = f"SO-{order_seq:06d}"
                order_seq += 1
                day = int(rng.integers(1, 28))
                odate = dt.replace(day=day)
                picks = rng.choice(len(SKUS), size=int(rng.integers(2, 7)), replace=False)
                for k, si in enumerate(picks):
                    sku = SKUS[si]
                    sku_id, family, material, size, wt, price, upc, line = sku
                    base_qty = {"national_retail": 240000, "foodservice": 90000,
                                "distributor": 150000, "private_label": 300000}[channel]
                    qty = base_qty * SEASONALITY[family][mi] * rng.uniform(0.55, 1.45)
                    qty = int(round(qty / upc)) * upc
                    if qty <= 0:
                        continue
                    # customer discount + occasional deal pricing
                    d = disc + rng.normal(0, 0.015)
                    # planted: SKU-2003/2004 price never rose after the resin spike
                    net_price = price * (1 - d)
                    lines.append({
                        "order_id": order_id, "line_no": k + 1,
                        "order_date": odate.date(), "customer_id": cid,
                        "sku_id": sku_id, "qty_units": qty,
                        "unit_price_usd": round(net_price, 5),
                        "freight_terms": freight_terms,
                    })
    df = pd.DataFrame(lines)

    # planted anomalies: duplicate lines and unflagged returns
    dupes = df.sample(n=9, random_state=7).copy()
    rets = df.sample(n=14, random_state=11).copy()
    rets["qty_units"] = -(rets["qty_units"] * 0.1).round().astype(int)
    rets["line_no"] = 99
    df = pd.concat([df, dupes, rets], ignore_index=True)
    return df.sort_values(["order_date", "order_id", "line_no"]).reset_index(drop=True)


def build_freight(orders, sku_df, rng):
    m = orders.merge(sku_df[["sku_id", "family", "unit_weight_g"]], on="sku_id")
    m["cube_index"] = m["family"].map(CUBE_FACTOR)
    # freight billed per shipment, driven by cube - this is the cost-to-serve trap
    m["freight_cost_usd"] = (
        m["qty_units"] * m["unit_weight_g"] / 1000 * 0.062 * m["cube_index"]
    ) * (1 + np.random.default_rng(3).normal(0, 0.08, len(m)))
    out = m.groupby(["order_id", "sku_id"], as_index=False)["freight_cost_usd"].sum()
    out["freight_cost_usd"] = out["freight_cost_usd"].round(2)
    return out


def build_production(orders, sku_df, months_idx, rng):
    m = orders[orders.qty_units > 0].merge(
        sku_df[["sku_id", "line", "unit_weight_g", "material"]], on="sku_id")
    m["month"] = pd.to_datetime(m["order_date"]).values.astype("datetime64[M]")
    g = m.groupby(["month", "sku_id", "line", "unit_weight_g", "material"],
                  as_index=False)["qty_units"].sum()
    g["plant"] = g["line"].map(lambda l: LINES[l]["plant"])
    g["scrap_rate"] = g["line"].map(SCRAP_RATE)
    g["units_produced"] = (g["qty_units"] / (1 - g["scrap_rate"])).round().astype(int)
    g["machine_hours"] = g["units_produced"] / g["line"].map(
        lambda l: LINES[l]["units_per_machine_hr"])
    g["labor_hours"] = g["machine_hours"] * g["line"].map(
        lambda l: LINES[l]["labor_hr_per_mh"])
    g["labor_cost_usd"] = (g["labor_hours"] * g["plant"].map(LABOR_RATE)).round(2)
    g["material_kg"] = (g["units_produced"] * g["unit_weight_g"] / 1000).round(2)
    g["machine_hours"] = g["machine_hours"].round(3)
    g["labor_hours"] = g["labor_hours"].round(2)
    g["month"] = g["month"].dt.date
    return g[["month", "plant", "line", "sku_id", "material", "units_produced",
              "material_kg", "machine_hours", "labor_hours", "labor_cost_usd",
              "scrap_rate"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="raw")
    ap.add_argument("--months", type=int, default=24)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--start", default="2024-08-01")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    os.makedirs(args.out, exist_ok=True)
    months_idx = month_range(args.start, args.months)

    sku_df = pd.DataFrame(SKUS, columns=[
        "sku_id", "family", "material", "size", "unit_weight_g",
        "list_price_usd", "units_per_case", "line"])
    cust_df = pd.DataFrame(CUSTOMERS, columns=[
        "customer_id", "customer_name", "channel", "payment_terms_days",
        "base_discount_pct", "rebate_pct", "freight_terms"])

    mat = build_material_costs(months_idx, rng)
    ovh = build_overhead(months_idx, rng)
    orders = build_orders(months_idx, sku_df, rng)
    freight = build_freight(orders, sku_df, rng)
    prod = build_production(orders, sku_df, months_idx, rng)

    files = {
        "dim_sku.csv": sku_df,
        "dim_customer.csv": cust_df,
        "fact_order_lines.csv": orders,
        "fact_freight.csv": freight,
        "fact_production.csv": prod,
        "ref_material_costs.csv": mat,
        "ref_overhead_pools.csv": ovh,
    }
    for name, df in files.items():
        path = os.path.join(args.out, name)
        df.to_csv(path, index=False)
        print(f"{name:26s} {len(df):>7,} rows")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# FINDINGS planted in the data (demo answer key - keep out of the agent prompt):
#
# 1. Rebate trap. CUST-101 (Vantage Wholesale Club) sits mid-pack on gross
#    margin (~52%) but drops to worst on net (~37%) once the 12.5% off-invoice
#    rebate and freight are applied. Gross-margin reporting hides it entirely.
# 2. Unpassed cost spike. rPET steps up ~34% at month 13. SKU-2003 / SKU-2004
#    average selling price barely moves. Margin erodes from month 13 onward.
# 3. Cost-to-serve. Freight is cube-driven, so bowls and cups carry roughly 2-3x
#    the freight burden of plates and cutlery per revenue dollar. Weight-based
#    or flat-rate allocation misses this entirely.
# 4. Allocation method reorders the SKU ranking. Overhead by units produced vs
#    by machine hours flips bowls (SKU-1004/1005) from mid-pack to worst, and
#    moves plates the other way. Neither method is "correct" - it is a judgment
#    call a human must own, and it changes which SKUs look worth keeping.
# 5. Dirty data. 9 exact duplicate order lines and 14 unflagged negative-qty
#    returns. Any agent that does not reconcile row counts will overstate revenue.
# ---------------------------------------------------------------------------