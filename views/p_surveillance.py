import html

import pandas as pd
import streamlit as st

from aaip import config as C
from aaip import intelligence as I
from aaip import surveillance as S
from views import common as U

b = U.bundle()
ev = S.events()
U.page_header("Market Surveillance", "Developments that change the financing environment for agricultural SMEs: guarantees, DFI facilities, bank products, policy, monetary decisions, climate outlooks and market infrastructure. Each event is structured, sourced and linked to the data that tests its effect.",
              "Market")
U.decision("Decide where new risk-sharing, funding or policy changes justify expanding lending, redesigning a product or tightening exposure.", "Head of Agribusiness, CRO, CEO and Strategy, DFI")
U.quality("Official announcements and press reports, checked against the source", pd.Timestamp(S.AS_OF).strftime("%d %B %Y"), f"{len(ev)} events logged, 2021 to 2026", "High")

live = ev[~ev["status"].isin(["Historical", "Completed"])]
capacity = live[live["category"].isin(["Finance", "DFIs", "Banks"]) & ~live["id"].isin(["E04"])]["amount_kes"].sum()
U.kpi_cards([
    dict(label="New in the last 45 days", value=int((ev["freshness"] == "New").sum()), note="Events logged", accent=C.GREEN),
    dict(label="Lending capacity announced", value=U.kes(capacity), note="Active guarantee and DFI facilities with a Kenya amount", accent=C.HARVEST,
         help="RK-FINFA leveraged lending, IFC first-loss programme and EBRD credit line. Regional facilities without a Kenya allocation are excluded."),
    dict(label="Active risk-sharing instruments", value=int((live["effect"] == "Risk sharing up").sum()), note="Guarantees and first-loss cover", accent=C.SKY),
    dict(label="Risk and funding alerts", value=int(live["tone"].eq("Red").sum()), note="Climate and donor funding", tone="bad", accent=C.RAG["Red"]),
])
st.write("")

# --------------------------------------------------------------------------- #
st.markdown("#### Briefing: what changed")
recent = ev[ev["freshness"] == "New"]
chg = I.what_changed(b["seg"]["chain"], b["prev"]["chain"], b["data"]["market"], b["data"]["climate"], b["month"])
groups = {
    "Finance": recent[recent["category"].isin(["Finance", "DFIs", "Banks"])],
    "Policy": recent[recent["category"].isin(["Policy", "Monetary", "Market infrastructure"])],
    "Climate": recent[recent["category"] == "Climate"],
}
cols = st.columns(4)
for col, (name, g) in zip(cols, groups.items()):
    with col:
        st.markdown(f"**{name}**")
        for r in g.itertuples():
            U.tile(r.institution if len(r.institution) < 40 else r.event_type, f"{r.date_label}: {r.instrument}", r.tone)
with cols[3]:
    st.markdown("**Markets and portfolio (platform data)**")
    for it in chg[:4]:
        U.tile(it["title"], it["detail"], it["tone"])
st.markdown(
    "<div class='explain'><b>Implication.</b> Risk-sharing capacity has increased: nationwide R-CGS coverage, the IFC first-loss programme and the EBRD credit line "
    "lower the cost of lending to rural, women-owned and green SMEs. Cheaper fertiliser reduces working-capital needs for crop farmers ahead of the short rains. "
    "The above-average rainfall outlook improves prospects in dry counties but raises flood and post-harvest loss risk; loans maturing November to January in "
    "low-lying areas warrant review. Commitments linked to terminated USAID programmes should not be counted as current supply.</div>", unsafe_allow_html=True)
st.write("")

# --------------------------------------------------------------------------- #
st.markdown("#### Event log")
c1, c2, c3, c4 = st.columns([2.6, 1.2, 1.2, 1.2])
with c1:
    cat = st.segmented_control("Category", ["All"] + S.CATEGORIES, default="All", key="sv_cat") or "All"
status = c2.multiselect("Status", ["Announced", "Active", "Completed", "Historical"], default=["Announced", "Active"], key="sv_status")
vc = c3.selectbox("Value chain", ["Any"] + list(C.VALUE_CHAINS), key="sv_vc")
q = c4.text_input("Search", key="sv_q", placeholder="e.g. guarantee, KCB")
v = ev
if cat != "All":
    v = v[v["category"] == cat]
if status:
    v = v[v["status"].isin(status)]
if vc != "Any":
    v = v[v["value_chains"].map(lambda x: vc in x or "All" in x)]
if q:
    v = v[v.apply(lambda r: q.lower() in " ".join(str(r[k]) for k in ("institution", "partner", "instrument", "event_type", "target", "note")).lower(), axis=1)]
st.caption(f"{len(v)} of {len(ev)} events shown.")


