import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from aaip import borrower_ews as E
from aaip import config as C
from views import common as U

b = U.bundle()
feats, fired, model, T = b["feats"], b["fired"], b["model"], b["T"]
U.page_header("Borrower intelligence", "Agri SME 360: repayment, cash flow against last season, climate and market conditions, product fit and the actions that follow.", "Risk")
U.decision("Decide whether to call, visit, restructure to the harvest cycle, or grow the relationship.", "Relationship Manager, Credit Manager")

inst = st.session_state["institution"]
lt = U.filt(b["latest"])
mine = lt[lt["lender"] == inst].sort_values("score", ascending=False)
if mine.empty:
    st.info(f"{inst} has no borrowers matching the current filters.")
    st.stop()
opts = mine["borrower_id"].tolist()
default = st.session_state.get("borrower_id")
label = {r.borrower_id: f"{r.business} · {r.value_chain} · {r.actor} · {r.county} · {r.status} {r.score:.0f}" for r in mine.itertuples()}
if default in opts:
    st.session_state["bw_select"] = default
elif st.session_state.get("bw_select") not in opts:
    st.session_state["bw_select"] = opts[0]
bid = st.selectbox(f"Borrower ({inst}, sorted by warning score)", opts, format_func=label.get, key="bw_select")
st.session_state["borrower_id"] = bid
r = mine.set_index("borrower_id").loc[bid]
hist = feats[feats["borrower_id"] == bid].sort_values("t")

st.markdown(f"<div class='headcard'><div class='name'>{html.escape(r['business'])} {U.pill(r['status'])}</div>"
            f"<div class='meta'>{html.escape(r['value_chain'])} ({html.escape(r['l2'])}) · {html.escape(r['actor'])} · {html.escape(r['county'])}{' (ASAL)' if r['asal'] else ''} · {html.escape(r['size'])} · "
            f"{html.escape(r['product'])}, {r['tenor_months']:.0f} months at {r['interest_rate']:.1%} · Collateral: {html.escape(r['collateral'])}</div></div>", unsafe_allow_html=True)
U.kpi_cards([
    dict(label="Warning score", value=f"{r['score']:.0f}", note=f"{r['velocity_3m']:+.0f} in 3 months" if pd.notna(r["velocity_3m"]) else "", tone="bad" if (r["velocity_3m"] or 0) > 10 else None),
    dict(label="3-month default probability", value=U.pct(r["pd_3m"]) if pd.notna(r["pd_3m"]) else "In arrears"),
    dict(label="Outstanding", value=U.kes(r["outstanding_kes"]), note=f"Utilisation {r['utilization']:.0%}"),
    dict(label="Days past due", value=f"{r['dpd']:.0f}", note=f"Worst in 6 months {r['max_dpd_6m']:.0f}"),
    dict(label="Sales vs last season", value=U.pct(r["inflow_yoy"], 0, True), tone="bad" if (r["inflow_yoy"] or 0) < -0.2 else None),
])
st.write("")

c1, c2 = st.columns([1.2, 1])
with c1:
    st.markdown("#### Why the model scores this borrower")
    con = E.contributions(model, mine.set_index("borrower_id").loc[[bid]]).iloc[0].rename(E.LABELS).sort_values(key=np.abs, ascending=False).head(8).sort_values()
    f = go.Figure(go.Bar(x=con.values, y=con.index, orientation="h", marker_color=[C.RAG["Red"] if v > 0 else C.GREEN for v in con.values]))
    f.update_layout(xaxis_title="Contribution to log-odds (red raises risk)")
    U.show(U.fig(f, 330))
with c2:
    st.markdown("#### Triggers fired this month")
    fr = fired[(fired["borrower_id"] == bid) & (fired["t"] == T)]
    if fr.empty:
        st.success("No triggers this month.")
    for x in fr.itertuples():
        U.tile(x.Trigger, x.Action, {"Critical": "Red", "High": "Red", "Medium": "Amber", "Low": "Green"}[x.Severity], x.Severity)

