import html

import numpy as np
import pandas as pd
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from aaip import surveillance as S
from views import common as U

b = U.bundle()
inst = st.session_state["institution"]
U.page_header("Ask the platform", "Plain-language questions answered from the data, with the numbers, the reasoning and where to go next. Answers are computed, not generated, so every figure can be traced.",
              "Overview")

seg_c, prev_c, cell, lt = b["seg"]["chain"], b["prev"]["chain"], U.visible_segments(b["seg"]["cell"]), b["latest"]


def a_grow():
    t = seg_c[seg_c["quadrant"].isin(["Grow", "Grow with structure"])].sort_values("opportunity", ascending=False).head(4)
    lines = [f"<b>{r.value_chain}</b>: opportunity {r.opportunity:.0f}, risk {r.risk_index:.0f}, gap {U.kes(r.gap_kes)}, NPL {r.npl:.1%}, main driver {I.drivers(seg_c.set_index('value_chain').loc[r.value_chain], 'opportunity', 1)[0][0].lower()}."
             for r in t.itertuples()]
    return "The strongest growth cases combine a large financing gap with manageable risk:", lines, "opportunity"


def a_risk():
    d = seg_c.set_index("value_chain")["risk_index"] - prev_c.set_index("value_chain")["risk_index"]
    d = d.sort_values(ascending=False).head(4)
    s = seg_c.set_index("value_chain")
    lines = [f"<b>{vc}</b>: risk index {s.loc[vc, 'risk_index']:.0f} ({v:+.0f} in 3 months); signals: {s.loc[vc, 'signal_list'] or 'none'}; NPL {s.loc[vc, 'npl']:.1%}." for vc, v in d.items()]
    red = cell[cell["ew_status"] == "Red"]
    lines.append(f"{len(red)} value chain and county segments are Red, with {U.kes(red['exposure_kes'].sum())} of exposure.")
    return "Risk has risen most over the last three months in:", lines, "risk"


def a_gap():
    g = b["gap"].groupby("county")[["gap_kes", "demand_kes", "formal_credit_kes"]].sum()
    g["pen"] = g["formal_credit_kes"] / g["demand_kes"]
    g = g.sort_values("gap_kes", ascending=False).head(5)
    lines = [f"<b>{c}</b>: gap {U.kes(r.gap_kes)}, credit meets {r.pen:.0%} of estimated demand." for c, r in g.iterrows()]
    return f"The total estimated gap is {U.kes(b['gap']['gap_kes'].sum())}. The largest county gaps are:", lines, "gap"


def a_rains():
    r = I.scenario(lt, C.SCENARIO_PRESETS["Failed long rains"])
    g = r.groupby("value_chain")[["el_base", "el_stress"]].sum()
    g = (g["el_stress"] - g["el_base"]).sort_values(ascending=False).head(3)
    lines = [f"Expected loss rises from {U.kes(r['el_base'].sum())} to {U.kes(r['el_stress'].sum())} ({r['el_stress'].sum() / r['el_base'].sum() - 1:+.0%}).",
             f"{r['affected'].mean():.0%} of performing borrowers see operating cash flow fall 30% or more.",
             "Largest increases: " + ", ".join(f"{vc} ({U.kes(v)})" for vc, v in g.items()) + "."]
    return "A long-rains failure (rainfall 35% below normal) would:", lines, "scenario"


def a_bench():
    bm = I.benchmark(lt, b["feats"], inst).set_index("Metric")
    g = bm.loc["Agricultural credit growth, 12 months"]
    n = bm.loc["NPL ratio"]
    s = bm.loc["Structured products (not term loan or overdraft)"]
    w = bm.loc["Women-owned borrowers"]
    lines = [f"Growth: {g.iloc[0]:.1%} versus market {g.iloc[1]:.1%}.", f"NPL: {n.iloc[0]:.1%} versus market {n.iloc[1]:.1%}.",
             f"Structured products: {s.iloc[0]:.0%} of borrowers versus {s.iloc[1]:.0%}.", f"Women-owned borrowers: {w.iloc[0]:.0%} versus {w.iloc[1]:.0%}."]
    return f"{inst} compared with other institutions combined:", lines, "benchmark"


def a_calls():
    m = lt[(lt["lender"] == inst) & lt["status"].isin(["Amber", "Red"])].sort_values("score", ascending=False)
    fr = b["fired"][b["fired"]["t"] == b["T"]]
    lines = []
    for r in m.head(5).itertuples():
        trig = fr[fr["borrower_id"] == r.borrower_id]["Trigger"].tolist()
        lines.append(f"<b>{r.business}</b> ({r.value_chain}, {r.county}): {r.status}, score {r.score:.0f}; {', '.join(trig[:2]) if trig else 'model probability rising'}.")
    return f"{inst} has {len(m)} borrowers on Amber or Red. Start with:", lines, "borrower"


