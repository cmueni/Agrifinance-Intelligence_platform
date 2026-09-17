"""Data dictionary, source map, value-chain taxonomy, governance tiers and roadmap.

Each variable: domain, name, definition or formula, unit, frequency, granularity, intended Kenyan source,
access tier, delivery phase and whether it is populated in this prototype (simulated).
"""
from __future__ import annotations

import pandas as pd

DOMAINS = {
    "A": "Credit and portfolio", "B": "Applications and approvals", "C": "Enterprise profile", "D": "Behavioural and cash flow",
    "E": "Macro and monetary", "F": "Climate and satellite", "G": "Market and prices", "H": "Production and value-chain structure",
    "I": "Trade and export", "J": "Inclusion", "K": "Derived scores and indices", "L": "Data quality and metadata", "M": "Market surveillance",
}

# name | definition or formula | unit | frequency | granularity | source | tier | phase | in prototype (Y/N)
_RAW = {
"A": """Outstanding balance|Principal outstanding at month end|KES|Monthly|Loan|Lender core banking system|Confidential|MVP|Y
Loan amount disbursed|Original principal at disbursement|KES|Event|Loan|Lender core banking system|Confidential|MVP|Y
Days past due|Days since the oldest unpaid instalment|Days|Monthly|Loan|Lender core banking system|Confidential|MVP|Y
NPL flag|1 if days past due at least 90 or classified substandard or worse|Flag|Monthly|Loan|Lender, CBK Prudential Guidelines|Confidential|MVP|Y
NPL ratio|Balance with NPL flag divided by total balance|%|Monthly|Segment|Derived|Restricted|MVP|Y
PAR30|Balance at least 30 days past due divided by total balance|%|Monthly|Segment|Derived|Restricted|MVP|Y
Restructured flag|1 if terms modified due to financial difficulty|Flag|Monthly|Loan|Lender core banking system|Confidential|MVP|Y
Product type|Seasonal working capital, term loan, overdraft, asset finance, receivables, warehouse receipt, input, contract farming, insurance-linked, group|Category|Event|Loan|Lender product master|Confidential|MVP|Y
Tenor|Contractual term|Months|Event|Loan|Lender core banking system|Confidential|MVP|Y
Interest rate|Annual contractual rate|%|Event|Loan|Lender core banking system|Confidential|MVP|Y
Collateral type|Title deed, chattels, receivables, warehouse receipt, group guarantee, unsecured|Category|Event|Loan|Lender collateral register|Confidential|MVP|Y
Repayment structure|Monthly, seasonal balloon, harvest-linked or buyer deduction|Category|Event|Loan|Lender core banking system|Confidential|Phase 2|N
Utilisation|Drawn balance divided by approved limit|%|Monthly|Loan|Lender core banking system|Confidential|MVP|Y
Write-off amount|Balance written off in the month|KES|Monthly|Loan|Lender finance system|Confidential|Phase 2|N
Recoveries|Cash recovered on written-off or NPL loans|KES|Monthly|Loan|Lender collections system|Confidential|Phase 2|N
Credit growth, 12 months|Balance now divided by balance 12 months earlier minus 1|%|Monthly|Segment|Derived|Restricted|MVP|Y
Lender type|Tier 1, 2, 3 bank, microfinance bank, SACCO, DFI, fintech|Category|Static|Institution|CBK, SASRA registers|Public|MVP|Y
Sector credit to agriculture|Gross loans to agriculture by banking sector|KES|Monthly|National|CBK sectoral credit statistics|Public|MVP|N""",
"B": """Application count|Number of credit applications received|Count|Monthly|Segment|Lender loan origination system|Confidential|MVP|Y
Amount requested|Amount applied for|KES|Event|Application|Lender loan origination system|Confidential|MVP|Y
Approval flag|1 if approved|Flag|Event|Application|Lender loan origination system|Confidential|MVP|Y
Approval rate|Approved applications divided by applications|%|Monthly|Segment|Derived|Restricted|MVP|Y
Decline reason|Collateral, cash flow, credit history, climate risk, documentation, sector limit|Category|Event|Application|Lender loan origination system|Confidential|MVP|Y
Time to decision|Days from complete application to decision|Days|Event|Application|Lender loan origination system|Confidential|Phase 2|N
Time to disbursement|Days from approval to first disbursement|Days|Event|Application|Lender loan origination system|Confidential|Phase 2|N
Amount approved ratio|Approved amount divided by requested amount|%|Event|Application|Derived|Confidential|Phase 2|N
Demand growth|Applications in last 3 months divided by same months last year minus 1|%|Monthly|Segment|Derived|Restricted|MVP|Y
Referral channel|Branch, agent, cooperative, offtaker, digital|Category|Event|Application|Lender CRM|Confidential|Phase 2|N
Guarantee scheme used|Credit guarantee cover applied, for example partial guarantee programmes|Flag|Event|Application|Lender, guarantee scheme administrator|Confidential|Phase 2|N
Pipeline value|Applications under assessment|KES|Weekly|Segment|Lender loan origination system|Confidential|Phase 3|N
Rejected then approved elsewhere|Declined applicant later financed by another institution|Flag|Monthly|Enterprise|Credit reference bureau match|Highly confidential|Phase 3|N
Farmers borrowing, share|Share of farmers who borrowed in the reference period|%|Annual|National|CBK Agriculture Survey|Public|MVP|Y
Source of farmer credit|Share of farmer borrowing by source|%|Annual|National|CBK Agriculture Survey|Public|MVP|Y
Credit constraint rate|Share of enterprises that needed credit but did not apply or were declined|%|Annual|National|CBK MSME Survey, FinAccess|Public|Phase 2|N""",
"C": """Enterprise identifier|Pseudonymised unique enterprise key|ID|Static|Enterprise|Platform key service|Highly confidential|MVP|Y
Value chain (level 1)|Primary value chain, 12-chain taxonomy|Category|Static|Enterprise|Lender classification mapped to platform taxonomy|Confidential|MVP|Y
Sector group|Sector grouping of the value chain: livestock, food crops, cash crops, horticulture, industrial crops, blue economy|Category|Static|Enterprise|Lender classification|Confidential|MVP|Y
Actor type|Input supplier, producer, cooperative, aggregator, processor, exporter, distributor|Category|Static|Enterprise|Lender classification|Confidential|MVP|Y
County|County of main operation|Category|Static|Enterprise|Lender KYC, KNBS codes|Confidential|MVP|Y
ASAL flag|1 if county classified arid or semi-arid|Flag|Static|County|NDMA, Ministry of EAC and ASALs|Public|MVP|Y
Enterprise size|Micro, small or medium by turnover and employment|Category|Annual|Enterprise|Lender KYC, MSE Act definitions|Confidential|MVP|Y
Annual turnover|Sales in last 12 months|KES|Annual|Enterprise|Financial statements, mobile money|Confidential|MVP|Y
Years in operation|Years since the business started|Years|Static|Enterprise|Lender KYC|Confidential|Phase 2|N
Formally registered|Registered with the Business Registration Service or county|Flag|Static|Enterprise|BRS, lender KYC|Confidential|MVP|Y
Land tenure|Title, lease, family or communal|Category|Static|Enterprise|Lender KYC|Confidential|Phase 2|N
Farm or operating size|Hectares cultivated, herd size or throughput capacity|Unit|Annual|Enterprise|Lender appraisal|Confidential|Phase 2|N
Irrigation access|Share of cultivated area irrigated|%|Annual|Enterprise|Lender appraisal, county irrigation data|Confidential|Phase 2|N
Cooperative membership|Member of a registered cooperative|Flag|Static|Enterprise|State Department for Cooperatives|Confidential|Phase 2|N
Contracted sales share|Share of sales under a written offtake contract|%|Annual|Enterprise|Lender appraisal, offtaker data|Confidential|MVP|Y
Largest buyer share|Sales to largest buyer divided by total sales|%|Annual|Enterprise|Lender appraisal, mobile money|Confidential|MVP|Y
Insured|Crop, livestock or asset insurance in force|Flag|Annual|Enterprise|Insurers, index insurance programmes|Confidential|MVP|Y
Certification|GlobalG.A.P., Fairtrade, organic or export registration|Category|Annual|Enterprise|Certifiers, KEPHIS, AFA|Confidential|Phase 3|N""",
"D": """Monthly inflows|Credits to operating accounts and mobile money|KES|Monthly|Enterprise|Bank statements, mobile money|Highly confidential|MVP|Y
Sales versus last season|Last 3 months inflows divided by same months last year minus 1|%|Monthly|Enterprise|Derived|Highly confidential|MVP|Y
Receivable days|Receivables divided by sales times 365|Days|Monthly|Enterprise|Management accounts, offtaker data|Confidential|MVP|Y
Receivable days change|Receivable days now minus 3 months ago|Days|Monthly|Enterprise|Derived|Confidential|MVP|Y
Utilisation change|Utilisation now minus 3 months ago|pp|Monthly|Loan|Derived|Confidential|MVP|Y
Late payment months|Months with 1 to 29 days past due in last 6 months|Count|Monthly|Loan|Derived|Confidential|MVP|Y
Worst days past due, 6 months|Maximum days past due over 6 months|Days|Monthly|Loan|Derived|Confidential|MVP|Y
Cash cycle|Days from input purchase to cash receipt from buyer|Days|Static|Enterprise|Value-chain profile, lender appraisal|Restricted|MVP|Y
Account balance volatility|Coefficient of variation of month-end balances|Ratio|Monthly|Enterprise|Bank statements|Highly confidential|Phase 2|N
Cheque or debit order returns|Number of bounced payments|Count|Monthly|Enterprise|Lender payments system|Confidential|Phase 2|N
Credit bureau enquiries|Number of new enquiries in last 3 months|Count|Monthly|Enterprise|Credit reference bureaus|Highly confidential|Phase 2|N
Other lender arrears|Days past due at other institutions|Days|Monthly|Enterprise|Credit reference bureaus|Highly confidential|Phase 2|N
Buyer payment delays|Days offtaker payments are late versus contract|Days|Monthly|Enterprise|Offtaker or cooperative systems|Confidential|Phase 3|N
Input purchase volume|Value of inputs bought|KES|Monthly|Enterprise|Agro-dealer and e-voucher systems|Confidential|Phase 3|N
Delivery volumes to buyer|Kilograms or litres delivered|Unit|Monthly|Enterprise|Cooperative, processor, KTDA-type records|Confidential|Phase 3|N
Product-cycle mismatch|Term loan or overdraft on a cash cycle of 110 days or more for producers, cooperatives, aggregators|Flag|Monthly|Loan|Derived|Confidential|MVP|Y""",
"E": """Central Bank Rate|Policy rate set by the Monetary Policy Committee|%|Monthly|National|CBK|Public|MVP|Y
Headline inflation|12-month change in CPI|%|Monthly|National|KNBS|Public|MVP|Y
Food inflation|12-month change in food CPI|%|Monthly|National|KNBS|Public|Phase 2|N
USD/KES exchange rate|Mean monthly exchange rate|KES|Monthly|National|CBK|Public|MVP|Y
Diesel pump price|Nairobi retail diesel price|KES per litre|Monthly|National|EPRA|Public|MVP|Y
Fertiliser price index|Index of retail fertiliser prices|Index|Monthly|National|MoALD, KAMIS, World Bank Pink Sheet|Public|MVP|Y
Animal feed price index|Index of feed prices|Index|Monthly|National|KAMIS, industry associations|Public|MVP|Y
Average lending rate|Weighted average commercial bank lending rate|%|Monthly|National|CBK|Public|Phase 2|N
Private sector credit growth|12-month growth in private sector credit|%|Monthly|National|CBK|Public|Phase 2|N
Agriculture GDP growth|Real growth in agriculture, forestry and fishing|%|Quarterly|National|KNBS Quarterly GDP|Public|Phase 2|N
Agriculture share of GDP|Agriculture value added divided by GDP|%|Annual|National|KNBS Economic Survey|Public|Phase 2|N
Banking sector agriculture NPL|Gross NPL ratio for the agriculture sector|%|Quarterly|National|CBK, KBA State of the Banking Industry|Public|MVP|N
Government agriculture spending|National and county budget allocation to agriculture|KES|Annual|County|Controller of Budget|Public|Phase 3|N
Diaspora remittances|Monthly remittance inflows|USD|Monthly|National|CBK|Public|Phase 3|N
Electricity tariff|Commercial tariff per kWh|KES|Monthly|National|EPRA|Public|Phase 3|N
Mobile money value|Value of mobile money transactions|KES|Monthly|National|CBK|Public|Phase 3|N""",
"F": """Rainfall anomaly|Monthly rainfall versus long-term mean|%|Monthly|County|KMD, CHIRPS|Public|MVP|Y
Rainfall anomaly, 3 months|Mean anomaly over last 3 months|%|Monthly|County|Derived|Public|MVP|Y
Last season rainfall|Mean anomaly over last 6 months|%|Monthly|County|Derived|Public|MVP|Y
Rainfall volatility|Standard deviation of monthly anomalies|pp|Monthly|County|Derived|Public|MVP|Y
Vegetation anomaly (NDVI)|Vegetation index versus long-term mean|%|Monthly|County|MODIS, Copernicus, NDMA VCI|Public|MVP|Y
Drought phase|Normal, alert, alarm, emergency|Category|Monthly|County|NDMA early warning bulletins|Public|MVP|Y
Seasonal rainfall outlook|Forecast rainfall versus normal for next season|%|Seasonal|County|KMD, ICPAC|Public|MVP|Y
Soil moisture anomaly|Root-zone soil moisture versus normal|%|Monthly|County|SMAP, Copernicus|Public|Phase 2|N
Temperature anomaly|Mean temperature versus long-term mean|deg C|Monthly|County|KMD, ERA5|Public|Phase 2|N
Flood events|Number of flood events reported|Count|Monthly|County|NDMA, Kenya Red Cross|Public|Phase 2|N
Irrigation share|Irrigated share of cropland|%|Annual|County|National Irrigation Authority|Public|MVP|Y
Climate sensitivity of chain|Expert rating of yield sensitivity to rainfall, 0 to 1|Score|Static|Value chain|Platform methodology, KALRO|Public|MVP|Y
Pest and disease alerts|Fall armyworm, locust or livestock disease alerts|Count|Monthly|County|MoALD, FAO, Directorate of Veterinary Services|Public|Phase 2|N
Farm-level vegetation index|NDVI at plot boundary|%|Fortnightly|Plot|Satellite imagery with geo-tagged farms|Confidential|Phase 3|N
Heat stress days|Days above crop or livestock threshold|Count|Monthly|County|ERA5, KMD|Public|Phase 3|N
Water stress index|Surface water availability for livestock|Index|Monthly|County|NDMA|Public|Phase 3|N
Forage condition|Pasture condition in pastoral counties|Index|Monthly|County|NDMA, satellite|Public|Phase 2|N""",
"G": """Farm-gate price index|Producer price index by value chain|Index|Monthly|Value chain|KAMIS, AFA directorates, KDB, NCPB|Public|MVP|Y
Price change, 3 months|Price index now divided by 3 months ago minus 1|%|Monthly|Value chain|Derived|Public|MVP|Y
Price volatility|Standard deviation of monthly log price changes, 12 months|Ratio|Monthly|Value chain|Derived|Public|MVP|Y
Input cost index|Weighted index of fertiliser, seed, feed, chemicals|Index|Monthly|Value chain|KAMIS, agro-dealers|Public|MVP|Y
Input cost change, 6 months|Input index now divided by 6 months ago minus 1|%|Monthly|Value chain|Derived|Public|MVP|Y
Margin index|Price index divided by input cost index|Index|Monthly|Value chain|Derived|Public|MVP|Y
Wholesale market price|Wholesale price at main markets|KES per unit|Weekly|Market|KAMIS|Public|Phase 2|N
Retail price|Retail price of key products|KES per unit|Monthly|County|KNBS CPI micro prices|Public|Phase 2|N
Auction price, tea|Mombasa auction average price|USD per kg|Weekly|National|Tea Board, East African Tea Trade Association|Public|Phase 2|N
Auction price, coffee|Nairobi Coffee Exchange average price|USD per 50kg|Weekly|National|Nairobi Coffee Exchange|Public|Phase 2|N
Milk producer price|Price paid to farmers per litre|KES per litre|Monthly|County|Kenya Dairy Board|Public|Phase 2|N
Maize producer price|NCPB and market maize price per 90kg bag|KES per bag|Monthly|County|NCPB, KAMIS|Public|Phase 2|N
Cross-border price gap|Kenya price minus regional price|%|Monthly|Value chain|FEWS NET, EAGC|Public|Phase 3|N
World commodity price|International benchmark price|USD|Monthly|Global|World Bank Pink Sheet, FAO|Public|Phase 2|N
Buyer concentration, chain|Share of volume bought by top 5 buyers|%|Annual|Value chain|AFA, industry data|Restricted|Phase 3|N
Warehouse receipt volume|Commodities stored under receipts|Tonnes|Monthly|County|Warehouse Receipt System Council|Public|Phase 3|N""",
"H": """Production index|Volume produced versus base year|Index|Monthly|Value chain|MoALD, AFA directorates, KDB|Public|MVP|Y
Production change, 12 months|Production index now divided by 12 months ago minus 1|%|Monthly|Value chain|Derived|Public|MVP|Y
Market value change|Price times production change over 12 months|%|Monthly|Value chain|Derived|Public|MVP|Y
Area planted|Hectares planted by crop|Hectares|Seasonal|County|MoALD, county departments|Public|Phase 2|N
Yield|Output per hectare or per animal|Unit|Seasonal|County|MoALD, KALRO|Public|Phase 2|N
Livestock population|Head of cattle, goats, poultry|Count|Annual|County|KNBS census, Directorate of Livestock|Public|Phase 2|N
Number of enterprises|Estimated agri SMEs by chain, county and actor|Count|Annual|Segment|KNBS MSME survey, cooperatives registry, AFA licences|Restricted|MVP|Y
Average enterprise turnover|Mean turnover by chain, county and actor|KES|Annual|Segment|KNBS, lender data|Restricted|MVP|Y
Working-capital need|Turnover times cash cycle divided by 365|KES|Annual|Segment|Derived|Restricted|MVP|Y
Financing demand|Enterprises times working-capital need plus investment need|KES|Annual|Segment|Derived|Restricted|MVP|Y
Harvest calendar|Main and secondary harvest months|Months|Static|Value chain|MoALD crop calendars, FAO|Public|MVP|Y
Storage capacity|Certified storage capacity|Tonnes|Annual|County|WRS Council, NCPB|Public|Phase 3|N
Processing capacity utilisation|Throughput divided by installed capacity|%|Quarterly|Value chain|Processors, AFA|Restricted|Phase 3|N
Cooperatives registered|Active agricultural cooperatives|Count|Annual|County|State Department for Cooperatives|Public|Phase 2|N
Post-harvest loss|Share of output lost after harvest|%|Annual|Value chain|KALRO, FAO APHLIS|Public|Phase 3|N
Extension coverage|Farmers reached by extension services|%|Annual|County|County departments|Public|Phase 3|N""",
"I": """Export value index|Export earnings by chain versus base|Index|Monthly|Value chain|KNBS, KRA customs, AFA|Public|MVP|Y
Export share of chain|Share of chain output exported|%|Annual|Value chain|AFA, KNBS|Public|MVP|Y
Export volume|Tonnes exported|Tonnes|Monthly|Value chain|KRA customs, AFA|Public|Phase 2|N
Export price|Unit value of exports|USD per tonne|Monthly|Value chain|Derived from customs|Public|Phase 2|N
Top destination share|Share of exports to largest destination market|%|Quarterly|Value chain|KNBS trade statistics|Public|Phase 2|N
Import volume, competing|Imports of competing products|Tonnes|Monthly|Value chain|KRA customs|Public|Phase 2|N
Interceptions and rejections|Export consignments rejected for residues or pests|Count|Monthly|Value chain|KEPHIS, EU RASFF|Public|Phase 3|N
Trade finance volume|Letters of credit and export pre-finance issued|KES|Monthly|Value chain|Lenders|Confidential|Phase 3|N
FX earnings conversion|Share of export proceeds converted locally|%|Monthly|Enterprise|Lender FX desk|Confidential|Phase 3|N
Freight cost index|Container freight rate to main destinations|Index|Monthly|Global|Freight indices|Public|Phase 3|N
Regional trade (EAC, COMESA)|Exports to regional markets|USD|Quarterly|Value chain|KNBS, EAC|Public|Phase 3|N
Export concentration by buyer|Share of chain exports handled by top 5 exporters|%|Annual|Value chain|AFA, KRA customs|Restricted|Phase 3|N
Phytosanitary compliance cost|Cost of certification and residue testing per tonne|KES per tonne|Annual|Value chain|KEPHIS, industry|Public|Phase 3|N
Export seasonality|Share of annual exports shipped in peak quarter|%|Annual|Value chain|KNBS trade statistics|Public|Phase 2|N
Hedged FX exposure|Share of FX receivables hedged|%|Quarterly|Enterprise|Lender treasury|Confidential|Phase 3|N
Export licence holders|Registered exporters by chain|Count|Annual|Value chain|AFA, HCD|Public|Phase 2|N""",
"J": """Women-owned|Majority women ownership or management|Flag|Static|Enterprise|Lender KYC|Confidential|MVP|Y
Youth-owned|Majority owners aged 18 to 35|Flag|Static|Enterprise|Lender KYC|Confidential|MVP|Y
First-time borrower|No formal credit before this facility|Flag|Static|Enterprise|Credit reference bureau, lender|Confidential|MVP|Y
Share of borrowers by group|Group borrowers divided by all borrowers|%|Monthly|Segment|Derived|Restricted|MVP|Y
Share of credit by group|Group balance divided by total balance|%|Monthly|Segment|Derived|Restricted|MVP|Y
Approval rate gap|Group approval rate minus others|pp|Monthly|Segment|Derived|Restricted|MVP|Y
Average loan size gap|Group average loan divided by others|Ratio|Monthly|Segment|Derived|Restricted|MVP|Y
Pricing gap|Group average rate minus others|pp|Monthly|Segment|Derived|Restricted|MVP|Y
Suitability rate|Share of borrowers in a product that matches their cash cycle|%|Monthly|Segment|Derived|Restricted|MVP|Y
Resilience rate|Share of borrowers insured or with contracted sales|%|Monthly|Segment|Derived|Restricted|MVP|Y
ASAL credit share|Balance in ASAL counties divided by total|%|Monthly|Segment|Derived|Restricted|MVP|Y
Smallholder reach|Borrowers with less than 5 acres|Count|Monthly|Segment|Lender appraisal|Restricted|Phase 2|N
Credit access, adults|Share of adults using formal credit|%|Periodic|National|FinAccess Household Survey|Public|Phase 2|N
Persons with disability|Enterprise owned by a person with disability|Flag|Static|Enterprise|Lender KYC|Highly confidential|Phase 3|N
Digital loan share|Share of agri borrowers served through digital channels|%|Monthly|Segment|Lender channel data|Restricted|Phase 2|N
Distance to branch or agent|Kilometres from enterprise to nearest access point|km|Annual|Enterprise|Geo-coded KYC, CBK access point maps|Confidential|Phase 3|N
Graduation rate|First-time borrowers who take a second, larger loan|%|Quarterly|Segment|Derived|Restricted|Phase 2|N""",
"K": """Credit risk score|Weighted: portfolio quality 30, behaviour 20, leverage 15, cash-flow stress 15, concentration 10, deterioration 10|0 to 100|Monthly|Segment|Platform|Restricted|MVP|Y
Climate risk score|Weighted: exposure 30, volatility 25, current anomaly 20, outlook 15, adaptive capacity gap 10|0 to 100|Monthly|Segment|Platform|Restricted|MVP|Y
Market risk score|Weighted: price volatility 30, price trend 20, input pressure 20, buyer concentration 15, export and FX 15|0 to 100|Monthly|Segment|Platform|Restricted|MVP|Y
Risk index|0.45 credit + 0.30 climate + 0.25 market|0 to 100|Monthly|Segment|Platform|Restricted|MVP|Y
Opportunity score|Weighted: gap 25, credit growth 20, demand growth 15, quality 15, market growth 10, borrower growth 10, suitability 5|0 to 100|Monthly|Segment|Platform|Restricted|MVP|Y
Credibility weight|Borrowers divided by 30, capped at 1; shrinks small-segment scores toward the average|0 to 1|Monthly|Segment|Platform|Restricted|MVP|Y
Quadrant|Grow, grow with structure, selective, tighten and monitor|Category|Monthly|Segment|Platform|Restricted|MVP|Y
Segment early warning status|Green, amber (2 signals), red (3 or more) from 7 market, climate and credit signals|Category|Monthly|Segment|Platform|Restricted|MVP|Y
Financing gap|Financing demand minus formal credit observed divided by market coverage|KES|Monthly|Segment|Platform|Restricted|MVP|Y
Credit penetration|Formal credit divided by financing demand|%|Monthly|Segment|Platform|Restricted|MVP|Y
Borrower 3-month default probability|Logistic model of 30+ DPD or restructure within 3 months|%|Monthly|Loan|Platform|Confidential|MVP|Y
Trigger points|Sum of severity points of fired triggers, capped at 100|Points|Monthly|Loan|Platform|Confidential|MVP|Y
Borrower warning score|0.65 model points + 0.35 trigger points|0 to 100|Monthly|Loan|Platform|Confidential|MVP|Y
Borrower status|Green, amber, red, NPL|Category|Monthly|Loan|Platform|Confidential|MVP|Y
Product fit score|Rule score of each product against actor, cycle, contracts, collateral and climate|0 to 100|Monthly|Enterprise|Platform|Confidential|MVP|Y
Scenario cash-flow change|Revenue and cost shock transmitted through actor and county exposure|%|On demand|Loan|Platform|Confidential|MVP|Y
Stressed expected loss|Stressed 12-month PD times LGD times exposure|KES|On demand|Segment|Platform|Restricted|MVP|Y""",
"M": """Event identifier|Unique reference for a logged development|ID|Event|Event|Platform event log|Public|MVP|Y
Event date|Announcement date and its precision (day, year, figures as at)|Date|Event|Event|Primary source|Public|MVP|Y
Event category|Finance, DFIs, banks, policy, monetary, climate, market infrastructure, funding risk|Category|Event|Event|Platform tagging|Public|MVP|Y
Event type|Guarantee, credit line, first-loss cover, subsidy, rate decision, product launch and similar|Category|Event|Event|Platform tagging|Public|MVP|Y
Institution and partner|Lender, DFI, government body or donor involved|Text|Event|Event|Primary source|Public|MVP|Y
Instrument|Credit line, guarantee, risk-sharing, subsidy, collateral infrastructure|Text|Event|Event|Primary source|Public|MVP|Y
Announced amount|Published value converted to KES; blank where no Kenya allocation is disclosed|KES|Event|Event|Primary source, CBK exchange rate|Public|MVP|Y
Targeted value chains and geography|Value chains, counties or regions the event names|Text|Event|Event|Primary source, platform tagging|Public|MVP|Y
Financing effect|Credit supply up, risk sharing up, input costs down, market access up, production risk up, funding withdrawn|Category|Event|Event|Platform analyst|Public|MVP|Y
Event status|Announced, active, completed or historical|Category|Monthly|Event|Platform analyst|Public|MVP|Y
Source confidence|High for primary sources, medium for press reports or performance totals|Category|Event|Event|Platform analyst|Public|MVP|Y
Follow-through growth|Credit growth in the targeted segment minus market growth since the event|pp|Monthly|Segment|Derived from loan tapes|Restricted|Phase 2|Y"""  ,
"L": """Source system|Originating system or publisher|Text|Per load|Dataset|Platform metadata|Restricted|MVP|Y
Last updated|Date of latest record|Date|Per load|Dataset|Platform metadata|Restricted|MVP|Y
Coverage|Share of the market represented in the data|%|Per load|Dataset|Platform metadata|Restricted|MVP|Y
Confidence level|High, medium or low by sample size and coverage|Category|Monthly|Segment|Platform|Restricted|MVP|Y
Institutions in cell|Number of reporting institutions in an aggregate|Count|Monthly|Segment|Platform|Restricted|MVP|Y
Borrowers in cell|Number of borrowers in an aggregate|Count|Monthly|Segment|Platform|Restricted|MVP|Y
Suppression flag|1 if fewer than 3 institutions or 10 borrowers|Flag|Monthly|Segment|Platform|Restricted|MVP|Y
Completeness|Share of mandatory fields populated|%|Per load|Dataset|Platform data quality checks|Restricted|MVP|N
Validity failures|Records failing range or code checks|Count|Per load|Dataset|Platform data quality checks|Restricted|MVP|N
Duplicate records|Records sharing a key|Count|Per load|Dataset|Platform data quality checks|Restricted|MVP|N
Taxonomy mapping rate|Share of loans mapped to value chain and actor|%|Per load|Dataset|Platform data quality checks|Restricted|MVP|N
Model version|Version of scoring model used|Text|Per run|Model|Model registry|Restricted|Phase 2|N
Consent flag|Borrower consent for data sharing recorded|Flag|Static|Enterprise|Lender consent register, Data Protection Act 2019|Highly confidential|Phase 2|N
Access log|User, time and view of confidential data|Log|Event|User|Platform audit trail|Highly confidential|Phase 2|N
Reporting lag|Days between period end and data receipt|Days|Per load|Dataset|Platform metadata|Restricted|MVP|N
Revision flag|Record changed after first publication|Flag|Per load|Dataset|Platform metadata|Restricted|Phase 2|N
Reconciliation difference|Loan tape total minus regulatory return total|%|Monthly|Institution|Platform data quality checks|Confidential|MVP|N""",
}


