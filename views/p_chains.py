import html
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from views import common as U

b = U.bundle()
feats, data = b["feats"], b["data"]
U.page_header("Value chain explorer", "The value chain is the unit of analysis: credit, risk, prices, climate and gaps for one chain, from input suppliers to exporters.", "Market")

chains = list(C.VALUE_CHAINS)
sel = st.session_state.get("filters", {}).get("value_chain") or []
vc = st.selectbox("Value chain", chains, index=chains.index(sel[0]) if sel else 0, key="vc_select")
p = C.VALUE_CHAINS[vc]
row = b["seg"]["chain"].set_index("value_chain").loc[vc]
d_all = feats[feats["value_chain"] == vc]
lt = b["latest"][b["latest"]["value_chain"] == vc]

months_harvest = ", ".join(pd.Period(f"2026-{m:02d}", "M").strftime("%b") for m in p["harvest"]) if len(p["harvest"]) < 12 else "Year-round"
st.markdown(f"<div class='headcard'><div class='name'>{html.escape(vc)} {U.pill(row['quadrant'])} {U.pill('EW ' + row['ew_status'], row['ew_status'])}</div>"
            f"<div class='meta'>{html.escape(p['l2'])} · Cash cycle {p['cycle']} days · Harvest: {months_harvest} · Export share {p['export']:.0%} · Climate sensitivity {p['climate']:.2f}</div></div>",
            unsafe_allow_html=True)
U.kpi_cards([
    dict(label="Outstanding", value=U.kes(row["exposure_kes"]), note=f"{row['exposure_kes'] / row['exposure_12'] - 1:+.1%} in 12 months"),
    dict(label="Borrowers", value=f"{row['borrowers']:,.0f}", note=f"{row['institutions']:.0f} institutions"),
    dict(label="NPL ratio", value=U.pct(row["npl"]), note=f"{(row['npl'] - row['npl_12']) * 100:+.1f} pp in 12 months", tone="bad" if row["npl"] > row["npl_12"] else "good"),
    dict(label="Financing gap", value=U.kes(row["gap_kes"]), note=f"Penetration {row['formal_credit_kes'] / row['demand_kes']:.0%}", tone="warn"),
    dict(label="Demand growth", value=U.pct(row["demand_growth"], 0, True), note="Applications vs same months last year"),
])
st.write("")

U.decision(f"Set appetite, limits and product design for {vc.lower()} lending, and which actors to target.", "Head of Agribusiness, Credit Manager")
c1, c2 = st.columns([1, 1.6])
with c1:
    st.markdown("#### Health scorecard")
    U.score_bar("Opportunity", row["opportunity"], C.GREEN)
    U.score_bar("Credit risk", row["credit_risk"], C.RAG["Red"])
    U.score_bar("Climate risk", row["climate_risk"], C.SKY)
    U.score_bar("Market risk", row["market_risk"], C.HARVEST)
    U.score_bar("Risk index (45% credit, 30% climate, 25% market)", row["risk_index"], C.SOIL)
    if row["signals"]:
        st.markdown(f"**Warning signals:** {row['signal_list']}")
with c2:
    st.markdown("#### What drives each score")
    score = st.segmented_control("Score", ["opportunity", "credit_risk", "climate_risk", "market_risk"], default="opportunity",
                                 format_func=lambda s: s.replace("_", " ").capitalize(), key="vc_score") or "opportunity"
    w = C.WEIGHTS[score]
    dd = pd.DataFrame({"Component": list(w), "Score": [row[f"{score}::{k}"] for k in w], "Weight": list(w.values())})
    dd["Contribution"] = dd["Score"] * dd["Weight"]
    f = go.Figure()
    f.add_bar(y=dd["Component"], x=dd["Score"], orientation="h", name="Component score (0 to 100)", marker_color="#CFE0D5")
    f.add_bar(y=dd["Component"], x=dd["Contribution"], orientation="h", name="Weighted contribution", marker_color=C.GREEN,
              text=[f"{c:.0f} (w {wt:.0%})" for c, wt in zip(dd["Contribution"], dd["Weight"])], textposition="outside")
    f.update_layout(barmode="overlay", yaxis=dict(autorange="reversed"), xaxis=dict(range=[0, 110]))
    U.show(U.fig(f, 300))

st.markdown("#### Chain structure: credit by actor")
act = lt.groupby("actor").agg(exposure=("outstanding_kes", "sum"), borrowers=("borrower_id", "nunique"),
                               npl=("dpd", lambda s: 0)).reset_index()
act["npl"] = [lt.loc[(lt["actor"] == a) & (lt["dpd"] >= 90), "outstanding_kes"].sum() / max(1, e) for a, e in zip(act["actor"], act["exposure"])]
gap = b["gap"][b["gap"]["value_chain"] == vc].groupby("actor")[["gap_kes", "demand_kes"]].sum()
act = act.merge(gap, left_on="actor", right_index=True, how="left")
order = [a for a in C.ACTORS if a in set(act["actor"])]
dot = ["digraph G { rankdir=LR; bgcolor=transparent; node [shape=box style=\"rounded,filled\" fontname=\"Plus Jakarta Sans\" fontsize=11 color=\"#CFE0D5\" fillcolor=\"#FFFFFF\"]; edge [color=\"#9FB8A8\"];"]
for a in order:
    r = act.set_index("actor").loc[a]
    fill = "#FBE3E7" if r["npl"] > 0.15 else "#FDF3D6" if r["npl"] > 0.07 else "#E3F4EC"
    dot.append(f'"{a}" [label="{a}\\n{U.kes(r["exposure"], 0)} credit · NPL {r["npl"]:.0%}\\nGap {U.kes(r["gap_kes"], 1)}" fillcolor="{fill}"];')
