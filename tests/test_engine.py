"""Engine checks: data shape, score bounds, dictionary size, scenario monotonicity, suppression."""
import numpy as np
import pytest

from aaip import borrower_ews as E
from aaip import config as C
from aaip import dictionary as D
from aaip import intelligence as I
from aaip import simulate


@pytest.fixture(scope="module")
def run():
    data = simulate.build_all()
    feats, fired, model, perf = E.run(data)
    return data, feats, fired, model, perf


def test_dictionary_has_212_unique_variables():
    dd = D.data_dictionary()
    assert len(dd) == 212 and dd["Code"].is_unique and dd["Domain"].nunique() == 13


def test_model_beats_chance(run):
    perf = run[4]
    assert perf["auc"] > 0.7 and 0.05 < perf["alert_rate"] < 0.35


def test_scores_bounded_and_weights_sum_to_one(run):
    data, feats = run[0], run[1]
    for w in C.WEIGHTS.values():
        assert abs(sum(w.values()) - 1) < 1e-9
    s = I.segment_table(data, feats, int(feats["t"].max()), ("value_chain", "county"))
    for col in ["credit_risk", "climate_risk", "market_risk", "opportunity", "risk_index"]:
        assert s[col].between(0, 100).all()
    assert ((s["borrowers"] < C.AGGREGATION_MIN_BORROWERS) <= s["suppressed"]).all()


def test_scenario_worse_shock_raises_loss(run):
    feats = run[1]
    lt = feats[feats["t"] == feats["t"].max()]
    mild = I.scenario(lt, dict(rain=-10, price=0, inputs=0, cbr=0, fuel=0, fx=0))
    severe = I.scenario(lt, dict(rain=-40, price=-10, inputs=20, cbr=1, fuel=20, fx=10))
    assert severe["el_stress"].sum() > mild["el_stress"].sum() > mild["el_base"].sum() * 0.999
    neutral = I.scenario(lt, dict(rain=0, price=0, inputs=0, cbr=0, fuel=0, fx=0))
    assert np.isclose(neutral["el_stress"].sum(), neutral["el_base"].sum())


def test_gap_non_negative(run):
    g = I.financing_gap(run[0], run[1])
    assert (g["gap_kes"] >= 0).all() and g["penetration"].between(0, 1).all()


def test_surveillance_events_complete(run):
    from aaip import surveillance as S
    ev = S.events()
    assert ev["id"].is_unique and ev["url"].str.startswith("https://").all()
    assert set(ev["effect"]) <= set(S.EFFECTS) and set(ev["category"]) <= set(S.CATEGORIES)
    ft = S.follow_through(run[1])
    assert set(ft["id"]) <= set(ev["id"]) and ft["Outstanding"].gt(0).all()


def test_flood_scenario_raises_loss(run):
    feats = run[1]
    lt = feats[feats["t"] == feats["t"].max()]
    r = I.scenario(lt, C.SCENARIO_PRESETS["El Niño heavy rains and flooding"])
    assert r["el_stress"].sum() > r["el_base"].sum()
