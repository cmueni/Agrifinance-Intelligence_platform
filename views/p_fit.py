import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from views import common as U

b = U.bundle()
lt = U.filt(b["latest"])
fit = b["fit"].loc[lt.index]
feats = b["feats"]
U.page_header("Product fit", "Agri SMEs rarely fail because agriculture is unbankable; they fail when repayment terms ignore the crop, the buyer and the weather. Match the product to the constraint.", "Access to finance")
U.decision("Redesign products and restructure at renewal where the current product does not fit the borrower's cash cycle.", "Credit Manager, Product team")

conv = lt["product"].isin(C.CONVENTIONAL).mean()
U.kpi_cards([
    dict(label="Term loans and overdrafts", value=U.pct(conv, 0), note="Share of agri SME borrowers", accent=C.SOIL),
    dict(label="Borrowers in a poorly fitting product", value=U.pct(fit["mismatch"].mean(), 0), note=f"{fit['mismatch'].sum():,} borrowers, {U.kes(lt.loc[fit['mismatch'], 'outstanding_kes'].sum())}", tone="warn", accent=C.HARVEST),
    dict(label="Most common best-fit product", value=fit["best_product"].value_counts().index[0], note=f"{fit['best_product'].value_counts(normalize=True).iloc[0]:.0%} of borrowers", accent=C.GREEN),
    dict(label="Published benchmark", value="Over 85%", note="MSME lending in term loans and overdrafts (CBK, 2024)", accent=C.SKY),
])

st.markdown("#### Constraint → finance solution")
st.dataframe(I.CONSTRAINT_SOLUTIONS, hide_index=True, use_container_width=True)

st.markdown("#### Evidence: does fit matter for repayment?")
hist = feats[feats["target_3m"].notna()].copy()
hist["group"] = np.where(hist["mismatch"] == 1, "Conventional product on a long seasonal cycle", "Other borrowers")
c1, c2 = st.columns(2)
with c1:
    ev = hist.groupby("group")["target_3m"].mean().reset_index()
    f = px.bar(ev, x="group", y="target_3m", text=ev["target_3m"].map(lambda v: f"{v:.1%}"), color="group",
               color_discrete_sequence=[C.HARVEST, C.GREEN], labels={"target_3m": "Monthly rate of falling 30+ days past due within 3 months", "group": ""})
    f.update_layout(showlegend=False, yaxis_tickformat=".0%")
    U.show(U.fig(f, 340, "Deterioration rate by product fit, 24 months"))
with c2:
    ct = pd.crosstab(lt["product"], fit["best_product"], normalize="index") * 100
    f = px.imshow(ct.round(0), text_auto=".0f", aspect="auto", color_continuous_scale=[[0, "#FFFFFF"], [1, C.GREEN]], labels=dict(x="Best-fit product", y="Current product", color="%"))
    f.update_xaxes(tickangle=35)
    U.show(U.fig(f, 420, "Current product versus best fit (% of row)"))

st.markdown("#### Borrower recommendations")
c1, c2, c3 = st.columns(3)
only_mis = c1.toggle("Only poorly fitting products", True, key="fit_only")
mine = c2.toggle("Only my institution", True, key="fit_mine")
prod_f = c3.multiselect("Current product", C.PRODUCTS, key="fit_prod", placeholder="All products")
v = lt.drop(columns=["mismatch"]).join(fit[["best_product", "best_score", "current_score", "fit_gap", "reason", "mismatch"]])
if only_mis:
    v = v[v["mismatch"]]
if mine:
    v = v[v["lender"] == st.session_state["institution"]]
if prod_f:
    v = v[v["product"].isin(prod_f)]
t = v.sort_values("fit_gap", ascending=False)[["business", "value_chain", "actor", "county", "product", "current_score", "best_product", "best_score", "reason", "outstanding_kes"]]
t.columns = ["Business", "Value chain", "Actor", "County", "Current product", "Fit now", "Recommended", "Fit", "Why", "Outstanding"]
ev = st.dataframe(t.style.format({"Fit now": "{:.0f}", "Fit": "{:.0f}", "Outstanding": lambda x: U.kes(x)}), hide_index=True, use_container_width=True, height=320,
                  on_select="rerun", selection_mode="single-row", key="fit_table")
st.caption(f"{len(t):,} borrowers. Your institution's own borrowers are shown by name; peers' borrowers are never visible outside their institution." if mine else
           "Market view shown for demonstration. In production, other institutions' borrowers are not visible.")
if len(t):
    rows = ev.selection.rows if ev and ev.selection else []
    i = v.sort_values("fit_gap", ascending=False).index[rows[0] if rows else 0]
    sc = b["fit"].loc[i, C.PRODUCTS].sort_values()
    cur = lt.loc[i, "product"]
    f = go.Figure(go.Bar(x=sc.values, y=sc.index, orientation="h", marker_color=[C.HARVEST if p == cur else C.GREEN if p == sc.index[-1] else "#CFE0D5" for p in sc.index],
                         text=[f"{x:.0f}" for x in sc.values], textposition="outside"))
    f.update_layout(xaxis=dict(range=[0, 110]))
    U.show(U.fig(f, 360, f"Product fit scores: {lt.loc[i, 'business']} (amber: current, green: best)"))
