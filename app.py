"""AgriFinance Intelligence Platform: monitor and drive access to finance for agricultural SMEs.

Run:  python -m streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="AgriFinance Intelligence Platform", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

from views import common  # noqa: E402

CSS = """
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1440px;}
.eyebrow {font-size: .74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #B7791F; margin-bottom: .1rem;}
h1.page-title {font-size: 1.85rem; font-weight: 800; margin: 0 0 .15rem 0; padding: 0; color: #12372A; letter-spacing: -.01em;}
p.page-sub {color: #5C6B63; font-size: .98rem; margin: 0 0 .9rem 0; max-width: 80ch;}
.kpi {background: #FFFFFF; border: 1px solid #E3E1D6; border-radius: 12px; padding: .85rem 1rem .8rem; height: 100%; box-shadow: 0 1px 2px rgba(18,55,42,.05);}
.kpi-label {font-size: .78rem; font-weight: 600; color: #5C6B63; margin-bottom: .2rem;}
.kpi-value {font-size: 1.5rem; font-weight: 700; color: #12372A; line-height: 1.2; font-variant-numeric: tabular-nums;}
.kpi-note {font-size: .8rem; font-weight: 600; margin-top: .25rem;}
.pill {display: inline-block; padding: .1rem .55rem; border-radius: 999px; font-size: .76rem; font-weight: 700; white-space: nowrap; margin-left: .3rem;}
.tile {background:#FFFFFF; border:1px solid #E3E1D6; border-radius:12px; padding:.7rem .9rem; margin-bottom:.55rem;}
.tile .t {font-weight:700; color:#12372A; font-size:.93rem; display:flex; justify-content:space-between; align-items:center; gap:.4rem;}
.tile .m {font-size:.84rem; color:#5C6B63; margin-top:.25rem;}
.decision {background:#FFF8E8; border:1px solid #F1DDA8; border-radius:12px; padding:.6rem 1rem; margin:.2rem 0 .9rem; color:#3B2F12; font-size:.92rem;}
.decision .lbl {font-size:.7rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#B7791F; margin-right:.6rem;}
.decision .who {font-size:.72rem; font-weight:700; color:#5C6B63; background:#FFFFFF; border:1px solid #F1DDA8; border-radius:999px; padding:.05rem .5rem;}
.dq {display:flex; flex-wrap:wrap; gap:.4rem 1.2rem; font-size:.78rem; color:#5C6B63; margin:.2rem 0 1rem; padding:.4rem .8rem; background:#EEF1EA; border-radius:10px;}
.dq b {color:#12372A; font-weight:700; margin-right:.25rem;}
.explain {background:#EAF4EE; border:1px solid #CFE5D8; border-radius:12px; padding:.9rem 1.1rem; color:#1D2B24;}
.headcard {background:#12372A; color:#FFFFFF; border-radius:14px; padding:1rem 1.25rem; margin-bottom:.8rem;}
.headcard .name {font-size:1.35rem; font-weight:800;}
.headcard .meta {color:#CFE0D5; font-size:.88rem; margin-top:.15rem;}
.persona {background:#FFFFFF; border:1px solid #E3E1D6; border-radius:12px; padding:.75rem .9rem; height:100%;}
.persona .r {font-weight:800; color:#12372A;} .persona .q {font-size:.84rem; color:#5C6B63; margin:.2rem 0 .3rem;} .persona .p {font-size:.8rem; font-weight:700; color:#1F6F4A;}
.sbar {margin:.15rem 0 .55rem;} .sbar .sl {display:flex; justify-content:space-between; font-size:.84rem; color:#1D2B24;}
.sbar .track {height:8px; background:#EEF1EA; border-radius:6px; overflow:hidden;} .sbar .track div {height:8px; border-radius:6px;}
.answer {background:#FFFFFF; border:1px solid #E3E1D6; border-left:4px solid #1F6F4A; border-radius:12px; padding:.9rem 1.1rem;}
.side-label {font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#CFE0D5; margin:.6rem 0 .2rem;}
[data-testid="stSidebarHeader"] img {height: 2.7rem; max-width: 100%;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

common.init_state()
b = common.bundle()
st.logo("static/logo.svg", size="large", icon_image="static/icon.svg")

P = {
    "home": st.Page("views/p_home.py", title="Home", icon=":material/home:", default=True),
    "overview": st.Page("views/p_overview.py", url_path="overview", title="Executive overview", icon=":material/space_dashboard:"),
    "ask": st.Page("views/p_ask.py", url_path="ask", title="Ask the platform", icon=":material/forum:"),
    "surveillance": st.Page("views/p_surveillance.py", url_path="surveillance", title="Market surveillance", icon=":material/radar:"),
    "flows": st.Page("views/p_flows.py", url_path="flows", title="Credit flows", icon=":material/account_tree:"),
    "chains": st.Page("views/p_chains.py", url_path="chains", title="Value chain explorer", icon=":material/agriculture:"),
    "geo": st.Page("views/p_geo.py", url_path="geo", title="Geographic intelligence", icon=":material/map:"),
    "gap": st.Page("views/p_gap.py", url_path="gap", title="Financing gap", icon=":material/stacked_bar_chart:"),
    "opportunity": st.Page("views/p_opportunity.py", url_path="opportunity", title="Opportunity finder", icon=":material/travel_explore:"),
    "fit": st.Page("views/p_fit.py", url_path="fit", title="Product fit", icon=":material/extension:"),
    "risk": st.Page("views/p_risk.py", url_path="risk", title="Risk and early warning", icon=":material/notifications_active:"),
    "climate": st.Page("views/p_climate.py", url_path="climate", title="Climate exposure", icon=":material/rainy:"),
    "scenario": st.Page("views/p_scenario.py", url_path="scenario", title="Scenario lab", icon=":material/science:"),
    "borrower": st.Page("views/p_borrower.py", url_path="borrower", title="Borrower intelligence", icon=":material/person_search:"),
    "benchmark": st.Page("views/p_benchmark.py", url_path="benchmark", title="Benchmarking and inclusion", icon=":material/diversity_3:"),
    "method": st.Page("views/p_method.py", url_path="method", title="Data and methodology", icon=":material/menu_book:"),
}
st.session_state["pages"] = P
nav = st.navigation({
    "Overview": [P["home"], P["overview"], P["ask"]],
    "Market": [P["surveillance"], P["flows"], P["chains"], P["geo"]],
    "Access to finance": [P["gap"], P["opportunity"], P["fit"]],
    "Risk": [P["risk"], P["climate"], P["scenario"], P["borrower"]],
    "Institution": [P["benchmark"], P["method"]],
}, expanded=True)
common.sidebar(b)
nav.run()
