"""Borrower-level early warning for agri SMEs: seasonally adjusted features, trigger rules, model and status.

Agricultural cash flows are seasonal, so inflow deterioration is measured against the same months a year
earlier rather than the previous quarter. Borrower signals are combined with the climate and market
conditions of the borrower's county and value chain.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config as C

SEV_POINTS = {"Critical": 40, "High": 25, "Medium": 12, "Low": 6}


def _roll(g, col, w, fn, mp=1):
    return getattr(g[col].rolling(w, min_periods=mp), fn)().reset_index(level=0, drop=True)


def build_features(data: dict) -> pd.DataFrame:
    b, p = data["borrowers"], data["panel"]
    df = p.merge(b, on="borrower_id", how="left").sort_values(["borrower_id", "t"]).reset_index(drop=True)
    g = df.groupby("borrower_id", sort=False)
    df["max_dpd_6m"] = _roll(g, "dpd", 6, "max")
    df["late"] = ((df["dpd"] > 0) & (df["dpd"] < 30)).astype(int)
    df["late_6m"] = _roll(g, "late", 6, "sum")
    df["inflow_3m"] = _roll(g, "inflow_kes", 3, "mean")
    df["inflow_3m_ly"] = g["inflow_3m"].shift(12)
    df["inflow_yoy"] = df["inflow_3m"] / df["inflow_3m_ly"] - 1          # seasonally adjusted
    df["util_chg_3m"] = (df["utilization"] - g["utilization"].shift(3)) * 100
    df["recv_chg_3m"] = df["receivable_days"] - g["receivable_days"].shift(3)
    # context: climate and market
    cl = data["climate"].copy().sort_values(["county", "month"])
    cl["rain_3m"] = cl.groupby("county")["rain_anomaly"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    df = df.merge(cl[["month", "county", "rain_3m", "ndvi_anomaly", "drought_phase"]], on=["month", "county"], how="left")
    mk = data["market"].copy().sort_values(["value_chain", "month"])
    gm = mk.groupby("value_chain")
    mk["price_chg_3m"] = mk["price_index"] / gm["price_index"].shift(3) - 1
    mk["input_chg_6m"] = mk["input_cost_index"] / gm["input_cost_index"].shift(6) - 1
    mk["margin_chg_6m"] = mk["margin_index"] / gm["margin_index"].shift(6) - 1
    df = df.merge(mk[["month", "value_chain", "price_chg_3m", "input_chg_6m", "margin_chg_6m"]], on=["month", "value_chain"], how="left")
    df["mismatch"] = (df["product"].isin(C.CONVENTIONAL) & df["actor"].isin(["Producer", "Aggregator", "Cooperative"]) & (df["cash_cycle_days"] >= 110)).astype(int)
    df = df.sort_values(["borrower_id", "t"]).reset_index(drop=True)
    g = df.groupby("borrower_id", sort=False)
    fut = pd.concat([g["dpd"].shift(-k) for k in (1, 2, 3)], axis=1)
    fut_r = pd.concat([g["restructured"].shift(-k) for k in (1, 2, 3)], axis=1)
    obs = fut.notna().all(axis=1)
    event = (fut.max(axis=1) >= 30) | (fut_r.max(axis=1).astype(float) > df["restructured"].astype(float))
    df["target_3m"] = np.where(obs & (df["dpd"] < 30), event.astype(float), np.nan)
    first30 = df[(df["dpd"] >= 30) & (g["dpd"].shift(1).fillna(0) < 30)].groupby("borrower_id")["t"].min()
    df["first_30dpd_t"] = df["borrower_id"].map(first30)
    return df.replace([np.inf, -np.inf], np.nan)


RULES = [
    ("A01", "Repayment", "Arrears building up", "1 to 29 days past due and rising", "Medium", "Call the borrower and confirm the reason and expected harvest or sales date.",
     lambda d: (d["dpd"] > 0) & (d["dpd"] < 30)),
    ("A02", "Repayment", "30+ days past due", "DPD at least 30", "High", "Agree a remedial plan aligned to the next harvest or sales cycle.",
     lambda d: (d["dpd"] >= 30) & (d["dpd"] < 90)),
    ("A03", "Cash flow", "Sales below last season", "Inflows 25% or more below the same months last year", "High", "Visit the business; check volumes, prices and buyer payments.",
     lambda d: d["inflow_yoy"].fillna(0) <= -0.25),
    ("A04", "Cash flow", "Buyer payments slowing", "Receivable days up 20 or more in 3 months", "Medium", "Confirm offtaker payment status; consider receivables finance.",
     lambda d: d["recv_chg_3m"].fillna(0) >= 20),
    ("A05", "Exposure", "Facility near limit", "Utilisation above 90%", "Medium", "Review whether the limit matches the seasonal working-capital need.",
     lambda d: d["utilization"] >= 0.9),
    ("A06", "Climate", "Rainfall failure in county", "3-month rainfall anomaly below -25%", "High", "Assess crop or pasture condition; check insurance; consider rescheduling to the next harvest.",
     lambda d: d["rain_3m"].fillna(0) <= -25),
    ("A07", "Climate", "Drought alarm, uninsured", "NDMA-type drought alarm and no insurance", "Critical", "Escalate to agribusiness credit; plan restructuring before arrears build.",
     lambda d: (d["drought_phase"] == "Alarm") & (~d["insured"])),
    ("A08", "Market", "Commodity price falling", "Value-chain price down 10% or more in 3 months", "Medium", "Re-run the cash-flow projection at current prices.",
     lambda d: d["price_chg_3m"].fillna(0) <= -0.10),
    ("A09", "Market", "Margin squeeze", "Margin index down 12% or more in 6 months", "High", "Check input-cost pass-through; consider input finance or buyer-linked pricing.",
     lambda d: d["margin_chg_6m"].fillna(0) <= -0.12),
    ("A10", "Structure", "Product does not match cash cycle", "Term loan or overdraft on a long seasonal cycle", "Medium", "Restructure to seasonal repayments or a structured product at renewal.",
     lambda d: d["mismatch"] == 1),
    ("A11", "Concentration", "Dependent on one buyer", "Largest buyer above 70% of sales, no contract", "Low", "Obtain buyer contract or assignment of proceeds.",
     lambda d: (d["buyer_concentration"] >= 0.7) & (d["contracted_sales_share"] < 0.3)),
]
RULE_META = pd.DataFrame([dict(Rule=r[0], Family=r[1], Trigger=r[2], Definition=r[3], Severity=r[4], Points=SEV_POINTS[r[4]], Action=r[5]) for r in RULES])

FEATURES = {"dpd": 0, "max_dpd_6m": 0, "late_6m": 0, "inflow_yoy": 0, "util_chg_3m": 0, "recv_chg_3m": 0, "utilization": 0.6,
            "rain_3m": 0, "ndvi_anomaly": 0, "price_chg_3m": 0, "margin_chg_6m": 0, "mismatch": 0, "buyer_concentration": 0.5,
            "contracted_sales_share": 0.3, "insured": 0, "first_time": 0, "registered": 1}
LABELS = {"dpd": "Days past due", "max_dpd_6m": "Worst DPD, 6 months", "late_6m": "Late months, 6m", "inflow_yoy": "Sales vs last season",
          "util_chg_3m": "Utilisation change", "recv_chg_3m": "Receivable days change", "utilization": "Utilisation", "rain_3m": "Rainfall anomaly",
          "ndvi_anomaly": "Vegetation anomaly", "price_chg_3m": "Commodity price change", "margin_chg_6m": "Margin change", "mismatch": "Product-cycle mismatch",
          "buyer_concentration": "Buyer concentration", "contracted_sales_share": "Contracted sales", "insured": "Insured", "first_time": "First-time borrower",
          "registered": "Formally registered"}
TRAIN_END, TEST = 11, (12, 20)


def design(df):
    X = pd.DataFrame({k: df[k].astype(float).fillna(v) for k, v in FEATURES.items()})
    return X.clip(X.quantile(0.005), X.quantile(0.995), axis=1)


def run(data: dict):
    f = build_features(data)
    pts = np.zeros(len(f))
    crit = np.zeros(len(f), bool)
    fired = []
    for rid, fam, name, _, sev, action, cond in RULES:
        m = cond(f).fillna(False).to_numpy(bool)
        pts += m * SEV_POINTS[sev]
        crit |= m & (sev == "Critical")
        if m.any():
            fired.append(pd.DataFrame({"borrower_id": f.loc[m, "borrower_id"].to_numpy(), "t": f.loc[m, "t"].to_numpy(), "rule": rid}))
    fired = pd.concat(fired, ignore_index=True).merge(RULE_META[["Rule", "Family", "Trigger", "Severity", "Action"]], left_on="rule", right_on="Rule").drop(columns="Rule")
    f["rule_points"] = np.minimum(pts, 100)
    lab = f[f["target_3m"].notna()]
    tr = lab[lab["t"] <= TRAIN_END]
    model = make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000)).fit(design(tr), tr["target_3m"].astype(int))
    f["pd_3m"] = model.predict_proba(design(f))[:, 1]
    f.loc[f["dpd"] >= 30, "pd_3m"] = np.nan
    mp = np.where(f["dpd"] >= 30, 100, np.minimum(100, 100 * np.sqrt(f["pd_3m"].fillna(1))))
    f["score"] = (0.65 * mp + 0.35 * f["rule_points"]).round(1)
    f["status"] = np.select([f["dpd"] >= 90, (f["score"] >= C.BORROWER_STATUS["Red"]) | crit, f["score"] >= C.BORROWER_STATUS["Amber"]], ["NPL", "Red", "Amber"], default="Green")
    f["velocity_3m"] = f["score"] - f.groupby("borrower_id")["score"].shift(3)

    test = f[f["target_3m"].notna() & f["t"].between(*TEST)]
    y = test["target_3m"].astype(int)
    alert = test["status"].isin(["Amber", "Red"])
    ev = f.loc[f["t"] == f["first_30dpd_t"], ["borrower_id", "t"]]
    ev = ev[ev["t"].between(TEST[0], f["t"].max())]
    hist = f[["borrower_id", "t", "status"]].merge(ev.rename(columns={"t": "event_t"}), on="borrower_id")
    win = hist[(hist["t"] < hist["event_t"]) & (hist["t"] >= hist["event_t"] - 6) & hist["status"].isin(["Amber", "Red"])]
    first = win.groupby("borrower_id").agg(first=("t", "min"), event=("event_t", "first"))
    n_ev = max(1, ev["borrower_id"].nunique())
    coef = pd.DataFrame({"feature": list(FEATURES), "coefficient": model[-1].coef_[0]})
    coef["label"] = coef["feature"].map(LABELS)
    perf = dict(auc=float(roc_auc_score(y, test["pd_3m"])), precision=float((alert & (y == 1)).sum() / max(1, alert.sum())), alert_rate=float(alert.mean()),
                recall=float((alert & (y == 1)).sum() / max(1, (y == 1).sum())), base_rate=float(y.mean()),
                detected_before_30=len(first) / n_ev, share_90d=float(((first["event"] - first["first"]) >= 3).sum() / n_ev), events=int(n_ev),
                coefficients=coef.sort_values("coefficient", key=np.abs, ascending=False))
    return f, fired, model, perf


def contributions(model, rows: pd.DataFrame) -> pd.DataFrame:
    X = design(rows)
    sc, lr = model[0], model[-1]
    return pd.DataFrame((X.to_numpy() - sc.mean_) / sc.scale_ * lr.coef_[0], columns=X.columns, index=rows.index)