def data_dictionary() -> pd.DataFrame:
    rows = []
    for dom, block in _RAW.items():
        for i, line in enumerate(block.strip().splitlines(), start=1):
            parts = [p.strip() for p in line.split("|")]
            assert len(parts) == 9, line
            name, definition, unit, freq, gran, source, tier, phase, proto = parts
            rows.append(dict(Code=f"{dom}{i:02d}", Domain=DOMAINS[dom], Variable=name, Definition=definition, Unit=unit, Frequency=freq,
                             Granularity=gran, Source=source, Access=tier, Phase=phase, **{"In prototype": proto == "Y"}))
    return pd.DataFrame(rows)


SOURCES = pd.DataFrame([
    ("Lender core banking and origination systems", "Loans, repayments, applications, decisions", "Monthly file or API", "Confidential", "MVP"),
    ("Central Bank of Kenya", "CBR, exchange rate, sectoral credit, Agriculture Survey, MSME Survey", "Monthly and periodic", "Public", "MVP"),
    ("Kenya National Bureau of Statistics", "CPI, GDP, Economic Survey, trade, enterprise counts", "Monthly to annual", "Public", "MVP"),
    ("Kenya Meteorological Department and CHIRPS", "Rainfall, anomalies, seasonal outlooks", "Dekadal and monthly", "Public", "MVP"),
    ("National Drought Management Authority", "Drought phase, vegetation condition, forage", "Monthly", "Public", "MVP"),
    ("KAMIS and Agriculture and Food Authority", "Farm-gate and wholesale prices, production, licences", "Weekly to monthly", "Public", "MVP"),
    ("Kenya Dairy Board, NCPB, tea and coffee exchanges", "Chain-specific prices and volumes", "Weekly to monthly", "Public", "Phase 2"),
    ("EPRA", "Fuel and electricity prices", "Monthly", "Public", "MVP"),
    ("Credit reference bureaus", "Enquiries, arrears at other lenders", "Monthly", "Highly confidential", "Phase 2"),
    ("Mobile money and bank statements (with consent)", "Inflows, volatility, buyer payments", "Monthly", "Highly confidential", "Phase 2"),
    ("SASRA and SACCOs", "SACCO agricultural lending", "Quarterly", "Restricted", "Phase 2"),
    ("Cooperatives, processors, offtakers", "Deliveries, payments, contracts", "Monthly", "Confidential", "Phase 3"),
    ("Satellite (MODIS, Sentinel, Copernicus)", "NDVI, soil moisture, plot monitoring", "Fortnightly", "Public or confidential at plot level", "Phase 3"),
    ("FinAccess (CBK, KNBS, FSD Kenya)", "Household and enterprise financial access", "Periodic", "Public", "Phase 2"),
], columns=["Source", "What it provides", "Refresh", "Access", "Phase"])

