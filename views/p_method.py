import pandas as pd
import plotly.express as px
import streamlit as st

from aaip import borrower_ews as E
from aaip import config as C
from aaip import dictionary as D
from aaip import intelligence as I
from views import common as U

b = U.bundle()
perf = b["perf"]
U.page_header("Data and methodology", "How the platform is built: architecture, the 212-variable data dictionary, sources, taxonomy, scoring formulas, governance, validation, roadmap and limitations.",
              "Institution")
st.warning("All loan, borrower, application and segment data in this prototype is simulated. Published statistics are labelled with their source. Do not use outputs for lending decisions until the platform runs on real data and the models are validated.")

tabs = st.tabs(["Architecture", "Data dictionary", "Sources and taxonomy", "Scores", "Model validation", "Governance", "Roadmap and limitations"])

with tabs[0]:
    st.markdown("#### Seven layers, one question each")
    st.graphviz_chart("""
digraph { rankdir=LR; bgcolor=transparent; node [shape=box style="rounded,filled" fontname="Plus Jakarta Sans" fontsize=11 color="#CFE0D5" fillcolor="#FFFFFF"]; edge [color="#9FB8A8"];
 subgraph cluster_src { label="Data sources"; fontname="Plus Jakarta Sans"; color="#E3E1D6";
   lend [label="Lender loan tapes\\nand applications"]; pub [label="CBK, KNBS\\nmacro and surveys"]; clim [label="KMD, CHIRPS, NDMA\\nsatellite"]; mkt [label="KAMIS, AFA, KDB\\nprices and production"]; alt [label="Bureau, mobile money\\noff-takers (Phase 2-3)"]; news [label="Announcements and news\\nCBK, Treasury, DFIs, banks"]; }
 surv [label="Market surveillance\\nevent log, effects, follow-through" fillcolor="#FDF3D6"];
 ing [label="Ingest and validate\\nquality checks, taxonomy mapping\\npseudonymisation" fillcolor="#EEF1EA"];
 core [label="Value-chain data model\\nchain × county × actor × month" fillcolor="#E3F4EC"];
 eng [label="Engines\\nscores, financing gap, early warning\\nproduct fit, scenarios, benchmarks" fillcolor="#FDF3D6"];
 gov [label="Governance\\naccess tiers, suppression\\naudit, consent" fillcolor="#FBE3E7"];
 ui [label="Decision views\\n16 screens by persona\\nask the platform" fillcolor="#12372A" fontcolor="white"];
 lend -> ing; pub -> ing; clim -> ing; mkt -> ing; alt -> ing; ing -> core -> eng -> gov -> ui; news -> surv -> eng; }
""", use_container_width=True)
    layers = pd.DataFrame([
        ("Economy", "Is the environment getting easier or harder for agri lending?", "CBR, inflation, FX, fuel, fertiliser", "Executive overview"),
        ("Value chains", "Which chains are healthy, growing and under-financed?", "Prices, costs, production, credit, gaps", "Value chain explorer, Financing gap"),
        ("Businesses", "Who are the SMEs and what do they need?", "Actor, size, cash cycle, contracts, inclusion", "Product fit, Benchmarking and inclusion"),
        ("Credit", "Where does credit flow and how does it perform?", "Balances, arrears, approvals, products", "Credit flows, Geographic intelligence"),
        ("Risk", "What is deteriorating and why?", "Signals, climate, scenarios, borrower triggers", "Risk and early warning, Climate, Scenario lab"),
        ("Market surveillance", "What is changing outside the data that affects financing?", "Guarantees, DFI facilities, bank products, policy, CBK, climate outlooks", "Market surveillance, Executive overview"),
        ("Action", "What should each role do next?", "Quadrants, recommendations, watchlists", "Opportunity finder, Borrower intelligence, Ask"),
    ], columns=["Layer", "Question", "Data", "Screens"])
    st.dataframe(layers, hide_index=True, use_container_width=True)
    st.markdown("**Design rule:** no chart without a decision. Every screen states the decision it supports and the data quality behind it (source, date, coverage, confidence).")