def card(r):
    color = {"Green": C.RAG["Green"], "Amber": C.RAG["Amber"], "Red": C.RAG["Red"]}[r["tone"]]
    faded = "opacity:.72;" if r["status"] in ("Historical", "Completed") else ""
    who = html.escape(r["institution"]) + (f" <span style='color:#5C6B63;font-weight:600'>with {html.escape(r['partner'])}</span>" if r["partner"] else "")
    amt = f"<div class='sv-amt'>{html.escape(U.kes(r['amount_kes']))}</div>" if pd.notna(r["amount_kes"]) else ""
    chain = "<span class='sv-arrow'>→</span>".join(f"<span class='sv-step'>{html.escape(s)}</span>" for s in r["chain"])
    note = f"<div class='sv-note'>{html.escape(r['note'])}</div>" if isinstance(r.get("note"), str) and r["note"] else ""
    new = U.pill("New", "Green") if r["freshness"] == "New" else ""
    return (f"<div class='sv-card' style='border-top:4px solid {color};{faded}'>"
            f"<div class='sv-top'><span>{U.pill(r['category'], 'Restricted')}{U.pill(r['effect'], r['tone'])}{new}</span><span class='sv-date'>{r['date_label']}</span></div>"
            f"<div class='sv-type'>{html.escape(r['event_type'])}</div><div class='sv-who'>{who}</div>{amt}"
            f"<div class='sv-inst'>{html.escape(r['instrument'])}</div>"
            f"<div class='sv-meta'><b>Target</b> {html.escape(r['target'])} · <b>Value chains</b> {html.escape(r['value_chains_text'])} · <b>Geography</b> {html.escape(r['geography'])}</div>"
            f"<div class='sv-chain'>{chain}</div>"
            f"<div class='sv-act'><b>Lender action</b> {html.escape(r['action'])}</div>"
            f"<div class='sv-act'><b>Platform monitors</b> {html.escape(r['monitor'])}</div>{note}"
            f"<div class='sv-src'>Source: <a href='{html.escape(r['url'])}' target='_blank'>{html.escape(r['source'])}</a> · Confidence {html.escape(r['confidence'])} · Status {html.escape(r['status'])}</div></div>")


st.markdown("""<style>
.sv-card {background:#fff; border:1px solid #E3E1D6; border-radius:14px; padding:.85rem 1rem; margin-bottom:.9rem;}
.sv-top {display:flex; justify-content:space-between; align-items:center;} .sv-top .pill:first-child {margin-left:0;}
.sv-date {font-size:.8rem; color:#5C6B63; font-weight:600;}
.sv-type {font-size:.72rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; color:#B7791F; margin-top:.5rem;}
.sv-who {font-size:1.05rem; font-weight:800; color:#12372A;} .sv-amt {font-size:1.3rem; font-weight:800; color:#1F6F4A; font-variant-numeric:tabular-nums;}
.sv-inst {font-size:.9rem; color:#1D2B24; margin:.2rem 0 .35rem;} .sv-meta {font-size:.8rem; color:#5C6B63;}
.sv-chain {display:flex; flex-wrap:wrap; align-items:center; gap:.3rem; margin:.6rem 0; }
.sv-step {background:#EEF1EA; border-radius:8px; padding:.2rem .5rem; font-size:.78rem; color:#12372A;} .sv-arrow {color:#B7791F; font-weight:800;}
.sv-act {font-size:.84rem; color:#1D2B24; margin-top:.2rem;} .sv-act b {color:#12372A;}
.sv-note {font-size:.78rem; color:#7A5700; background:#FFF8E8; border-radius:8px; padding:.3rem .5rem; margin-top:.45rem;}
.sv-src {font-size:.76rem; color:#5C6B63; margin-top:.5rem;} .sv-src a {color:#1F6F4A; font-weight:700;}
</style>""", unsafe_allow_html=True)
left, right = st.columns(2)
for i, (_, r) in enumerate(v.iterrows()):
    (left if i % 2 == 0 else right).markdown(card(r), unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
st.markdown("#### Follow-through: is lending moving where announcements point?")
st.caption("Compares 6-month credit growth in the segment each announcement targets with the whole market. Figures use the platform's simulated loan data until lender tapes are connected.")
ft = S.follow_through(b["feats"]).merge(ev[["id", "institution", "event_type"]], on="id")
t = ft[["event_type", "institution", "Tracked", "Borrowers", "Outstanding", "Growth", "Market", "Signal"]]
t.columns = ["Event", "Institution", "Segment tracked", "Borrowers", "Outstanding", "Growth, 6 months", "Market growth", "Signal"]
st.dataframe(t.style.format({"Outstanding": lambda x: U.kes(x), "Growth, 6 months": "{:+.1%}", "Market growth": "{:+.1%}"})
             .map(lambda s: "color:#1E7A50;font-weight:700" if s == "Moving ahead of market" else "color:#A3223A;font-weight:700" if s == "Lagging market" else "", subset=["Signal"]),
             hide_index=True, use_container_width=True)

with st.expander("Event database and method"):
    st.markdown("""
- **Scope.** Financial-sector developments (guarantees, DFI lines, risk-sharing, bank products), government and regulatory action (subsidies, CBK decisions, AFC, trade measures),
  market infrastructure (warehouse receipts, commodity exchanges), climate outlooks, and funding risks.
- **Sources.** CBK, National Treasury, Ministry of Agriculture, AFA, KMSA, NDMA, county governments, DFI press rooms (IFC, EBRD, AfDB, IFAD, AFD, EIB), bank announcements, and established news outlets.
- **Verification.** Every event is checked against the primary announcement where available. Amounts are recorded as published; USD is converted at KES 129.4. Regional facilities without a Kenya allocation carry no KES amount.
- **Confidence.** High: primary source or official statement. Medium: press report without a primary document, or a figure that is a performance total rather than a new commitment.
- **Status.** Announced, Active, Completed, or Historical. Commitments tied to programmes that have since ended are marked Historical and excluded from capacity totals.
- **Next phase.** Automated collection from official feeds and press rooms, with language-model extraction into these fields and analyst approval before publication.
""")
    st.download_button("Download event log (CSV)", S.export().to_csv(index=False).encode(), "market_surveillance_events.csv", "text/csv", icon=":material/download:")
    st.dataframe(S.export()[["id", "date_label", "category", "event_type", "institution", "partner", "amount_kes", "effect", "status", "confidence", "source"]],
                 hide_index=True, use_container_width=True)