GOVERNANCE = pd.DataFrame([
    ("Public", "Macro, climate, prices, published surveys and aggregated market views", "All users, can be shared externally", "No restriction beyond attribution"),
    ("Restricted", "Market aggregates by chain and county built from lender data", "Subscribing institutions, regulators, DFIs", "Shown only where at least 3 institutions and 10 borrowers contribute"),
    ("Confidential", "An institution's own loan-level and application data", "That institution's authorised staff", "Row-level security by institution; never visible to peers"),
    ("Highly confidential", "Identifiers, bureau data, mobile money and bank statements", "Named analysts with consent on file", "Pseudonymised keys, consent register, access logging, Data Protection Act 2019"),
], columns=["Tier", "Data", "Who sees it", "Control"])

TAXONOMY = pd.DataFrame([
    ("Livestock", "Dairy", "Milk production, collection, processing"),
    ("Livestock", "Beef and livestock", "Cattle, sheep and goats, feedlots, livestock trade"),
    ("Livestock", "Poultry", "Layers, broilers, hatcheries, feed"),
    ("Food crops", "Maize", "Maize and cereals production, trading, milling"),
    ("Food crops", "Pulses", "Beans, green grams, cowpeas, pigeon peas"),
    ("Cash crops", "Tea", "Smallholder tea, factories"),
    ("Cash crops", "Coffee", "Cherry production, cooperatives, milling"),
    ("Cash crops", "Sugarcane", "Outgrowers, millers"),
    ("Horticulture", "Horticulture", "Vegetables, fruits, cut flowers"),
    ("Horticulture", "Avocado and macadamia", "Tree crops for export"),
    ("Industrial crops", "Edible oils", "Sunflower, soya, oil processing"),
    ("Blue economy", "Fisheries and aquaculture", "Capture fisheries, fish farming, cold chain"),
], columns=["Sector", "Value chain", "Includes"])

ROADMAP = pd.DataFrame([
    ("MVP (0 to 6 months)", "One or two lenders plus public data", "Executive overview, value chain explorer, financing gap, risk and early warning, scenario lab, borrower watchlist",
     "Monthly loan tape mapped to taxonomy; public climate, price and macro feeds; transparent scores"),
    ("Phase 2 (6 to 12 months)", "5 or more lenders, SACCOs, bureau", "Benchmarking with suppression, inclusion dashboards, product fit, what changed alerts",
     "Bureau and statement data with consent; out-of-time model validation; data quality scorecards"),
    ("Phase 3 (12 to 24 months)", "Cooperatives, offtakers, insurers, DFIs", "Plot-level satellite monitoring, offtaker payment signals, guarantee and blended finance targeting",
     "APIs to value-chain partners; model governance and independent validation; regulator views"),
], columns=["Phase", "Data partners", "Capabilities", "Foundations"])
