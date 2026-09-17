import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from views import common as U

b = U.bundle()
data = b["data"]
U.page_header("Geographic intelligence", "Where agri SME credit sits, where it performs, and where climate and gaps point to risk or opportunity.", "Market")
U.decision("Allocate county targets, branch and agent coverage, and climate-adjusted limits by county.", "Head of Agribusiness, CRO, DFI")

co = b["seg"]["county"].copy()
co["lat"] = co["county"].map(lambda c: C.COUNTIES[c][0])
co["lon"] = co["county"].map(lambda c: C.COUNTIES[c][1])
co["region"] = co["county"].map(lambda c: C.COUNTIES[c][4])
co["asal"] = co["county"].map(lambda c: "ASAL" if C.COUNTIES[c][2] else "Non-ASAL")
metrics = {"Opportunity score": ("opportunity", "Greens", False), "Risk index": ("risk_index", "Reds", False), "Climate risk": ("climate_risk", "Blues", False),
           "NPL ratio": ("npl", "Reds", True), "Financing gap (KES)": ("gap_kes", "YlOrBr", False), "Credit penetration": ("penetration", "Greens", True)}
co["penetration"] = co["formal_credit_kes"] / co["demand_kes"]

c1, c2 = st.columns([2.2, 1])
with c2:
    mname = st.radio("Colour counties by", list(metrics), key="geo_metric")
    col, scale, is_pct = metrics[mname]
    st.markdown("**Ranking**")
    rk = co.sort_values(col, ascending=False)[["county", col]].head(18)
    rk[col] = rk[col].map(lambda v: U.pct(v) if is_pct else U.kes(v) if "kes" in col else f"{v:.0f}")
    st.dataframe(rk.rename(columns={"county": "County", col: mname}), hide_index=True, use_container_width=True, height=420)
with c1:
    f = px.scatter_geo(co, lat="lat", lon="lon", size="exposure_kes", color=col, hover_name="county", color_continuous_scale=scale, size_max=40, text="county",
                       hover_data={"lat": False, "lon": False, "exposure_kes": ":,.0f", "npl": ":.1%", "opportunity": True, "risk_index": True, "quadrant": True})
    f.update_traces(textposition="top center", textfont=dict(size=10, color=C.INK), marker=dict(line=dict(width=1, color="white")))
    f.update_geos(scope="africa", lataxis_range=[-4.9, 4.8], lonaxis_range=[33.8, 41.9], showcountries=True, countrycolor="#9FB8A8", showland=True, landcolor="#EEF1EA",
                  showocean=True, oceancolor="#E3EDF6", showlakes=True, lakecolor="#E3EDF6", bgcolor="rgba(0,0,0,0)", showframe=False)
    f.update_layout(coloraxis_colorbar=dict(title="", thickness=12), margin=dict(l=0, r=0, t=0, b=0))
    U.show(U.fig(f, 560))
    st.caption("Bubble size: outstanding agri SME credit. Centroids are approximate county locations.")

st.markdown("#### County profile")
counties = list(C.COUNTIES)
sel = st.session_state.get("filters", {}).get("county") or []
cty = st.selectbox("County", counties, index=counties.index(sel[0]) if sel else counties.index("Makueni"), key="geo_county")
r = co.set_index("county").loc[cty]
U.kpi_cards([
    dict(label="Outstanding", value=U.kes(r["exposure_kes"]), note=f"{r['borrowers']:.0f} borrowers, {r['institutions']:.0f} institutions"),
    dict(label="NPL ratio", value=U.pct(r["npl"]), note=f"{(r['npl'] - r['npl_12']) * 100:+.1f} pp in 12 months", tone="bad" if r["npl"] > r["npl_12"] else "good"),
    dict(label="Financing gap", value=U.kes(r["gap_kes"]), note=f"Penetration {r['penetration']:.0%}", tone="warn"),
    dict(label="Last season rainfall", value=f"{r['rain_season']:+.0f}%", note=f"Outlook {r['outlook']:+.0f}% · irrigation {r['irrigation']:.0%}", tone="bad" if r["rain_season"] < -10 else None),
    dict(label="Appetite", value=r["quadrant"], note=f"Opportunity {r['opportunity']:.0f} · risk {r['risk_index']:.0f}"),
])
st.write("")
c1, c2 = st.columns(2)
with c1:
    cell = b["seg"]["cell"]
    cc = cell[cell["county"] == cty].sort_values("exposure_kes")
    f = go.Figure()
    f.add_bar(y=cc["value_chain"], x=cc["exposure_kes"] / 1e6, orientation="h", name="Outstanding (KES M)", marker_color=C.GREEN)
    f.add_bar(y=cc["value_chain"], x=cc["gap_kes"] / 1e6, orientation="h", name="Financing gap (KES M)", marker_color=C.HARVEST)
    f.update_layout(barmode="group")
    U.show(U.fig(f, 360, f"Value chains in {cty}"))
with c2:
    cl = data["climate"][data["climate"]["county"] == cty]
    f = go.Figure()
    f.add_bar(x=cl["month"], y=cl["rain_anomaly"], name="Rainfall anomaly %", marker_color=[C.RAG["Red"] if v < -25 else C.HARVEST if v < -12 else C.SKY for v in cl["rain_anomaly"]])
    f.add_scatter(x=cl["month"], y=cl["ndvi_anomaly"], name="Vegetation anomaly %", line=dict(color=C.GREEN, width=3))
    U.show(U.fig(f, 360, f"Rainfall and vegetation in {cty}"))
vis = U.visible_segments(cc).sort_values("opportunity", ascending=False)
t = vis[["value_chain", "borrowers", "npl", "gap_kes", "opportunity", "risk_index", "quadrant", "ew_status", "signal_list"]].copy()
t.columns = ["Value chain", "Borrowers", "NPL", "Gap", "Opportunity", "Risk", "Appetite", "Early warning", "Signals"]
st.dataframe(U.tint_cols(t.style.format({"NPL": "{:.1%}", "Gap": lambda v: U.kes(v), "Borrowers": "{:.0f}", "Opportunity": "{:.0f}", "Risk": "{:.0f}"}), ["Appetite", "Early warning"]),
             hide_index=True, use_container_width=True)
st.caption(f"{len(cc) - len(vis)} value-chain cells in {cty} suppressed (fewer than {C.AGGREGATION_MIN_INSTITUTIONS} institutions or {C.AGGREGATION_MIN_BORROWERS} borrowers).")
