"""Segment intelligence: risk, climate, market and opportunity scores, financing gap, product fit, scenarios,
benchmarking, inclusion and change detection.

Every score is a weighted sum of 0-100 components with stated anchors, so any score can be decomposed into
the drivers that produced it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def scale(x, lo, hi):
    """Linear 0-100 score between anchors lo (0) and hi (100)."""
    return (100 * (np.asarray(x, dtype=float) - lo) / (hi - lo)).clip(0, 100)


# --------------------------------------------------------------------------- #
# Financing gap
# --------------------------------------------------------------------------- #
MARKET_COVERAGE = 0.60   # reporting institutions' estimated share of formal agricultural credit


def financing_gap(data: dict, feats: pd.DataFrame, t: int | None = None) -> pd.DataFrame:
    T = int(feats["t"].max()) if t is None else int(t)
    cur = feats[feats["t"] == T].groupby(["value_chain", "county", "actor"])["outstanding_kes"].sum().rename("observed_credit_kes")
    u = data["universe"].set_index(["value_chain", "county", "actor"]).join(cur).fillna({"observed_credit_kes": 0}).reset_index()
    u["formal_credit_kes"] = u["observed_credit_kes"] / MARKET_COVERAGE
    u["gap_kes"] = (u["demand_kes"] - u["formal_credit_kes"]).clip(lower=0)
    u["penetration"] = (u["formal_credit_kes"] / u["demand_kes"]).clip(0, 1)
    return u


# --------------------------------------------------------------------------- #
# Product fit
# --------------------------------------------------------------------------- #
def product_fit(rows: pd.DataFrame, climate_risk: pd.Series | None = None) -> pd.DataFrame:
    """Score each financing structure 0-100 for each borrower, with the main reason."""
    r = rows
    vc = r["value_chain"].map(C.VALUE_CHAINS)
    storable = vc.map(lambda p: p["storable"])
    export = vc.map(lambda p: p["export"])
    climate = vc.map(lambda p: p["climate"])
    cycle = r["cash_cycle_days"]
    seasonal = r["actor"].isin(["Producer", "Aggregator", "Cooperative"])
    recv = r.get("receivable_days", r["receivable_days_base"])
    crisk = climate_risk if climate_risk is not None else pd.Series(50, index=r.index)
    s = pd.DataFrame(index=r.index)
    s["Seasonal working capital"] = 40 + 30 * seasonal + 20 * (cycle >= 90) - 10 * r["actor"].isin(["Distributor"])
    s["Term loan"] = 45 + 25 * (r["collateral"] == "Title deed") + 15 * (~seasonal) - 25 * (cycle >= 120) * seasonal - 10 * (crisk >= 60)
    s["Overdraft"] = 40 + 25 * r["actor"].isin(["Distributor", "Input supplier", "Processor"]) - 20 * seasonal * (cycle >= 90)
    s["Asset and equipment finance"] = 30 + 40 * r["actor"].isin(["Processor", "Cooperative", "Exporter"]) + 15 * (r["size"] != "Micro")
    s["Invoice and receivables finance"] = 25 + 0.6 * recv.clip(0, 90) + 15 * (r["buyer_concentration"] >= 0.5) - 20 * (r["actor"] == "Producer")
    s["Warehouse receipt finance"] = np.where(storable, 45 + 30 * r["actor"].isin(["Aggregator", "Cooperative", "Producer"]) + 10 * (cycle >= 120), 0)
    s["Input finance"] = 30 + 45 * (r["actor"] == "Producer") + 10 * r["value_chain"].isin(["Maize", "Pulses", "Horticulture", "Tea", "Coffee", "Sugarcane"])
    s["Contract and purchase-order finance"] = 25 + 60 * r["contracted_sales_share"] + 10 * r["actor"].isin(["Aggregator", "Processor"])
    s["Trade and pre-shipment finance"] = np.where(r["actor"].isin(["Exporter", "Processor"]), 30 + 60 * export, 5)
    s["Insurance-linked loan"] = 20 + 50 * climate * seasonal + 0.25 * crisk - 30 * r["insured"]
    s = s.clip(0, 100).round(0)
    best = s.idxmax(axis=1)
    reason_map = {
        "Seasonal working capital": "Cash arrives at harvest; repayments should follow the crop or production cycle",
        "Term loan": "Stable non-seasonal cash flow and registered collateral",
        "Overdraft": "Frequent, steady inflows from trading",
        "Asset and equipment finance": "Growth depends on processing or storage equipment that can secure the loan",
        "Invoice and receivables finance": "Sales are made on credit to identifiable buyers; receivables tie up working capital",
        "Warehouse receipt finance": "Storable commodity; stock can secure finance and avoid distress sales at harvest",
        "Input finance": "Input purchases drive production; finance can be paid directly to input suppliers",
        "Contract and purchase-order finance": "A large share of sales is contracted with offtakers",
        "Trade and pre-shipment finance": "Export sales with confirmed orders",
        "Insurance-linked loan": "High exposure to rainfall failure and no insurance cover",
    }
    out = s.copy()
    out["best_product"] = best
    out["best_score"] = s.max(axis=1)
    out["current_score"] = [s.loc[i, p] if p in s.columns else np.nan for i, p in zip(r.index, r["product"])]
    out["fit_gap"] = out["best_score"] - out["current_score"]
    out["reason"] = best.map(reason_map)
    out["mismatch"] = (out["fit_gap"] >= 25) & r["product"].isin(C.CONVENTIONAL)
    return out


CONSTRAINT_SOLUTIONS = pd.DataFrame([
    ("Lack of collateral", "Collateral-to-loan ratios of 93% to 112% for MSMEs (CBK, 2024)", "Cash-flow lending, movable asset registration, partial credit guarantees"),
    ("Seasonal cash flow", "Inflows concentrated in harvest months", "Seasonal working capital with harvest-aligned repayment"),
    ("Buyer payment delays", "Receivable days rising; offtaker concentration", "Invoice and receivables finance; assignment of proceeds"),
    ("Climate risk", "Rainfall and vegetation anomalies; 78% of farmers rain-fed (CBK, July 2026)", "Insurance-linked lending; climate-adjusted limits"),
    ("Input cost pressure", "Input cost index rising faster than farm-gate prices", "Input finance paid directly to suppliers"),
    ("Long production cycle", "Cash cycle above 120 days (sugarcane, beef, maize)", "Longer tenor and grace periods matched to cycle"),
    ("Price volatility", "High monthly price volatility and harvest-time price dips", "Warehouse receipt finance; structured trade finance"),
    ("Fragmented suppliers", "Many small producers selling through aggregators", "Aggregator and cooperative finance with on-lending"),
    ("Weak records", "Unregistered or first-time borrowers", "Alternative data scoring from M-Pesa and buyer payment records"),
    ("Export dependence", "High share of sales to export markets", "Pre-shipment and trade finance; FX hedging"),
], columns=["Constraint", "Evidence in the data", "Financing response"])


# --------------------------------------------------------------------------- #
# Segment scores
# --------------------------------------------------------------------------- #
def segment_table(data: dict, feats: pd.DataFrame, t: int, keys=("value_chain", "county")) -> pd.DataFrame:
    keys = list(keys)
    f = feats[feats["t"] == t]
    f6 = feats[feats["t"] == t - 6]
    f12 = feats[feats["t"] == t - 12]
    f3 = feats[feats["t"] == t - 3]

    def agg(d):
        bal = d["outstanding_kes"].sum()
        return pd.Series({
            "exposure_kes": bal, "borrowers": d["borrower_id"].nunique(), "institutions": d["lender"].nunique(),
            "npl": d.loc[d["dpd"] >= 90, "outstanding_kes"].sum() / bal if bal else 0,
            "par30": d.loc[d["dpd"] >= 30, "outstanding_kes"].sum() / bal if bal else 0,
            "late_share": ((d["dpd"] > 0) & (d["dpd"] < 30)).mean(),
            "util": d["utilization"].mean(), "inflow_stress": (d["inflow_yoy"] <= -0.2).mean(),
            "buyer_conc": d["buyer_concentration"].mean(), "insured": d["insured"].mean(), "mismatch": d["mismatch"].mean(),
            "women_share": d["women_owned"].mean(),
        })

    cur = f.groupby(keys).apply(agg, include_groups=False)
    for lbl, frame in (("6", f6), ("12", f12), ("3", f3)):
        prev = frame.groupby(keys).apply(agg, include_groups=False)
        cur[f"npl_{lbl}"] = prev["npl"].reindex(cur.index)
        cur[f"par30_{lbl}"] = prev["par30"].reindex(cur.index)
        cur[f"exposure_{lbl}"] = prev["exposure_kes"].reindex(cur.index)
        cur[f"borrowers_{lbl}"] = prev["borrowers"].reindex(cur.index)
    cur = cur.reset_index()

    # climate context
    months = sorted(data["climate"]["month"].unique())
    m_now = feats.loc[feats["t"] == t, "month"].iloc[0]
    idx = months.index(m_now)
    cl = data["climate"]
    recent = cl[cl["month"].isin(months[max(0, idx - 2): idx + 1])].groupby("county")["rain_anomaly"].mean()
    season = cl[cl["month"].isin(months[max(0, idx - 5): idx + 1])].groupby("county")["rain_anomaly"].mean()   # last rainy season
    vol = cl[cl["month"].isin(months[: idx + 1])].groupby("county")["rain_anomaly"].std()
    outlook = cl.groupby("county")["season_outlook"].first()
    ndvi = cl[cl["month"] == m_now].set_index("county")["ndvi_anomaly"]
    phase = cl[cl["month"] == m_now].set_index("county")["drought_phase"]
    mk = data["market"]
    mkm = sorted(mk["month"].unique())
    j = mkm.index(m_now)
    mkc = mk[mk["month"] == m_now].set_index("value_chain")
    mk3 = mk[mk["month"] == mkm[max(0, j - 3)]].set_index("value_chain")
    mk6 = mk[mk["month"] == mkm[max(0, j - 6)]].set_index("value_chain")
    mk12 = mk[mk["month"] == mkm[max(0, j - 12)]].set_index("value_chain")
    pvol = mk[mk["month"].isin(mkm[max(0, j - 11): j + 1])].sort_values("month").groupby("value_chain")["price_index"].apply(lambda s: np.log(s).diff().std())
    ap = data["applications"]
    ap_now = ap[ap["month"].isin(mkm[max(0, j - 2): j + 1])].groupby(keys).size()
    ap_ly = ap[ap["month"].isin(mkm[max(0, j - 14): max(0, j - 11)])].groupby(keys).size()

    if "county" in keys:
        cur["rain_3m"] = cur["county"].map(recent)
        cur["rain_season"] = cur["county"].map(season)
        cur["rain_vol"] = cur["county"].map(vol)
        cur["outlook"] = cur["county"].map(outlook)
        cur["ndvi"] = cur["county"].map(ndvi)
        cur["drought_phase"] = cur["county"].map(phase)
        cur["irrigation"] = cur["county"].map(lambda c: C.COUNTIES[c][3])
    else:
        w = feats[feats["t"] == t].groupby(keys + ["county"])["outstanding_kes"].sum().rename("w").reset_index()
        w["rain"] = w["county"].map(recent); w["season"] = w["county"].map(season); w["vol"] = w["county"].map(vol); w["out"] = w["county"].map(outlook)
        w["ndvi"] = w["county"].map(ndvi); w["irr"] = w["county"].map(lambda c: C.COUNTIES[c][3])
        wa = w.groupby(keys).apply(lambda d: pd.Series({k: np.average(d[c], weights=d["w"] + 1) for k, c in
                                                        (("rain_3m", "rain"), ("rain_season", "season"), ("rain_vol", "vol"), ("outlook", "out"), ("ndvi", "ndvi"), ("irrigation", "irr"))}), include_groups=False)
        cur = cur.merge(wa.reset_index(), on=keys, how="left")
        cur["drought_phase"] = np.select([cur["ndvi"] <= -25, cur["ndvi"] <= -12], ["Alarm", "Alert"], default="Normal")
    if "value_chain" in keys:
        vcp = cur["value_chain"].map(C.VALUE_CHAINS)
        cur["climate_sens"] = vcp.map(lambda p: p["climate"])
        cur["export"] = vcp.map(lambda p: p["export"])
        cur["price_vol"] = cur["value_chain"].map(pvol)
        cur["price_chg_3m"] = cur["value_chain"].map(mkc["price_index"] / mk3["price_index"] - 1)
        cur["input_chg_6m"] = cur["value_chain"].map(mkc["input_cost_index"] / mk6["input_cost_index"] - 1)
        cur["price_chg_6m"] = cur["value_chain"].map(mkc["price_index"] / mk6["price_index"] - 1)
        cur["production_chg_12m"] = cur["value_chain"].map(mkc["production_index"] / mk12["production_index"] - 1)
        cur["market_value_chg_12m"] = cur["value_chain"].map((mkc["price_index"] * mkc["production_index"]) / (mk12["price_index"] * mk12["production_index"]) - 1)
    else:
        sh = feats[feats["t"] == t].groupby(keys + ["value_chain"])["outstanding_kes"].sum().rename("w").reset_index()
        for col, series in (("climate_sens", pd.Series({k: v["climate"] for k, v in C.VALUE_CHAINS.items()})),
                            ("export", pd.Series({k: v["export"] for k, v in C.VALUE_CHAINS.items()})), ("price_vol", pvol),
                            ("price_chg_3m", mkc["price_index"] / mk3["price_index"] - 1), ("input_chg_6m", mkc["input_cost_index"] / mk6["input_cost_index"] - 1),
                            ("price_chg_6m", mkc["price_index"] / mk6["price_index"] - 1), ("production_chg_12m", mkc["production_index"] / mk12["production_index"] - 1),
                            ("market_value_chg_12m", (mkc["price_index"] * mkc["production_index"]) / (mk12["price_index"] * mk12["production_index"]) - 1)):
            sh[col] = sh["value_chain"].map(series)
        wa = sh.groupby(keys).apply(lambda d: pd.Series({c: np.average(d[c], weights=d["w"] + 1) for c in
                                                         ["climate_sens", "export", "price_vol", "price_chg_3m", "input_chg_6m", "price_chg_6m", "production_chg_12m", "market_value_chg_12m"]}),
                                    include_groups=False)
        cur = cur.merge(wa.reset_index(), on=keys, how="left")
    cur["demand_growth"] = [ap_now.get(tuple(r) if len(keys) > 1 else r[0], 0) / max(1, ap_ly.get(tuple(r) if len(keys) > 1 else r[0], 0)) - 1 for r in cur[keys].itertuples(index=False)]

    gap = financing_gap(data, feats, t)   # demand estimate held at the latest enterprise census; observed credit as at month t
    gg = gap.groupby(keys).agg(demand_kes=("demand_kes", "sum"), gap_kes=("gap_kes", "sum"), formal_credit_kes=("formal_credit_kes", "sum")).reset_index()
    cur = cur.merge(gg, on=keys, how="left")
    cur["gap_share"] = (cur["gap_kes"] / cur["demand_kes"]).fillna(0.5)

    # ---- component scores
    comp = {}
    comp["credit_risk"] = {
        "Portfolio quality": scale(cur["npl"], 0.02, 0.30),
        "Borrower behaviour": scale(cur["late_share"] + cur["par30"] - cur["npl"], 0.0, 0.25),
        "Leverage": scale(cur["util"], 0.45, 0.95),
        "Cash-flow stress": scale(cur["inflow_stress"], 0.05, 0.45),
        "Concentration": scale(cur["buyer_conc"], 0.35, 0.80),
        "Recent deterioration": scale((cur["npl"] - cur["npl_6"].fillna(cur["npl"])) * 100, -2, 8),
    }
    comp["climate_risk"] = {
        "Climate exposure": scale(cur["climate_sens"] * (1 - cur["irrigation"]), 0.1, 0.8),
        "Historical volatility": scale(cur["rain_vol"], 8, 30),
        "Current anomaly": scale(-cur["rain_3m"], 0, 40),
        "Seasonal outlook": scale(-cur["outlook"], -5, 30),
        "Adaptive capacity gap": scale(1 - (cur["irrigation"] + cur["insured"]), 0.5, 1.0),
    }
    comp["market_risk"] = {
        "Price volatility": scale(cur["price_vol"], 0.02, 0.08),
        "Price trend": scale(-cur["price_chg_3m"] * 100, -5, 15),
        "Input-cost pressure": scale((cur["input_chg_6m"] - cur["price_chg_6m"]) * 100, -5, 20),
        "Buyer concentration": scale(cur["buyer_conc"], 0.35, 0.80),
        "Export and FX exposure": scale(cur["export"], 0, 1),
    }
    growth = cur["exposure_kes"] / cur["exposure_12"] - 1
    bgrowth = cur["borrowers"] / cur["borrowers_12"] - 1
    comp["opportunity"] = {
        "Financing gap": scale(cur["gap_share"], 0.3, 0.9),
        "Credit growth": scale(growth.fillna(0) * 100, -10, 25),
        "Demand growth": scale(cur["demand_growth"] * 100, -10, 30),
        "Portfolio quality": 100 - scale(cur["npl"], 0.02, 0.30),
        "Market growth": scale(cur["market_value_chg_12m"].fillna(0) * 100, -10, 20),
        "Borrower growth": scale(bgrowth.fillna(0) * 100, -10, 25),
        "Product suitability": 100 - scale(cur["mismatch"], 0, 0.6),
    }
    for name, parts in comp.items():
        w = C.WEIGHTS[name]
        cur[name] = sum(w[k] * np.asarray(v) for k, v in parts.items()).round(0)
        for k, v in parts.items():
            cur[f"{name}::{k}"] = np.round(v, 0)
    # credibility weighting: small segments are pulled toward the average so that a handful of loans cannot top a ranking
    cred = np.minimum(1.0, cur["borrowers"] / C.CREDIBILITY_BORROWERS)
    cur["credibility"] = cred.round(2)
    for name in comp:
        raw = cur[name].copy()
        cur[name] = (raw.mean() + (raw - raw.mean()) * cred).round(0)
    cur["risk_index"] = sum(C.RISK_BLEND[k] * cur[k] for k in C.RISK_BLEND).round(0)
    q = C.QUADRANT_CUTS
    cur["quadrant"] = np.select([(cur["opportunity"] >= q["opportunity"]) & (cur["risk_index"] < q["grow_risk"]), (cur["opportunity"] >= q["opportunity"]), (cur["risk_index"] < q["selective_risk"])],
                                ["Grow", "Grow with structure", "Selective"], default="Tighten and monitor")
    # early warning signals moving together
    sig = pd.DataFrame({
        "Commodity price falling": cur["price_chg_3m"] <= -0.05,
        "Rainfall below normal": (cur["rain_3m"] <= -15) | (cur["rain_season"] <= -12),
        "Vegetation stress": cur["ndvi"] <= -10,
        "Margin squeeze": (cur["input_chg_6m"] - cur["price_chg_6m"]) >= 0.06,
        "Sales below last season": cur["inflow_stress"] >= 0.25,
        "Arrears rising": (cur["par30"] - cur["par30_3"].fillna(cur["par30"])) >= 0.015,
        "Credit quality worsening": (cur["npl"] - cur["npl_6"].fillna(cur["npl"])) >= 0.02,
    })
    cur["signals"] = sig.sum(axis=1)
    cur["signal_list"] = sig.apply(lambda r: ", ".join(k for k, v in r.items() if v), axis=1)
    cur["ew_status"] = np.select([cur["signals"] >= C.EW_THRESHOLDS["Red"], cur["signals"] >= C.EW_THRESHOLDS["Amber"]], ["Red", "Amber"], default="Green")
    cur["confidence"] = np.select([cur["borrowers"] >= 30, cur["borrowers"] >= 10], ["High", "Medium"], default="Low")
    cur["suppressed"] = (cur["institutions"] < C.AGGREGATION_MIN_INSTITUTIONS) | (cur["borrowers"] < C.AGGREGATION_MIN_BORROWERS)
    return cur


def drivers(row: pd.Series, score: str, n: int = 3) -> list[tuple[str, float]]:
    w = C.WEIGHTS[score]
    contrib = {k: w[k] * row[f"{score}::{k}"] for k in w}
    return sorted(contrib.items(), key=lambda kv: -kv[1])[:n]


# --------------------------------------------------------------------------- #
# Scenario lab
# --------------------------------------------------------------------------- #
LGD = {"Title deed": 0.35, "Chattels and equipment": 0.50, "Receivables": 0.40, "Warehouse receipt": 0.30, "Group or cooperative guarantee": 0.55, "Unsecured": 0.80}


def scenario(latest: pd.DataFrame, shock: dict) -> pd.DataFrame:
    d = latest[latest["dpd"] < 90].copy()
    vc = d["value_chain"].map(C.VALUE_CHAINS)
    tr = d["actor"].map(C.ACTOR_TRANSMISSION)
    clim = vc.map(lambda p: p["climate"])
    export = vc.map(lambda p: p["export"])
    prod = tr.map(lambda x: x["production"])
    inp = tr.map(lambda x: x["input_share"])
    fuel = tr.map(lambda x: x["fuel_share"])
    intr = tr.map(lambda x: x["interest_share"])
    irr = d["county"].map(lambda c: C.COUNTIES[c][3])
    rain = shock["rain"] / 100 * np.where(d["asal"], 1.3, 1.0)
    volume = np.minimum(rain, 0) * clim * prod * (1 - irr) * np.where(d["insured"], 0.5, 1.0) + np.minimum(np.maximum(rain, 0), 0.20) * 0.2 * clim * prod
    # rainfall well above normal: waterlogging, flood damage and post-harvest losses outweigh the yield gain
    volume = volume - np.maximum(rain - 0.20, 0) * 1.2 * clim * prod * np.where(d["insured"], 0.5, 1.0)
    # farm-gate price moves hit producers fully; traders and processors pass part of the move back through their raw-material costs
    price = shock["price"] / 100 * (0.3 + 0.7 * prod)
    passthrough = shock["price"] / 100 * inp * (1 - prod) * 0.5
    revenue = volume + price + export * shock["fx"] / 100 * 0.5
    costs = inp * (shock["inputs"] / 100 + 0.3 * shock["fx"] / 100) + fuel * shock["fuel"] / 100 + intr * shock["cbr"] / (d["interest_rate"] * 100) + passthrough
    margin = 0.30
    cf_change = ((1 + revenue) - (1 - margin) * (1 + costs)) / margin - 1
    d["cash_flow_change"] = np.clip(cf_change, -1.0, 1.0)
    base_pd12 = np.clip(1 - (1 - d["pd_3m"].fillna(0.5)) ** 4, 0.005, 0.95)
    logit = np.log(base_pd12 / (1 - base_pd12)) - C.CASHFLOW_TO_LOGODDS * np.minimum(d["cash_flow_change"], 0)
    d["pd12_base"] = base_pd12
    d["pd12_stress"] = 1 / (1 + np.exp(-logit))
    d["lgd"] = d["collateral"].map(LGD)
    d["el_base"] = d["pd12_base"] * d["lgd"] * d["outstanding_kes"]
    d["el_stress"] = d["pd12_stress"] * d["lgd"] * d["outstanding_kes"]
    d["affected"] = d["cash_flow_change"] <= -0.30
    return d


# --------------------------------------------------------------------------- #
# Benchmarking and inclusion
# --------------------------------------------------------------------------- #
def benchmark(latest: pd.DataFrame, feats: pd.DataFrame, lender: str) -> pd.DataFrame:
    T = int(feats["t"].max())
    ly = feats[feats["t"] == T - 12]

    def metrics(d, dly):
        bal = d["outstanding_kes"].sum()
        return {
            "Agricultural credit growth, 12 months": bal / max(1, dly["outstanding_kes"].sum()) - 1,
            "NPL ratio": d.loc[d["dpd"] >= 90, "outstanding_kes"].sum() / bal,
            "Average loan size (KES)": d["loan_amount_kes"].mean(),
            "Women-owned borrowers": d["women_owned"].mean(),
            "Youth-owned borrowers": d["youth_owned"].mean(),
            "First-time borrowers": d["first_time"].mean(),
            "Micro and small borrowers": d["size"].isin(["Micro", "Small"]).mean(),
            "Structured products (not term loan or overdraft)": (~d["product"].isin(C.CONVENTIONAL)).mean(),
            "Exposure in ASAL counties": d.loc[d["asal"], "outstanding_kes"].sum() / bal,
            "Insured borrowers": d["insured"].mean(),
            "Average interest rate": d["interest_rate"].mean(),
        }
    mine = metrics(latest[latest["lender"] == lender], ly[ly["lender"] == lender])
    mkt = metrics(latest[latest["lender"] != lender], ly[ly["lender"] != lender])
    return pd.DataFrame({"Metric": list(mine), "Your institution": list(mine.values()), "Market (other institutions)": list(mkt.values())})


def inclusion(latest: pd.DataFrame, apps: pd.DataFrame, months: list[str]) -> dict:
    a = apps[apps["month"].isin(months)]
    out = {}
    for label, col in (("Women-owned", "women_owned"), ("Youth-owned", "youth_owned"), ("First-time", "first_time")):
        grp = latest[latest[col]]
        rest = latest[~latest[col]]
        ag, ar = a[a[col]], a[~a[col]]
        out[label] = {
            "Share of borrowers": latest[col].mean(),
            "Share of credit": grp["outstanding_kes"].sum() / latest["outstanding_kes"].sum(),
            "Approval rate": ag["approved"].mean(), "Approval rate (others)": ar["approved"].mean(),
            "Average loan (KES)": grp["loan_amount_kes"].mean(), "Average loan (others)": rest["loan_amount_kes"].mean(),
            "NPL ratio": grp.loc[grp["dpd"] >= 90, "outstanding_kes"].sum() / max(1, grp["outstanding_kes"].sum()),
            "NPL ratio (others)": rest.loc[rest["dpd"] >= 90, "outstanding_kes"].sum() / max(1, rest["outstanding_kes"].sum()),
            "Average rate": grp["interest_rate"].mean(), "Average rate (others)": rest["interest_rate"].mean(),
        }
    return out


# --------------------------------------------------------------------------- #
# What changed
# --------------------------------------------------------------------------- #
def what_changed(chain_now: pd.DataFrame, chain_prev: pd.DataFrame, market: pd.DataFrame, climate: pd.DataFrame, month: str) -> list[dict]:
    a = chain_now.set_index("value_chain")
    b = chain_prev.set_index("value_chain")
    items = []
    d_risk = (a["risk_index"] - b["risk_index"]).dropna()
    d_opp = (a["opportunity"] - b["opportunity"]).dropna()
    for vc, v in d_risk.sort_values(ascending=False).head(2).items():
        if v >= 3:
            top = drivers(a.loc[vc], "credit_risk", 1)[0][0] if a.loc[vc]["credit_risk"] >= a.loc[vc]["climate_risk"] else drivers(a.loc[vc], "climate_risk", 1)[0][0]
            items.append(dict(tone="Red", title=f"{vc}: risk up {v:.0f} points in 3 months", detail=f"Main driver: {top.lower()}. Exposure {a.loc[vc]['exposure_kes'] / 1e6:,.0f}M."))
    for vc, v in d_opp.sort_values(ascending=False).head(2).items():
        if v >= 3:
            items.append(dict(tone="Green", title=f"{vc}: opportunity up {v:.0f} points", detail=f"Financing gap {a.loc[vc]['gap_kes'] / 1e9:,.1f}bn; NPL {a.loc[vc]['npl']:.1%}."))
    months = sorted(market["month"].unique())
    i = months.index(month)
    m0 = market[market["month"] == months[i - 3]].set_index("value_chain")
    m1 = market[market["month"] == month].set_index("value_chain")
    pc = (m1["price_index"] / m0["price_index"] - 1).sort_values()
    if pc.iloc[0] <= -0.05:
        items.append(dict(tone="Amber", title=f"{pc.index[0]} prices down {abs(pc.iloc[0]):.0%} in 3 months", detail="Re-test borrower cash flows at current prices."))
    if pc.iloc[-1] >= 0.05:
        items.append(dict(tone="Green", title=f"{pc.index[-1]} prices up {pc.iloc[-1]:.0%} in 3 months", detail="Margins improving for producers and aggregators."))
    ic = (m1["input_cost_index"] / m0["input_cost_index"] - 1).sort_values()
    if ic.iloc[-1] >= 0.05:
        items.append(dict(tone="Amber", title=f"Input costs up {ic.iloc[-1]:.0%} for {ic.index[-1].lower()}", detail="Margin squeeze where farm-gate prices lag."))
    cl = climate[climate["month"] == month]
    alarm = cl[cl["drought_phase"] == "Alarm"]["county"].tolist()
    if alarm:
        items.append(dict(tone="Red", title=f"Drought alarm in {len(alarm)} counties", detail=", ".join(alarm)))
    return items[:6]
