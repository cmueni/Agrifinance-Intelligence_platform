import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from views import common as U

b = U.bundle()
data, feats = b["data"], b["feats"]
lt = U.filt(b["latest"])
cl = data["climate"]
U.page_header("Climate exposure", f"Rainfall, vegetation and drought signals mapped to credit exposure. About 78% of Kenyan farmers rely on rain-fed production (CBK, July 2026).", "Risk")
U.decision("Set climate-adjusted limits, require insurance, and prepare restructuring ahead of failed seasons.", "CRO, Head of Agribusiness, DFI")
U.quality("KMD and CHIRPS rainfall, MODIS vegetation, NDMA drought phases", U.month_label(b["month"]), "18 counties, monthly", "High")

cell = b["seg"]["cell"]
lt2 = lt.merge(cell[["value_chain", "county", "climate_risk"]], on=["value_chain", "county"], how="left")
bal = lt2["outstanding_kes"].sum()
high = lt2["climate_risk"] >= 45
season = cl[cl["month"].isin(b["months"][-6:])].groupby("county")["rain_anomaly"].mean()
dry = lt2["county"].map(season) <= -12
U.kpi_cards([
    dict(label="Exposure in high climate-risk segments", value=U.kes(lt2.loc[high, "outstanding_kes"].sum()), note=f"{lt2.loc[high, 'outstanding_kes'].sum() / bal:.0%} of credit (score 45+)", tone="warn", accent=C.RAG["Red"]),
    dict(label="Exposure where last season failed", value=U.kes(lt2.loc[dry, "outstanding_kes"].sum()), note=f"Rainfall 12%+ below normal over 6 months", tone="warn", accent=C.HARVEST),
    dict(label="Exposure in ASAL counties", value=U.pct(lt2.loc[lt2["asal"], "outstanding_kes"].sum() / bal, 0), note=U.kes(lt2.loc[lt2["asal"], "outstanding_kes"].sum()), accent=C.SOIL),
    dict(label="Borrowers insured", value=U.pct(lt2["insured"].mean(), 0), note=f"{U.pct(lt2.loc[high, 'insured'].mean(), 0)} in high-risk segments", accent=C.SKY),
])

st.markdown("#### Rainfall anomaly by county (% versus long-term mean)")
hm = cl.pivot(index="county", columns="month", values="rain_anomaly").reindex(list(C.COUNTIES))
f = px.imshow(hm, color_continuous_scale=[[0, "#8A5A2B"], [0.35, "#E9B949"], [0.5, "#FFFFFF"], [0.75, "#8EC3E6"], [1, "#2F5F86"]], zmin=-60, zmax=60, aspect="auto",
              labels=dict(color="%", x="", y=""))
U.show(U.fig(f, 470))
st.caption("Brown: drier than normal. Blue: wetter. Long rains fall March to May, short rains October to December.")

c1, c2 = st.columns(2)
with c1:
    ph = cl.groupby(["month", "drought_phase"]).size().unstack().reindex(columns=["Normal", "Alert", "Alarm"]).fillna(0)
    f = go.Figure()
    for p, col in (("Normal", C.RAG["Green"]), ("Alert", C.RAG["Amber"]), ("Alarm", C.RAG["Red"])):
        f.add_bar(x=ph.index, y=ph[p], name=p, marker_color=col)
    f.update_layout(barmode="stack", yaxis_title="Counties")
    U.show(U.fig(f, 340, "Drought phase: counties by month"))
with c2:
    ch = b["seg"]["chain"].sort_values("climate_risk")
    f = go.Figure()
    for k, col in zip(C.WEIGHTS["climate_risk"], [C.SOIL, C.HARVEST, C.RAG["Red"], C.SKY, C.MUTED]):
        f.add_bar(y=ch["value_chain"], x=ch[f"climate_risk::{k}"] * C.WEIGHTS["climate_risk"][k], orientation="h", name=k, marker_color=col)
    f.update_layout(barmode="stack", xaxis_title="Climate risk score (weighted components)", legend=dict(font=dict(size=10)))
    U.show(U.fig(f, 380, "Climate risk by value chain"))

st.markdown("#### Exposure versus climate risk")
co = b["seg"]["county"]
f = px.scatter(co, x="rain_season", y="climate_risk", size="exposure_kes", color="npl", hover_name="county", size_max=44, color_continuous_scale="Reds",
               labels={"rain_season": "Last season rainfall anomaly (%)", "climate_risk": "Climate risk score", "npl": "NPL"}, text="county")
f.update_traces(textposition="top center", textfont_size=10)
f.add_vline(x=-12, line_dash="dot", line_color=C.MUTED, annotation_text="Failed season threshold")
U.show(U.fig(f, 440))

st.markdown("#### Climate-exposed borrowers without insurance")
v = lt2[high & ~lt2["insured"]].sort_values("outstanding_kes", ascending=False)
if st.toggle("Only my institution", True, key="cl_mine"):
    v = v[v["lender"] == st.session_state["institution"]]
t = v[["business", "value_chain", "actor", "county", "product", "climate_risk", "rain_3m", "status", "outstanding_kes"]]
t.columns = ["Business", "Value chain", "Actor", "County", "Product", "Segment climate risk", "Rainfall 3m %", "Status", "Outstanding"]
st.dataframe(U.tint_cols(t.style.format({"Segment climate risk": "{:.0f}", "Rainfall 3m %": "{:+.0f}", "Outstanding": lambda x: U.kes(x)}), ["Status"]), hide_index=True, use_container_width=True, height=320)
st.caption(f"{len(t):,} borrowers. Suggested action: offer index insurance at renewal and align repayments to harvest months.")
