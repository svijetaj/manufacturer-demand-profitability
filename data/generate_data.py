"""
Meridian Finance & Analytics - synthetic data generator (merged schema).

Schema is Srinivas's star schema with two structural changes:
  - overhead removed from Fact_COGS -> Fact_Overhead_Pool (plant x month, UNALLOCATED)
  - freight removed from Fact_COGS  -> Fact_Freight (order grain, cube-driven)

Everything ties arithmetically. Findings are planted deliberately; the answer key
is eval/answer_key.yaml. Do not put the key in an agent prompt.

    python data/generate_data.py --out data/raw
"""
import argparse, os
import numpy as np
import pandas as pd

TODAY = pd.Timestamp("2026-08-15")

CATEGORIES = {
    # category      : (cube_index, base_price, base_wt_g, material)
    "Paper Plates":   (0.9, 0.104, 15.0, "Bagasse"),
    "Bowls":          (3.4, 0.121, 20.0, "Molded Fiber"),
    "Paper Cups":     (4.2, 0.108, 11.0, "PLA Paper"),
    "Food Containers":(3.0, 0.243, 28.0, "RPET"),
    "Cutlery":        (0.5, 0.044,  5.5, "PLA Paper"),
}
SUBCATS = {"Standard": 1.00, "Heavy Duty": 1.18, "Premium": 1.34}
BRANDS = ["EcoServe", "GreenChoice", "PurePack", "EarthWare"]
MATERIALS = {"Bagasse": 1.85, "Molded Fiber": 2.10, "PLA Paper": 3.95, "RPET": 3.40}
MATERIAL_VOL = {"Bagasse": .04, "Molded Fiber": .05, "PLA Paper": .09, "RPET": .12}

PLANTS = ["PLANT-EAST", "PLANT-WEST", "PLANT-CENTRAL", "PLANT-SOUTH"]
LABOR_RATE = {"PLANT-EAST": 24.5, "PLANT-WEST": 27.8, "PLANT-CENTRAL": 22.9, "PLANT-SOUTH": 21.3}
# units per machine hour by category - cutlery is injection moulded and very fast
THROUGHPUT = {"Paper Plates": 42000, "Bowls": 26000, "Paper Cups": 55000,
              "Food Containers": 19000, "Cutlery": 96000}
SCRAP = {"Paper Plates": .031, "Bowls": .048, "Paper Cups": .022,
         "Food Containers": .052, "Cutlery": .017}

TYPES = ["Distributor", "Food Service", "Retail", "Wholesale"]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
INDUSTRIES = ["Distribution", "Hospitality", "Restaurants", "Retail"]
REGIONS = ["Midwest", "Northeast", "South", "West"]
STATES = {"Midwest": ["IL", "OH"], "Northeast": ["NY", "PA"],
          "South": ["TX", "FL"], "West": ["CA", "WA"]}
BUS = ["Foodservice Packaging", "Retail Packaging", "Industrial", "Private Label"]

SEASON = {  # month 1-12
    "Paper Plates":    [.85,.82,.92,1.05,1.22,1.35,1.40,1.28,1.05,.95,1.10,1.15],
    "Bowls":           [1.05,1.02,.98,.95,.94,.96,.98,1.00,1.06,1.12,1.18,1.16],
    "Paper Cups":      [.78,.80,.95,1.12,1.30,1.48,1.52,1.42,1.10,.92,.82,.85],
    "Food Containers": [.95,.94,.98,1.02,1.08,1.14,1.16,1.12,1.04,1.00,1.02,1.06],
    "Cutlery":         [.90,.88,.96,1.04,1.16,1.26,1.30,1.22,1.04,.98,1.02,1.04],
}


