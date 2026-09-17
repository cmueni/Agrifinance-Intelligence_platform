import html

import streamlit as st

from aaip import config as C
from views import common as U

b = U.bundle()
lt, seg, cl = b["latest"], b["seg"], b["data"]["climate"]
bal = lt["outstanding_kes"].sum()
npl = lt.loc[lt["dpd"] >= 90, "outstanding_kes"].sum() / bal
gap = b["gap"]["gap_kes"].sum()
pen = b["gap"]["formal_credit_kes"].sum() / b["gap"]["demand_kes"].sum()
ch = seg["chain"].set_index("value_chain")
co = seg["county"].set_index("county")
dry = co["rain_season"].idxmin()
top = ch["opportunity"].idxmax()
alerts = int(lt["status"].isin(["Amber", "Red"]).sum())
spark = ch["opportunity"].sort_values().to_numpy()
pts = " ".join(f"{i * 150 / (len(spark) - 1):.0f},{46 - (v - spark.min()) / max(1, spark.max() - spark.min()) * 40:.0f}" for i, v in enumerate(spark))

st.markdown(f"""
<style>
.hero {{position:relative; border-radius:22px; overflow:hidden; min-height:520px; margin:-.4rem 0 1.2rem;
  background:linear-gradient(90deg, rgba(12,40,30,.94) 0%, rgba(12,40,30,.82) 34%, rgba(12,40,30,.25) 62%, rgba(12,40,30,.05) 100%), url('app/static/hero.jpg') center 30%/cover no-repeat;}}
.hero::after {{content:""; position:absolute; inset:0; pointer-events:none;
  background-image:radial-gradient(rgba(242,193,78,.35) 1px, transparent 1.4px); background-size:22px 22px;
  -webkit-mask-image:linear-gradient(90deg, #000 0%, rgba(0,0,0,.55) 40%, transparent 70%); mask-image:linear-gradient(90deg, #000 0%, rgba(0,0,0,.55) 40%, transparent 70%);}}
.hero .copy {{position:relative; z-index:2; max-width:560px; padding:3.2rem 0 3rem 3rem; color:#fff;}}
.hero .kicker {{font-size:.76rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:#F2C14E;}}
.hero h1 {{font-size:2.9rem; line-height:1.08; font-weight:800; color:#fff; margin:.5rem 0 .9rem; padding:0; letter-spacing:-.02em;}}
.hero p {{font-size:1.06rem; line-height:1.55; color:#DDE9E1; margin:0 0 1.3rem;}}
.hero .facts {{display:flex; gap:1.1rem; flex-wrap:wrap;}}
.hero .facts div {{border-left:2px solid #F2C14E; padding-left:.7rem;}}
.hero .facts b {{display:block; font-size:1.3rem; color:#fff; font-weight:800; font-variant-numeric:tabular-nums;}}
.hero .facts span {{font-size:.78rem; color:#CFE0D5;}}
.chip {{position:absolute; z-index:3; background:rgba(255,255,255,.90); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,.7); border-radius:14px; padding:.6rem .85rem; box-shadow:0 10px 30px rgba(12,40,30,.25); color:#12372A; min-width:190px;}}
.chip .l {{font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:#5C6B63;}}
.chip .v {{font-size:1.2rem; font-weight:800; font-variant-numeric:tabular-nums;}}
.chip .n {{font-size:.76rem; color:#5C6B63;}}
.chip .dot {{display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:.35rem; vertical-align:middle;}}
.chip.c1 {{right:3%; top:8%;}} .chip.c2 {{right:24%; top:44%;}} .chip.c3 {{right:4%; bottom:9%;}}
.hero svg.link {{position:absolute; inset:0; width:100%; height:100%; z-index:1; pointer-events:none;}}
.step {{background:#fff; border:1px solid #E3E1D6; border-radius:14px; padding:1rem 1.1rem; height:100%;}}
.step .i {{width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-weight:800; color:#fff; margin-bottom:.55rem;}}
.step .t {{font-weight:800; color:#12372A; font-size:1rem;}} .step .d {{font-size:.88rem; color:#5C6B63; margin-top:.25rem;}}
.pub {{background:#fff; border:1px solid #E3E1D6; border-radius:14px; padding:.85rem 1rem; height:100%;}}
.pub b {{font-size:1.6rem; color:#12372A; font-weight:800;}} .pub div {{font-size:.86rem; color:#1D2B24;}} .pub span {{font-size:.74rem; color:#5C6B63;}}
@media (max-width: 900px) {{ .chip {{display:none;}} .hero .copy {{padding:2rem 1.4rem;}} .hero h1 {{font-size:2.1rem;}} }}
</style>
<div class="hero">
  <svg class="link" viewBox="0 0 1000 520" preserveAspectRatio="none">
    <path d="M560,430 C700,380 720,250 820,210 S930,120 980,90" fill="none" stroke="rgba(242,193,78,.75)" stroke-width="2" stroke-dasharray="6 6"/>
    <circle cx="820" cy="210" r="5" fill="#F2C14E"/><circle cx="980" cy="90" r="5" fill="#F2C14E"/><circle cx="560" cy="430" r="5" fill="#F2C14E"/>
  </svg>
  <div class="copy">
    <div class="kicker">Kenya · Agricultural SME finance</div>
    <h1>AgriFinance Intelligence Platform</h1>
    <p>Credit, climate and market data brought together by value chain, so that lenders, development partners and policymakers can see where agricultural SMEs are financed, where they are not, and where risk is building.</p>
    <div class="facts">
      <div><b>{html.escape(U.kes(bal))}</b><span>Agri SME credit tracked</span></div>
      <div><b>{html.escape(U.kes(gap))}</b><span>Estimated financing gap</span></div>
      <div><b>{pen:.0%}</b><span>Of demand met by formal credit</span></div>
    </div>
  </div>
  <div class="chip c1"><div class="l">Top opportunity</div><div class="v">{html.escape(top)}</div>
    <svg width="150" height="48" viewBox="0 0 150 50"><polyline points="{pts}" fill="none" stroke="#1F6F4A" stroke-width="2.5" stroke-linecap="round"/></svg>
    <div class="n">Opportunity score {ch.loc[top, 'opportunity']:.0f} of 100</div></div>
  <div class="chip c2"><div class="l">Climate signal</div><div class="v"><span class="dot" style="background:#D1344B"></span>{html.escape(dry)} {co.loc[dry, 'rain_season']:+.0f}%</div>
    <div class="n">Rainfall, last 6 months vs normal</div></div>
  <div class="chip c3"><div class="l">Early warning</div><div class="v"><span class="dot" style="background:#E0A100"></span>{alerts:,} borrowers</div>
    <div class="n">Amber or Red · market NPL {npl:.1%}</div></div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, _ = st.columns([1.1, 1.1, 1.1, 2.7])
c1.page_link(st.session_state["pages"]["overview"], label="Open the overview", icon=":material/space_dashboard:")
c2.page_link(st.session_state["pages"]["opportunity"], label="Find opportunities", icon=":material/travel_explore:")
c3.page_link(st.session_state["pages"]["ask"], label="Ask a question", icon=":material/forum:")

st.markdown("#### How the platform works")
steps = [
    (C.SKY, "1", "Data", "Loan tapes from reporting lenders, CBK and KNBS statistics, KMD rainfall, NDMA drought phases and KAMIS prices, checked and mapped to 12 value chains and 18 counties."),
    (C.HARVEST, "2", "Intelligence", "Transparent scores for credit, climate and market risk and for opportunity; financing gap estimates; borrower early warning; scenario testing."),
    (C.GREEN, "3", "Action", "Clear next steps by role: where to grow, which product to offer, which borrowers to call, and where guarantee or blended finance is needed."),
]
for col, (color, n, t, d) in zip(st.columns(3), steps):
    col.markdown(f"<div class='step'><div class='i' style='background:{color}'>{n}</div><div class='t'>{t}</div><div class='d'>{d}</div></div>", unsafe_allow_html=True)

st.markdown("#### Choose a starting point")
personas = [
    ("Head of Agribusiness", "Where to grow next", "opportunity", "Find opportunities"),
    ("Chief Risk Officer", "Chains and counties deteriorating", "risk", "Early warning"),
    ("Credit Manager", "Right product for the borrower", "fit", "Product fit"),
    ("Relationship Manager", "Clients who need a call", "borrower", "My borrowers"),
    ("CEO and Strategy", "Position against the market", "benchmark", "Benchmarks"),
    ("DFI and Government", "Where finance is not reaching", "gap", "Financing gap"),
]
for col, (role, q, key, label) in zip(st.columns(6), personas):
    with col:
        st.markdown(f"<div class='persona'><div class='r'>{role}</div><div class='q'>{q}</div></div>", unsafe_allow_html=True)
        st.page_link(st.session_state["pages"][key], label=label, icon=":material/arrow_forward:")

st.markdown("#### The context")
pubs = [("34%", "of farmers borrowed for farming", "CBK Agriculture Survey, July 2026"),
        ("78%", "of farmers rely on rain-fed production", "CBK Agriculture Survey, July 2026"),
        ("Over 85%", "of MSME lending is term loans and overdrafts", "CBK MSME Survey, December 2024"),
        ("19%", "of farmers who borrowed used buyers of produce", "CBK Agriculture Survey, July 2026")]
for col, (v, d, s) in zip(st.columns(4), pubs):
    col.markdown(f"<div class='pub'><b>{v}</b><div>{d}</div><span>{s}</span></div>", unsafe_allow_html=True)
st.caption("Published figures are cited. Loan, borrower and segment figures in this prototype are simulated.")
