"""Shared UI helpers: cached engine run, filters, formatting, cards, pills, decision boxes and chart styling."""
from __future__ import annotations

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from aaip import borrower_ews as E
from aaip import config as C
from aaip import intelligence as I
from aaip import simulate

TINT = {
    "Green": ("#E3F4EC", "#1E7A50"), "Amber": ("#FDF3D6", "#7A5700"), "Red": ("#FBE3E7", "#A3223A"), "NPL": ("#E6E9EE", "#2D3748"),
    "Grow": ("#E3F4EC", "#1E7A50"), "Grow with structure": ("#FCEFD6", "#8A5A00"), "Selective": ("#E3EDF6", "#2F5F86"),
    "Tighten and monitor": ("#FBE3E7", "#A3223A"), "High": ("#E3F4EC", "#1E7A50"), "Medium": ("#FDF3D6", "#7A5700"), "Low": ("#FBE3E7", "#A3223A"),
    "Critical": ("#FBE3E7", "#A3223A"), "Normal": ("#E3F4EC", "#1E7A50"), "Alert": ("#FDF3D6", "#7A5700"), "Alarm": ("#FBE3E7", "#A3223A"),
    "Public": ("#E3F4EC", "#1E7A50"), "Restricted": ("#E3EDF6", "#2F5F86"), "Confidential": ("#FDF3D6", "#7A5700"), "Highly confidential": ("#FBE3E7", "#A3223A"),
    "MVP": ("#E3F4EC", "#1E7A50"), "Phase 2": ("#FDF3D6", "#7A5700"), "Phase 3": ("#E3EDF6", "#2F5F86"),
}

pio.templates["agri"] = go.layout.Template(layout=dict(
    font=dict(family=C.FONT, size=13, color=C.INK),
    colorway=[C.GREEN, C.HARVEST, C.SKY, C.SOIL, C.LEAF, "#D1344B", "#7B4FC9", "#6B8E23", "#B5651D", "#4A5568", "#2A9D8F", "#E76F51"],
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor=C.GRID, zerolinecolor=C.GRID, linecolor=C.GRID),
    yaxis=dict(gridcolor=C.GRID, zerolinecolor=C.GRID, linecolor=C.GRID),
    hoverlabel=dict(font=dict(family=C.FONT)), margin=dict(l=8, r=8, t=76, b=8),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
    title=dict(font=dict(size=15, color=C.INK), x=0, xanchor="left", y=0.985, yanchor="top", yref="container"),
))
pio.templates.default = "plotly+agri"


# --------------------------------------------------------------------------- #
# Engine run (cached once per server)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Building market data, borrower early warning and value-chain intelligence...")
def bundle() -> dict:
    data = simulate.build_all()
    feats, fired, model, perf = E.run(data)
    T = int(feats["t"].max())
    seg = {name: I.segment_table(data, feats, T, keys) for name, keys in (("chain", ("value_chain",)), ("county", ("county",)), ("cell", ("value_chain", "county")))}
    prev = {name: I.segment_table(data, feats, T - 3, keys) for name, keys in (("chain", ("value_chain",)), ("county", ("county",)))}
    latest = feats[feats["t"] == T].copy()
    crisk = latest.merge(seg["cell"][["value_chain", "county", "climate_risk"]], on=["value_chain", "county"], how="left")["climate_risk"]
    crisk.index = latest.index
    fit = I.product_fit(latest, crisk.fillna(50))
    months = sorted(feats["month"].unique())
    return dict(data=data, feats=feats, fired=fired, model=model, perf=perf, T=T, month=months[-1], months=months, seg=seg, prev=prev,
                latest=latest, fit=fit, gap=I.financing_gap(data, feats))


def month_label(m: str) -> str:
    return pd.Period(m, "M").strftime("%B %Y")


# --------------------------------------------------------------------------- #
# Sidebar and filters
# --------------------------------------------------------------------------- #
def init_state():
    ss = st.session_state
    ss.setdefault("institution", "Bank 01")
    ss.setdefault("filters", {})


def sidebar(b: dict):
    with st.sidebar:
        st.markdown("<div class='side-label'>Your institution</div>", unsafe_allow_html=True)
        st.selectbox("Institution", list(C.LENDERS), key="institution", label_visibility="collapsed",
                     help="Your own loan-level data is visible to you. Other institutions appear only as market aggregates.")
        st.markdown("<div class='side-label'>Market filters</div>", unsafe_allow_html=True)
        f = {}
        f["value_chain"] = st.multiselect("Value chain", list(C.VALUE_CHAINS), key="f_vc", placeholder="All value chains")
        f["county"] = st.multiselect("County", list(C.COUNTIES), key="f_county", placeholder="All counties")
        f["lender_type"] = st.multiselect("Lender type", sorted({v[0] for v in C.LENDERS.values()}), key="f_lt", placeholder="All lender types")
        st.session_state["filters"] = f
        n = sum(bool(v) for v in f.values())
        st.caption(f"Data as at **{month_label(b['month'])}**  \nSimulated example data" + (f"  \n{n} filter(s) applied" if n else ""))


