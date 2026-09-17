import html

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import borrower_ews as E
from aaip import config as C
from views import common as U

b = U.bundle()
feats, fired, perf, T = b["feats"], b["fired"], b["perf"], b["T"]
U.page_header("Risk and early warning", "Two layers: segment signals that move together across price, climate and repayment, and a borrower watchlist with the trigger, driver and action.", "Risk")
U.decision("Tighten, restructure or engage early, before arrears reach 30 days.", "CRO, Credit Manager, Relationship Manager")

SIGNAL_ACTION = {
    "Commodity price falling": "Re-run cash flows at current prices; defer limit increases.",
    "Rainfall below normal": "Check crop and pasture condition; prepare harvest-aligned rescheduling.",
    "Vegetation stress": "Prioritise field visits in affected counties; confirm insurance claims.",
    "Margin squeeze": "Offer input finance or buyer-linked pricing; review limits.",
    "Sales below last season": "Call borrowers with falling inflows; verify buyer payments.",
    "Arrears rising": "Start early collections contact at 1 to 29 days past due.",
    "Credit quality worsening": "Pause new lending pending portfolio review.",
}

tab1, tab2, tab3 = st.tabs(["Segment early warning", "Borrower watchlist", "How the warning works"])
with tab1:
    cell = U.visible_segments(U.filt(b["seg"]["cell"], cols=("value_chain", "county")))
    lt = b["latest"]
    counts = cell["ew_status"].value_counts()
    U.kpi_cards([
        dict(label="Red segments", value=int(counts.get("Red", 0)), note=f"{U.kes(cell.loc[cell['ew_status'] == 'Red', 'exposure_kes'].sum())} exposure", tone="bad", accent=C.RAG["Red"]),
        dict(label="Amber segments", value=int(counts.get("Amber", 0)), note=f"{U.kes(cell.loc[cell['ew_status'] == 'Amber', 'exposure_kes'].sum())} exposure", tone="warn", accent=C.RAG["Amber"]),
        dict(label="Green segments", value=int(counts.get("Green", 0)), accent=C.RAG["Green"]),
        dict(label="Rule", value=f"Amber {C.EW_THRESHOLDS['Amber']}+ · Red {C.EW_THRESHOLDS['Red']}+", note="Adverse signals moving together", accent=C.SKY),
    ])
    st.write("")
    w = cell[cell["ew_status"] != "Green"].sort_values(["signals", "exposure_kes"], ascending=False).copy()
    ids = lt.groupby(["value_chain", "county"])["status"].apply(lambda s: s.isin(["Amber", "Red"]).sum())
    w["affected"] = [ids.get((v, c), 0) for v, c in zip(w["value_chain"], w["county"])]
    w["driver"] = w.apply(lambda r: max(("credit risk", r["credit_risk"]), ("climate risk", r["climate_risk"]), ("market risk", r["market_risk"]), key=lambda x: x[1])[0], axis=1)
    w["action"] = w["signal_list"].map(lambda s: SIGNAL_ACTION.get(s.split(", ")[0], "") if s else "")
    t = w[["ew_status", "value_chain", "county", "signal_list", "driver", "exposure_kes", "affected", "action"]]
    t.columns = ["Status", "Value chain", "County", "Signals", "Main driver", "Exposure", "Borrowers on watch", "Suggested action"]
    st.dataframe(U.tint_cols(t.style.format({"Exposure": lambda v: U.kes(v)}), ["Status"]), hide_index=True, use_container_width=True, height=380)

    sig = pd.Series({k: cell["signal_list"].str.contains(k).sum() for k in SIGNAL_ACTION}).sort_values()
    c1, c2 = st.columns(2)
    with c1:
        f = px.bar(x=sig.values, y=sig.index, orientation="h", labels={"x": "Segments with signal", "y": ""}, color_discrete_sequence=[C.HARVEST])
        U.show(U.fig(f, 330, "Which signals are firing"))
    with c2:
        tr = U.filt(feats).groupby(["month", "status"])["outstanding_kes"].sum().unstack().fillna(0)
        tr = tr.div(tr.sum(axis=1), axis=0) * 100
        f = go.Figure()
        for s in ["Green", "Amber", "Red", "NPL"]:
            if s in tr:
                f.add_scatter(x=tr.index, y=tr[s], name=s, stackgroup="one", line=dict(width=0.5, color=C.RAG[s]))
        f.update_layout(yaxis=dict(range=[0, 100], title="% of exposure"))
        U.show(U.fig(f, 330, "Borrower status mix over time"))