c1, c2 = st.columns(2)
with c1:
    f = go.Figure()
    f.add_bar(x=hist["month"], y=hist["inflow_kes"] / 1e3, name="Inflows (KES K)", marker_color="#CFE0D5")
    f.add_scatter(x=hist["month"], y=hist["dpd"], name="Days past due", yaxis="y2", line=dict(color=C.RAG["Red"], width=3))
    f.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, rangemode="tozero"))
    U.show(U.fig(f, 320, "Cash inflows and arrears"))
with c2:
    f = go.Figure()
    f.add_scatter(x=hist["month"], y=hist["score"], name="Warning score", line=dict(color=C.FOREST, width=3))
    f.add_bar(x=hist["month"], y=hist["rain_3m"], name="County rainfall anomaly 3m %", marker_color=C.SKY, opacity=0.45, yaxis="y2")
    f.add_hline(y=C.BORROWER_STATUS["Amber"], line_dash="dot", line_color=C.RAG["Amber"])
    f.add_hline(y=C.BORROWER_STATUS["Red"], line_dash="dot", line_color=C.RAG["Red"])
    f.update_layout(yaxis=dict(range=[0, 100]), yaxis2=dict(overlaying="y", side="right", showgrid=False, range=[-60, 60]))
    U.show(U.fig(f, 320, "Warning score and rainfall"))

st.markdown("#### Product fit and structure")
fit = b["fit"].loc[mine.index[mine["borrower_id"] == bid][0]]
c1, c2 = st.columns([1, 1.2])
with c1:
    sc = fit[C.PRODUCTS].astype(float).sort_values()
    f = go.Figure(go.Bar(x=sc.values, y=sc.index, orientation="h", text=[f"{v:.0f}" for v in sc.values], textposition="outside",
                         marker_color=[C.HARVEST if p == r["product"] else C.GREEN if p == fit["best_product"] else "#CFE0D5" for p in sc.index]))
    f.update_layout(xaxis=dict(range=[0, 110]))
    U.show(U.fig(f, 360, "Fit score by product (amber: current, green: best)"))
with c2:
    acts = []
    if fit["best_product"] != r["product"] and fit["fit_gap"] >= 15:
        acts.append(f"At renewal, move from {r['product'].lower()} to <b>{fit['best_product'].lower()}</b>: {fit['reason'].lower()}.")
    if r["status"] in ("Amber", "Red"):
        acts.append("Call within 5 working days; confirm harvest or sales date and buyer payments.")
    if not r["insured"] and r["rain_3m"] < -10:
        acts.append("Rainfall is below normal and the business is uninsured: discuss index insurance and a harvest-aligned repayment holiday.")
    if r["buyer_concentration"] >= 0.7 and r["contracted_sales_share"] < 0.3:
        acts.append("Sales depend on one buyer without a contract: obtain an offtake agreement or assignment of proceeds.")
    if r["status"] == "Green" and r["dpd"] == 0 and (r["inflow_yoy"] or 0) > 0:
        acts.append("Performing with growing sales: candidate for a limit increase or additional structured product.")
    if not acts:
        acts.append("Continue standard monitoring.")
    st.markdown("<div class='explain'><b>Suggested actions</b>" + "".join(f"<p style='margin:.35rem 0'>{i + 1}. {a}</p>" for i, a in enumerate(acts)) + "</div>", unsafe_allow_html=True)
    st.markdown(f"""
| Profile | |
|---|---|
| Cash cycle | {r['cash_cycle_days']:.0f} days |
| Contracted sales | {r['contracted_sales_share']:.0%} |
| Largest buyer | {r['buyer_concentration']:.0%} of sales |
| Receivable days | {r['receivable_days']:.0f} ({r['recv_chg_3m']:+.0f} in 3 months) |
| Insured / registered / first-time | {'Yes' if r['insured'] else 'No'} / {'Yes' if r['registered'] else 'No'} / {'Yes' if r['first_time'] else 'No'} |
| Women-owned / youth-owned | {'Yes' if r['women_owned'] else 'No'} / {'Yes' if r['youth_owned'] else 'No'} |
""")