with tabs[1]:
    dd = D.data_dictionary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Variables", len(dd))
    c2.metric("Domains", dd["Domain"].nunique())
    c3.metric("Populated in prototype", int(dd["In prototype"].sum()))
    c4.metric("MVP variables", int((dd["Phase"] == "MVP").sum()))
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.2])
    dom = c1.multiselect("Domain", list(D.DOMAINS.values()), key="dd_dom", placeholder="All domains")
    ph = c2.multiselect("Phase", ["MVP", "Phase 2", "Phase 3"], key="dd_phase", placeholder="All phases")
    tier = c3.multiselect("Access tier", ["Public", "Restricted", "Confidential", "Highly confidential"], key="dd_tier", placeholder="All tiers")
    q = c4.text_input("Search", key="dd_q", placeholder="e.g. rainfall, NPL")
    v = dd
    if dom:
        v = v[v["Domain"].isin(dom)]
    if ph:
        v = v[v["Phase"].isin(ph)]
    if tier:
        v = v[v["Access"].isin(tier)]
    if q:
        v = v[v.apply(lambda r: q.lower() in (r["Variable"] + r["Definition"] + r["Source"]).lower(), axis=1)]
    st.dataframe(U.tint_cols(v.style, ["Access", "Phase"]), hide_index=True, use_container_width=True, height=460)
    st.download_button("Download data dictionary (CSV)", dd.to_csv(index=False).encode(), "agrifinance_data_dictionary.csv", "text/csv", icon=":material/download:")
    cnt = dd.groupby(["Domain", "Phase"]).size().reset_index(name="Variables")
    f = px.bar(cnt, x="Variables", y="Domain", color="Phase", orientation="h", color_discrete_map={"MVP": C.GREEN, "Phase 2": C.HARVEST, "Phase 3": C.SKY})
    U.show(U.fig(f, 380, "Variables by domain and delivery phase"))

with tabs[2]:
    st.markdown("#### Data sources")
    st.dataframe(U.tint_cols(D.SOURCES.style, ["Access", "Phase"]), hide_index=True, use_container_width=True)
    st.markdown("#### Value-chain taxonomy")
    tx = D.TAXONOMY.copy()
    tx["Cash cycle (days)"] = tx["Value chain"].map(lambda v: C.VALUE_CHAINS[v]["cycle"])
    tx["Climate sensitivity"] = tx["Value chain"].map(lambda v: C.VALUE_CHAINS[v]["climate"])
    tx["Export share"] = tx["Value chain"].map(lambda v: f"{C.VALUE_CHAINS[v]['export']:.0%}")
    tx["Storable"] = tx["Value chain"].map(lambda v: "Yes" if C.VALUE_CHAINS[v]["storable"] else "No")
    st.dataframe(tx, hide_index=True, use_container_width=True)
    st.markdown("Actors: " + ", ".join(C.ACTORS) + ". Every loan maps to one value chain, one actor and one county.")
    st.markdown("#### Published statistics used")
    st.dataframe(pd.DataFrame(C.MACRO_CURRENT, columns=["Indicator", "Value", "Source"]), hide_index=True, use_container_width=True)

