import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from views import common as U

b = U.bundle()
inst = st.session_state["institution"]
lt = U.filt(b["latest"], cols=("value_chain", "county"))
feats = U.filt(b["feats"], cols=("value_chain", "county"))
U.page_header(f"{inst} versus the market", "Benchmark growth, quality, pricing and reach against other institutions, and measure inclusion across access, affordability, suitability, quality and resilience.",
              "Benchmarking and inclusion")
U.decision("Set growth targets, pricing and inclusion commitments relative to peers.", "CEO and Strategy, Head of Agribusiness, DFI")
st.caption(f"Market figures combine other institutions and are shown only where at least {C.AGGREGATION_MIN_INSTITUTIONS} institutions and {C.AGGREGATION_MIN_BORROWERS} borrowers contribute. No peer is identifiable.")

tab1, tab2 = st.tabs(["Benchmarking", "Inclusion"])
with tab1:
    bm = I.benchmark(lt, feats, inst)
    better_high = {"Agricultural credit growth, 12 months", "Women-owned borrowers", "Youth-owned borrowers", "First-time borrowers", "Micro and small borrowers",
                   "Structured products (not term loan or overdraft)", "Insured borrowers"}
    better_low = {"NPL ratio", "Average interest rate"}

    def verdict(row):
        d = row["Your institution"] - row["Market (other institutions)"]
        if row["Metric"] in better_high:
            return "Ahead" if d > 0 else "Behind"
        if row["Metric"] in better_low:
            return "Ahead" if d < 0 else "Behind"
        return "Different"
    bm["Position"] = bm.apply(verdict, axis=1)
    fmt = lambda m, v: U.kes(v) if "KES" in m else f"{v:.1%}"
    show = pd.DataFrame({"Metric": bm["Metric"], "Your institution": [fmt(m, v) for m, v in zip(bm["Metric"], bm["Your institution"])],
                         "Market": [fmt(m, v) for m, v in zip(bm["Metric"], bm["Market (other institutions)"])], "Position": bm["Position"]})
    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.dataframe(show.style.map(lambda v: "color:#1E7A50;font-weight:700" if v == "Ahead" else "color:#A3223A;font-weight:700" if v == "Behind" else "", subset=["Position"]),
                     hide_index=True, use_container_width=True, height=430)
    with c2:
        me = lt[lt["lender"] == inst].groupby("value_chain")["outstanding_kes"].sum()
        mk = lt[lt["lender"] != inst].groupby("value_chain")["outstanding_kes"].sum()
        sh = pd.DataFrame({"Your share of portfolio": me / me.sum(), "Market share of portfolio": mk / mk.sum()}).fillna(0).sort_values("Market share of portfolio")
        f = go.Figure()
        f.add_bar(y=sh.index, x=sh["Market share of portfolio"] * 100, orientation="h", name="Market", marker_color="#CFE0D5")
        f.add_bar(y=sh.index, x=sh["Your share of portfolio"] * 100, orientation="h", name=inst, marker_color=C.GREEN)
        f.update_layout(barmode="group", xaxis_title="% of agri SME portfolio")
        U.show(U.fig(f, 430, "Portfolio mix by value chain"))

    st.markdown("#### Market share and relative quality by value chain")
    rows = []
    for vc, d in lt.groupby("value_chain"):
        me_d, mk_d = d[d["lender"] == inst], d[d["lender"] != inst]
        ok = mk_d["lender"].nunique() >= C.AGGREGATION_MIN_INSTITUTIONS and len(mk_d) >= C.AGGREGATION_MIN_BORROWERS
        npl = lambda x: x.loc[x["dpd"] >= 90, "outstanding_kes"].sum() / max(1, x["outstanding_kes"].sum())
        seg = b["seg"]["chain"].set_index("value_chain").loc[vc]
        rows.append({"Value chain": vc, "Your market share": me_d["outstanding_kes"].sum() / d["outstanding_kes"].sum() if ok else np.nan,
                     "Your NPL": npl(me_d) if len(me_d) else np.nan, "Market NPL": npl(mk_d) if ok else np.nan, "Opportunity": seg["opportunity"], "Appetite": seg["quadrant"]})
    t = pd.DataFrame(rows)
    t["Action"] = np.select([(t["Your market share"] < 0.12) & t["Appetite"].isin(["Grow", "Grow with structure"]), (t["Your NPL"] > t["Market NPL"] + 0.03)],
                            ["Under-represented in a growth chain", "Quality worse than market: review underwriting"], "")
    st.dataframe(U.tint_cols(t.style.format({"Your market share": "{:.0%}", "Your NPL": "{:.1%}", "Market NPL": "{:.1%}", "Opportunity": "{:.0f}"}, na_rep="Suppressed"), ["Appetite"]),
                 hide_index=True, use_container_width=True)

