import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from aaip import surveillance as S
from views import common as U

b = U.bundle()
feats, T, data = b["feats"], b["T"], b["data"]
lt = U.filt(b["latest"])
ly = U.filt(feats[feats["t"] == T - 12])

U.page_header("Agricultural SME Credit Overview", f"{U.active_filters()} · {U.month_label(b['month'])}. Credit, risk and financing gaps across value chains, based on pooled lender data with climate, price and macroeconomic indicators.",
              "Executive overview")

bal = lt["outstanding_kes"].sum()
npl = lt.loc[lt["dpd"] >= 90, "outstanding_kes"].sum() / bal
npl_ly = ly.loc[ly["dpd"] >= 90, "outstanding_kes"].sum() / ly["outstanding_kes"].sum()
growth = bal / ly["outstanding_kes"].sum() - 1
gap = U.filt(b["gap"])
apps = U.filt(data["applications"])
apps3 = apps[apps["month"].isin(b["months"][-3:])]
alerts = lt["status"].isin(["Amber", "Red"])
U.kpi_cards([
    dict(label="Agri SME credit outstanding", value=U.kes(bal), note=f"{growth:+.1%} in 12 months", tone="good" if growth > 0 else "bad", accent=C.GREEN),
    dict(label="NPL ratio", value=U.pct(npl), note=f"{(npl - npl_ly) * 100:+.1f} pp in 12 months", tone="bad" if npl > npl_ly else "good", accent=C.RAG["Red"]),
    dict(label="Estimated financing gap", value=U.kes(gap["gap_kes"].sum()), note=f"Credit meets {gap['formal_credit_kes'].sum() / gap['demand_kes'].sum():.0%} of demand", tone="warn", accent=C.HARVEST),
    dict(label="Approval rate, 3 months", value=U.pct(apps3["approved"].mean(), 0), note=f"{len(apps3):,} applications", accent=C.SKY),
    dict(label="Borrowers on early warning", value=f"{alerts.sum():,}", note=f"{U.kes(lt.loc[alerts, 'outstanding_kes'].sum())} exposure", tone="warn", accent=C.RAG["Amber"]),
])
U.quality("Pooled loan tapes (12 institutions), KMD, NDMA, KAMIS, CBK, KNBS", U.month_label(b["month"]), "Est. 60% of formal agri SME credit", "Medium")

st.write("")
st.markdown("#### Financing environment: latest developments")
_ev = S.events()
_ev = _ev[_ev["freshness"] == "New"].head(4)
for _col, (_, _r) in zip(st.columns(4), _ev.iterrows()):
    with _col:
        U.tile(f"{_r['event_type']}: {_r['institution'][:38]}", f"{_r['date_label']}. {_r['effect']}. {_r['action']}", _r["tone"])
st.page_link(st.session_state["pages"]["surveillance"], label="Open market surveillance", icon=":material/radar:")
st.write("")
c1, c2, c3 = st.columns([1.05, 1, 1])
with c1:
    st.markdown("#### What changed in the last 3 months")
    for it in I.what_changed(b["seg"]["chain"], b["prev"]["chain"], data["market"], data["climate"], b["month"]):
        U.tile(it["title"], it["detail"], it["tone"])
cell = U.visible_segments(U.filt(b["seg"]["cell"]))
with c2:
    st.markdown("#### Top growth opportunities")
    top = cell[cell["quadrant"].isin(["Grow", "Grow with structure"])].sort_values("opportunity", ascending=False).head(5)
    for _, r in top.iterrows():
        d = ", ".join(k.lower() for k, _ in I.drivers(r, "opportunity", 2))
        U.tile(f"{r['value_chain']} · {r['county']}", f"Opportunity {r['opportunity']:.0f}, risk {r['risk_index']:.0f}. Gap {U.kes(r['gap_kes'])}. Drivers: {d}.", "Green", r["quadrant"])
with c3:
    st.markdown("#### Emerging risks")
    risky = cell.sort_values(["signals", "risk_index"], ascending=False).head(5)
    for _, r in risky.iterrows():
        tone = r["ew_status"] if r["ew_status"] != "Green" else "Amber"
        U.tile(f"{r['value_chain']} · {r['county']}", f"{r['signals']} signals: {r['signal_list'] or 'none'}. Exposure {U.kes(r['exposure_kes'])}, NPL {U.pct(r['npl'])}.", tone, r["ew_status"])

st.markdown("#### Value chain scorecard")
U.decision("Set sector appetite: grow, grow with structure, lend selectively, or tighten and monitor, by value chain.", "Head of Agribusiness, CRO")
ch = U.filt(b["seg"]["chain"], cols=("value_chain",))
tbl = pd.DataFrame({
    "Value chain": ch["value_chain"], "Exposure": ch["exposure_kes"] / 1e6, "Borrowers": ch["borrowers"].astype(int),
    "Growth 12m": (ch["exposure_kes"] / ch["exposure_12"] - 1) * 100, "NPL": ch["npl"] * 100, "Financing gap": ch["gap_kes"] / 1e6,
    "Opportunity": ch["opportunity"], "Risk": ch["risk_index"], "Appetite": ch["quadrant"], "Early warning": ch["ew_status"],
}).sort_values("Opportunity", ascending=False)
sty = tbl.style.format({"Exposure": "{:,.0f}M", "Growth 12m": "{:+.1f}%", "NPL": "{:.1f}%", "Financing gap": "{:,.0f}M", "Opportunity": "{:.0f}", "Risk": "{:.0f}"})
sty = U.tint_cols(sty, ["Appetite", "Early warning"]).background_gradient(subset=["Opportunity"], cmap="Greens", vmin=20, vmax=90).background_gradient(subset=["Risk"], cmap="Reds", vmin=5, vmax=60)
st.dataframe(sty, hide_index=True, use_container_width=True, height=(len(tbl) + 1) * 35 + 3)

st.markdown("#### Market context")
cols = st.columns(len(C.MACRO_CURRENT))
for col, (k, v, s) in zip(cols, C.MACRO_CURRENT):
    col.markdown(f"<div class='kpi'><div class='kpi-label'>{html.escape(k)}</div><div class='kpi-value' style='font-size:1.2rem'>{v}</div>"
                 f"<div class='kpi-note' style='color:{C.MUTED}'>{html.escape(s)}</div></div>", unsafe_allow_html=True)
st.caption("Market context figures are published statistics. All loan, borrower and segment figures on this platform are simulated for demonstration.")