def build_dims(rng, n_cust=120, n_prod=80, n_reps=24):
    months = pd.date_range("2024-09-01", "2026-08-01", freq="MS")

    # ---- Dim_Date
    days = pd.date_range(months[0], TODAY, freq="D")
    dim_date = pd.DataFrame({
        "Date_Key": days.strftime("%Y%m%d").astype(int), "Date": days.date,
        "Day": days.day, "Week": days.isocalendar().week.values, "Month": days.month,
        "Quarter": days.quarter, "Year": days.year,
        "Fiscal_Period": days.month, "Fiscal_Quarter": days.quarter, "Fiscal_Year": days.year})

    # ---- Dim_Product
    rows = []
    for i in range(n_prod):
        cat = list(CATEGORIES)[i % len(CATEGORIES)]
        cube, price, wt, mat = CATEGORIES[cat]
        sub = list(SUBCATS)[(i // len(CATEGORIES)) % 3]
        rows.append({
            "Product_ID": f"P{i+1:04d}", "Product_Code": f"{cat[:2].upper()}-{i+1:04d}",
            "Product_Name": f"{cat} {sub} {i+1}", "Product_Category": cat,
            "Product_Subcategory": sub, "Brand": BRANDS[i % 4],
            "SKU": f"SKU-{i+1:05d}", "Product_Line": f"{cat} Line",
            "Material": mat, "Unit_Weight_G": round(wt * SUBCATS[sub], 2),
            "Cube_Index": cube, "List_Price_USD": round(price * SUBCATS[sub], 4),
            "Plant_ID": PLANTS[i % 4], "Launch_Date": "2024-01-01", "Discontinued_Flag": "N"})
    dim_product = pd.DataFrame(rows)

    # ---- Dim_Sales_Rep
    dim_rep = pd.DataFrame([{
        "Sales_Rep_ID": f"SR{i+1:03d}", "Sales_Rep_Name": f"Sales Rep {i+1}",
        "Sales_Region": REGIONS[i % 4], "Sales_Org": f"Sales Org {i%5+1}",
        "Hire_Date": "2022-01-01"} for i in range(n_reps)])

    # ---- Dim_Customer  (Pareto revenue weights -> real concentration)
    w = rng.pareto(1.1, n_cust) + 1
    w = np.sort(w)[::-1]
    rows = []
    for i in range(n_cust):
        reg = REGIONS[i % 4]
        ctype = TYPES[i % 4]
        seg = "Enterprise" if i < n_cust*.12 else ("Mid-Market" if i < n_cust*.45 else "SMB")
        rows.append({
            "Customer_ID": f"C{i+1:05d}", "Customer_Name": f"Customer {i+1}",
            "Customer_Type": ctype, "Customer_Segment": seg,
            "Industry": INDUSTRIES[i % 4], "Sales_Region": reg,
            "Country": "USA", "State": STATES[reg][i % 2], "City": f"City {i+1}",
            "Parent_Customer": "", "Sales_Rep_ID": f"SR{(i % n_reps)+1:03d}",
            "Payment_Terms_Days": [30, 45, 60][i % 3],
            "Base_Discount_Pct": round(0.06 if f"C{i+1:05d}" == "C00003" else
                {"Distributor": .30, "Wholesale": .26, "Retail": .21, "Food Service": .15}[ctype]
                + rng.normal(0, .015), 4),
            "_weight": w[i]})
    dim_customer = pd.DataFrame(rows)

    # ---- Dim_Rebate_Program : rebate is a CONTRACT, one rate per customer
    rows = []
    for i, c in dim_customer.iterrows():
        if c.Customer_ID == "C00003":          # planted rebate trap (F1)
            rate, rtype = .155, "Volume"
        elif c.Customer_Segment == "Enterprise":
            rate, rtype = rng.uniform(.035, .06), "Volume"
        elif c.Customer_Segment == "Mid-Market":
            rate, rtype = rng.uniform(.015, .035), rng.choice(["Volume", "Growth"])
        else:
            rate, rtype = 0.0, "None"
        rows.append({"Rebate_Program_ID": f"RP{i+1:04d}", "Customer_ID": c.Customer_ID,
                     "Rebate_Type": rtype, "Rebate_Rate": round(rate, 4), "Status": "Active"})
    dim_rebate = pd.DataFrame(rows)

    dim_org = pd.DataFrame([{"Business_Unit": b, "Division": f"Division {i%2+1}",
                             "Department": f"Department {i+1}", "Cost_Center": f"CC{i+1:03d}",
                             "Profit_Center": f"PC{i%4+1:03d}", "Sales_Org": f"Sales Org {i%5+1}",
                             "Region": REGIONS[i % 4], "Country": "USA"}
                            for i, b in enumerate(BUS * 2)])
    dim_pc = pd.DataFrame([{"Profit_Center_ID": f"PC{i+1:03d}",
                            "Profit_Center_Name": f"Profit Center {i+1}",
                            "Business_Unit": BUS[i], "Division": f"Division {i%2+1}",
                            "Manager": f"Manager {i+1}"} for i in range(4)])
    return months, dim_date, dim_product, dim_customer, dim_rep, dim_rebate, dim_org, dim_pc


def build_material_costs(months, rng):
    """RPET steps up 34% at month 13 and never comes back. PLA rises 11%."""
    rows = []
    for m, base in MATERIALS.items():
        c = base
        for i, dt in enumerate(months):
            c *= 1 + rng.normal(.002, MATERIAL_VOL[m] / 4)
            if i == 12 and m == "RPET":
                c *= 1.34
            if i == 12 and m == "PLA Paper":
                c *= 1.11
            rows.append({"Month": dt.date(), "Material": m, "Cost_Per_Kg": round(c, 4)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)

    months, dim_date, dp, dc, drep, dreb, dorg, dpc = build_dims(rng)
    matcost = build_material_costs(months, rng)
    mc_lookup = {(r.Month, r.Material): r.Cost_Per_Kg for r in matcost.itertuples()}

    prod = dp.set_index("Product_ID")
    cust = dc.set_index("Customer_ID")
    reb_rate = dreb.set_index("Customer_ID").Rebate_Rate.to_dict()

    sales, cogs, freight = [], [], []
    tid = oid = 0
    weights = dc._weight.values / dc._weight.sum()

    for dt in months:
        mi = dt.month - 1
        for _ in range(260):
            oid += 1
            order_id = f"O{oid:07d}"
            ci = rng.choice(len(dc), p=weights)
            c = cust.iloc[ci]
            cid = dc.Customer_ID.iloc[ci]
            day = int(rng.integers(1, 29))
            odate = dt.replace(day=day)
            if odate > TODAY:
                continue
            picks = rng.choice(len(dp), size=int(rng.integers(1, 5)), replace=False)
            order_cube = 0.0
            for ln, pi in enumerate(picks, start=1):
                tid += 1
                p = prod.iloc[pi]
                pid = dp.Product_ID.iloc[pi]
                cat = p.Product_Category

                base_units = {"Enterprise": 26000, "Mid-Market": 9000, "SMB": 3000}[c.Customer_Segment]
                qty = max(int(base_units * SEASON[cat][mi] * rng.uniform(.5, 1.6)), 500)

                # PRICE: list less customer discount. RPET items are never repriced
                # after the material step change -> planted finding F2.
                gross_list = qty * p.List_Price_USD
                discount = gross_list * c.Base_Discount_Pct
                returns = gross_list * rng.uniform(.004, .012) if rng.random() < .06 else 0.0
                net = gross_list - discount - returns

                # COST: material + labour from real drivers. NO overhead, NO freight here.
                kg = qty / (1 - SCRAP[cat]) * p.Unit_Weight_G / 1000
                mat_cost = kg * mc_lookup[(dt.date(), p.Material)]
                mach_hrs = qty / (1 - SCRAP[cat]) / THROUGHPUT[cat]
                lab_cost = mach_hrs * 1.4 * LABOR_RATE[p.Plant_ID]

                sales.append({
                    "Transaction_ID": f"T{tid:07d}", "Order_ID": order_id,
                    "Invoice_ID": f"INV{oid:07d}", "Invoice_Line_ID": f"IL{tid:07d}",
                    "Transaction_Date": odate.date(), "Posting_Date": odate.date(),
                    "Customer_ID": cid, "Product_ID": pid, "Sales_Rep_ID": c.Sales_Rep_ID,
                    "Region_ID": c.Sales_Region, "Business_Unit": BUS[pi % 4],
                    "Quantity_Sold": qty,
                    "Gross_Sales_Amount": round(gross_list, 2),
                    "Discount_Amount": round(discount, 2),
                    "Returns_Amount": round(returns, 2),
                    "Net_Sales_Amount": round(net, 2)})
                cogs.append({
                    "Transaction_ID": f"T{tid:07d}", "Product_ID": pid,
                    "Plant_ID": p.Plant_ID, "Material_ID": p.Material,
                    "Production_Date": odate.date(),
                    "Units_Produced": int(qty / (1 - SCRAP[cat])),
                    "Material_KG": round(kg, 3),
                    "Machine_Hours": round(mach_hrs, 4),
                    "Material_Cost": round(mat_cost, 2),
                    "Labor_Cost": round(lab_cost, 2),
                    "Scrap_Rate": SCRAP[cat]})
                order_cube += qty * p.Unit_Weight_G / 1000 * p.Cube_Index

            # FREIGHT at order grain, cube-driven -> planted finding F3
            if order_cube:
                freight.append({
                    "Order_ID": order_id, "Customer_ID": cid, "Ship_Date": odate.date(),
                    "Freight_Cost": round(order_cube * .085 * rng.uniform(.9, 1.1), 2)})

    fs = pd.DataFrame(sales); fc = pd.DataFrame(cogs); ff = pd.DataFrame(freight)

    # ---- Fact_Rebate : accrual at customer x month against the contract rate
    fs["_m"] = pd.to_datetime(fs.Transaction_Date).values.astype("datetime64[M]")
    g = fs.groupby(["Customer_ID", "_m"], as_index=False).Net_Sales_Amount.sum()
    g["Rebate_Rate"] = g.Customer_ID.map(reb_rate)
    g["Rebate_Amount"] = (g.Net_Sales_Amount * g.Rebate_Rate).round(2)
    fr = g.rename(columns={"_m": "Period"})[["Customer_ID", "Period", "Rebate_Rate", "Rebate_Amount"]]
    fr = fr.merge(dreb[["Customer_ID", "Rebate_Program_ID"]], on="Customer_ID")
    fr["Period"] = pd.to_datetime(fr.Period).dt.date

    # ---- Fact_Commission : rep x month
    gc = fs.groupby(["Sales_Rep_ID", "_m"], as_index=False).Net_Sales_Amount.sum()
    gc["Commission_Rate"] = np.round(rng.uniform(.018, .032, len(gc)), 4)
    gc["Commission_Amount"] = (gc.Net_Sales_Amount * gc.Commission_Rate).round(2)
    gc["Period"] = pd.to_datetime(gc._m).dt.date
    fcm = gc[["Sales_Rep_ID", "Period", "Commission_Rate", "Commission_Amount"]]

    # ---- Fact_Overhead_Pool : plant x month, UNALLOCATED (finding F4 lives here)
    mh = fc.copy()
    mh["_m"] = pd.to_datetime(mh.Production_Date).values.astype("datetime64[M]")
    pool_rows = []
    for (plant, m), _ in mh.groupby(["Plant_ID", "_m"]):
        base = {"PLANT-EAST": 41000, "PLANT-WEST": 52000,
                "PLANT-CENTRAL": 32000, "PLANT-SOUTH": 27000}[plant]
        pool_rows.append({"Month": pd.Timestamp(m).date(), "Plant_ID": plant,
                          "Overhead_Pool_USD": round(base * (1 + rng.normal(0, .04)), 2)})
    fop = pd.DataFrame(pool_rows)

    # ---- OpEx and Budget, calibrated to actual revenue
    net_by_month = fs.groupby("_m").Net_Sales_Amount.sum()
    oe = []
    for m, rev in net_by_month.items():
        for dept, share in [("SG&A", .085), ("Sales", .062), ("Marketing", .031), ("Operations", .048)]:
            oe.append({"Expense_ID": f"E{len(oe)+1:06d}", "GL_Account": 6100 + len(oe) % 4,
                       "Cost_Center": f"CC{len(oe)%8+1:03d}", "Expense_Function": dept,
                       "Expense_Date": pd.Timestamp(m).date(),
                       "Expense_Amount": round(rev * share * rng.uniform(.9, 1.1), 2)})
    foe = pd.DataFrame(oe)

    # ---- Fact_Budget, tied to actual revenue by business unit so variance is real
    bu_by_pc = dpc.set_index("Business_Unit").Profit_Center_ID.to_dict()
    act = fs.groupby(["Business_Unit", "_m"], as_index=False).Net_Sales_Amount.sum()
    act["Profit_Center"] = act.Business_Unit.map(bu_by_pc)
    # each profit centre carries a persistent performance bias: two beat plan, two miss
    bias = {pc: b for pc, b in zip(sorted(dpc.Profit_Center_ID), [0.91, 1.06, 0.97, 1.12])}
    bud = []
    for r in act.itertuples():
        # budget was set BEFORE the period, so it is actual / bias plus noise
        br = r.Net_Sales_Amount / bias[r.Profit_Center] * rng.uniform(.97, 1.03)
        bud.append({"Fiscal_Year": pd.Timestamp(r._2).year,
                    "Fiscal_Period": pd.Timestamp(r._2).month,
                    "Profit_Center": r.Profit_Center, "Business_Unit": r.Business_Unit,
                    "Cost_Center": f"CC{rng.integers(1,9):03d}",
                    "Budget_Revenue": round(br, 2), "Budget_Cost": round(br * .64, 2),
                    "Budget_Profit": round(br * .36, 2),
                    "Forecast_Revenue": round(br * rng.uniform(.98, 1.06), 2),
                    "Forecast_Cost": round(br * .64 * rng.uniform(.98, 1.06), 2)})
    fb = pd.DataFrame(bud)

    # ---- planted dirty rows (F5) - workstream D should find these
    dupes = fs.sample(9, random_state=7)
    rets = fs.sample(14, random_state=11).copy()
    for col in ["Quantity_Sold", "Gross_Sales_Amount", "Discount_Amount", "Net_Sales_Amount"]:
        rets[col] = -(rets[col] * .1).round(2)
    rets["Invoice_Line_ID"] = rets.Invoice_Line_ID + "-R"
    rets["Transaction_ID"] = rets.Transaction_ID + "-R"
    fs = pd.concat([fs, dupes, rets], ignore_index=True).drop(columns=["_m"])

    out = {"Dim_Date": dim_date, "Dim_Product": dp, "Dim_Customer": dc.drop(columns=["_weight"]),
           "Dim_Sales_Rep": drep, "Dim_Rebate_Program": dreb, "Dim_Organization": dorg,
           "Dim_Profit_Center": dpc, "Ref_Material_Cost": matcost,
           "Fact_Sales": fs, "Fact_COGS": fc, "Fact_Freight": ff, "Fact_Rebate": fr,
           "Fact_Commission": fcm, "Fact_Overhead_Pool": fop,
           "Fact_Operating_Expense": foe, "Fact_Budget": fb}
    for name, df in out.items():
        df.to_csv(os.path.join(a.out, f"{name}.csv"), index=False)
        print(f"{name:24s} {len(df):>7,} rows")


if __name__ == "__main__":
    main()