with tab2:
    scope = st.radio("Scope", [inst, "Whole market"], horizontal=True, key="inc_scope")
    base = lt if scope == "Whole market" else lt[lt["lender"] == inst]
    apps = U.filt(b["data"]["applications"], cols=("value_chain", "county"))
    apps = apps if scope == "Whole market" else apps[apps["lender"] == inst]
    inc = I.inclusion(base, apps, b["months"][-6:])
    fit = b["fit"].loc[base.index]
    U.kpi_cards([
        dict(label="Access: women-owned share of borrowers", value=U.pct(inc["Women-owned"]["Share of borrowers"], 0), note=f"{U.pct(inc['Women-owned']['Share of credit'], 0)} of credit", accent=C.GREEN),
        dict(label="Affordability: average rate", value=U.pct(base["interest_rate"].mean()), note=f"Micro {U.pct(base.loc[base['size'] == 'Micro', 'interest_rate'].mean())}", accent=C.HARVEST),
        dict(label="Suitability: borrowers in a well-fitting product", value=U.pct(1 - fit["mismatch"].mean(), 0), accent=C.SKY),
        dict(label="Quality: NPL, first-time borrowers", value=U.pct(inc["First-time"]["NPL ratio"]), note=f"Others {U.pct(inc['First-time']['NPL ratio (others)'])}", accent=C.SOIL),
        dict(label="Resilience: insured or contracted", value=U.pct((base["insured"] | (base["contracted_sales_share"] >= 0.5)).mean(), 0), accent=C.LEAF),
    ])
    st.write("")
    rows = []
    for grp, m in inc.items():
        rows += [dict(Group=grp, Dimension="Access", Measure="Approval rate", Group_value=m["Approval rate"], Others=m["Approval rate (others)"]),
                 dict(Group=grp, Dimension="Access", Measure="Share of credit vs share of borrowers", Group_value=m["Share of credit"], Others=m["Share of borrowers"]),
                 dict(Group=grp, Dimension="Affordability", Measure="Average interest rate", Group_value=m["Average rate"], Others=m["Average rate (others)"]),
                 dict(Group=grp, Dimension="Quality", Measure="NPL ratio", Group_value=m["NPL ratio"], Others=m["NPL ratio (others)"])]
    inc_t = pd.DataFrame(rows)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        d = inc_t[inc_t["Measure"] == "Approval rate"]
        f = go.Figure()
        f.add_bar(x=d["Group"], y=d["Group_value"] * 100, name="Group", marker_color=C.GREEN, text=[f"{v:.0%}" for v in d["Group_value"]], textposition="outside")
        f.add_bar(x=d["Group"], y=d["Others"] * 100, name="Everyone else", marker_color="#CFE0D5", text=[f"{v:.0%}" for v in d["Others"]], textposition="outside")
        f.update_layout(barmode="group", yaxis=dict(title="Approval rate %", range=[0, 100]))
        U.show(U.fig(f, 340, "Approval rates, last 6 months"))
    with c2:
        show = inc_t.copy()
        show["Group value"] = show["Group_value"].map(lambda v: f"{v:.1%}")
        show["Comparison"] = show["Others"].map(lambda v: f"{v:.1%}")
        st.dataframe(show[["Group", "Dimension", "Measure", "Group value", "Comparison"]], hide_index=True, use_container_width=True, height=340)
        st.caption("For 'share of credit vs share of borrowers', the comparison column is the group's share of borrowers. Credit share below borrower share means smaller loans.")
    st.markdown("#### Reach by value chain")
    r = base.groupby("value_chain").agg(women=("women_owned", "mean"), youth=("youth_owned", "mean"), first=("first_time", "mean"), micro=("size", lambda s: (s == "Micro").mean())).reset_index()
    r = r.melt(id_vars="value_chain", var_name="Group", value_name="share")
    r["Group"] = r["Group"].map({"women": "Women-owned", "youth": "Youth-owned", "first": "First-time", "micro": "Micro enterprises"})
    f = px.bar(r, x="value_chain", y="share", color="Group", barmode="group", labels={"share": "Share of borrowers", "value_chain": ""})
    f.update_layout(yaxis_tickformat=".0%")
    U.show(U.fig(f, 380))
