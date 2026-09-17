"""Configuration: value-chain taxonomy, geography, lenders, products, score weights, scenarios and colours.

All thresholds and weights are starting points to be validated against historical outcomes
before the platform informs lending decisions.
"""
from __future__ import annotations

AS_OF = "2026-08-31"
HISTORY_MONTHS = 24
N_BORROWERS = 3200

# --------------------------------------------------------------------------- #
# Colours
# --------------------------------------------------------------------------- #
FOREST = "#12372A"
GREEN = "#1F6F4A"
LEAF = "#3E9B6C"
HARVEST = "#D99A1E"
SOIL = "#8A5A2B"
SKY = "#3F7CAC"
INK = "#1D2B24"
MUTED = "#5C6B63"
GRID = "rgba(92,107,99,0.15)"
FONT = "Plus Jakarta Sans, Segoe UI, Arial, sans-serif"
RAG = {"Green": "#2E9E6A", "Amber": "#E0A100", "Red": "#D1344B", "NPL": "#4A5568"}
QUADRANT_COLORS = {"Grow": "#2E9E6A", "Grow with structure": "#D99A1E", "Selective": "#3F7CAC", "Tighten and monitor": "#D1344B"}

# --------------------------------------------------------------------------- #
# Geography (county centroid, agro-ecological profile)
# --------------------------------------------------------------------------- #
COUNTIES = {
    # name: (lat, lon, ASAL, irrigation share, region)
    "Nairobi": (-1.29, 36.82, False, 0.30, "Nairobi"),
    "Kiambu": (-1.03, 36.83, False, 0.18, "Central"),
    "Murang'a": (-0.72, 37.15, False, 0.12, "Central"),
    "Nyeri": (-0.42, 36.95, False, 0.12, "Central"),
    "Meru": (0.05, 37.65, False, 0.15, "Eastern"),
    "Machakos": (-1.52, 37.27, True, 0.08, "Eastern"),
    "Makueni": (-2.26, 37.89, True, 0.06, "Eastern"),
    "Nakuru": (-0.30, 36.07, False, 0.22, "Rift Valley"),
    "Narok": (-1.08, 35.87, True, 0.05, "Rift Valley"),
    "Kericho": (-0.37, 35.28, False, 0.04, "Rift Valley"),
    "Uasin Gishu": (0.52, 35.27, False, 0.04, "Rift Valley"),
    "Trans Nzoia": (1.02, 35.00, False, 0.04, "Rift Valley"),
    "Kajiado": (-1.85, 36.78, True, 0.10, "Rift Valley"),
    "Bungoma": (0.57, 34.56, False, 0.03, "Western"),
    "Kakamega": (0.28, 34.75, False, 0.03, "Western"),
    "Kisumu": (-0.09, 34.77, False, 0.12, "Nyanza"),
    "Homa Bay": (-0.53, 34.46, False, 0.05, "Nyanza"),
    "Kilifi": (-3.63, 39.85, True, 0.05, "Coast"),
}

# --------------------------------------------------------------------------- #
# Value-chain taxonomy
# --------------------------------------------------------------------------- #
ACTORS = ["Input supplier", "Producer", "Cooperative", "Aggregator", "Processor", "Exporter", "Distributor"]