def filt(df: pd.DataFrame, cols=("value_chain", "county", "lender_type")) -> pd.DataFrame:
    for col, vals in st.session_state.get("filters", {}).items():
        if vals and col in df.columns and col in cols:
            df = df[df[col].isin(vals)]
    return df


def active_filters() -> str:
    f = st.session_state.get("filters", {})
    parts = [", ".join(v) for v in f.values() if v]
    return " · ".join(parts) if parts else "Whole market"


# --------------------------------------------------------------------------- #
# Formatting and components
# --------------------------------------------------------------------------- #
def kes(x, digits: int = 1) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    a = abs(x)
    if a >= 1e9:
        return f"KES {x / 1e9:,.{digits}f}bn"
    if a >= 1e6:
        return f"KES {x / 1e6:,.{0 if a >= 1e8 else digits}f}M"
    if a >= 1e3:
        return f"KES {x / 1e3:,.0f}K"
    return f"KES {x:,.0f}"


def pct(x, digits: int = 1, signed: bool = False) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x * 100:+.{digits}f}%" if signed else f"{x * 100:.{digits}f}%"


def pill(label: str, key: str | None = None) -> str:
    bg, fg = TINT.get(key or label, ("#EEF1EA", "#1D2B24"))
    return f"<span class='pill' style='background:{bg};color:{fg}'>{html.escape(str(label))}</span>"


def page_header(title: str, subtitle: str, eyebrow: str | None = None):
    eb = f"<div class='eyebrow'>{html.escape(eyebrow)}</div>" if eyebrow else ""
    st.markdown(f"{eb}<h1 class='page-title'>{html.escape(title)}</h1><p class='page-sub'>{html.escape(subtitle)}</p>", unsafe_allow_html=True)


def decision(text: str, who: str | None = None):
    w = f"<span class='who'>{html.escape(who)}</span>" if who else ""
    st.markdown(f"<div class='decision'><span class='lbl'>Decision this supports</span>{w}<div>{html.escape(text)}</div></div>", unsafe_allow_html=True)


def quality(source: str, updated: str, coverage: str, confidence: str):
    st.markdown(
        f"<div class='dq'><span><b>Source</b> {html.escape(source)}</span><span><b>Updated</b> {html.escape(updated)}</span>"
        f"<span><b>Coverage</b> {html.escape(coverage)}</span><span><b>Confidence</b> {pill(confidence)}</span></div>", unsafe_allow_html=True)


def kpi_cards(items: list[dict], columns: int | None = None):
    """items: dict(label, value, note, tone in {None,'good','bad','warn'}, help, accent)."""
    cols = st.columns(columns or len(items))
    for col, it in zip(cols, items):
        tone = {"good": "#1E7A50", "bad": "#A3223A", "warn": "#7A5700"}.get(it.get("tone"), C.MUTED)
        note = f"<div class='kpi-note' style='color:{tone}'>{html.escape(it.get('note', ''))}</div>" if it.get("note") else ""
        style = f" style='border-top:3px solid {it['accent']}'" if it.get("accent") else ""
        col.markdown(f"<div class='kpi'{style} title='{html.escape(it.get('help', ''))}'><div class='kpi-label'>{html.escape(it['label'])}</div>"
                     f"<div class='kpi-value'>{html.escape(str(it['value']))}</div>{note}</div>", unsafe_allow_html=True)


def tile(title: str, body: str, tone: str = "Green", tag: str | None = None):
    color = {"Green": C.RAG["Green"], "Amber": C.RAG["Amber"], "Red": C.RAG["Red"]}.get(tone, C.SKY)
    t = pill(tag, tone) if tag else ""
    st.markdown(f"<div class='tile' style='border-left:4px solid {color}'><div class='t'>{html.escape(title)}{t}</div>"
                f"<div class='m'>{html.escape(body)}</div></div>", unsafe_allow_html=True)


def tint_cols(styler, cols):
    def fmt(v):
        if isinstance(v, str) and v in TINT:
            bg, fg = TINT[v]
            return f"background-color:{bg};color:{fg};font-weight:600"
        return ""
    return styler.map(fmt, subset=[c for c in cols if c in styler.data.columns])


def fig(f, height=340, title=None, **kw):
    f.update_layout(height=height, title=title, **kw)
    if not title and "margin" not in kw:
        f.update_layout(margin=dict(t=40))
    return f


def show(f, **kw):
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False}, **kw)


def visible_segments(seg: pd.DataFrame) -> pd.DataFrame:
    """Market aggregates shown only where enough institutions and borrowers contribute."""
    return seg[~seg["suppressed"]]


def score_bar(label: str, value: float, color: str):
    v = 0 if pd.isna(value) else float(value)
    st.markdown(f"<div class='sbar'><div class='sl'>{html.escape(label)}<b>{v:.0f}</b></div><div class='track'><div style='width:{v:.0f}%;background:{color}'></div></div></div>",
                unsafe_allow_html=True)