with tab2:
    lt = U.filt(b["latest"])
    mine = st.toggle("Only my institution", True, key="risk_mine")
    if mine:
        lt = lt[lt["lender"] == st.session_state["institution"]]
    watch = lt[lt["status"].isin(["Amber", "Red"])].sort_values("score", ascending=False)
    fr = fired[fired["t"] == T]
    top = fr.merge(E.RULE_META[["Rule", "Points"]], left_on="rule", right_on="Rule").sort_values("Points", ascending=False).drop_duplicates("borrower_id").set_index("borrower_id")
    watch = watch.assign(trigger=watch["borrower_id"].map(top["Trigger"]).fillna("Model: rising default probability"),
                         action=watch["borrower_id"].map(top["Action"]).fillna("Review cash flow and next harvest or sales date."),
                         n_trig=watch["borrower_id"].map(fr.groupby("borrower_id").size()).fillna(0).astype(int))
    U.kpi_cards([
        dict(label="Red", value=int((watch["status"] == "Red").sum()), note=U.kes(watch.loc[watch["status"] == "Red", "outstanding_kes"].sum()), tone="bad", accent=C.RAG["Red"]),
        dict(label="Amber", value=int((watch["status"] == "Amber").sum()), note=U.kes(watch.loc[watch["status"] == "Amber", "outstanding_kes"].sum()), tone="warn", accent=C.RAG["Amber"]),
        dict(label="Rising fast", value=int((watch["velocity_3m"] >= 15).sum()), note="Score up 15+ points in 3 months", accent=C.HARVEST),
        dict(label="Climate-triggered", value=int(watch["borrower_id"].isin(fr[fr["Family"] == "Climate"]["borrower_id"]).sum()), note="Rainfall or drought triggers", accent=C.SKY),
    ])
    st.write("")
    t = watch[["status", "business", "value_chain", "county", "score", "pd_3m", "velocity_3m", "trigger", "n_trig", "outstanding_kes", "action"]]
    t.columns = ["Status", "Business", "Value chain", "County", "Score", "3-month PD", "Change 3m", "Top trigger", "Triggers", "Outstanding", "Action"]
    ev = st.dataframe(U.tint_cols(t.style.format({"Score": "{:.0f}", "3-month PD": "{:.1%}", "Change 3m": "{:+.0f}", "Outstanding": lambda v: U.kes(v)}), ["Status"]),
                      hide_index=True, use_container_width=True, height=440, on_select="rerun", selection_mode="single-row", key="risk_watch")
    rows = ev.selection.rows if ev and ev.selection else []
    if rows:
        st.session_state["borrower_id"] = watch.iloc[rows[0]]["borrower_id"]
        st.page_link(st.session_state["pages"]["borrower"], label=f"Open {watch.iloc[rows[0]]['business']} in Borrower intelligence", icon=":material/arrow_forward:")
    else:
        st.caption("Select a row to open the borrower profile.")

with tab3:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Out-of-time AUC", f"{perf['auc']:.2f}")
    c2.metric("Defaults flagged before 30 DPD", f"{perf['detected_before_30']:.0%}")
    c3.metric("Flagged 90+ days ahead", f"{perf['share_90d']:.0%}")
    c4.metric("Alert rate / precision", f"{perf['alert_rate']:.0%} / {perf['precision']:.0%}")
    st.markdown(f"""
<div class='explain'>
<p><b>Borrower score</b> = 0.65 × model points + 0.35 × trigger points. Model points = 100 × √(3-month probability of 30+ DPD or restructure), from a logistic regression on
{len(E.FEATURES)} borrower, climate and market features trained on months 1 to {E.TRAIN_END} and tested on months {E.TEST[0]} to {E.TEST[1]}.
Status: Amber from {C.BORROWER_STATUS['Amber']}, Red from {C.BORROWER_STATUS['Red']} or any critical trigger, NPL at 90+ DPD.</p>
<p><b>Segment status</b> counts seven adverse signals for each value chain and county: price falling 5%+ in 3 months, rainfall 15% below normal (or last season 12% below),
vegetation 10% below normal, input costs outpacing prices by 6 pp, a quarter of borrowers with sales 20% below last season, PAR30 up 1.5 pp in 3 months, NPL up 2 pp in 6 months.</p>
<p>Sales are compared with the same months last year, not the previous quarter, so the harvest cycle does not trigger false alarms.</p></div>""", unsafe_allow_html=True)
    st.markdown("#### Trigger rules")
    st.dataframe(U.tint_cols(E.RULE_META.style, ["Severity"]), hide_index=True, use_container_width=True)