# climate: sensitivity of cash flow to rainfall (0-1); storable: suits warehouse receipts
# price_vol: monthly price volatility; input: main cost driver; export: export dependence (0-1)
# harvest: peak inflow months; cycle: working-capital cycle (days); wc_share: working capital as share of turnover
VALUE_CHAINS = {
    "Dairy": dict(l2="Livestock", climate=0.45, storable=False, price_vol=0.025, input="Animal feed", export=0.05, harvest=[4, 5, 11, 12],
                  cycle=45, npl=0.10, growth=0.07, penetration=0.40, actors={"Producer": 0.35, "Cooperative": 0.20, "Aggregator": 0.10, "Processor": 0.20, "Distributor": 0.10, "Input supplier": 0.05},
                  counties={"Nakuru": 3, "Kiambu": 3, "Nyeri": 2, "Murang'a": 2, "Uasin Gishu": 2, "Meru": 2, "Kericho": 1, "Nairobi": 1}),
    "Maize": dict(l2="Food crops", climate=0.85, storable=True, price_vol=0.06, input="Fertiliser", export=0.0, harvest=[8, 9, 10],
                  cycle=150, npl=0.18, growth=0.02, penetration=0.30, actors={"Producer": 0.45, "Aggregator": 0.25, "Processor": 0.15, "Input supplier": 0.10, "Distributor": 0.05},
                  counties={"Trans Nzoia": 3, "Uasin Gishu": 3, "Nakuru": 2, "Bungoma": 2, "Kakamega": 1, "Narok": 2, "Machakos": 1, "Makueni": 1}),
    "Tea": dict(l2="Cash crops", climate=0.35, storable=True, price_vol=0.035, input="Fertiliser", export=0.90, harvest=[3, 4, 5, 10, 11, 12],
                cycle=60, npl=0.09, growth=0.01, penetration=0.55, actors={"Producer": 0.30, "Cooperative": 0.30, "Processor": 0.25, "Exporter": 0.15},
                counties={"Kericho": 3, "Nyeri": 2, "Murang'a": 2, "Meru": 2, "Kiambu": 1, "Kakamega": 1}),
    "Coffee": dict(l2="Cash crops", climate=0.55, storable=True, price_vol=0.05, input="Fertiliser", export=0.95, harvest=[10, 11, 12, 1],
                   cycle=120, npl=0.16, growth=0.03, penetration=0.35, actors={"Producer": 0.30, "Cooperative": 0.35, "Processor": 0.20, "Exporter": 0.15},
                   counties={"Kiambu": 3, "Murang'a": 3, "Nyeri": 2, "Meru": 2, "Machakos": 1, "Bungoma": 1}),
    "Horticulture": dict(l2="Horticulture", climate=0.50, storable=False, price_vol=0.045, input="Fertiliser", export=0.60, harvest=list(range(1, 13)),
                         cycle=60, npl=0.12, growth=0.09, penetration=0.35, actors={"Producer": 0.35, "Aggregator": 0.25, "Exporter": 0.20, "Processor": 0.10, "Input supplier": 0.10},
                         counties={"Nakuru": 3, "Kiambu": 2, "Meru": 2, "Machakos": 2, "Kajiado": 2, "Nairobi": 1, "Murang'a": 1}),
    "Avocado and macadamia": dict(l2="Horticulture", climate=0.45, storable=False, price_vol=0.05, input="Fertiliser", export=0.80, harvest=[3, 4, 5, 6],
                                  cycle=90, npl=0.11, growth=0.12, penetration=0.22, actors={"Producer": 0.35, "Aggregator": 0.25, "Processor": 0.15, "Exporter": 0.25},
                                  counties={"Murang'a": 3, "Meru": 2, "Kiambu": 2, "Nyeri": 1, "Kakamega": 1}),
    "Pulses": dict(l2="Food crops", climate=0.80, storable=True, price_vol=0.055, input="Fertiliser", export=0.10, harvest=[2, 3, 7, 8],
                   cycle=120, npl=0.17, growth=0.05, penetration=0.18, actors={"Producer": 0.45, "Aggregator": 0.35, "Processor": 0.10, "Distributor": 0.10},
                   counties={"Makueni": 3, "Machakos": 3, "Meru": 2, "Bungoma": 1, "Kakamega": 1, "Homa Bay": 1}),
    "Sugarcane": dict(l2="Cash crops", climate=0.55, storable=False, price_vol=0.03, input="Fertiliser", export=0.0, harvest=list(range(1, 13)),
                      cycle=240, npl=0.24, growth=-0.01, penetration=0.30, actors={"Producer": 0.50, "Cooperative": 0.15, "Processor": 0.25, "Input supplier": 0.10},
                      counties={"Kakamega": 3, "Bungoma": 2, "Kisumu": 2, "Homa Bay": 1}),
    "Edible oils": dict(l2="Industrial crops", climate=0.60, storable=True, price_vol=0.04, input="Fuel", export=0.05, harvest=[7, 8, 9],
                        cycle=120, npl=0.14, growth=0.06, penetration=0.20, actors={"Producer": 0.35, "Aggregator": 0.25, "Processor": 0.30, "Distributor": 0.10},
                        counties={"Narok": 2, "Trans Nzoia": 2, "Kilifi": 2, "Homa Bay": 1}),
    "Beef and livestock": dict(l2="Livestock", climate=0.60, storable=False, price_vol=0.035, input="Animal feed", export=0.15, harvest=list(range(1, 13)),
                               cycle=180, npl=0.19, growth=0.04, penetration=0.15, actors={"Producer": 0.40, "Aggregator": 0.30, "Processor": 0.20, "Distributor": 0.10},
                               counties={"Narok": 3, "Kajiado": 3, "Makueni": 2, "Machakos": 1, "Kilifi": 2, "Nakuru": 1}),
    "Poultry": dict(l2="Livestock", climate=0.20, storable=False, price_vol=0.03, input="Animal feed", export=0.0, harvest=list(range(1, 13)),
                    cycle=50, npl=0.13, growth=0.10, penetration=0.25, actors={"Producer": 0.45, "Input supplier": 0.20, "Processor": 0.15, "Distributor": 0.20},
                    counties={"Kiambu": 3, "Nairobi": 2, "Nakuru": 2, "Machakos": 2, "Kakamega": 1, "Kisumu": 1}),
    "Fisheries and aquaculture": dict(l2="Blue economy", climate=0.30, storable=False, price_vol=0.04, input="Fuel", export=0.25, harvest=list(range(1, 13)),
                                      cycle=60, npl=0.21, growth=0.06, penetration=0.12, actors={"Producer": 0.40, "Aggregator": 0.30, "Processor": 0.20, "Distributor": 0.10},
                                      counties={"Kisumu": 3, "Homa Bay": 3, "Kilifi": 2, "Kakamega": 1}),
}

