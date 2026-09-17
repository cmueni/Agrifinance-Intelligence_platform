import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from views import common as U

b = U.bundle()
g = U.filt(b["gap"], cols=("value_chain", "county"))
U.page_header("Financing gap", "Estimated financing demand minus formal credit observed, by value chain, county and actor. The gap shows where finance is not reaching.", "Access to finance")
U.decision("Target new lending, guarantee cover and blended finance where the gap is large and risk is manageable.", "DFI, Government, Head of Agribusiness")
U.quality("Enterprise estimates (KNBS, AFA, cooperatives registry) and pooled loan tapes", U.month_label(b["month"]), f"Reporting lenders scaled to {I.MARKET_COVERAGE:.0%} market coverage", "Medium")

dem, cred, gap = g["demand_kes"].sum(), g["formal_credit_kes"].sum(), g["gap_kes"].sum()
U.kpi_cards([
    dict(label="Estimated financing demand", value=U.kes(dem), note="Working capital plus investment", accent=C.SKY),
    dict(label="Formal credit (market estimate)", value=U.kes(cred), note=f"Observed {U.kes(cred * I.MARKET_COVERAGE)} ÷ {I.MARKET_COVERAGE:.0%} coverage", accent=C.GREEN),
    dict(label="Financing gap", value=U.kes(gap), note=f"{gap / dem:.0%} of demand unmet", tone="warn", accent=C.HARVEST),
    dict(label="Enterprises in scope", value=f"{g['enterprises'].sum():,}", note=f"{g['financed'].sum():,} with formal credit in the sample", accent=C.SOIL),
])
with st.expander("How the gap is estimated"):
    st.markdown(f"""
- **Demand** = enterprises × median turnover × (cash cycle ÷ 365 × 0.8 + investment share by actor). Investment share ranges from 6% for traders to 25% for processors.
- **Formal credit** = outstanding balances from reporting institutions ÷ {I.MARKET_COVERAGE:.0%}, their estimated share of formal agri SME credit.
- **Gap** = demand minus formal credit, floored at zero. **Penetration** = formal credit ÷ demand.
- **Confidence** is High where at least 30 financed enterprises inform the cell, Medium for 10 to 29 and Low below 10. Low-confidence cells are indicative only.
- Demand is an estimate, not an observed number. It should be triangulated with the CBK MSME Survey, KNBS enterprise data and value-chain censuses before it is used to set targets.
""")

by = st.segmented_control("View by", ["Value chain", "County", "Actor"], default="Value chain", key="gap_by") or "Value chain"
col = {"Value chain": "value_chain", "County": "county", "Actor": "actor"}[by]
agg = g.groupby(col).agg(demand=("demand_kes", "sum"), credit=("formal_credit_kes", "sum"), gap=("gap_kes", "sum"), financed=("financed", "sum")).reset_index()
agg["penetration"] = agg["credit"] / agg["demand"]
agg["confidence"] = np.select([agg["financed"] >= 30, agg["financed"] >= 10], ["High", "Medium"], "Low")
agg = agg.sort_values("gap")
c1, c2 = st.columns([1.5, 1])
with c1:
    f = go.Figure()
    f.add_bar(y=agg[col], x=agg["credit"] / 1e9, orientation="h", name="Formal credit", marker_color=C.GREEN)
    f.add_bar(y=agg[col], x=agg["gap"] / 1e9, orientation="h", name="Gap", marker_color=C.HARVEST,
              text=[f"{p:.0%} met" for p in agg["penetration"]], textposition="outside")
    f.update_layout(barmode="stack", xaxis_title="KES bn")
    U.show(U.fig(f, 460, f"Demand split into formal credit and gap, by {by.lower()}"))
with c2:
    t = agg.sort_values("gap", ascending=False)[[col, "gap", "penetration", "confidence"]]
    t.columns = [by, "Gap", "Penetration", "Confidence"]
    st.dataframe(U.tint_cols(t.style.format({"Gap": lambda v: U.kes(v), "Penetration": "{:.0%}"}), ["Confidence"]), hide_index=True, use_container_width=True, height=460)

st.markdown("#### Gap heatmap: value chain × county")
hm = g.groupby(["value_chain", "county"])["gap_kes"].sum().unstack().reindex(columns=list(C.COUNTIES)).dropna(axis=1, how="all") / 1e6
f = px.imshow(hm, color_continuous_scale=[[0, "#FFF8E8"], [0.5, "#E9B949"], [1, "#8A5A2B"]], aspect="auto", labels=dict(color="KES M", x="", y=""), text_auto=".0f")
f.update_traces(textfont_size=10)
U.show(U.fig(f, 520))
st.caption("Blank cells: no enterprises estimated for that chain in that county in this example.")

st.markdown("#### Where the gap is large and risk is manageable")
cell = U.visible_segments(U.filt(b["seg"]["cell"], cols=("value_chain", "county")))
f = px.scatter(cell, x="risk_index", y="gap_kes", size="demand_kes", color="value_chain", hover_name="county", size_max=36,
               labels={"risk_index": "Risk index (lower is better)", "gap_kes": "Financing gap (KES)", "value_chain": ""},
               hover_data={"npl": ":.1%", "opportunity": True, "confidence": True})
f.add_vline(x=C.QUADRANT_CUTS["grow_risk"], line_dash="dot", line_color=C.MUTED, annotation_text="Risk threshold for growth")
U.show(U.fig(f, 460))
