# AgriFinance Intelligence Platform

A Streamlit prototype for monitoring and driving access to finance for agricultural SMEs in Kenya. The value chain is the core unit: every loan maps to one of 12 value chains, one of 7 actors (input supplier to exporter) and a county. The platform combines pooled lender data with climate, price and macro signals to answer seven questions:

| Layer | Question |
|---|---|
| Economy | Is the environment getting easier or harder for agri lending? |
| Value chains | Which chains are healthy, growing and under-financed? |
| Businesses | Who are the SMEs and what financing structure fits them? |
| Credit | Where does credit flow and how does it perform? |
| Risk | What is deteriorating, and why? |
| Market surveillance | What is changing outside the data that affects financing? |
| Action | What should each role do next? |

> **All loan, borrower, application and segment data is simulated.** Published statistics (CBR, CPI, exchange rate, CBK Agriculture Survey and MSME Survey figures) are labelled with their source.

## Run locally

```bash
cd agrifinance-intelligence-platform
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The first load builds the data and models (about 10 seconds), then pages are cached.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and push the folder contents (app.py must be at the repository root).
2. On share.streamlit.io choose **Create app**, select the repository, branch `main`, main file `app.py`.
3. Deploy. The `.streamlit/config.toml` theme and bundled fonts in `static/` load automatically.

## Screens

| Group | Screen | Decision it supports |
|---|---|---|
| Overview | Home | Landing page: photo with live data highlights, how the platform works, starting point by role |
| | Executive overview | Sector appetite; persona "start here"; what changed; top opportunities and emerging risks |
| | Ask the platform | Guided questions answered from governed calculations |
| Market | Market surveillance | Structured log of guarantees, DFI facilities, bank products, policy, CBK decisions and climate outlooks; effect chain, lender action, follow-through tracking |
| | Credit flows | Lender type → value chain → actor, product or county; approvals and decline reasons |
| | Value chain explorer | Scorecard, score drivers, chain structure, prices and costs, recommended lender focus |
| | Geographic intelligence | County map, county profile, rainfall and vegetation |
| Access to finance | Financing gap | Demand vs formal credit by chain, county and actor, with confidence |
| | Opportunity finder | Ranked segments, opportunity vs risk quadrant, lead product and target actors |
| | Product fit | Constraint → finance solution; mismatch evidence; borrower recommendations |
| Risk | Risk and early warning | Segment signals with driver and action; borrower watchlist with triggers |
| | Climate exposure | Rainfall anomalies, drought phases, climate risk by chain, uninsured exposure |
| | Scenario lab | Rain, price, input, fuel, CBR and FX shocks → cash flow → PD → expected loss |
| | Borrower intelligence | Agri SME 360: model contributions, triggers, product fit, actions |
| Institution | Benchmarking and inclusion | Your institution vs market (suppressed aggregates); access, affordability, suitability, quality, resilience |
| | Data and methodology | Architecture, 212-variable dictionary, sources, scores, validation, governance, roadmap |

## Method in brief

- **Scores** (0 to 100, weighted components with stated anchors):
  - Credit risk: portfolio quality 30, borrower behaviour 20, leverage 15, cash-flow stress 15, concentration 10, recent deterioration 10.
  - Climate risk: exposure 30, historical volatility 25, current anomaly 20, seasonal outlook 15, adaptive capacity gap 10.
  - Market risk: price volatility 30, price trend 20, input-cost pressure 20, buyer concentration 15, export and FX 15.
  - Opportunity: financing gap 25, credit growth 20, demand growth 15, portfolio quality 15, market growth 10, borrower growth 10, product suitability 5.
  - Risk index = 0.45 credit + 0.30 climate + 0.25 market. Segments with fewer than 30 borrowers are shrunk toward the average.
- **Appetite quadrant**: Grow (opportunity ≥ 60, risk < 30), Grow with structure (opportunity ≥ 60), Selective (risk < 35), Tighten and monitor.
- **Segment early warning**: seven signals (price, rainfall, vegetation, margin squeeze, sales vs last season, PAR30 change, NPL change); Amber at 2, Red at 3+.
- **Borrower early warning**: 11 trigger rules plus a logistic model of 30+ DPD or restructure within 3 months, trained out of time. Sales are compared with the same months last year so harvest seasonality does not cause false alarms. Score = 0.65 model points + 0.35 trigger points.
- **Financing gap** = estimated demand (enterprises × turnover × cash-cycle and investment need) − observed credit ÷ 60% market coverage.
- **Scenario lab**: shocks transmit through chain climate sensitivity, irrigation, insurance and actor cost shares to operating cash flow, then to 12-month PD (log-odds) and expected loss (PD × LGD × exposure).
- **Governance**: public, restricted, confidential and highly confidential tiers; market cells suppressed below 3 institutions or 10 borrowers.

## Structure

```
app.py                  navigation, theme CSS
aaip/config.py          taxonomy, counties, lenders, products, weights, thresholds, scenarios, published statistics
aaip/simulate.py        macro, climate, market, borrower panel, applications, enterprise universe (simulated)
aaip/borrower_ews.py    borrower features, trigger rules, model, validation
aaip/intelligence.py    segment scores, financing gap, product fit, scenarios, benchmarking, inclusion, what changed
aaip/surveillance.py   verified development event log, effect tagging, follow-through tracker
aaip/dictionary.py      212-variable data dictionary, sources, taxonomy, governance, roadmap
views/                  one file per screen, plus common.py helpers
docs/                   CSV exports of the dictionary, sources, rules, taxonomy, governance, roadmap
tests/                  engine checks and page smoke and interaction tests (pytest)
```

Run the tests with `python -m pytest -q`.

## Limitations

- Weights, thresholds and scenario elasticities are expert starting points. Calibrate them on real outcomes, including at least one drought season, before use.
- Demand is modelled, and the example enterprise universe only covers segments where some lending exists.
- County-level climate data masks farm-level variation; plot-level monitoring is a Phase 3 capability.
- Market coverage (60%) is assumed and must be measured against CBK sectoral credit data.

## Sources for published figures

- Central Bank of Kenya, Agriculture Sector Survey (July 2026): share of farmers borrowing, sources of farmer credit, reliance on rain-fed production.
- Central Bank of Kenya, MSME Survey (December 2024): product mix and collateral requirements in MSME lending.
- Central Bank of Kenya: Central Bank Rate and exchange rate. Kenya National Bureau of Statistics: CPI inflation.
- Kenya Bankers Association, State of the Banking Industry Report 2025: sector context.