SIZES = {"Micro": (0.45, 12.2), "Small": (0.38, 14.1), "Medium": (0.17, 16.0)}   # share, log loan size mean
ACTOR_SIZE_UPLIFT = {"Input supplier": 0.6, "Producer": 0.0, "Cooperative": 0.9, "Aggregator": 0.5, "Processor": 1.4, "Exporter": 1.6, "Distributor": 0.6}

LENDERS = {
    # name: (type, market share weight, base rate)
    "Bank 01": ("Tier 1 bank", 0.20, 0.145), "Bank 02": ("Tier 1 bank", 0.14, 0.150), "Bank 03": ("Tier 1 bank", 0.10, 0.150),
    "Bank 04": ("Tier 2 bank", 0.08, 0.160), "Bank 05": ("Tier 2 bank", 0.07, 0.165), "Bank 06": ("Tier 3 bank", 0.05, 0.175),
    "MFB 01": ("Microfinance bank", 0.07, 0.220), "MFB 02": ("Microfinance bank", 0.04, 0.230),
    "SACCO 01": ("SACCO", 0.09, 0.140), "SACCO 02": ("SACCO", 0.06, 0.145),
    "DFI 01": ("Development lender", 0.06, 0.110), "Fintech 01": ("Digital lender", 0.04, 0.280),
}

PRODUCTS = ["Seasonal working capital", "Term loan", "Overdraft", "Asset and equipment finance", "Invoice and receivables finance",
            "Warehouse receipt finance", "Input finance", "Contract and purchase-order finance", "Trade and pre-shipment finance", "Insurance-linked loan"]
CONVENTIONAL = {"Term loan", "Overdraft"}
COLLATERAL = ["Title deed", "Chattels and equipment", "Receivables", "Warehouse receipt", "Group or cooperative guarantee", "Unsecured"]