with tabs[3]:
    st.markdown("Every score is a weighted sum of 0 to 100 components, each scaled linearly between stated anchors. Any score can be decomposed into its drivers.")
    names = {"credit_risk": "Credit risk", "climate_risk": "Climate risk", "market_risk": "Market risk", "opportunity": "Opportunity"}
    cols = st.columns(4)
    for col, (k, n) in zip(cols, names.items()):
        with col:
            st.markdown(f"**{n}**")
            st.dataframe(pd.DataFrame({"Component": list(C.WEIGHTS[k]), "Weight": [f"{w:.0%}" for w in C.WEIGHTS[k].values()]}), hide_index=True, use_container_width=True)
    q = C.QUADRANT_CUTS
    st.markdown(f"""
- **Risk index** = {C.RISK_BLEND['credit_risk']:.2f} × credit + {C.RISK_BLEND['climate_risk']:.2f} × climate + {C.RISK_BLEND['market_risk']:.2f} × market.
- **Appetite quadrant**: Grow if opportunity ≥ {q['opportunity']} and risk < {q['grow_risk']}; Grow with structure if opportunity ≥ {q['opportunity']}; Selective if risk < {q['selective_risk']}; otherwise Tighten and monitor.
- **Credibility weighting**: segments with fewer than {C.CREDIBILITY_BORROWERS} borrowers are pulled toward the average score in proportion to borrowers ÷ {C.CREDIBILITY_BORROWERS}, so that a handful of loans cannot top a ranking.
- **Segment early warning**: Amber at {C.EW_THRESHOLDS['Amber']} adverse signals, Red at {C.EW_THRESHOLDS['Red']} or more.
- **Confidence**: High with 30+ borrowers, Medium with 10 to 29, Low below 10. **Suppression**: fewer than {C.AGGREGATION_MIN_INSTITUTIONS} institutions or {C.AGGREGATION_MIN_BORROWERS} borrowers.
- **Financing gap** = demand − observed credit ÷ {I.MARKET_COVERAGE:.0%} market coverage. **Scenario**: cash-flow change → 12-month PD via log-odds (+{C.CASHFLOW_TO_LOGODDS} per 100% fall) → expected loss = PD × LGD × exposure.
""")
    st.markdown("**Loss given default assumptions by collateral**")
    st.dataframe(pd.DataFrame({"Collateral": list(I.LGD), "LGD": [f"{v:.0%}" for v in I.LGD.values()]}), hide_index=True)

with tabs[4]:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("AUC (out of time)", f"{perf['auc']:.3f}")
    c2.metric("Precision", f"{perf['precision']:.0%}", help="Share of Amber or Red borrowers who reach 30+ DPD or restructure within 3 months")
    c3.metric("Recall", f"{perf['recall']:.0%}")
    c4.metric("Alert rate", f"{perf['alert_rate']:.0%}", help=f"Base rate of events {perf['base_rate']:.1%} a month")
    c5.metric("Flagged before 30 DPD", f"{perf['detected_before_30']:.0%}", help=f"{perf['events']} events; {perf['share_90d']:.0%} flagged 90+ days ahead")
    co = perf["coefficients"].sort_values("coefficient")
    f = px.bar(co, x="coefficient", y="label", orientation="h", color=co["coefficient"] > 0, color_discrete_map={True: C.RAG["Red"], False: C.GREEN},
               labels={"coefficient": "Standardised coefficient (red raises risk)", "label": ""})
    f.update_layout(showlegend=False)
    U.show(U.fig(f, 460, "Borrower model: what drives 3-month deterioration"))
    st.caption(f"Trained on months 1 to {E.TRAIN_END}, tested on months {E.TEST[0]} to {E.TEST[1]}. On real data, validate by value chain, lender type and season, and monitor stability monthly.")

with tabs[5]:
    st.dataframe(U.tint_cols(D.GOVERNANCE.style, ["Tier"]), hide_index=True, use_container_width=True)
    st.markdown("""
- Institutions see their own borrowers by name and the market only as aggregates.
- Aggregates are suppressed below minimum institution and borrower counts, and dominance checks apply before release.
- Borrower identifiers are pseudonymised; statement and bureau data require recorded consent under the Data Protection Act, 2019.
- Model changes follow a register: version, validation results, approver, date.
""")

with tabs[6]:
    st.dataframe(D.ROADMAP, hide_index=True, use_container_width=True)
    st.markdown("""
#### MVP definition
One or two lenders' monthly loan tapes mapped to 12 value chains, 7 actors and counties; public climate, price and macro feeds; the executive overview, value chain explorer,
financing gap, risk and early warning, scenario lab and borrower watchlist; transparent scores with documented weights; data quality metadata on every screen.

#### Limitations
- Data is simulated. Score weights, thresholds and scenario elasticities are expert starting points, not calibrated estimates.
- Financing demand is modelled from enterprise counts and turnover; the enterprise universe here only includes segments where some lending exists, so fully unserved segments are missing.
- Market coverage is assumed at 60%. Real coverage must be measured against CBK sectoral credit data.
- County climate data is an average; farm-level exposure differs, which Phase 3 plot monitoring addresses.
- The borrower model uses 12 months of training history; production use needs several seasons, including a drought year.
""")
