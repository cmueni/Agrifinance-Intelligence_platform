"""Simulated Kenyan agrifinance data: macro, climate, markets, agri-SME loan panel, applications and enterprise universe.

Everything here is synthetic so the platform can be demonstrated without confidential data. The structure mirrors
the data contract a live deployment would receive from CBK, KNBS, KAMIS, KMD/CHIRPS, lenders and credit bureaus.
Causal links are built in deliberately: rainfall drives production and producer cash flow; commodity prices and
input costs drive margins; interest rates drive debt service; product structure that does not match the cash cycle
raises repayment stress.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def _sig(x):
    return 1 / (1 + np.exp(-x))


def _months(burn: int):
    return pd.period_range(end=pd.Period(C.AS_OF, "M"), periods=C.HISTORY_MONTHS + burn, freq="M")


# --------------------------------------------------------------------------- #
# Macro
# --------------------------------------------------------------------------- #
def macro_series(months: pd.PeriodIndex) -> pd.DataFrame:
    cbr_points = {"2023-12": 12.5, "2024-02": 13.0, "2024-08": 12.75, "2024-10": 12.0, "2024-12": 11.25, "2025-02": 10.75, "2025-04": 10.0,
                  "2025-06": 9.75, "2025-08": 9.5, "2025-10": 9.25, "2025-12": 9.0, "2026-02": 8.75}
    cbr, cur = [], 12.5
    for m in months:
        cur = cbr_points.get(str(m), cur)
        cbr.append(cur)
    n = len(months)
    rng = np.random.default_rng(7)
    infl = np.interp(np.arange(n), [0, n * 0.35, n * 0.8, n - 3, n - 1], [5.5, 3.2, 4.4, 5.5, 6.6]) + rng.normal(0, 0.12, n)
    infl[-1] = 6.6
    fx = np.interp(np.arange(n), [0, n * 0.3, n - 1], [150, 129.5, 129.4]) + rng.normal(0, 0.3, n)
    diesel = np.interp(np.arange(n), [0, n * 0.5, n - 4, n - 1], [182, 168, 171, 180]) + rng.normal(0, 1.0, n)
    fert = np.exp(np.cumsum(rng.normal(-0.002, 0.02, n)))
    fert = fert / fert[-13] * 100
    feed = np.exp(np.cumsum(rng.normal(0.003, 0.018, n)))
    feed = feed / feed[-13] * 100
    return pd.DataFrame({"month": [str(m) for m in months], "cbr": cbr, "inflation": infl.round(1), "usd_kes": fx.round(1),
                         "diesel_kes": diesel.round(1), "fertiliser_index": fert.round(1), "feed_index": feed.round(1)})


# --------------------------------------------------------------------------- #
# Climate
# --------------------------------------------------------------------------- #
def climate_series(months: pd.PeriodIndex, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    seasons = sorted({(m.year if m.month >= 3 else m.year - 1, "MAM" if 3 <= m.month <= 5 else "OND") for m in months})
    region_shock = {}
    for s in seasons:
        base = rng.normal(0, 0.15)
        for r in {v[4] for v in C.COUNTIES.values()}:
            region_shock[(s, r)] = base + rng.normal(0, 0.12)
    # recent poor seasons in eastern, coastal and southern rift ASAL counties
    for r in ("Eastern", "Coast"):
        region_shock[((2025, "OND"), r)] = -0.30
        region_shock[((2026, "MAM"), r)] = -0.35
    region_shock[((2026, "MAM"), "Rift Valley")] = -0.12
    for cty, (lat, lon, asal, irr, region) in C.COUNTIES.items():
        prev = 0.0
        for m in months:
            season = (m.year if m.month >= 3 else m.year - 1, "MAM" if 3 <= m.month <= 5 else "OND")
            rainy = m.month in (3, 4, 5, 10, 11, 12)
            s_anom = region_shock[(season, region)] * (1.3 if asal else 1.0) + rng.normal(0, 0.06)
            anom = s_anom if rainy else 0.3 * prev + rng.normal(0, 0.04)
            ndvi = 0.6 * prev + 0.4 * anom
            rows.append(dict(month=str(m), county=cty, rain_anomaly=round(anom * 100, 1), ndvi_anomaly=round(ndvi * 100, 1)))
            prev = anom
    df = pd.DataFrame(rows)
    df["drought_phase"] = np.select([df["ndvi_anomaly"] <= -25, df["ndvi_anomaly"] <= -12], ["Alarm", "Alert"], default="Normal")
    outlook = {cty: (-20 if C.COUNTIES[cty][4] in ("Eastern", "Coast") else -5 if C.COUNTIES[cty][4] == "Rift Valley" else 5) + rng.normal(0, 4)
               for cty in C.COUNTIES}
    df["season_outlook"] = df["county"].map(outlook).round(1)   # next-season rainfall outlook, % vs normal
    return df


# --------------------------------------------------------------------------- #
# Markets
# --------------------------------------------------------------------------- #
def market_series(months: pd.PeriodIndex, climate: pd.DataFrame, macro: pd.DataFrame, seed: int = 21) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(months)
    rain = climate.pivot(index="month", columns="county", values="rain_anomaly").reindex([str(m) for m in months]) / 100
    rows = []
    for vc, p in C.VALUE_CHAINS.items():
        w = pd.Series(p["counties"], dtype=float)
        chain_rain = (rain[w.index] * w / w.sum()).sum(axis=1).to_numpy()
        lag_rain = np.concatenate([[0, 0], chain_rain[:-2]])
        drift = {"Coffee": -0.008, "Tea": -0.003, "Maize": -0.004, "Avocado and macadamia": 0.004, "Dairy": 0.003, "Poultry": 0.002}.get(vc, 0.001)
        shocks = rng.normal(drift, p["price_vol"], n) - 0.25 * np.diff(np.concatenate([[0], lag_rain]))  # scarcity lifts prices
        season = np.array([0.04 * np.cos(2 * np.pi * (m.month - p["harvest"][0]) / 12) for m in months]) * (1 if p["storable"] else 0.3)
        price = 100 * np.exp(np.cumsum(shocks) + season)
        price = price / price[-13] * 100
        inp = macro["fertiliser_index"].to_numpy() if p["input"] == "Fertiliser" else macro["feed_index"].to_numpy() if p["input"] == "Animal feed" else macro["diesel_kes"].to_numpy() / macro["diesel_kes"].iloc[-13] * 100
        inp = inp * np.exp(rng.normal(0, 0.01, n))
        production = 100 * (1 + p["climate"] * 0.8 * lag_rain + p["growth"] * np.arange(n) / 12 - p["growth"] * (n - 13) / 12) * np.exp(rng.normal(0, 0.02, n))
        export = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.02, n))) if p["export"] > 0.2 else np.full(n, np.nan)
        for i, m in enumerate(months):
            rows.append(dict(month=str(m), value_chain=vc, price_index=round(price[i], 1), input_cost_index=round(inp[i], 1),
                             production_index=round(production[i], 1), export_index=None if np.isnan(export[i]) else round(export[i], 1)))
    df = pd.DataFrame(rows)
    df["margin_index"] = (100 * df["price_index"] / df["input_cost_index"]).round(1)
    return df


# --------------------------------------------------------------------------- #
# Borrowers and monthly loan panel
# --------------------------------------------------------------------------- #
def borrowers_and_panel(months: pd.PeriodIndex, burn: int, climate: pd.DataFrame, market: pd.DataFrame, macro: pd.DataFrame, n: int = C.N_BORROWERS, seed: int = 2026):
    rng = np.random.default_rng(seed)
    M = len(months)
    vcs = list(C.VALUE_CHAINS)
    chain_w = np.array([{"Dairy": 1.6, "Maize": 1.4, "Horticulture": 1.3, "Tea": 0.9, "Coffee": 0.8, "Poultry": 1.0, "Avocado and macadamia": 0.6,
                         "Pulses": 0.6, "Sugarcane": 0.6, "Edible oils": 0.4, "Beef and livestock": 0.6, "Fisheries and aquaculture": 0.4}[v] for v in vcs])
    chain = rng.choice(vcs, n, p=chain_w / chain_w.sum())
    actor = np.empty(n, dtype=object)
    county = np.empty(n, dtype=object)
    for v in vcs:
        idx = np.where(chain == v)[0]
        a = C.VALUE_CHAINS[v]["actors"]
        actor[idx] = rng.choice(list(a), len(idx), p=np.array(list(a.values())) / sum(a.values()))
        c = C.VALUE_CHAINS[v]["counties"]
        county[idx] = rng.choice(list(c), len(idx), p=np.array(list(c.values()), float) / sum(c.values()))
    processors = np.isin(actor, ["Processor", "Exporter"])
    county = np.where(processors & (rng.random(n) < 0.25), "Nairobi", county)

    lnames = list(C.LENDERS)
    lw = np.array([C.LENDERS[l][1] for l in lnames])
    lender = rng.choice(lnames, n, p=lw / lw.sum())
    ltype = np.array([C.LENDERS[l][0] for l in lender])
    size = rng.choice(list(C.SIZES), n, p=[v[0] for v in C.SIZES.values()])
    size = np.where(np.isin(actor, ["Processor", "Exporter"]) & (size == "Micro"), "Small", size)
    women = rng.random(n) < np.where(np.isin(chain, ["Horticulture", "Poultry", "Dairy", "Pulses"]), 0.36, 0.22) * np.where(size == "Medium", 0.6, 1.0)
    youth = rng.random(n) < 0.22
    first_time = rng.random(n) < np.where(np.isin(ltype, ["Digital lender", "SACCO", "Microfinance bank"]), 0.40, 0.18)
    registered = rng.random(n) < np.where(size == "Micro", 0.45, np.where(size == "Small", 0.80, 0.97))
    insured = rng.random(n) < np.where(actor == "Producer", 0.14, 0.08)
    contracted = np.clip(rng.beta(2, 3, n) + np.where(np.isin(chain, ["Tea", "Sugarcane", "Coffee"]), 0.25, 0) + np.where(processors, 0.1, 0), 0, 1)
    buyer_conc = np.clip(rng.beta(2.5, 3, n) + np.where(np.isin(chain, ["Sugarcane", "Tea"]), 0.2, 0), 0.05, 0.98)
    recv_days = np.clip(rng.normal(np.where(processors, 55, np.where(actor == "Aggregator", 40, np.where(actor == "Cooperative", 60, 20))), 15), 0, 180)
    if True:
        recv_days = np.where(chain == "Sugarcane", recv_days + 40, recv_days)   # delayed miller payments
    turnover = np.exp(np.array([C.SIZES[s][1] for s in size]) + 1.6 + np.array([C.ACTOR_SIZE_UPLIFT[a] for a in actor]) + rng.normal(0, 0.5, n))

    # products: conventional products dominate, as in CBK MSME data
    product = np.empty(n, dtype=object)
    for i in range(n):
        opts = {"Term loan": 0.38, "Overdraft": 0.22, "Seasonal working capital": 0.10, "Asset and equipment finance": 0.07, "Input finance": 0.06,
                "Invoice and receivables finance": 0.04, "Warehouse receipt finance": 0.03, "Contract and purchase-order finance": 0.04,
                "Trade and pre-shipment finance": 0.03, "Insurance-linked loan": 0.03}
        if actor[i] != "Exporter":
            opts["Trade and pre-shipment finance"] = 0.0
        if not C.VALUE_CHAINS[chain[i]]["storable"]:
            opts["Warehouse receipt finance"] = 0.0
        if ltype[i] == "Digital lender":
            opts = {"Input finance": 0.4, "Seasonal working capital": 0.35, "Overdraft": 0.25}
        pv = np.array(list(opts.values()))
        product[i] = rng.choice(list(opts), p=pv / pv.sum())
    loan = np.maximum(20_000, turnover * rng.uniform(0.15, 0.45, n))
    loan = np.where(ltype == "Digital lender", np.minimum(loan, rng.uniform(20_000, 300_000, n)), loan)
    tenor = np.where(np.isin(product, ["Term loan", "Asset and equipment finance"]), rng.integers(24, 61, n),
                     np.where(product == "Overdraft", 12, rng.integers(4, 13, n)))
    rate = np.array([C.LENDERS[l][2] for l in lender]) + rng.normal(0, 0.01, n) + np.where(size == "Micro", 0.02, 0)
    collateral = np.select(
        [product == "Warehouse receipt finance", product == "Invoice and receivables finance", product == "Asset and equipment finance",
         np.isin(actor, ["Cooperative"]) | (ltype == "SACCO"), ltype == "Digital lender", size == "Micro"],
        ["Warehouse receipt", "Receivables", "Chattels and equipment", "Group or cooperative guarantee", "Unsecured", "Unsecured"], default="Title deed")

    cycle = np.array([C.VALUE_CHAINS[c]["cycle"] for c in chain])
    seasonal_actor = np.isin(actor, ["Producer", "Aggregator", "Cooperative"])
    mismatch = np.isin(product, ["Term loan", "Overdraft"]) & seasonal_actor & (cycle >= 110)
    structured = np.isin(product, ["Invoice and receivables finance", "Warehouse receipt finance", "Contract and purchase-order finance", "Trade and pre-shipment finance", "Insurance-linked loan"])

    orig = -rng.integers(0, 30, n)
    orig = np.where(rng.random(n) < 0.3, rng.integers(burn, M - 2, n), orig)
    active = np.arange(M)[None, :] >= orig[:, None]

    # latent health
    mkt = market.pivot(index="month", columns="value_chain", values="margin_index").reindex([str(m) for m in months])
    marg = np.log(mkt / mkt.iloc[0])
    rain = climate.pivot(index="month", columns="county", values="rain_anomaly").reindex([str(m) for m in months]) / 100
    cbr = macro["cbr"].to_numpy()
    prod_share = np.array([C.ACTOR_TRANSMISSION[a]["production"] for a in actor])
    int_share = np.array([C.ACTOR_TRANSMISSION[a]["interest_share"] for a in actor])
    clim = np.array([C.VALUE_CHAINS[c]["climate"] for c in chain])
    base_npl = np.array([C.VALUE_CHAINS[c]["npl"] for c in chain])
    det = rng.random(n) < 0.06 + 1.0 * base_npl + 0.15 * (chain == "Sugarcane")
    h0 = 0.8 + 0.45 * rng.standard_normal(n) - 6.0 * (base_npl - 0.14) - 0.25 * (size == "Micro") - 0.1 * (~registered)
    H = np.zeros((n, M))
    h = h0.copy()
    shock = np.zeros(n)
    d0 = rng.integers(2, M, n)
    dlen = rng.integers(4, 10, n)
    for t in range(M):
        m = months[t]
        margin_t = marg.iloc[t].reindex(chain).to_numpy()
        margin_lag = marg.iloc[max(0, t - 2)].reindex(chain).to_numpy()
        rain_t = rain.iloc[max(0, t - 1)].reindex(county).to_numpy()
        climate_hit = np.minimum(rain_t, 0) * clim * prod_share * np.where(insured, 0.5, 1.0)
        off_season = np.array([m.month not in C.VALUE_CHAINS[c]["harvest"] for c in chain])
        struct = np.where(mismatch & off_season, -0.02, 0) + np.where(structured, 0.015, 0) - 0.02 * (base_npl - 0.14) * 10
        rate_hit = -(cbr[t] - 10.0) * 0.04 * int_share * 10
        drift = np.where(det & (t >= d0) & (t < d0 + dlen), -0.2, 0)
        shock = 0.6 * shock + climate_hit * 0.10
        h = 0.85 * h + 0.15 * h0 + 0.35 * (margin_lag) * (1 - 0.5 * prod_share) + shock * 0.5 + struct + rate_hit * 0.1 + drift + rng.normal(0, 0.09, n)
        H[:, t] = h

    # observables
    harvest_factor = np.zeros((n, M))
    for t, m in enumerate(months):
        in_h = np.array([m.month in C.VALUE_CHAINS[c]["harvest"] for c in chain])
        amp = np.where(seasonal_actor, 0.6, 0.15)
        harvest_factor[:, t] = np.where(in_h, 1 + amp, 1 - amp * 0.5)
    inflow = (turnover / 12)[:, None] * harvest_factor * np.exp(0.35 * (H - h0[:, None]) + rng.normal(0, 0.08, (n, M)))
    util = np.clip(_sig(0.3 - 1.2 * (H - h0[:, None]) + rng.normal(0, 0.15, (n, M))), 0.05, 1.05)
    recv = np.clip(recv_days[:, None] * np.exp(-0.25 * (H - h0[:, None])) + rng.normal(0, 3, (n, M)), 0, 240)

    dpd = np.zeros((n, M))
    restr = np.zeros((n, M), dtype=bool)
    prev = np.zeros(n)
    rs = np.zeros(n, dtype=bool)
    for t in range(M):
        rel = H[:, max(0, t - 2)] - h0
        missed = (0.7 * rel + 0.3 * (H[:, max(0, t - 2)] - 0.8) + 0.15 * rng.standard_normal(n)) < -0.7
        cure = rng.random(n) < _sig(3.5 * (H[:, t] - h0 + 0.5)) * np.where(prev >= 90, 0.015, 0.6)
        cur = np.where(missed, prev + 30, np.where(prev > 0, np.where(cure, 0, prev + 30), 0))
        late = (cur == 0) & (rng.random(n) < 0.03 + 0.15 * np.clip(-(H[:, t] - h0) - 0.2, 0, 2))
        cur = np.where(late, rng.integers(1, 21, n), cur)
        do_r = (cur >= 60) & (cur < 120) & ~rs & (rng.random(n) < 0.2)
        rs |= do_r
        cur = np.where(do_r, 0, cur)
        cur = np.where(active[:, t], cur, 0)
        written = cur >= 450
        active[:, t:] &= ~written[:, None] | (np.arange(M - t)[None, :] == 0)
        dpd[:, t] = cur
        restr[:, t] = rs
        prev = cur
    mob = np.arange(M)[None, :] - orig[:, None]
    amort = np.where(np.isin(product, ["Term loan", "Asset and equipment finance"])[:, None], np.clip(1 - mob / tenor[:, None], 0.05, 1), 1.0)
    outstanding = np.where(np.isin(product, ["Overdraft", "Seasonal working capital", "Input finance", "Invoice and receivables finance",
                                             "Warehouse receipt finance", "Contract and purchase-order finance", "Trade and pre-shipment finance"])[:, None],
                           loan[:, None] * util, loan[:, None] * amort)
    outstanding = np.where(active, outstanding, 0)

    borrowers = pd.DataFrame({
        "borrower_id": [f"A{100000 + i}" for i in range(n)], "business": [f"Agri SME {i + 1:05d}" for i in range(n)],
        "value_chain": chain, "l2": [C.VALUE_CHAINS[c]["l2"] for c in chain], "actor": actor, "county": county,
        "region": [C.COUNTIES[c][4] for c in county], "asal": [C.COUNTIES[c][2] for c in county],
        "lender": lender, "lender_type": ltype, "size": size, "women_owned": women, "youth_owned": youth, "first_time": first_time,
        "registered": registered, "insured": insured, "contracted_sales_share": contracted.round(2), "buyer_concentration": buyer_conc.round(2),
        "receivable_days_base": recv_days.round(0), "annual_turnover_kes": turnover.round(-3), "product": product, "loan_amount_kes": loan.round(-3),
        "tenor_months": tenor, "interest_rate": rate.round(3), "collateral": collateral, "cash_cycle_days": cycle,
        "origination_t": orig - burn,
    })
    flat = lambda a: a.reshape(-1)
    panel = pd.DataFrame({
        "borrower_id": np.repeat(borrowers["borrower_id"].to_numpy(), M), "month": np.tile([str(m) for m in months], n), "t": np.tile(np.arange(M), n),
        "active": flat(active), "outstanding_kes": flat(outstanding), "dpd": flat(dpd), "restructured": flat(restr),
        "inflow_kes": flat(inflow), "utilization": flat(util), "receivable_days": flat(recv),
    })
    panel = panel[panel["active"] & (panel["t"] >= burn)].drop(columns="active")
    panel["t"] -= burn
    borrowers = borrowers[borrowers["borrower_id"].isin(panel["borrower_id"].unique())].reset_index(drop=True)
    return borrowers, panel.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Applications (demand and approvals)
# --------------------------------------------------------------------------- #
def applications(months: pd.PeriodIndex, borrowers: pd.DataFrame, seed: int = 31) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    reasons = ["Insufficient collateral", "Incomplete records or financials", "Sector or climate risk", "Poor credit history", "Insufficient cash flow"]
    base = borrowers.sample(frac=1.0, replace=True, random_state=seed)
    per_month = 900
    for t, m in enumerate(months):
        s = base.sample(per_month, replace=True, random_state=seed + t)
        growth = 1 + np.array([C.VALUE_CHAINS[v]["growth"] for v in s["value_chain"]]) * t / 12
        keep = rng.random(len(s)) < np.clip(growth / 1.3, 0, 1)
        s = s[keep]
        collateral_ok = (s["collateral"] != "Unsecured").to_numpy() | (s["size"] == "Medium").to_numpy()
        risk = np.array([C.VALUE_CHAINS[v]["npl"] for v in s["value_chain"]])
        logit = 1.2 + 0.9 * collateral_ok - 6 * (risk - 0.14) + 0.5 * s["registered"].to_numpy() - 0.35 * s["women_owned"].to_numpy() - 0.3 * s["first_time"].to_numpy() + rng.normal(0, 0.5, len(s))
        approved = rng.random(len(s)) < _sig(logit)
        rw = np.array([0.34, 0.24, 0.16, 0.14, 0.12])
        reason = np.where(approved, "", [rng.choice(reasons, p=(rw * np.array([1.4 if not c else 0.6, 1.3 if not r else 0.8, 1.0 + 3 * rk, 1, 1]))
                                                     / (rw * np.array([1.4 if not c else 0.6, 1.3 if not r else 0.8, 1.0 + 3 * rk, 1, 1])).sum())
                                         for c, r, rk in zip(collateral_ok, s["registered"], risk)])
        amount = s["loan_amount_kes"].to_numpy() * rng.uniform(0.7, 1.4, len(s))
        rows.append(pd.DataFrame({"month": str(m), "value_chain": s["value_chain"].to_numpy(), "county": s["county"].to_numpy(), "actor": s["actor"].to_numpy(),
                                  "size": s["size"].to_numpy(), "women_owned": s["women_owned"].to_numpy(), "youth_owned": s["youth_owned"].to_numpy(),
                                  "first_time": s["first_time"].to_numpy(), "lender": s["lender"].to_numpy(), "lender_type": s["lender_type"].to_numpy(),
                                  "product": s["product"].to_numpy(), "amount_kes": amount.round(-3), "approved": approved, "decline_reason": reason}))
    return pd.concat(rows, ignore_index=True)


# --------------------------------------------------------------------------- #
# Enterprise universe (for financing demand)
# --------------------------------------------------------------------------- #
def enterprise_universe(borrowers: pd.DataFrame, seed: int = 41) -> pd.DataFrame:
    """Estimated number of agri SMEs and turnover by value chain, county and actor (proxy for census and survey data)."""
    rng = np.random.default_rng(seed)
    g = borrowers.groupby(["value_chain", "county", "actor"]).agg(financed=("borrower_id", "size"), avg_turnover=("annual_turnover_kes", "median")).reset_index()
    pen = g["value_chain"].map(lambda v: C.VALUE_CHAINS[v]["penetration"])
    g["enterprises"] = np.maximum(g["financed"], np.round(g["financed"] / (pen * rng.uniform(0.6, 1.4, len(g))))).astype(int)
    g["cycle_days"] = g["value_chain"].map(lambda v: C.VALUE_CHAINS[v]["cycle"])
    capex = g["actor"].map({"Processor": 0.25, "Exporter": 0.15, "Producer": 0.10, "Cooperative": 0.12, "Aggregator": 0.08, "Distributor": 0.06, "Input supplier": 0.06})
    g["demand_kes"] = g["enterprises"] * g["avg_turnover"] * (g["cycle_days"] / 365 * 0.8 + capex)
    g["coverage"] = np.select([g["financed"] >= 30, g["financed"] >= 10], ["High", "Medium"], default="Low")
    return g


def build_all(n: int = C.N_BORROWERS, seed: int = 2026):
    burn = 24
    months = _months(burn)
    macro = macro_series(months)
    climate = climate_series(months)
    market = market_series(months, climate, macro)
    borrowers, panel = borrowers_and_panel(months, burn, climate, market, macro, n=n, seed=seed)
    keep = [str(m) for m in months[burn:]]
    apps = applications(months[burn:], borrowers)
    universe = enterprise_universe(borrowers)
    macro, climate, market = (d[d["month"].isin(keep)].reset_index(drop=True) for d in (macro, climate, market))
    return dict(macro=macro, climate=climate, market=market, borrowers=borrowers, panel=panel, applications=apps, universe=universe)