# --------------------------------------------------------------------------- #
# Scores: components and weights (transparent, validated before use)
# --------------------------------------------------------------------------- #
WEIGHTS = {
    "credit_risk": {"Portfolio quality": 0.30, "Borrower behaviour": 0.20, "Leverage": 0.15, "Cash-flow stress": 0.15, "Concentration": 0.10, "Recent deterioration": 0.10},
    "climate_risk": {"Climate exposure": 0.30, "Historical volatility": 0.25, "Current anomaly": 0.20, "Seasonal outlook": 0.15, "Adaptive capacity gap": 0.10},
    "market_risk": {"Price volatility": 0.30, "Price trend": 0.20, "Input-cost pressure": 0.20, "Buyer concentration": 0.15, "Export and FX exposure": 0.15},
    "opportunity": {"Financing gap": 0.25, "Credit growth": 0.20, "Demand growth": 0.15, "Portfolio quality": 0.15, "Market growth": 0.10, "Borrower growth": 0.10, "Product suitability": 0.05},
}
RISK_BLEND = {"credit_risk": 0.45, "climate_risk": 0.30, "market_risk": 0.25}
CREDIBILITY_BORROWERS = 30                        # segments with fewer borrowers are shrunk toward the average score
QUADRANT_CUTS = {"opportunity": 60, "grow_risk": 30, "selective_risk": 35}
EW_THRESHOLDS = {"Amber": 2, "Red": 3}          # number of adverse signals moving together
BORROWER_STATUS = {"Amber": 25, "Red": 45}       # composite borrower score thresholds
AGGREGATION_MIN_INSTITUTIONS = 3                 # industry cells shown only with >= 3 contributing institutions
AGGREGATION_MIN_BORROWERS = 10

# --------------------------------------------------------------------------- #
# Macro context (latest published) and scenario defaults
# --------------------------------------------------------------------------- #
MACRO_CURRENT = [
    ("Central Bank Rate", "8.75%", "CBK, held since February 2026"),
    ("CPI inflation", "6.6%", "KNBS, August 2026"),
    ("KES per USD", "129.4", "CBK, 9 September 2026"),
    ("Farmers who borrowed for farming", "34%", "CBK Agriculture Survey, July 2026"),
    ("Farmers relying on rain-fed production", "78%", "CBK Agriculture Survey, July 2026"),
    ("Term loans and overdrafts in MSME lending", "Over 85%", "CBK MSME Survey, December 2024"),
]
FARMER_CREDIT_SOURCES = {  # CBK Agriculture Survey, July 2026 (multiple responses)
    "Family and friends": 38, "Commercial banks": 21, "Buyers of farm produce": 19, "SACCOs": 17, "Digital lenders": 16,
    "Informal money lenders": 9, "MFIs": 5, "Agricultural Finance Corporation": 5, "Informal savings groups": 3,
}

SCENARIO_PRESETS = {
    "Custom": None,
    "Failed long rains": dict(rain=-35, price=5, inputs=5, cbr=0.0, fuel=0, fx=0),
    "Commodity price slump": dict(rain=0, price=-15, inputs=0, cbr=0.0, fuel=0, fx=0),
    "Input and fuel cost spike": dict(rain=0, price=5, inputs=30, cbr=0.0, fuel=25, fx=8),
    "Monetary tightening": dict(rain=0, price=0, inputs=5, cbr=2.0, fuel=5, fx=5),
    "El Niño heavy rains and flooding": dict(rain=45, price=-5, inputs=0, cbr=0.0, fuel=5, fx=0),
    "Combined drought and cost shock": dict(rain=-25, price=-5, inputs=15, cbr=1.0, fuel=15, fx=8),
}
# transmission assumptions by actor: share of revenue exposed to own production, input cost share, fuel share, debt service share
ACTOR_TRANSMISSION = {
    "Producer": dict(production=1.0, input_share=0.35, fuel_share=0.08, interest_share=0.06),
    "Cooperative": dict(production=0.8, input_share=0.20, fuel_share=0.08, interest_share=0.05),
    "Aggregator": dict(production=0.6, input_share=0.05, fuel_share=0.15, interest_share=0.08),
    "Processor": dict(production=0.4, input_share=0.45, fuel_share=0.12, interest_share=0.08),
    "Exporter": dict(production=0.3, input_share=0.50, fuel_share=0.15, interest_share=0.07),
    "Distributor": dict(production=0.2, input_share=0.60, fuel_share=0.12, interest_share=0.06),
    "Input supplier": dict(production=0.5, input_share=0.55, fuel_share=0.08, interest_share=0.07),
}
CASHFLOW_TO_LOGODDS = 3.0   # log-odds change in 12-month default probability per 100% fall in operating cash flow
