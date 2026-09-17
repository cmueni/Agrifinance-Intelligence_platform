import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from views import common as U

b = U.bundle()
lt = U.filt(b["latest"])
U.page_header("Scenario lab", "Shock rainfall, prices, input costs, fuel, the policy rate and the exchange rate, and see how cash flows, default probability and expected loss respond by value chain and county.", "Risk")
U.decision("Size provisions and capital buffers, and decide where to pre-emptively restructure or pause growth.", "CRO, CEO and Strategy")

keys = ["rain", "price", "inputs", "fuel", "cbr", "fx"]
if "sc" not in st.session_state:
    st.session_state["sc"] = dict(C.SCENARIO_PRESETS["Failed long rains"])
    st.session_state["sc_preset"] = "Failed long rains"
    for k in keys:
        st.session_state[f"sc_{k}"] = st.session_state["sc"][k]


def apply_preset():
    p = C.SCENARIO_PRESETS[st.session_state["sc_preset"]]
    if p:
        for k in keys:
            st.session_state[f"sc_{k}"] = p[k]


def mark_custom():
    st.session_state["sc_preset"] = "Custom"


with st.container(border=True):
    c0, c1, c2, c3, c4, c5, c6 = st.columns([1.4, 1, 1, 1, 1, 1, 1])
    c0.selectbox("Scenario", list(C.SCENARIO_PRESETS), key="sc_preset", on_change=apply_preset)
    c1.slider("Rainfall vs normal %", -60, 60, key="sc_rain", step=5, on_change=mark_custom)
    c2.slider("Farm-gate prices %", -40, 30, key="sc_price", step=5, on_change=mark_custom)
    c3.slider("Input costs %", -10, 50, key="sc_inputs", step=5, on_change=mark_custom)
    c4.slider("Fuel price %", -10, 50, key="sc_fuel", step=5, on_change=mark_custom)
    c5.slider("CBR change, pp", -2.0, 4.0, key="sc_cbr", step=0.25, on_change=mark_custom)
    c6.slider("KES depreciation %", -10, 30, key="sc_fx", step=2, on_change=mark_custom)
shock = {k: st.session_state[f"sc_{k}"] for k in keys}
r = I.scenario(lt, shock)

el0, el1 = r["el_base"].sum(), r["el_stress"].sum()
aff = r["affected"]
U.kpi_cards([
    dict(label="Borrowers with cash flow down 30%+", value=f"{aff.sum():,}", note=f"{aff.mean():.0%} of performing borrowers", tone="bad" if aff.mean() > 0.2 else "warn", accent=C.RAG["Red"]),
    dict(label="Exposure affected", value=U.kes(r.loc[aff, "outstanding_kes"].sum()), note=f"{r.loc[aff, 'outstanding_kes'].sum() / r['outstanding_kes'].sum():.0%} of performing credit", accent=C.HARVEST),
    dict(label="12-month expected loss", value=U.kes(el1), note=f"Up {U.kes(el1 - el0)} ({el1 / el0 - 1:+.0%}) vs baseline", tone="bad", accent=C.SOIL),
    dict(label="Average 12-month PD", value=U.pct(r["pd12_stress"].mean()), note=f"Baseline {U.pct(r['pd12_base'].mean())}", tone="bad", accent=C.SKY),
    dict(label="Median cash-flow change", value=U.pct(r["cash_flow_change"].median(), 0, True), note="Operating cash flow", accent=C.GREEN),
])

st.markdown("#### How the shock transmits")
st.graphviz_chart("""
digraph { rankdir=LR; bgcolor=transparent; node [shape=box style="rounded,filled" fillcolor="#FFFFFF" color="#CFE0D5" fontname="Plus Jakarta Sans" fontsize=11]; edge [color="#9FB8A8"];
 rain [label="Rainfall shock\\n× chain climate sensitivity\\n× (1 − irrigation), halved if insured" fillcolor="#E3EDF6"];
 price [label="Price shock\\n× producer exposure" fillcolor="#FDF3D6"];
 cost [label="Input, fuel, FX, CBR\\n× actor cost shares" fillcolor="#FBE3E7"];
 rev [label="Revenue change"]; costs [label="Cost change"]; cf [label="Operating cash flow\\n(30% margin)" fillcolor="#E3F4EC"];
 pd [label="12-month PD\\nlog-odds + 3.0 × cash-flow fall"]; el [label="Expected loss\\nPD × LGD × exposure" fillcolor="#12372A" fontcolor="white"];
 rain -> rev; price -> rev; cost -> costs; rev -> cf; costs -> cf; cf -> pd; pd -> el; }
""", use_container_width=True)

c1, c2 = st.columns(2)
for col, key, label in ((c1, "value_chain", "value chain"), (c2, "county", "county")):
    g = r.groupby(key).agg(base=("el_base", "sum"), stress=("el_stress", "sum"), exp=("outstanding_kes", "sum")).reset_index()
    g["uplift"] = g["stress"] - g["base"]
    g = g.sort_values("uplift").tail(12)
    with col:
        f = go.Figure()
        f.add_bar(y=g[key], x=g["base"] / 1e6, orientation="h", name="Baseline EL", marker_color="#CFE0D5")
        f.add_bar(y=g[key], x=g["uplift"] / 1e6, orientation="h", name="Scenario uplift", marker_color=C.RAG["Red"])
        f.update_layout(barmode="stack", xaxis_title="KES M")
        U.show(U.fig(f, 420, f"Expected loss by {label}"))

st.markdown("#### Most affected segments")
s = r.groupby(["value_chain", "county"]).agg(borrowers=("borrower_id", "nunique"), institutions=("lender", "nunique"), exposure=("outstanding_kes", "sum"),
                                              affected=("affected", "mean"), cf=("cash_flow_change", "median"), el0=("el_base", "sum"), el1=("el_stress", "sum")).reset_index()
s = s[(s["borrowers"] >= C.AGGREGATION_MIN_BORROWERS) & (s["institutions"] >= C.AGGREGATION_MIN_INSTITUTIONS)]
s["uplift"] = s["el1"] - s["el0"]
s = s.sort_values("uplift", ascending=False).head(15)
t = s[["value_chain", "county", "borrowers", "exposure", "affected", "cf", "el0", "el1"]]
t.columns = ["Value chain", "County", "Borrowers", "Exposure", "Share affected", "Median cash-flow change", "EL baseline", "EL scenario"]
st.dataframe(t.style.format({"Exposure": lambda v: U.kes(v), "Share affected": "{:.0%}", "Median cash-flow change": "{:+.0%}", "EL baseline": lambda v: U.kes(v), "EL scenario": lambda v: U.kes(v)})
             .background_gradient(subset=["Share affected"], cmap="Reds", vmin=0, vmax=1), hide_index=True, use_container_width=True)
st.caption("Transmission elasticities are expert assumptions for illustration. Calibrate them to past droughts (for example 2016-17 and 2021-22) and price shocks before use in provisioning.")
