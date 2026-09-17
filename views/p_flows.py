import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from views import common as U

b = U.bundle()
lt = U.filt(b["latest"])
apps = U.filt(b["data"]["applications"])

U.page_header("Credit Flows", "Follow credit from lender type to value chain, actor, product and county, and see where applications stall.", "Credit flows")
U.decision("Identify which lender types and products reach each value chain, and where demand is being declined.", "Head of Agribusiness, DFI")
U.quality("Pooled loan tapes and origination systems", U.month_label(b["month"]), "12 reporting institutions", "Medium")

c1, c2 = st.columns([3, 1])
with c2:
    third = st.radio("Third level", ["Actor", "Product", "County"], key="flow_third")
    metric = st.radio("Measure", ["Outstanding (KES)", "Borrowers"], key="flow_metric")
    top_n = st.slider("Show top value chains", 4, 12, 8, key="flow_topn")
col3 = {"Actor": "actor", "Product": "product", "County": "county"}[third]
val = "outstanding_kes" if metric.startswith("Out") else "borrower_id"
agg = "sum" if val == "outstanding_kes" else "nunique"
keep = lt.groupby("value_chain")["outstanding_kes"].sum().nlargest(top_n).index
d = lt[lt["value_chain"].isin(keep)]
l1 = d.groupby(["lender_type", "value_chain"])[val].agg(agg).reset_index()
l2 = d.groupby(["value_chain", col3])[val].agg(agg).reset_index()
nodes = list(dict.fromkeys(list(l1["lender_type"]) + list(l1["value_chain"]) + list(l2[col3])))
idx = {n: i for i, n in enumerate(nodes)}
color = [C.FOREST if n in set(l1["lender_type"]) else C.GREEN if n in set(keep) else C.HARVEST for n in nodes]
link_color = ["rgba(31,111,74,0.30)"] * len(l1) + ["rgba(217,154,30,0.38)"] * len(l2)
fig = go.Figure(go.Sankey(
    arrangement="snap", valueformat=",.0f",
    textfont=dict(family="Plus Jakarta Sans, Segoe UI, Arial, sans-serif", size=13, color=C.INK, weight=600, shadow="none"),
    node=dict(label=nodes, color=color, pad=18, thickness=18, line=dict(width=0),
              hovertemplate="%{label}<br>%{value:,.0f}<extra></extra>"),
    link=dict(source=[idx[x] for x in l1["lender_type"]] + [idx[x] for x in l2["value_chain"]],
              target=[idx[x] for x in l1["value_chain"]] + [idx[x] for x in l2[col3]],
              value=list(l1[val]) + list(l2[val]), color=link_color)))
with c1:
    U.show(U.fig(fig, 600, f"Lender type → value chain → {third.lower()}"))

st.markdown("#### Applications and decisions")
m = apps.groupby("month").agg(applications=("approved", "size"), approved=("approved", "sum")).reset_index()
m["approval_rate"] = m["approved"] / m["applications"]
c1, c2 = st.columns(2)
with c1:
    f = go.Figure()
    f.add_bar(x=m["month"], y=m["applications"], name="Applications", marker_color="#CFE0D5")
    f.add_bar(x=m["month"], y=m["approved"], name="Approved", marker_color=C.GREEN)
    f.add_scatter(x=m["month"], y=m["approval_rate"] * 100, name="Approval rate %", yaxis="y2", line=dict(color=C.HARVEST, width=3))
    f.update_layout(barmode="overlay", yaxis2=dict(overlaying="y", side="right", range=[0, 100], showgrid=False, title="%"))
    U.show(U.fig(f, 340, "Monthly applications and approval rate"))
with c2:
    dec = apps[~apps["approved"]]
    dr = dec[dec["decline_reason"] != ""].groupby("decline_reason").size().sort_values()
    f = px.bar(x=dr.values / dr.sum() * 100, y=dr.index, orientation="h", labels={"x": "% of declines", "y": ""}, color_discrete_sequence=[C.SOIL])
    U.show(U.fig(f, 340, "Why applications are declined"))

c1, c2 = st.columns(2)
with c1:
    ar = apps[apps["month"].isin(b["months"][-6:])].groupby("value_chain")["approved"].agg(["mean", "size"]).reset_index().sort_values("mean")
    f = px.bar(ar, x="mean", y="value_chain", orientation="h", text=ar["mean"].map(lambda v: f"{v:.0%}"), labels={"mean": "Approval rate", "value_chain": ""},
               color="mean", color_continuous_scale=[[0, "#F4D9A0"], [1, C.GREEN]])
    f.update_layout(coloraxis_showscale=False, xaxis_tickformat=".0%")
    U.show(U.fig(f, 380, "Approval rate by value chain, last 6 months"))
with c2:
    src = pd.Series(C.FARMER_CREDIT_SOURCES).sort_values()
    f = px.bar(x=src.values, y=src.index, orientation="h", text=[f"{v}%" for v in src.values], labels={"x": "% of farmers who borrowed", "y": ""},
               color_discrete_sequence=[C.HARVEST])
    U.show(U.fig(f, 380, "Where farmers borrow (published, national)"))
    st.caption("Source: CBK Agriculture Survey, July 2026. Multiple responses allowed. Informal and buyer credit remain large, which is the formal market's opportunity.")

st.markdown("#### Lender mix by value chain")
mix = lt.groupby(["value_chain", "lender_type"])["outstanding_kes"].sum().reset_index()
mix["share"] = mix["outstanding_kes"] / mix.groupby("value_chain")["outstanding_kes"].transform("sum")
f = px.bar(mix, x="share", y="value_chain", color="lender_type", orientation="h", labels={"share": "Share of outstanding", "value_chain": "", "lender_type": ""})
f.update_layout(xaxis_tickformat=".0%")
U.show(U.fig(f, 420))
