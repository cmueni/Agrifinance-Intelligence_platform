"""Market surveillance: a structured database of developments that change the agricultural financing environment.

Each event records who did what, the instrument and amount, which value chains and counties it touches, how it is
expected to transmit to credit supply, demand or risk, what a lender should consider, and what the platform should
monitor to test whether the announcement produces results. Events are verified against the source before entry.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

AS_OF = "2026-09-17"          # date the event log was last reviewed
USD_KES = 129.4               # CBK rate used to convert announced USD amounts

CATEGORIES = ["Finance", "DFIs", "Banks", "Policy", "Monetary", "Climate", "Market infrastructure", "Funding risk"]
EFFECTS = {"Credit supply up": "Green", "Risk sharing up": "Green", "Input costs down": "Green", "Market access up": "Green",
           "Neutral": "Amber", "Watch": "Amber", "Production risk up": "Red", "Funding withdrawn": "Red"}

EVENTS = [
    dict(id="E14", date="2026-09-17", precision="Day", category="Banks", event_type="New lending approach", institution="Equity Bank Kenya", partner="",
         instrument="Value-addition and market-linked SME lending; asset finance up to 105%; unsecured lines up to KES 10M", amount_kes=None,
         target="Rural SMEs, livestock and agriculture enterprises", value_chains=["Beef and livestock"], geography="Narok County (launch)",
         effect="Credit supply up", chain=["Unsecured and asset finance for rural SMEs", "Lower collateral barrier", "More processing and value-addition investment", "Competition for livestock SME borrowers"],
         action="Review pricing and collateral terms for livestock and processing SMEs in Narok and neighbouring counties.",
         monitor="Approval rates and new lending to livestock processors in Rift Valley counties", link="chains",
         status="Announced", source="HapaKenya", url="https://hapakenya.com/2026/09/17/commercial-banks-in-kenya-pivot-to-value-addition-financing-for-rural-smes/", confidence="Medium"),
    dict(id="E13", date="2026-09-08", precision="Day", category="Finance", event_type="Credit guarantee expansion", institution="RK-FINFA (National Treasury)", partner="IFAD, AFD, Government of Finland",
         instrument="Rural Credit Guarantee Scheme (R-CGS) and Green Financing Facility", amount_kes=11.5e9,
         target="Smallholder households and rural MSMEs; 41 participating financial institutions", value_chains=["All"], geography="Nationwide (previously 14 counties)",
         effect="Risk sharing up", chain=["Mid-term review endorses nationwide coverage", "Guarantee cover available in all counties", "Lower expected loss for participating lenders", "More rural and agricultural SME lending"],
         action="Confirm participating-institution status and the guarantee terms; target counties newly covered.",
         monitor="Lending by SACCOs and microfinance banks to producers outside the original 14 counties", link="gap",
         status="Active", source="RK-FINFA", url="https://rkfinfa.go.ke/", confidence="High",
         note="KES 2.8 billion invested to leverage KES 11.5 billion in lending by participating institutions; 190,000 rural households reached."),
    dict(id="E12", date="2026-08-27", precision="Day", category="Climate", event_type="Seasonal outlook", institution="Kenya Meteorological Service Authority", partner="",
         instrument="October to December 2026 short rains outlook", amount_kes=None,
         target="Farmers and agricultural lenders", value_chains=["Maize", "Pulses", "Horticulture", "Dairy"], geography="About 80% of the country above average",
         effect="Production risk up", chain=["Above-average rainfall with El Niño conditions", "Better planting conditions in dry areas", "Flood, waterlogging and post-harvest loss risk in low-lying areas", "Mixed effect on repayment by county"],
         action="Separate counties that gain from wetter conditions from flood-prone ones; review insurance and repayment dates for loans maturing November to January.",
         monitor="Rainfall anomaly, flood events and arrears in Kisumu, Machakos, Makueni, Kilifi and Nakuru", link="climate",
         status="Active", source="The Star", url="https://www.the-star.co.ke/news/2026-08-27-brace-for-wetter-than-normal-october-dec-rains", confidence="High"),
    dict(id="E11", date="2026-08-23", precision="Day", category="Policy", event_type="Input subsidy", institution="Government of Kenya", partner="",
         instrument="Subsidised fertiliser cut from KES 2,500 to KES 2,000 per 50 kg bag; 50% subsidy on maize seed", amount_kes=None,
         target="Registered farmers", value_chains=["Maize", "Pulses", "Horticulture", "Sugarcane"], geography="Nationwide",
         effect="Input costs down", chain=["Fertiliser price falls 20%", "Lower cost of production for crop farmers", "Smaller seasonal working-capital need per acre", "Better margins if farm-gate prices hold"],
         action="Re-base input finance limits; watch for lower loan sizes but more borrowers ahead of the short rains.",
         monitor="Input cost index, input finance demand and maize approval rates", link="chains",
         status="Active", source="The Star", url="https://www.the-star.co.ke/news/2026-08-23-ruto-cuts-fertiliser-price-to-sh2000-in-new-relief-for-farmers", confidence="High"),
    dict(id="E10", date="2026-08-11", precision="Day", category="Monetary", event_type="Policy rate decision", institution="Central Bank of Kenya", partner="",
         instrument="Central Bank Rate retained at 8.75%", amount_kes=None,
         target="All lenders", value_chains=["All"], geography="Nationwide",
         effect="Neutral", chain=["Policy rate unchanged", "Average lending rate 14.3% in July", "Stable pricing for agricultural loans", "Private sector credit growth 10.2%"],
         action="No repricing trigger; maintain current pricing for agricultural facilities.",
         monitor="Average agricultural lending rate and credit growth", link="flows",
         status="Active", source="The Kenya Times", url="https://thekenyatimes.com/business/cbk-announces-bank-lending-rates-for-august-and-september-2026/", confidence="High",
         note="Reported gross NPL ratio 14.6%, down from 15.4% earlier in the year."),
    dict(id="E09", date="2026-08-04", precision="Day", category="DFIs", event_type="First-loss guarantee", institution="KCB Bank Kenya, Equity Bank Kenya, 4G Capital", partner="IFC and IDA Private Sector Window",
         instrument="Catalytic First Loss Guarantee: IFC USD 24.2M and IDA PSW USD 11M, about 11:1 leverage", amount_kes=144.4e6 * USD_KES,
         target="Microenterprises, women-owned and climate-focused businesses", value_chains=["All"], geography="Kenya",
         effect="Risk sharing up", chain=["First-loss cover for three lenders", "Lower capital and loss burden on riskier MSME loans", "About USD 144M of new MSME lending", "Competition for women-owned and micro borrowers"],
         action="Benchmark approval rates and pricing for women-owned micro borrowers against guarantee-backed lenders.",
         monitor="Tier 1 bank lending to women-owned micro borrowers", link="benchmark",
         status="Active", source="IFC", url="https://www.ifc.org/en/pressroom/2026/ifc-supports-expansion-of-financing-for-kenya-s-small-businesses-through-the-first", confidence="High",
         note="Agriculture's share of the programme is not stated."),
    dict(id="E08", date="2026-07-31", precision="Day", category="Policy", event_type="State lender product", institution="Agricultural Finance Corporation", partner="Nairobi Commodities Exchange, SACCOs and MFIs",
         instrument="Collateral-free lending using warehouse receipts, group lending and project viability assessment", amount_kes=5.2e9,
         target="Smallholders, youth, women, rural micro and small enterprises", value_chains=["Maize", "Pulses", "Dairy"], geography="Nationwide",
         effect="Credit supply up", chain=["Collateral replaced by receipts, groups and viability", "Lower entry barrier for smallholders", "More competition at the small end of the market", "Warehouse receipt volumes rise"],
         action="Consider partnering on warehouse receipt lending; watch for borrower overlap with AFC.",
         monitor="Warehouse receipt finance and first-time producer borrowers", link="fit",
         status="Active", source="allAfrica", url="https://allafrica.com/stories/202607310179.html", confidence="Medium",
         note="Amount is AFC's reported record disbursement, not a new facility. AFC reports NPLs down from 25% (2021) to about 13%."),
    dict(id="E07", date="2026-07-29", precision="Day", category="DFIs", event_type="DFI credit line", institution="KCB Bank Kenya", partner="EBRD",
         instrument="USD 100M credit line with technical assistance for green lending", amount_kes=100e6 * USD_KES,
         target="MSMEs: 35% women- and youth-led, 30% green investments", value_chains=["All"], geography="Kenya",
         effect="Credit supply up", chain=["Longer-term funding for a Tier 1 bank", "Ring-fenced lending for women, youth and green projects", "Climate-smart agriculture equipment finance", "Price competition in green SME lending"],
         action="Review green agricultural products (solar irrigation, cold chain, biogas) and pricing against DFI-funded competitors.",
         monitor="Tier 1 bank share of women- and youth-owned agri SME credit", link="benchmark",
         status="Active", source="EBRD", url="https://www.ebrd.com/home/news-and-events/news/2026/ebrd-supports-small-businesses-in-kenya.html", confidence="High",
         note="EBRD's first investment in Kenya's financial sector."),
    dict(id="E06", date="2026-04-29", precision="Day", category="DFIs", event_type="Risk-sharing facility", institution="Standard Chartered", partner="IFC",
         instrument="USD 300M supply chain and trade finance risk-sharing; IFC guarantees up to USD 150M", amount_kes=None,
         target="Suppliers and SMEs in agriculture, healthcare and manufacturing supply chains", value_chains=["Tea", "Coffee", "Avocado and macadamia", "Horticulture"], geography="8 African countries including Kenya",
         effect="Risk sharing up", chain=["Guarantee on payables and receivables programmes", "Cheaper finance for suppliers to large buyers", "Shorter cash cycles for export-linked SMEs", "Opportunity for receivables finance"],
         action="Identify export offtakers whose suppliers bank with you; offer receivables and pre-shipment finance.",
         monitor="Receivables finance to aggregators and exporters in export chains", link="fit",
         status="Active", source="IFC", url="https://www.ifc.org/en/pressroom/2026/ifc-and-standard-chartered-partner-on-supply-chain-finance-to-support-african-busi", confidence="High",
         note="Regional facility; Kenya's allocation is not disclosed, so no KES amount is attributed."),
    dict(id="E05", date="2026-02-27", precision="Day", category="Market infrastructure", event_type="Collateral infrastructure", institution="Warehouse Receipt System Council", partner="TradeMark Africa, British High Commission",
         instrument="Electronic Warehouse Receipt System Central Registry", amount_kes=None,
         target="Grain, coffee and other storable commodities", value_chains=["Maize", "Pulses", "Coffee"], geography="Nationwide",
         effect="Market access up", chain=["Digital receipts registered centrally", "Receipts usable as collateral", "Farmers avoid distress sales at harvest", "Warehouse receipt finance becomes bankable"],
         action="Set up receipt-backed lending with certified warehouses in grain counties.",
         monitor="Registered receipts, volumes and receipt-backed loans", link="fit",
         status="Active", source="The Star", url="https://www.the-star.co.ke/business/2026-02-27-state-unveils-e-warehouse-receipt-system-to-boost-commodity-trade-cut-post-harvest-losses", confidence="High",
         note="114 receipts for about 600,000 kg registered at launch."),
    dict(id="E04", date="2025-12-31", precision="Figures as at", category="Finance", event_type="Guarantee scheme performance", institution="Kenya Credit Guarantee Scheme (National Treasury)", partner="",
         instrument="Credit guarantees for MSME loans", amount_kes=6.67e9,
         target="MSMEs", value_chains=["All"], geography="46 counties",
         effect="Risk sharing up", chain=["KES 6.67bn disbursed under guarantee", "4,370 enterprises and 27,801 jobs supported", "Leverage ratio 2.46", "Scope to scale agricultural share"],
         action="Check the agricultural share of guaranteed loans and eligibility of agri SME portfolios.",
         monitor="Guaranteed share of agri SME lending", link="gap",
         status="Active", source="National Treasury CGS", url="https://cgs.treasury.go.ke/", confidence="High",
         note="Agriculture's share of guarantees is not published on the scheme page."),
    dict(id="E03", date="2025-02-06", precision="Day", category="Funding risk", event_type="Donor programme termination", institution="USAID programmes in Kenya", partner="",
         instrument="Termination of USAID contracts and grants", amount_kes=None,
         target="Development programmes including private-sector finance mechanisms", value_chains=["All"], geography="Kenya",
         effect="Funding withdrawn", chain=["Donor-funded facilities and technical assistance end", "Pay-for-results and blended structures lose support", "Commitments announced under these programmes may not be delivered", "Replacement funding needed"],
         action="Do not count USAID-linked commitments as current credit supply; confirm status with the lender.",
         monitor="Status of facilities announced under USAID mechanisms", link="surveillance",
         status="Active", source="The Star", url="https://www.the-star.co.ke/news/2025-02-06-usaid-exit-spells-doom-for-kenyan-jobs-and-funding", confidence="High"),
    dict(id="E02", date="2024-01-01", precision="Year", category="Banks", event_type="Agribusiness lending commitment", institution="Family Bank", partner="USAID Kenya Investment Mechanism, Palladium",
         instrument="KES 6 billion affordable credit, pay-for-performance", amount_kes=6.0e9,
         target="Agribusinesses in 17 counties", value_chains=["Dairy", "Horticulture", "Beef and livestock"], geography="17 counties (Western, Nyanza, Eastern, North)",
         effect="Watch", chain=["Commitment linked to a USAID mechanism", "USAID programmes terminated in 2025", "Delivery status unconfirmed", "Treat as historical"],
         action="Confirm with Family Bank whether the programme continued on its own balance sheet.",
         monitor="Family Bank-type lender growth in dairy and horticulture in the 17 counties", link="surveillance",
         status="Historical", source="KBC", url="https://www.kbc.co.ke/family-bank-commits-ksh-6-billion-to-finance-agribusiness/", confidence="Medium",
         note="Builds on the KES 500 million commitment of April 2021. Exact announcement date not given in the source."),
    dict(id="E01", date="2021-04-14", precision="Day", category="Banks", event_type="Bank and donor partnership", institution="Family Bank", partner="USAID Kenya Investment Mechanism",
         instrument="KES 500 million over one year, pay-for-results with capacity building", amount_kes=0.5e9,
         target="Agribusiness SMEs", value_chains=["Dairy", "Horticulture", "Beef and livestock"], geography="17 counties",
         effect="Watch", chain=["One-year commitment from 2021", "Period ended in 2022", "Superseded by the 2024 KES 6bn commitment", "Historical reference only"],
         action="Use as a precedent for pay-for-results structures, not as current supply.",
         monitor="None (completed)", link="surveillance",
         status="Completed", source="Family Bank", url="https://familybank.co.ke/?p=2756", confidence="High"),
]


def events() -> pd.DataFrame:
    df = pd.DataFrame(EVENTS)
    df["date"] = pd.to_datetime(df["date"])
    df["age_days"] = (pd.Timestamp(AS_OF) - df["date"]).dt.days
    df["freshness"] = np.select([df["status"].isin(["Historical", "Completed"]), df["age_days"] <= 45, df["age_days"] <= 180],
                                ["Historical", "New", "Recent"], default="Older")
    df["tone"] = df["effect"].map(EFFECTS)
    df["value_chains_text"] = df["value_chains"].map(", ".join)
    df["date_label"] = np.where(df["precision"] == "Year", df["date"].dt.strftime("%Y"),
                                np.where(df["precision"] == "Figures as at", "As at " + df["date"].dt.strftime("%d %b %Y"), df["date"].dt.strftime("%d %b %Y")))
    return df.sort_values("date", ascending=False).reset_index(drop=True)


def export(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = events() if df is None else df
    out = df.drop(columns=["tone"]).copy()
    out["chain"] = out["chain"].map(" → ".join)
    out["value_chains"] = out["value_chains_text"]
    return out.drop(columns=["value_chains_text"])


# --------------------------------------------------------------------------- #
# Follow-through: does lending move where an announcement says it will?
# --------------------------------------------------------------------------- #
TRACKERS = {
    "E13": ("SACCO and microfinance lending to producers", lambda d: d["lender_type"].isin(["SACCO", "Microfinance bank"]) & (d["actor"] == "Producer")),
    "E09": ("Tier 1 bank lending to women-owned micro borrowers", lambda d: (d["lender_type"] == "Tier 1 bank") & d["women_owned"] & (d["size"] == "Micro")),
    "E07": ("Tier 1 bank lending to women- and youth-owned borrowers", lambda d: (d["lender_type"] == "Tier 1 bank") & (d["women_owned"] | d["youth_owned"])),
    "E11": ("Input finance and seasonal working capital to crop producers", lambda d: d["product"].isin(["Input finance", "Seasonal working capital"]) & d["value_chain"].isin(["Maize", "Pulses", "Horticulture", "Sugarcane"])),
    "E05": ("Warehouse receipt finance", lambda d: d["product"] == "Warehouse receipt finance"),
    "E06": ("Receivables finance in export chains", lambda d: (d["product"] == "Invoice and receivables finance") & d["value_chain"].isin(["Tea", "Coffee", "Avocado and macadamia", "Horticulture"])),
}


def follow_through(feats: pd.DataFrame, months: int = 6) -> pd.DataFrame:
    T = int(feats["t"].max())
    now, before = feats[feats["t"] == T], feats[feats["t"] == T - months]
    mkt_growth = now["outstanding_kes"].sum() / before["outstanding_kes"].sum() - 1
    rows = []
    for eid, (label, rule) in TRACKERS.items():
        a, z = before.loc[rule(before), "outstanding_kes"].sum(), now.loc[rule(now), "outstanding_kes"].sum()
        n = int(rule(now).sum())
        g = z / a - 1 if a else np.nan
        rows.append(dict(id=eid, Tracked=label, Borrowers=n, Outstanding=z, Growth=g, Market=mkt_growth,
                         Signal="Moving ahead of market" if g - mkt_growth >= 0.03 else "In line with market" if g - mkt_growth > -0.03 else "Lagging market"))
    return pd.DataFrame(rows)