def a_women():
    inc = I.inclusion(lt, b["data"]["applications"], b["months"][-6:])["Women-owned"]
    lines = [f"Women-owned SMEs are {inc['Share of borrowers']:.0%} of borrowers but {inc['Share of credit']:.0%} of credit, so loans are smaller.",
             f"Approval rate {inc['Approval rate']:.0%} versus {inc['Approval rate (others)']:.0%} for others.",
             f"NPL {inc['NPL ratio']:.1%} versus {inc['NPL ratio (others)']:.1%}: repayment does not justify a lower approval rate." if inc["NPL ratio"] <= inc["NPL ratio (others)"] else
             f"NPL {inc['NPL ratio']:.1%} versus {inc['NPL ratio (others)']:.1%}."]
    return "Across the market:", lines, "benchmark"


def a_fit():
    fit = b["fit"]
    mis = lt.join(fit[["best_product"]]).loc[fit["mismatch"]]
    top = mis.groupby("value_chain").size().sort_values(ascending=False).head(3)
    hist = b["feats"][b["feats"]["target_3m"].notna()]
    r1, r0 = hist.loc[hist["mismatch"] == 1, "target_3m"].mean(), hist.loc[hist["mismatch"] == 0, "target_3m"].mean()
    lines = [f"{fit['mismatch'].mean():.0%} of borrowers ({U.kes(lt.loc[fit['mismatch'], 'outstanding_kes'].sum())}) hold a product that scores 25+ points below the best fit.",
             "Most affected chains: " + ", ".join(f"{vc} ({n})" for vc, n in top.items()) + ".",
             f"Conventional products on long seasonal cycles deteriorate at {r1:.1%} a month versus {r0:.1%} for others.",
             f"The most common better structure is {mis['best_product'].value_counts().index[0].lower()}."]
    return "Product mismatch is concentrated and costly:", lines, "fit"


def a_climate():
    co = b["seg"]["county"].sort_values("climate_risk", ascending=False).head(5)
    lines = [f"<b>{r.county}</b>: climate risk {r.climate_risk:.0f}, last season rainfall {r.rain_season:+.0f}%, irrigation {r.irrigation:.0%}, exposure {U.kes(r.exposure_kes)}." for r in co.itertuples()]
    return "The counties with the highest climate risk to agri SME credit:", lines, "climate"


def a_env():
    ev = S.events()
    new = ev[ev["freshness"] == "New"]
    lines = [f"<b>{r.institution}</b> ({r.date_label}): {r.instrument}. Effect: {r.effect.lower()}." for r in new.itertuples()]
    return f"{len(new)} developments logged in the last 45 days:", lines, "surveillance"


Q = {
    "Which value chains should we grow next?": (a_grow, ["grow", "expand", "opportunit", "next", "where to lend"]),
    "Where is risk rising fastest?": (a_risk, ["risk", "rising", "deteriorat", "worse", "warning"]),
    "Which counties have the largest financing gap?": (a_gap, ["gap", "unmet", "demand", "underserved", "not reaching"]),
    "What would a failed long rains season cost?": (a_rains, ["drought", "rain", "scenario", "stress", "cost", "loss"]),
    f"How does {inst} compare with the market?": (a_bench, ["compare", "benchmark", "market share", "peer", "versus"]),
    "Which of my borrowers need a call this week?": (a_calls, ["call", "borrower", "watch", "client", "relationship"]),
    "Are women-owned SMEs getting fair access?": (a_women, ["women", "gender", "inclusion", "female", "youth"]),
    "Where are products mismatched to cash cycles?": (a_fit, ["product", "mismatch", "fit", "structure", "term loan", "overdraft"]),
    "What changed in the financing environment?": (a_env, ["guarantee", "dfi", "news", "partnership", "facility", "policy", "subsidy", "environment"]),
    "Which counties are climate hotspots?": (a_climate, ["climate", "hotspot", "county", "weather", "asal"]),
}

text = st.text_input("Ask a question", placeholder="For example: where is the financing gap largest?", key="ask_text")
match = None
if text:
    scores = {q: sum(k in text.lower() for k in kw) for q, (_, kw) in Q.items()}
    best = max(scores, key=scores.get)
    match = best if scores[best] > 0 else None
    if not match:
        st.warning("That question is not covered yet. Choose one of the guided questions below.")
st.markdown("**Or choose a guided question**")
cols = st.columns(3)
clicked = None
for i, q in enumerate(Q):
    if cols[i % 3].button(q, key=f"ask_{i}", use_container_width=True):
        clicked = q
if clicked:
    st.session_state["ask_q"] = clicked
q = clicked or match or st.session_state.get("ask_q") or list(Q)[0]
if q not in Q:
    q = list(Q)[0]
intro, lines, page = Q[q][0]()
st.write("")
st.markdown(f"<div class='answer'><div style='font-weight:800;color:#12372A;font-size:1.05rem;margin-bottom:.35rem'>{html.escape(q)}</div><p style='margin:.2rem 0 .4rem'>{intro}</p>"
            + "".join(f"<p style='margin:.25rem 0'>• {l}</p>" for l in lines) + "</div>", unsafe_allow_html=True)
st.page_link(st.session_state["pages"][page], label="See the full analysis", icon=":material/arrow_forward:")
st.caption(f"Data as at {U.month_label(b['month'])}. Simulated example data. Phase 2 adds a language model that routes free-text questions to these governed calculations.")