for x, y in zip(order, order[1:]):
    dot.append(f'"{x}" -> "{y}";')
dot.append("}")
st.graphviz_chart("\n".join(dot), use_container_width=True)
st.caption("Box colour: green NPL below 7%, amber 7% to 15%, red above 15%. Gap is estimated financing demand not met by formal credit.")

c1, c2 = st.columns(2)
with c1:
    mk = data["market"][data["market"]["value_chain"] == vc].melt(id_vars="month", value_vars=["price_index", "input_cost_index", "production_index", "margin_index"])
    mk["variable"] = mk["variable"].map({"price_index": "Farm-gate price", "input_cost_index": "Input cost", "production_index": "Production", "margin_index": "Margin"})
    f = px.line(mk, x="month", y="value", color="variable", labels={"value": "Index", "month": "", "variable": ""},
                color_discrete_map={"Farm-gate price": C.GREEN, "Input cost": C.RAG["Red"], "Production": C.SKY, "Margin": C.HARVEST})
    U.show(U.fig(f, 330, "Prices, costs and production (index)"))
with c2:
    tr = d_all.groupby("month").apply(lambda g: pd.Series({"Outstanding (KES M)": g["outstanding_kes"].sum() / 1e6,
                                                            "NPL %": g.loc[g["dpd"] >= 90, "outstanding_kes"].sum() / g["outstanding_kes"].sum() * 100}), include_groups=False).reset_index()
    f = go.Figure()
    f.add_bar(x=tr["month"], y=tr["Outstanding (KES M)"], name="Outstanding (KES M)", marker_color="#CFE0D5")
    f.add_scatter(x=tr["month"], y=tr["NPL %"], name="NPL %", yaxis="y2", line=dict(color=C.RAG["Red"], width=3))
    f.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, rangemode="tozero"))
    U.show(U.fig(f, 330, "Credit and NPL trend"))

st.markdown("#### Recommended lender focus")
fit = b["fit"].loc[lt.index]
best_actor = act[act["exposure"] > 0].assign(rank=lambda x: x["gap_kes"].rank(ascending=False) + x["npl"].rank()).sort_values("rank").iloc[0]
top_prod = fit["best_product"].value_counts().index[0]
mism = (lt["product"].isin(C.CONVENTIONAL)).mean()
cty = U.visible_segments(b["seg"]["cell"][b["seg"]["cell"]["value_chain"] == vc]).sort_values("opportunity", ascending=False)
cons = I.CONSTRAINT_SOLUTIONS.set_index("Constraint")
constraint = "Long production cycle" if p["cycle"] >= 120 else "Climate risk" if p["climate"] >= 0.6 else "Price volatility" if p["price_vol"] >= 0.06 else "Buyer payment delays" if p["export"] >= 0.5 else "Seasonal cash flow"
def bold(x):
    return re.sub(r"[*][*](.+?)[*][*]", r"<b>\1</b>", x)


recs = [
    f"Target **{best_actor['actor'].lower()}s**: {U.kes(best_actor['gap_kes'])} unmet demand with NPL of {best_actor['npl']:.1%}.",
    f"Lead with **{top_prod.lower()}**, the best-fit structure for most borrowers in this chain; {mism:.0%} of current lending is term loans or overdrafts.",
    f"Main constraint: **{constraint.lower()}**. Response: {cons.loc[constraint, 'Financing response'].lower()}.",
]
if len(cty):
    recs.append("Priority counties: " + ", ".join(f"**{r.county}** (opportunity {r.opportunity:.0f}, risk {r.risk_index:.0f})" for r in cty.head(3).itertuples()) + ".")
st.markdown("<div class='explain'>" + "".join(f"<p style='margin:.2rem 0'>{i + 1}. {bold(x)}</p>" for i, x in enumerate(recs)) + "</div>", unsafe_allow_html=True)

st.markdown("#### Counties in this chain")
t = cty.assign(Exposure=lambda x: x["exposure_kes"] / 1e6, NPL=lambda x: x["npl"] * 100, Gap=lambda x: x["gap_kes"] / 1e6)[
    ["county", "borrowers", "institutions", "Exposure", "NPL", "Gap", "opportunity", "risk_index", "quadrant", "ew_status", "confidence"]]
t.columns = ["County", "Borrowers", "Institutions", "Exposure", "NPL", "Gap", "Opportunity", "Risk", "Appetite", "Early warning", "Confidence"]
st.dataframe(U.tint_cols(t.style.format({"Exposure": "{:,.0f}M", "NPL": "{:.1f}%", "Gap": "{:,.0f}M", "Borrowers": "{:.0f}", "Institutions": "{:.0f}", "Opportunity": "{:.0f}", "Risk": "{:.0f}"}),
                         ["Appetite", "Early warning", "Confidence"]), hide_index=True, use_container_width=True)
st.caption(f"Cells with fewer than {C.AGGREGATION_MIN_INSTITUTIONS} institutions or {C.AGGREGATION_MIN_BORROWERS} borrowers are suppressed.")
