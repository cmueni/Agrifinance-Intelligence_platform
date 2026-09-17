"""Smoke test: every page renders without an exception."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(p.name for p in (ROOT / "views").glob("p_*.py"))


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=240)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    at.switch_page(f"views/{page}").run()
    assert not at.exception, [e.value for e in at.exception]


def _app():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=240)
    at.run()
    return at


def test_ask_every_question():
    at = _app()
    at.switch_page("views/p_ask.py").run()
    for i in range(10):
        at.button(key=f"ask_{i}").click().run()
        assert not at.exception, (i, [e.value for e in at.exception])
    at.text_input(key="ask_text").input("where is the financing gap largest").run()
    assert not at.exception


def test_filters_and_institution_on_all_pages():
    at = _app()
    at.selectbox(key="institution").select("SACCO 01").run()
    at.multiselect(key="f_vc").select("Dairy").run()
    at.multiselect(key="f_county").select("Nakuru").run()
    for page in PAGES:
        at.switch_page(f"views/{page}").run()
        assert not at.exception, (page, [e.value for e in at.exception])


def test_scenario_presets():
    at = _app()
    at.switch_page("views/p_scenario.py").run()
    for preset in ["Commodity price slump", "Input and fuel cost spike", "Monetary tightening", "Combined drought and cost shock"]:
        at.selectbox(key="sc_preset").select(preset).run()
        assert not at.exception, (preset, [e.value for e in at.exception])
    at.slider(key="sc_rain").set_value(-50).run()
    assert not at.exception and at.selectbox(key="sc_preset").value == "Custom"


def test_chain_and_county_selectors():
    at = _app()
    at.switch_page("views/p_chains.py").run()
    for vc in ["Maize", "Beef and livestock", "Fisheries and aquaculture", "Tea"]:
        at.selectbox(key="vc_select").select(vc).run()
        assert not at.exception, (vc, [e.value for e in at.exception])
    at.switch_page("views/p_geo.py").run()
    for c in ["Nairobi", "Kilifi", "Narok"]:
        at.selectbox(key="geo_county").select(c).run()
        assert not at.exception, (c, [e.value for e in at.exception])
