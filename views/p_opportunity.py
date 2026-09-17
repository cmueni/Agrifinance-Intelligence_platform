import html

import pandas as pd
import plotly.express as px
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from views import common as U

b = U.bundle()
U.page_header("Opportunity finder", "Rank value chain and county segments by opportunity and risk, then see the drivers, the product to lead with and the actors to target.", "Access to finance")
U.decision("Choose the next segments to grow, and the structure that makes the lending safe.", "Head of Agribusiness, CEO and Strategy")

cell = U.filt(b["seg"]["cell"], cols=("value_chain", "county"))
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    min_opp = c1.slider("Minimum opportunity", 0, 90, 50, 5, key="of_opp")
    max_risk = c2.slider("Maximum risk index", 10, 80, 45, 5, key="of_risk")
    quads = c3.multiselect("Appetite", list(C.QUADRANT_COLORS), default=["Grow", "Grow with structure"], key="of_quad")
    conf = c4.multiselect("Confidence", ["High", "Medium", "Low"], default=["High", "Medium"], key="of_conf")
vis = U.visible_segments(cell)
res = vis[(vis["opportunity"] >= min_opp) & (vis["risk_index"] <= max_risk) & (vis["quadrant"].isin(quads or list(C.QUADRANT_COLORS))) & vis["confidence"].isin(conf or ["High", "Medium", "Low"])]
res = res.sort_values(["opportunity", "gap_kes"], ascending=False)
st.caption(f"{len(res)} of {len(vis)} visible segments match. {len(cell) - len(vis)} suppressed for confidentiality.")

c1, c2 = st.columns([1.25, 1])
with c1:
    f = px.scatter(vis, x="risk_index", y="opportunity", size="gap_kes", color="quadrant", color_discrete_map=C.QUADRANT_COLORS, size_max=34,
                   hover_name=vis["value_chain"] + " · " + vis["county"], hover_data={"gap_kes": ":,.0f", "npl": ":.1%", "borrowers": True, "quadrant": False},
                   labels={"risk_index": "Risk index", "opportunity": "Opportunity score", "quadrant": ""})
    f.update_traces(marker=dict(line=dict(width=1, color="white"), opacity=0.85))
    q = C.QUADRANT_CUTS
    f.add_hline(y=q["opportunity"], line_dash="dot", line_color=C.MUTED)
    f.add_vline(x=q["grow_risk"], line_dash="dot", line_color=C.MUTED)
    for x, y, t in ((8, 95, "Grow"), (70, 95, "Grow with structure"), (8, 8, "Selective"), (70, 8, "Tighten and monitor")):
        f.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(color=C.MUTED, size=11))
    f.update_layout(xaxis=dict(range=[0, 80]), yaxis=dict(range=[0, 100]))
    U.show(U.fig(f, 470, "Opportunity versus risk (bubble size: financing gap)"))
with c2:
    t = res[["value_chain", "county", "opportunity", "risk_index", "gap_kes", "quadrant", "confidence"]].copy()
    t.columns = ["Value chain", "County", "Opportunity", "Risk", "Gap", "Appetite", "Confidence"]
    ev = st.dataframe(U.tint_cols(t.style.format({"Opportunity": "{:.0f}", "Risk": "{:.0f}", "Gap": lambda v: U.kes(v)}), ["Appetite", "Confidence"]),
                      hide_index=True, use_container_width=True, height=470, on_select="rerun", selection_mode="single-row", key="of_table")

if len(res):
    rows = ev.selection.rows if ev and ev.selection else []
    r = res.iloc[rows[0] if rows else 0]
    st.markdown(f"#### {html.escape(r['value_chain'])} in {html.escape(r['county'])} {U.pill(r['quadrant'])} {U.pill('Confidence ' + r['confidence'], r['confidence'])}", unsafe_allow_html=True)
    st.caption("Select a row in the table to change the segment.")
    U.kpi_cards([
        dict(label="Financing gap", value=U.kes(r["gap_kes"]), note=f"Penetration {r['formal_credit_kes'] / r['demand_kes']:.0%}", tone="warn"),
        dict(label="Outstanding", value=U.kes(r["exposure_kes"]), note=f"{r['exposure_kes'] / r['exposure_12'] - 1:+.0%} in 12 months" if pd.notna(r["exposure_12"]) else ""),
        dict(label="NPL ratio", value=U.pct(r["npl"]), note=f"PAR30 {U.pct(r['par30'])}"),
        dict(label="Borrowers", value=f"{r['borrowers']:.0f}", note=f"{r['institutions']:.0f} institutions"),
        dict(label="Early warning", value=r["ew_status"], note=r["signal_list"] or "No adverse signals"),
    ])
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Why it scores well**")
        for k, v in I.drivers(r, "opportunity", 4):
            U.score_bar(f"{k} (weight {C.WEIGHTS['opportunity'][k]:.0%})", r[f"opportunity::{k}"], C.GREEN)
    with c2:
        st.markdown("**What to watch**")
        for k, v in I.drivers(r, "credit_risk", 2) + I.drivers(r, "climate_risk", 1) + I.drivers(r, "market_risk", 1):
            src = "credit_risk" if k in C.WEIGHTS["credit_risk"] else "climate_risk" if k in C.WEIGHTS["climate_risk"] else "market_risk"
            U.score_bar(f"{k} ({src.replace('_', ' ')})", r[f"{src}::{k}"], C.RAG["Red"] if src == "credit_risk" else C.SKY if src == "climate_risk" else C.HARVEST)
    with c3:
        st.markdown("**How to lend**")
        lt = b["latest"]
        idx = lt[(lt["value_chain"] == r["value_chain"]) & (lt["county"] == r["county"])].index
        fit = b["fit"].loc[idx]
        prod = fit["best_product"].value_counts()
        gap_act = b["gap"][(b["gap"]["value_chain"] == r["value_chain"]) & (b["gap"]["county"] == r["county"])].sort_values("gap_kes", ascending=False)
        st.markdown(f"<div class='explain'><p style='margin:.1rem 0'><b>Lead product:</b> {html.escape(prod.index[0])} (best fit for {prod.iloc[0] / prod.sum():.0%} of borrowers)</p>"
                    f"<p style='margin:.1rem 0'><b>Target actors:</b> {html.escape(', '.join(gap_act['actor'].head(2)))}</p>"
                    f"<p style='margin:.1rem 0'><b>Current mismatch:</b> {fit['mismatch'].mean():.0%} of borrowers in a product that does not fit their cash cycle</p>"
                    f"<p style='margin:.1rem 0'><b>Risk mitigant:</b> {'insurance-linked lending and harvest-aligned repayments' if r['climate_risk'] >= 40 else 'buyer contracts and assignment of proceeds' if r['market_risk'] >= 40 else 'standard monitoring with seasonal repayment plans'}</p></div>",
                    unsafe_allow_html=True)
else:
    st.info("No segments match these filters. Relax the risk or opportunity thresholds.")
