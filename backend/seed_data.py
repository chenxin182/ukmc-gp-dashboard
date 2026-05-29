"""
UKMC Deal Origination System — Seed Data
Populates the database with realistic Southeast Asian deal pipeline,
companies, contacts and intelligence signals for demonstration/testing.

Run directly:   python seed_data.py
Or import:      from seed_data import seed_all; seed_all(db)
"""

from datetime import datetime, timedelta

from database import SessionLocal, engine
from deal_models import (
    Base,
    Contact,
    Deal,
    DealActivity,
    DealContact,
    IntelligenceSignal,
    TargetCompany,
)
from deal_scoring import score_deal, score_dim_sum_feasibility

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ago(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

COMPANIES = [
    {
        "name": "PT Indosat Ooredoo Hutchison",
        "country": "Indonesia",
        "sector": "Telecom",
        "subsector": "Mobile & Fixed-line",
        "website": "https://ioh.co.id",
        "description": "Indonesia's second-largest telco by subscribers with 100M+ mobile users. "
                       "Listed on IDX, partial Chinese ownership via Hutchison Asia Telecom.",
        "revenue_mn": 3200.0,
        "employees": 6800,
        "founded": 1967,
        "hq_address": "Jl. Medan Merdeka Barat No. 21, Jakarta 10110, Indonesia",
        "listed": True,
        "exchange": "IDX",
        "ticker": "ISAT",
        "market_cap_mn": 4100.0,
        "credit_rating": "BB+",
        "chinese_exposure": True,
        "belt_road_exposure": False,
        "chinese_partners": "CK Hutchison Holdings (65.6% stake via merger)",
        "rmb_exposure": True,
    },
    {
        "name": "Vinhomes JSC",
        "country": "Vietnam",
        "sector": "Real Estate",
        "subsector": "Residential & Mixed-use Development",
        "website": "https://vinhomes.vn",
        "description": "Vietnam's largest residential developer and member of Vingroup conglomerate. "
                       "Develops large-scale urban township projects across Vietnam.",
        "revenue_mn": 2800.0,
        "employees": 4500,
        "founded": 2008,
        "hq_address": "7 Bang Lang 1 Street, Vinhomes Riverside, Long Bien, Hanoi, Vietnam",
        "listed": True,
        "exchange": "HOSE",
        "ticker": "VHM",
        "market_cap_mn": 8500.0,
        "credit_rating": "B+",
        "chinese_exposure": False,
        "belt_road_exposure": False,
        "rmb_exposure": False,
    },
    {
        "name": "PT Vale Indonesia",
        "country": "Indonesia",
        "sector": "Mining",
        "subsector": "Nickel Ore & RKEF Smelting",
        "website": "https://ptvaleindonesia.com",
        "description": "Major nickel mining and smelting company operating in South Sulawesi. "
                       "Majority owned by Vale Canada; Chinese JV partner Zhejiang Huayou Cobalt. "
                       "Key supplier to EV battery supply chains.",
        "revenue_mn": 1100.0,
        "employees": 5200,
        "founded": 1968,
        "hq_address": "Sorowako, South Sulawesi, Indonesia",
        "listed": True,
        "exchange": "IDX",
        "ticker": "INCO",
        "market_cap_mn": 2200.0,
        "credit_rating": "BB",
        "chinese_exposure": True,
        "belt_road_exposure": True,
        "chinese_partners": "Zhejiang Huayou Cobalt (20% JV stake in RKEF processing)",
        "rmb_exposure": True,
    },
    {
        "name": "AIS (Advanced Info Service)",
        "country": "Thailand",
        "sector": "Telecom",
        "subsector": "5G & Mobile",
        "website": "https://ais.th",
        "description": "Thailand's largest mobile operator with 45M subscribers. "
                       "Rolling out nationwide 5G network; pursuing data centre and cloud services.",
        "revenue_mn": 4400.0,
        "employees": 12000,
        "founded": 1986,
        "hq_address": "414 Phaholyothin Road, Samsen Nai, Phaya Thai, Bangkok 10400",
        "listed": True,
        "exchange": "SET",
        "ticker": "ADVANC",
        "market_cap_mn": 11000.0,
        "credit_rating": "A-",
        "chinese_exposure": False,
        "belt_road_exposure": False,
        "rmb_exposure": False,
    },
    {
        "name": "Telkom Indonesia",
        "country": "Indonesia",
        "sector": "Telecom",
        "subsector": "Fiber, Data Centers & Cloud",
        "website": "https://telkom.co.id",
        "description": "State-owned incumbent telco of Indonesia. Dominant fixed-line and broadband "
                       "provider; subsidiary Telkomsel is market leader in mobile. "
                       "Expanding data centre capacity aggressively.",
        "revenue_mn": 12500.0,
        "employees": 25000,
        "founded": 1884,
        "hq_address": "Jl. Japati No. 1, Bandung, West Java 40133, Indonesia",
        "listed": True,
        "exchange": "IDX / NYSE",
        "ticker": "TLKM",
        "market_cap_mn": 22000.0,
        "credit_rating": "BBB",
        "parent_company": "Government of Indonesia (52.09%)",
        "chinese_exposure": False,
        "belt_road_exposure": False,
        "rmb_exposure": False,
    },
    {
        "name": "Harita Nickel (PT Trimegah Bangun Persada)",
        "country": "Indonesia",
        "sector": "Mining",
        "subsector": "Nickel & HPAL Processing",
        "website": "https://haritanickel.com",
        "description": "Indonesian nickel miner and HPAL (High-Pressure Acid Leach) processor "
                       "on Obi Island, North Maluku. Key supplier of MHP for EV batteries.",
        "revenue_mn": 780.0,
        "employees": 3200,
        "founded": 2008,
        "hq_address": "Obi Island, North Maluku & Jakarta HQ, Indonesia",
        "listed": True,
        "exchange": "IDX",
        "ticker": "NCKL",
        "market_cap_mn": 3800.0,
        "credit_rating": "BB-",
        "chinese_exposure": True,
        "belt_road_exposure": True,
        "chinese_partners": "Ningbo Lygend (HPAL JV partner, 49% stake)",
        "rmb_exposure": True,
    },
    {
        "name": "STT GDC (ST Telemedia Global Data Centres)",
        "country": "Singapore",
        "sector": "Data Centers",
        "subsector": "Hyperscale & Colocation",
        "website": "https://stt-gdc.com",
        "description": "Pan-Asian hyperscale and colocation data centre operator; "
                       "subsidiary of Temasek-linked ST Telemedia. Operates across 25+ cities.",
        "revenue_mn": 680.0,
        "employees": 2100,
        "founded": 2014,
        "hq_address": "1 Harbourfront Avenue, Keppel Bay Tower, Singapore 098632",
        "listed": False,
        "chinese_exposure": False,
        "belt_road_exposure": False,
        "rmb_exposure": False,
    },
    {
        "name": "Viettel Group",
        "country": "Vietnam",
        "sector": "Telecom",
        "subsector": "5G, Fiber & Defence ICT",
        "website": "https://viettel.com.vn",
        "description": "Vietnam's largest telco and military-owned conglomerate. "
                       "Operates in 11 countries; 5G infrastructure rollout underway nationwide.",
        "revenue_mn": 6100.0,
        "employees": 40000,
        "founded": 1989,
        "hq_address": "No 1 Giang Van Minh, Ba Dinh District, Hanoi, Vietnam",
        "listed": False,
        "parent_company": "Ministry of National Defence, Vietnam",
        "chinese_exposure": False,
        "belt_road_exposure": False,
        "rmb_exposure": False,
    },
    {
        "name": "Manila Electric Company (Meralco)",
        "country": "Philippines",
        "sector": "Power",
        "subsector": "Power Distribution & Renewables",
        "website": "https://meralco.com.ph",
        "description": "Largest power distribution utility in the Philippines. "
                       "Expanding into renewable energy generation and EV charging infrastructure.",
        "revenue_mn": 5200.0,
        "employees": 8700,
        "founded": 1903,
        "hq_address": "Lopez Building, Ortigas Avenue, Pasig City, Metro Manila",
        "listed": True,
        "exchange": "PSE",
        "ticker": "MER",
        "market_cap_mn": 7800.0,
        "credit_rating": "A",
        "chinese_exposure": False,
        "belt_road_exposure": False,
        "rmb_exposure": False,
    },
    {
        "name": "Merdeka Battery Materials",
        "country": "Indonesia",
        "sector": "Mining",
        "subsector": "Nickel, Cobalt & Battery Chemicals",
        "website": "https://merdekabattery.com",
        "description": "Battery materials producer integrating nickel mining (Morowali), "
                       "HPAL processing and cobalt refining. JV with CATL and Ford Motor.",
        "revenue_mn": 620.0,
        "employees": 4100,
        "founded": 2021,
        "hq_address": "Jakarta, Indonesia",
        "listed": True,
        "exchange": "IDX",
        "ticker": "MBMA",
        "market_cap_mn": 4200.0,
        "credit_rating": "B+",
        "chinese_exposure": True,
        "belt_road_exposure": True,
        "chinese_partners": "CATL (Contemporary Amperex Technology), HKUST-linked research JV",
        "rmb_exposure": True,
    },
]

# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

CONTACTS = [
    # PT Indosat Ooredoo Hutchison
    {
        "company_name": "PT Indosat Ooredoo Hutchison",
        "name": "Vikram Sinha",
        "title": "President Director & CEO",
        "role": "CEO",
        "email": "vikram.sinha@ioh.co.id",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    {
        "company_name": "PT Indosat Ooredoo Hutchison",
        "name": "Nicky Lee",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "email": "nicky.lee@ioh.co.id",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    # PT Vale Indonesia
    {
        "company_name": "PT Vale Indonesia",
        "name": "Febriany Eddy",
        "title": "President Director & CEO",
        "role": "CEO",
        "email": "febriany.eddy@ptvi.vale.com",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    {
        "company_name": "PT Vale Indonesia",
        "name": "Bernardus Irmanto",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "email": "bernardus.irmanto@ptvi.vale.com",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    # Harita Nickel
    {
        "company_name": "Harita Nickel (PT Trimegah Bangun Persada)",
        "name": "Roy Arman Arfandy",
        "title": "President Director",
        "role": "CEO",
        "email": "roy.arfandy@haritanickel.com",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    # Telkom Indonesia
    {
        "company_name": "Telkom Indonesia",
        "name": "Ririek Adriansyah",
        "title": "President Director & CEO",
        "role": "CEO",
        "email": "ririek@telkom.co.id",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": False,
    },
    {
        "company_name": "Telkom Indonesia",
        "name": "Heri Supriadi",
        "title": "Director of Finance",
        "role": "CFO",
        "email": "heri.supriadi@telkom.co.id",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    # Vinhomes
    {
        "company_name": "Vinhomes JSC",
        "name": "Nguyen Viet Quang",
        "title": "Vice Chairman & CEO",
        "role": "CEO",
        "email": "quang.nv@vinhomes.vn",
        "country": "Vietnam",
        "is_decision_maker": True,
        "priority": True,
    },
    # Meralco
    {
        "company_name": "Manila Electric Company (Meralco)",
        "name": "Manuel V. Pangilinan",
        "title": "Chairman",
        "role": "BOARD",
        "email": "mvp@meralco.com.ph",
        "country": "Philippines",
        "is_decision_maker": True,
        "priority": True,
    },
    {
        "company_name": "Manila Electric Company (Meralco)",
        "name": "Ronnie Aperocho",
        "title": "Chief Finance Officer",
        "role": "CFO",
        "email": "r.aperocho@meralco.com.ph",
        "country": "Philippines",
        "is_decision_maker": True,
        "priority": True,
    },
    # AIS
    {
        "company_name": "AIS (Advanced Info Service)",
        "name": "Somchai Lertsutiwong",
        "title": "CEO",
        "role": "CEO",
        "email": "somchai@ais.th",
        "country": "Thailand",
        "is_decision_maker": True,
        "priority": True,
    },
    # Merdeka Battery
    {
        "company_name": "Merdeka Battery Materials",
        "name": "Devin Ridwan",
        "title": "President Director",
        "role": "CEO",
        "email": "devin.ridwan@mbma.co.id",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    {
        "company_name": "Merdeka Battery Materials",
        "name": "Tommy Tan",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "email": "tommy.tan@mbma.co.id",
        "country": "Indonesia",
        "is_decision_maker": True,
        "priority": True,
    },
    # STT GDC
    {
        "company_name": "STT GDC (ST Telemedia Global Data Centres)",
        "name": "Bruno Lopez",
        "title": "President & CEO",
        "role": "CEO",
        "email": "b.lopez@stt-gdc.com",
        "country": "Singapore",
        "is_decision_maker": True,
        "priority": True,
    },
    # Viettel
    {
        "company_name": "Viettel Group",
        "name": "Le Dang Dung",
        "title": "Chairman",
        "role": "BOARD",
        "email": "ledangdung@viettel.com.vn",
        "country": "Vietnam",
        "is_decision_maker": True,
        "priority": True,
    },
    {
        "company_name": "Viettel Group",
        "name": "Tao Duc Thang",
        "title": "General Director",
        "role": "CEO",
        "email": "taothang@viettel.com.vn",
        "country": "Vietnam",
        "is_decision_maker": True,
        "priority": True,
    },
]

# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------

DEALS_RAW = [
    # ── 1 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "PT Indosat Ooredoo Hutchison",
        "country": "Indonesia",
        "sector": "Telecom",
        "company_description": "Indonesia's second-largest telco by subscribers (100M+). "
                               "Hutchison Asia Telecom-controlled after 2022 merger.",
        "financing_type": "Dim Sum Bond",
        "estimated_size_mn": 400.0,
        "currency": "CNH",
        "purpose": "5G network infrastructure rollout across Java, Sumatra and Kalimantan",
        "tenor": "5Y",
        "urgency": "HIGH",
        "stage": "ANALYSIS",
        "source": "intelligence",
        "china_linked": True,
        "belt_road": False,
        "dim_sum_feasible": True,
        "dim_sum_notes": "Hutchison parent provides implicit support; CNH investor base comfortable with Indonesian telco credit.",
        "dim_sum_size_mn": 400.0,
        "dim_sum_tenor": "5Y",
        "dim_sum_investor_appeal": "CK Hutchison parentage, strong recurring cash flows, rated BB+.",
        "why_suitable": "UKMC has existing Hutchison Group relationships in HK. Indonesian telco with Chinese parent is perfect CNH bond issuer profile.",
        "financing_angle": "Leverage Hutchison parent guarantee or keepwell to achieve Dim Sum pricing advantage over USD bonds.",
        "potential_lenders": "CITIC Securities, Haitong International, CICC, HSBC, Standard Chartered",
        "chinese_counterparties": "CK Hutchison Holdings, China Development Bank",
        "entry_strategy": "Approach CFO Nicky Lee via HK Hutchison corporate team introduction.",
        "competitive_landscape": "Citi, HSBC, and Standard Chartered are incumbent DCM banks.",
        "next_action": "MEETING",
        "next_action_detail": "Schedule CFO introductory meeting via Hutchison Asia HK desk.",
        "priority": "HIGH",
        "created_at": _ago(18),
        "updated_at": _ago(2),
    },
    # ── 2 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "PT Vale Indonesia",
        "country": "Indonesia",
        "sector": "Mining / Nickel Smelting",
        "company_description": "Major nickel producer in South Sulawesi. Expanding RKEF smelting "
                               "capacity with Chinese JV partner Zhejiang Huayou Cobalt.",
        "financing_type": "Project Finance",
        "estimated_size_mn": 650.0,
        "currency": "USD",
        "purpose": "RKEF Smelter Phase 2 expansion at Sorowako (120k tonne nickel matte capacity)",
        "tenor": "10Y",
        "urgency": "HIGH",
        "stage": "OUTREACH",
        "source": "intelligence",
        "china_linked": True,
        "belt_road": True,
        "dim_sum_feasible": True,
        "dim_sum_notes": "Huayou JV provides Chinese bank comfort; could issue RMB tranche via Huayou guarantee.",
        "dim_sum_size_mn": 200.0,
        "dim_sum_tenor": "5Y",
        "why_suitable": "Chinese JV partner (Huayou Cobalt) is key. Nickel/EV battery nexus is highest-priority sector for UKMC.",
        "financing_angle": "ECA-backed USD tranche (Sinosure/CEXIM) + Dim Sum CNH tranche for Chinese equipment component.",
        "potential_lenders": "China Exim Bank, China Development Bank, ICBC, Bank of China, ING",
        "chinese_counterparties": "Zhejiang Huayou Cobalt, CITIC, China Merchants",
        "entry_strategy": "Engage through Huayou Cobalt Beijing office; Huayou will push for Chinese bank financing.",
        "competitive_landscape": "Vale Canada treasury team prefers Western banks. Chinese banks are aggressively competing.",
        "next_action": "PROPOSAL",
        "next_action_detail": "Submit indicative financing term sheet to CFO Bernardus Irmanto.",
        "priority": "HIGH",
        "created_at": _ago(25),
        "updated_at": _ago(1),
    },
    # ── 3 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "Harita Nickel",
        "country": "Indonesia",
        "sector": "Mining / HPAL Nickel",
        "company_description": "HPAL nickel processor on Obi Island. Chinese JV with Ningbo Lygend. "
                               "Significant MHP (mixed hydroxide precipitate) exporter to Korean/Japanese battery makers.",
        "financing_type": "ECA-Backed Project Finance",
        "estimated_size_mn": 500.0,
        "currency": "USD",
        "purpose": "HPAL Line 3 expansion for additional 37,000 tpa MHP output",
        "tenor": "12Y",
        "urgency": "HIGH",
        "stage": "PROPOSAL",
        "source": "referral",
        "china_linked": True,
        "belt_road": True,
        "dim_sum_feasible": True,
        "dim_sum_size_mn": 150.0,
        "dim_sum_tenor": "3Y",
        "dim_sum_notes": "Construction bridge financing tranche can be structured as Dim Sum via Lygend guarantee.",
        "why_suitable": "ECA mandate opportunity: Sinosure covers Chinese equipment (HPAL reactors sourced from China). UKMC positioned as arranger.",
        "financing_angle": "Dual-tranche: Sinosure/CEXIM USD term loan + CNH construction bridge via Lygend guarantee.",
        "potential_lenders": "China Exim Bank, Sinosure-backed commercial banks (ICBC, BOC), DBS, OCBC",
        "chinese_counterparties": "Ningbo Lygend Mining (49% JV), Sinosure",
        "entry_strategy": "Referred by DBS Jakarta; meet President Director Roy Arfandy to present mandate proposal.",
        "competitive_landscape": "DBS and Mandiri are incumbent banks; no dedicated Chinese bank arranger yet.",
        "next_action": "PROPOSAL",
        "next_action_detail": "Finalise term sheet and present to board within 2 weeks.",
        "priority": "HIGH",
        "created_at": _ago(10),
        "updated_at": _ago(1),
    },
    # ── 4 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "Viettel Group",
        "country": "Vietnam",
        "sector": "Telecom / 5G Infrastructure",
        "company_description": "Vietnam's largest telco and military conglomerate. "
                               "State-owned; nationwide 5G rollout mandated by government.",
        "financing_type": "Infrastructure Financing",
        "estimated_size_mn": 800.0,
        "currency": "USD",
        "purpose": "Nationwide 5G radio access network deployment (30,000+ base stations)",
        "tenor": "7Y",
        "urgency": "HIGH",
        "stage": "RESEARCH",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "State-backed sovereign credit; Vietnam is a priority market. "
                        "Telecom infrastructure is #1 sector priority for UKMC deal origination.",
        "financing_angle": "Export credit backed term loan (Ericsson ECA or Nokia ECA) with UKMC as arranger.",
        "potential_lenders": "Vietcombank, BIDV, Bank of China Vietnam, ANZ, Societe Generale",
        "entry_strategy": "Approach through Vietnam Ministry of Finance contacts; request introduction to Viettel treasury.",
        "competitive_landscape": "BIDV and Vietcombank provide domestic credit; no international structured finance arranger engaged.",
        "next_action": "MEETING",
        "next_action_detail": "Arrange meeting with General Director Tao Duc Thang via Ministry of Finance introduction.",
        "priority": "HIGH",
        "created_at": _ago(14),
        "updated_at": _ago(3),
    },
    # ── 5 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "Telkom Indonesia Data Centers",
        "country": "Indonesia",
        "sector": "Data Centers",
        "company_description": "Telkom Indonesia's hyperscale data centre subsidiary (Metra Digital Investama). "
                               "Plans 3 new hyperscale DCs in Jakarta, Batam and Surabaya.",
        "financing_type": "Project Finance",
        "estimated_size_mn": 350.0,
        "currency": "USD",
        "purpose": "Hyperscale data centre campus development — Jakarta Phase 2 (60MW capacity)",
        "tenor": "8Y",
        "urgency": "HIGH",
        "stage": "ANALYSIS",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "AI and data center infrastructure is fastest-growing segment in SEA. "
                        "Telkom's SOE status de-risks credit. Hyperscale DC finance is a key UKMC capability.",
        "financing_angle": "Green infrastructure loan with IFC or ADB participation; potential hyperscaler anchor tenant (Microsoft, AWS) provides offtake.",
        "potential_lenders": "IFC, ADB Private Sector, DBS, MUFG, Sumitomo Mitsui",
        "entry_strategy": "Engage through Telkom CFO office in Bandung; leverage existing Telkom IR contacts.",
        "competitive_landscape": "Mandiri, BNI, and MUFG are lead banks on prior Telkom facilities.",
        "next_action": "MEETING",
        "next_action_detail": "Meet Director of Finance Heri Supriadi to present DC project financing framework.",
        "priority": "HIGH",
        "created_at": _ago(8),
        "updated_at": _ago(2),
    },
    # ── 6 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "Merdeka Battery Materials",
        "country": "Indonesia",
        "sector": "Battery Supply Chain",
        "company_description": "Integrated battery materials producer (Ni, Co, Mn) in Morowali, Central Sulawesi. "
                               "JV with CATL for MHP-to-precursor processing.",
        "financing_type": "Structured Finance",
        "estimated_size_mn": 450.0,
        "currency": "USD",
        "purpose": "HPAL + precursor plant construction in Indonesia Morowali Industrial Park (IMIP)",
        "tenor": "10Y",
        "urgency": "HIGH",
        "stage": "OUTREACH",
        "source": "intelligence",
        "china_linked": True,
        "belt_road": True,
        "dim_sum_feasible": True,
        "dim_sum_size_mn": 130.0,
        "dim_sum_tenor": "3Y",
        "dim_sum_notes": "CATL can provide keepwell for a CNH bridge bond for pre-completion phase.",
        "why_suitable": "CATL JV provides Chinese bank comfort. Battery materials is highest conviction sector for UKMC.",
        "financing_angle": "Sinosure ECA + CATL guarantee; potential USD green bond for completed assets.",
        "potential_lenders": "China Exim Bank, ICBC, Bank of China, Mandiri, DBS Singapore",
        "chinese_counterparties": "CATL (Contemporary Amperex Technology), Ford Motor (for offtake)",
        "entry_strategy": "Engage CATL International Finance team in Shenzhen; they will mandate UKMC alongside Chinese banks.",
        "next_action": "OUTREACH",
        "next_action_detail": "Send introductory note to CFO Tommy Tan; reference CATL relationship.",
        "priority": "HIGH",
        "created_at": _ago(12),
        "updated_at": _ago(1),
    },
    # ── 7 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "Manila Electric Company (Meralco)",
        "country": "Philippines",
        "sector": "Power / Renewables",
        "company_description": "Philippines' largest power distributor. Expanding into solar, wind and "
                               "battery energy storage via subsidiary MGen Renewable Energy.",
        "financing_type": "ESG Financing",
        "estimated_size_mn": 300.0,
        "currency": "USD",
        "purpose": "Green bond issuance to fund 400MW solar + BESS projects in Luzon",
        "tenor": "7Y",
        "urgency": "MEDIUM",
        "stage": "RESEARCH",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Philippine utilities are strong credit. ESG/Green bond market growing rapidly. "
                        "Meralco has explicit ESG framework.",
        "financing_angle": "Green bond under CBI-certified framework; blended finance with ADB Green Climate Fund.",
        "potential_lenders": "ADB, IFC, Credit Suisse, HSBC, BPI Capital",
        "entry_strategy": "Approach through Manuel Pangilinan (MVP) network; UKMC HK office connection to First Pacific.",
        "next_action": "RESEARCH",
        "next_action_detail": "Obtain Meralco Green Finance Framework; review existing credit facilities.",
        "priority": "NORMAL",
        "created_at": _ago(20),
        "updated_at": _ago(5),
    },
    # ── 8 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "AIS (Advanced Info Service)",
        "country": "Thailand",
        "sector": "Telecom / 5G",
        "company_description": "Thailand's largest mobile operator (45M subscribers). "
                               "Deploying nationwide 5G with significant capex committed for 2024-2026.",
        "financing_type": "USD Bond",
        "estimated_size_mn": 500.0,
        "currency": "USD",
        "purpose": "Refinancing of 2019 USD notes maturing 2025; partially fund 5G capex programme",
        "tenor": "5Y / 10Y dual tranche",
        "urgency": "HIGH",
        "stage": "DISCOVERY",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Bond maturity event creates mandatory refinancing. AIS A- rated; highly bookable for Asian DCM syndicate.",
        "financing_angle": "144A/Reg-S USD benchmark bond; consider adding ESG/sustainability-linked tranche.",
        "potential_lenders": "HSBC, Citigroup, Deutsche Bank, UBS, Bangkok Bank",
        "entry_strategy": "Cold approach to AIS CFO via UKMC Bangkok network; pitch on competitive pricing and distribution.",
        "next_action": "RESEARCH",
        "next_action_detail": "Review existing AIS debt structure and bond covenants. Prepare pitch deck.",
        "priority": "NORMAL",
        "created_at": _ago(6),
        "updated_at": _ago(6),
    },
    # ── 9 ───────────────────────────────────────────────────────────────────
    {
        "company_name": "STT GDC SEA Expansion",
        "country": "Singapore",
        "sector": "Data Centers",
        "company_description": "ST Telemedia Global Data Centres expanding hyperscale campus in Singapore, "
                               "Malaysia (Johor) and Thailand. Temasek-linked balance sheet.",
        "financing_type": "Structured Finance",
        "estimated_size_mn": 600.0,
        "currency": "USD",
        "purpose": "Construction financing for 3 new hyperscale campuses (Singapore JTC, Johor, Bangkok)",
        "tenor": "7Y",
        "urgency": "MEDIUM",
        "stage": "RESEARCH",
        "source": "referral",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Temasek parent provides implicit support. AI infrastructure boom driving insatiable DC demand. "
                        "Singapore/Malaysia cross-border DC finance is a growing UKMC niche.",
        "financing_angle": "Green infrastructure loan; potential REIT spin-off creates exit for lenders.",
        "potential_lenders": "DBS, OCBC, UOB, Sumitomo, Macquarie Infrastructure Finance",
        "entry_strategy": "Introduced by Temasek infrastructure team. Approach CEO Bruno Lopez directly.",
        "next_action": "MEETING",
        "next_action_detail": "Initial meeting with STT GDC CFO to discuss construction financing options.",
        "priority": "NORMAL",
        "created_at": _ago(9),
        "updated_at": _ago(4),
    },
    # ── 10 ──────────────────────────────────────────────────────────────────
    {
        "company_name": "Vietnam Offshore Wind (EVN / Ørsted JV)",
        "country": "Vietnam",
        "sector": "Renewable Energy",
        "company_description": "Proposed JV between Electricity of Vietnam (EVN) and Ørsted for a "
                               "1.5 GW offshore wind farm in the Binh Thuan province.",
        "financing_type": "Project Finance",
        "estimated_size_mn": 2200.0,
        "currency": "USD",
        "purpose": "Construction and operation of 1.5 GW offshore wind project — Vietnam's first utility-scale offshore wind",
        "tenor": "18Y",
        "urgency": "MEDIUM",
        "stage": "DISCOVERY",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Largest renewable project in SEA pipeline. UKMC can lead blended finance with MDB participation. "
                        "Vietnam has committed to 6GW offshore wind by 2030.",
        "financing_angle": "Blended finance: Asian Development Bank + IFC + DFI equity; commercial debt syndication by UKMC.",
        "potential_lenders": "ADB, IFC, Proparco, MUFG, Sumitomo Mitsui, Standard Chartered",
        "entry_strategy": "Engage through ADB Clean Energy division; approach Ørsted Global Finance in Copenhagen.",
        "next_action": "RESEARCH",
        "next_action_detail": "Obtain Ørsted Vietnam project development status and offtake term sheet from EVN.",
        "priority": "NORMAL",
        "created_at": _ago(4),
        "updated_at": _ago(4),
    },
    # ── 11 ──────────────────────────────────────────────────────────────────
    {
        "company_name": "PT Pelabuhan Indonesia (Pelindo)",
        "country": "Indonesia",
        "sector": "Port / Logistics",
        "company_description": "State-owned Indonesian port operator managing 600+ ports nationwide "
                               "after 2021 merger of Pelindo I-IV. Modernisation and automation capex.",
        "financing_type": "Infrastructure Financing",
        "estimated_size_mn": 750.0,
        "currency": "USD",
        "purpose": "Port modernisation Phase 2: automation, quay extension and logistics hub at Tanjung Priok (Jakarta) and Belawan (Medan)",
        "tenor": "15Y",
        "urgency": "MEDIUM",
        "stage": "DISCOVERY",
        "source": "manual",
        "china_linked": True,
        "belt_road": True,
        "dim_sum_feasible": False,
        "why_suitable": "SOE client with sovereign backing; port infrastructure perfectly matches UKMC's BRI deal flow. "
                        "Chinese equipment suppliers (Zpmc cranes) create ECA angle.",
        "financing_angle": "Sinosure-backed ECA financing for Zpmc crane procurement; IFC/ADB co-loan for port infrastructure.",
        "potential_lenders": "China Exim Bank, IFC, ADB, Bank Mandiri, BNI",
        "entry_strategy": "Approach through Indonesian BUMN ministry contacts; Pelindo board has Ministry of SOE representatives.",
        "next_action": "RESEARCH",
        "next_action_detail": "Research Pelindo 2025-2029 capex plan and existing financing.",
        "priority": "NORMAL",
        "created_at": _ago(3),
        "updated_at": _ago(3),
    },
    # ── 12 ──────────────────────────────────────────────────────────────────
    {
        "company_name": "Vinhomes Green Smart City",
        "country": "Vietnam",
        "sector": "Real Estate",
        "company_description": "Vinhomes' flagship 900ha smart city township in Hanoi outer ring. "
                               "USD 4Bn development including residential, commercial and smart infrastructure.",
        "financing_type": "Bridge Financing",
        "estimated_size_mn": 250.0,
        "currency": "USD",
        "purpose": "Construction bridge facility for Phase 3 residential towers and commercial podium",
        "tenor": "3Y",
        "urgency": "MEDIUM",
        "stage": "RESEARCH",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Vinhomes is Vietnam's most creditworthy developer. Bridge-to-bond refinancing is a clear fee opportunity.",
        "financing_angle": "Construction bridge loan (3Y) to be refinanced with USD Reg-S bond on completion.",
        "potential_lenders": "HSBC, Standard Chartered, Techcombank, VPBank, Deutsche Bank",
        "entry_strategy": "Approach Vinhomes CFO team via HSBC Vietnam introduction.",
        "next_action": "MEETING",
        "next_action_detail": "Schedule intro meeting with Vinhomes corporate finance team.",
        "priority": "NORMAL",
        "created_at": _ago(7),
        "updated_at": _ago(7),
    },
    # ── 13 ──────────────────────────────────────────────────────────────────
    {
        "company_name": "Malaysia Airports Holdings Berhad (MAHB)",
        "country": "Malaysia",
        "sector": "Infrastructure / Aviation",
        "company_description": "State-linked operator of 39 airports in Malaysia including KLIA. "
                               "Sukuk issuer; significant upcoming capital works at KLIA Terminal 2.",
        "financing_type": "Structured Finance",
        "estimated_size_mn": 600.0,
        "currency": "USD",
        "purpose": "KLIA T2 expansion and KLIA Aeropolis logistics hub development",
        "tenor": "10Y",
        "urgency": "MEDIUM",
        "stage": "DISCOVERY",
        "source": "manual",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "GLC (Government-Linked Company) credit with implicit government support. Airport infrastructure is a core BRI-adjacent asset class.",
        "financing_angle": "Islamic sukuk + potential Dim Sum CNH tranche for Chinese tourist infrastructure investment narrative.",
        "potential_lenders": "CIMB, Maybank, RHB, HSBC, Standard Chartered",
        "entry_strategy": "Approach via Khazanah Nasional investment team; MAHB board has Khazanah representative.",
        "next_action": "RESEARCH",
        "next_action_detail": "Review MAHB masterplan and existing sukuk programme.",
        "priority": "NORMAL",
        "created_at": _ago(5),
        "updated_at": _ago(5),
    },
    # ── 14 ──────────────────────────────────────────────────────────────────
    {
        "company_name": "PT Medco Energi Internasional",
        "country": "Indonesia",
        "sector": "Oil & Gas",
        "company_description": "Leading Indonesian independent E&P company with operations in Indonesia, "
                               "Libya, Tanzania and South America. Listed on IDX.",
        "financing_type": "Prepayment Facility",
        "estimated_size_mn": 300.0,
        "currency": "USD",
        "purpose": "Oil prepayment facility for Corridor Block production advance (Sumatra)",
        "tenor": "5Y",
        "urgency": "LOW",
        "stage": "DISCOVERY",
        "source": "manual",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Prepayment structures are high-margin advisory product. Medco has established commodity trading relationships.",
        "financing_angle": "Commodity prepayment facility against contracted gas sales from Corridor Block.",
        "potential_lenders": "Standard Chartered, ING, BNP Paribas, Citigroup",
        "entry_strategy": "Direct approach to Medco CFO office in Jakarta; pitch commodity finance expertise.",
        "next_action": "RESEARCH",
        "next_action_detail": "Obtain Medco Corridor Block reserve report and existing credit facility terms.",
        "priority": "LOW",
        "created_at": _ago(15),
        "updated_at": _ago(15),
    },
    # ── 15 ──────────────────────────────────────────────────────────────────
    {
        "company_name": "Globe Telecom Philippines — Fiber Optic",
        "country": "Philippines",
        "sector": "Telecom / Fiber Optic",
        "company_description": "Globe Telecom is the second-largest telco in Philippines. "
                               "Aggressively expanding fiber-to-the-home (FTTH) to 3M homes.",
        "financing_type": "Infrastructure Financing",
        "estimated_size_mn": 250.0,
        "currency": "USD",
        "purpose": "FTTH fiber optic rollout: 3 million home-pass target by 2026 in Metro Manila and Cebu",
        "tenor": "8Y",
        "urgency": "MEDIUM",
        "stage": "RESEARCH",
        "source": "intelligence",
        "china_linked": False,
        "belt_road": False,
        "dim_sum_feasible": False,
        "why_suitable": "Philippines broadband penetration still <40%. Globe has Ayala and Singtel backing — strong credit. "
                        "Infrastructure financing is core UKMC product.",
        "financing_angle": "IFC/ADB participation reduces risk; potential Singtel parent support for pricing.",
        "potential_lenders": "ADB, IFC, BDO Unibank, BPI Capital, Singtel treasury",
        "entry_strategy": "Approach Globe CFO through BDO or BPI relationship introduction.",
        "next_action": "RESEARCH",
        "next_action_detail": "Obtain Globe annual report and ICT infrastructure bond issuance history.",
        "priority": "NORMAL",
        "created_at": _ago(11),
        "updated_at": _ago(11),
    },
]

# ---------------------------------------------------------------------------
# Intelligence Signals
# ---------------------------------------------------------------------------

SIGNALS_RAW = [
    {
        "signal_type": "SPECTRUM",
        "company_name": "PT Indosat Ooredoo Hutchison",
        "country": "Indonesia",
        "sector": "Telecom",
        "headline": "Indosat wins 5G spectrum block in 3.5 GHz band; announces USD 2Bn 5G capex plan",
        "summary": "Indonesia's Ministry of Communication awarded IOH a 35MHz block in the 3.5GHz mid-band. "
                   "CEO Vikram Sinha confirmed USD 2Bn in 5G network investment over 3 years starting 2025. "
                   "The company will seek offshore financing to supplement domestic bank facilities.",
        "source_url": "https://www.reuters.com/technology/indosat-5g-spectrum-2024",
        "source_name": "Reuters",
        "urgency": "HIGH",
        "financing_implied_mn": 2000.0,
        "detected_at": _ago(20),
        "deal_created": True,
    },
    {
        "signal_type": "SMELTER",
        "company_name": "PT Vale Indonesia",
        "country": "Indonesia",
        "sector": "Nickel Mining",
        "headline": "Vale Indonesia and Huayou Cobalt break ground on RKEF Phase 2 smelter expansion",
        "summary": "PT Vale Indonesia and Chinese partner Zhejiang Huayou Cobalt held a ground-breaking "
                   "ceremony for the USD 650M Phase 2 RKEF smelter expansion at Sorowako. "
                   "Financing is being arranged with multiple bank mandates expected by Q2 2025.",
        "source_url": "https://www.ft.com/content/vale-indonesia-smelter-2024",
        "source_name": "Financial Times",
        "urgency": "HIGH",
        "financing_implied_mn": 650.0,
        "detected_at": _ago(25),
        "deal_created": True,
    },
    {
        "signal_type": "EXPANSION",
        "company_name": "Harita Nickel",
        "country": "Indonesia",
        "sector": "Nickel HPAL",
        "headline": "Harita Nickel announces HPAL Line 3 feasibility study completion; targets 2026 production start",
        "summary": "PT Trimegah Bangun Persada (Harita Nickel) confirmed feasibility study for HPAL Line 3 "
                   "is complete. The project targets 37,000 tpa additional MHP capacity. "
                   "Bank mandates for USD 500M project financing expected Q3 2025.",
        "source_url": "https://www.bloomberg.com/news/harita-hpal-2024",
        "source_name": "Bloomberg",
        "urgency": "HIGH",
        "financing_implied_mn": 500.0,
        "detected_at": _ago(12),
        "deal_created": True,
    },
    {
        "signal_type": "INFRASTRUCTURE",
        "company_name": "Viettel Group",
        "country": "Vietnam",
        "sector": "Telecom",
        "headline": "Vietnam government mandates Viettel achieve 99% 5G coverage by 2028; USD 800M capex required",
        "summary": "Vietnam's Ministry of Information and Communications issued Directive 20/2024 "
                   "requiring state-owned telcos to achieve 99% 5G population coverage by end-2028. "
                   "Viettel estimates USD 800M in additional network capex is needed.",
        "source_url": "https://www.vir.com.vn/viettel-5g-directive-2024",
        "source_name": "Vietnam Investment Review",
        "urgency": "HIGH",
        "financing_implied_mn": 800.0,
        "detected_at": _ago(15),
        "deal_created": True,
    },
    {
        "signal_type": "DATA_CENTER",
        "company_name": "Telkom Indonesia Data Centers",
        "country": "Indonesia",
        "sector": "Data Centers",
        "headline": "Telkom Indonesia announces 200MW data centre masterplan; seeks project finance partners",
        "summary": "Telkom's subsidiary Metra Digital Investama unveiled a masterplan for 200MW of hyperscale "
                   "data centre capacity by 2030. Phase 2 (60MW, Jakarta) is shovel-ready with an estimated "
                   "project cost of USD 350M. Telkom seeks project finance rather than corporate debt.",
        "source_url": "https://techinasia.com/telkom-dc-masterplan-2024",
        "source_name": "Tech in Asia",
        "urgency": "HIGH",
        "financing_implied_mn": 350.0,
        "detected_at": _ago(9),
        "deal_created": True,
    },
    {
        "signal_type": "EXPANSION",
        "company_name": "Merdeka Battery Materials",
        "country": "Indonesia",
        "sector": "Battery Supply Chain",
        "headline": "CATL and Merdeka Battery confirm Phase 2 HPAL plant; USD 450M financing mandate",
        "summary": "Merdeka Battery Materials and Chinese partner CATL confirmed Phase 2 of the precursor "
                   "HPAL plant at IMIP Morowali. USD 450M in project financing is to be structured with "
                   "Chinese policy banks and commercial lenders. CATL may provide credit support.",
        "source_url": "https://www.spglobal.com/merdeka-catl-2024",
        "source_name": "S&P Global Platts",
        "urgency": "HIGH",
        "financing_implied_mn": 450.0,
        "detected_at": _ago(13),
        "deal_created": True,
    },
    {
        "signal_type": "RENEWABLE",
        "company_name": "Manila Electric Company (Meralco)",
        "country": "Philippines",
        "sector": "Power / Renewables",
        "headline": "Meralco MGen wins 3 solar + BESS contracts totalling 400MW; seeks green bond mandate",
        "summary": "MGen Renewable Energy (Meralco subsidiary) won 3 competitive renewable auction awards "
                   "totalling 400MW solar-plus-storage. The CFO confirmed a green bond roadshow is being "
                   "planned for H2 2025 to raise USD 300M.",
        "source_url": "https://businessmirror.com.ph/meralco-green-bond-2024",
        "source_name": "Business Mirror PH",
        "urgency": "MEDIUM",
        "financing_implied_mn": 300.0,
        "detected_at": _ago(22),
        "deal_created": True,
    },
    {
        "signal_type": "BOND_MATURITY",
        "company_name": "AIS (Advanced Info Service)",
        "country": "Thailand",
        "sector": "Telecom",
        "headline": "AIS USD 500M 3.9% notes due March 2025 — refinancing mandatory, no tender announced",
        "summary": "Advanced Info Service's USD 500M bond (ISIN XS1234567890) matures in March 2025. "
                   "The company has not yet announced a tender or replacement issuance. "
                   "Market consensus expects a new 5/10 year dual-tranche.",
        "source_url": "https://www.bondradar.com/ais-maturity-2025",
        "source_name": "BondRadar",
        "urgency": "HIGH",
        "financing_implied_mn": 500.0,
        "detected_at": _ago(7),
        "deal_created": True,
    },
    {
        "signal_type": "DATA_CENTER",
        "company_name": "STT GDC SEA Expansion",
        "country": "Singapore",
        "sector": "Data Centers",
        "headline": "ST Telemedia GDC secures 3 new DC site approvals in Singapore, Johor and Bangkok",
        "summary": "STT GDC announced regulatory approvals for three hyperscale campuses. "
                   "Total development cost estimated at USD 1.8Bn. The company plans to raise "
                   "USD 600M in project finance and use the remainder from parent balance sheet.",
        "source_url": "https://datacenterdynamics.com/stt-sea-expansion-2024",
        "source_name": "Data Center Dynamics",
        "urgency": "MEDIUM",
        "financing_implied_mn": 600.0,
        "detected_at": _ago(10),
        "deal_created": True,
    },
    # Unreviewed / not-yet-converted signals
    {
        "signal_type": "RENEWABLE",
        "company_name": "PLNP (PLN Indonesia Power)",
        "country": "Indonesia",
        "sector": "Renewable Energy",
        "headline": "PLN Indonesia Power seeks USD 1.2Bn green financing for 3GW geothermal expansion",
        "summary": "PLN's generation subsidiary submitted a request for proposal to international banks "
                   "for a USD 1.2Bn green loan facility to fund 3GW geothermal development in Sumatra and Java. "
                   "Responses expected by Q1 2025.",
        "source_url": "https://www.pln.co.id/media-release/geothermal-2024",
        "source_name": "PLN Official",
        "urgency": "HIGH",
        "financing_implied_mn": 1200.0,
        "detected_at": _ago(3),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "ACQUISITION",
        "company_name": "Axiata Group",
        "country": "Malaysia",
        "sector": "Telecom",
        "headline": "Axiata in advanced talks to acquire Indosat stake from Hutchison Asia — USD 2Bn deal",
        "summary": "Multiple sources confirm Axiata Group Berhad is in advanced negotiations to acquire "
                   "Hutchison Asia Telecom's 65.6% stake in PT Indosat Ooredoo Hutchison for approximately "
                   "USD 2Bn. Financing for the acquisition is yet to be arranged.",
        "source_url": "https://www.dealstreetasia.com/axiata-indosat-2024",
        "source_name": "DealStreetAsia",
        "urgency": "HIGH",
        "financing_implied_mn": 2000.0,
        "detected_at": _ago(2),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "INFRASTRUCTURE",
        "company_name": "Johor-Singapore SEZ Authority",
        "country": "Malaysia",
        "sector": "Industrial Park",
        "headline": "Johor-Singapore Special Economic Zone approved: USD 3Bn industrial infrastructure needed",
        "summary": "The Malaysian and Singapore governments officially gazetted the Johor-Singapore SEZ. "
                   "A development authority is seeking financing partners for USD 3Bn of industrial park "
                   "infrastructure including power, water, ICT and logistics. Chinese investors are among "
                   "the preferred industrial tenants.",
        "source_url": "https://www.straitstimes.com/johor-sez-2024",
        "source_name": "Straits Times",
        "urgency": "HIGH",
        "financing_implied_mn": 3000.0,
        "detected_at": _ago(1),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "CAPEX",
        "company_name": "Singtel / NCS Group",
        "country": "Singapore",
        "sector": "AI Infrastructure",
        "headline": "NCS (Singtel) to build SGD 1Bn AI compute campus in Jurong; seeks green financing",
        "summary": "NCS, Singtel's IT services arm, announced plans for a SGD 1Bn (USD 740M) AI compute "
                   "campus at Jurong Innovation District. The facility will house 50,000+ H100 GPUs for "
                   "regional AI workloads. Green financing partner RFP expected Q2 2025.",
        "source_url": "https://www.businesstimes.com.sg/ncs-ai-campus-2024",
        "source_name": "Business Times SG",
        "urgency": "HIGH",
        "financing_implied_mn": 740.0,
        "detected_at": _ago(2),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "REFINANCING",
        "company_name": "Genting Malaysia Berhad",
        "country": "Malaysia",
        "sector": "Hospitality",
        "headline": "Genting Malaysia refinancing MYR 5Bn revolving credit; exploring Dim Sum tranche",
        "summary": "Genting Malaysia is refinancing its MYR 5Bn revolving credit facility maturing in 2025. "
                   "The treasury team is exploring a Dim Sum CNH tranche to diversify the investor base and "
                   "fund expansion of Resorts World Genting's casino and hotel complex.",
        "source_url": "https://www.thestar.com.my/genting-refinancing-2024",
        "source_name": "The Star Malaysia",
        "urgency": "MEDIUM",
        "financing_implied_mn": 650.0,
        "detected_at": _ago(5),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "EXPANSION",
        "company_name": "Charoen Pokphand Group (CP)",
        "country": "Thailand",
        "sector": "Data Centers / Telecom",
        "headline": "CP Group announces USD 2Bn digital infrastructure investment in Thailand and Vietnam",
        "summary": "Charoen Pokphand Group (CP), Thailand's largest conglomerate, announced a USD 2Bn "
                   "digital infrastructure investment plan spanning data centres, fibre optic and 5G "
                   "tower infrastructure across Thailand and Vietnam, partly in partnership with Huawei.",
        "source_url": "https://www.bangkokpost.com/cp-digital-2024",
        "source_name": "Bangkok Post",
        "urgency": "MEDIUM",
        "financing_implied_mn": 2000.0,
        "detected_at": _ago(4),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "CAPEX",
        "company_name": "PT Freeport Indonesia",
        "country": "Indonesia",
        "sector": "Mining",
        "headline": "Freeport Indonesia announces USD 3Bn copper smelter project; seeks ECA financing",
        "summary": "PT Freeport Indonesia (51% Indonesian state ownership, 48.76% Freeport-McMoRan) "
                   "announced USD 3Bn copper smelter in Gresik, East Java is 80% complete. "
                   "Residual capex and working capital financing of USD 400M is being sought.",
        "source_url": "https://www.mining.com/freeport-smelter-2024",
        "source_name": "Mining.com",
        "urgency": "MEDIUM",
        "financing_implied_mn": 400.0,
        "detected_at": _ago(6),
        "deal_created": False,
        "reviewed": True,
    },
    {
        "signal_type": "IPO",
        "company_name": "Grab Holdings",
        "country": "Singapore",
        "sector": "Fintech",
        "headline": "Grab exploring secondary listing on HKEX; seeks USD 500M pre-IPO PIPE",
        "summary": "Grab Holdings is exploring a secondary listing on Hong Kong Stock Exchange in addition "
                   "to its existing Nasdaq listing. Pre-IPO PIPE investors are being sought for USD 500M "
                   "at a discount to Nasdaq price.",
        "source_url": "https://www.bloomberg.com/news/grab-hkex-2024",
        "source_name": "Bloomberg",
        "urgency": "MEDIUM",
        "financing_implied_mn": 500.0,
        "detected_at": _ago(8),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "INFRASTRUCTURE",
        "company_name": "EGAT (Electricity Generating Authority of Thailand)",
        "country": "Thailand",
        "sector": "Power / Renewable Energy",
        "headline": "EGAT launches USD 4Bn green bond programme; first USD tranche of USD 600M due H1 2025",
        "summary": "Thailand's state power utility EGAT announced a USD 4Bn green bond programme. "
                   "The first USD 600M tranche is expected in H1 2025 to fund solar and hydro "
                   "projects in Thailand and Laos. Lead managers have not yet been appointed.",
        "source_url": "https://www.bangkokpost.com/egat-green-bond-2024",
        "source_name": "Bangkok Post",
        "urgency": "HIGH",
        "financing_implied_mn": 600.0,
        "detected_at": _ago(3),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "EXPANSION",
        "company_name": "Vietnam Airlines",
        "country": "Vietnam",
        "sector": "Aviation",
        "headline": "Vietnam Airlines seeks USD 500M for 10 new A321neo aircraft; ECA or lease finance preferred",
        "summary": "Vietnam Airlines tendered for USD 500M in aircraft finance to cover 10 Airbus A321neo "
                   "deliveries in 2025-2026. The airline prefers EXIM-backed ECA financing or "
                   "Japanese operating lease with call options (JOLCO) structures.",
        "source_url": "https://www.aviationweek.com/vietnam-airlines-2024",
        "source_name": "Aviation Week",
        "urgency": "MEDIUM",
        "financing_implied_mn": 500.0,
        "detected_at": _ago(5),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "CAPEX",
        "company_name": "Indonesia Battery Corporation (IBC)",
        "country": "Indonesia",
        "sector": "Battery Supply Chain",
        "headline": "IBC and CATL sign MOU for 10 GWh battery cell gigafactory in Karawang, West Java",
        "summary": "Indonesia Battery Corporation (state-owned consortium including PLN and MIND ID) "
                   "and CATL signed an MOU for a 10 GWh battery cell gigafactory in Karawang. "
                   "Total investment estimated at USD 1.2Bn; financing structure TBD.",
        "source_url": "https://www.cnbc.com/ibc-catl-gigafactory-2024",
        "source_name": "CNBC",
        "urgency": "HIGH",
        "financing_implied_mn": 1200.0,
        "detected_at": _ago(1),
        "deal_created": False,
        "reviewed": False,
    },
    {
        "signal_type": "DISTRESS",
        "company_name": "Nusantara Infrastructure Tbk",
        "country": "Indonesia",
        "sector": "Infrastructure",
        "headline": "Nusantara Infrastructure seeks IDR 2Tn debt restructuring; payment default on toll concession",
        "summary": "Nusantara Infrastructure (IDX: META) disclosed a default on IDR 2Tn in toll road "
                   "concession debt. The company seeks a debt restructuring agreement with Indonesian banks "
                   "and has hired financial advisors.",
        "source_url": "https://www.bisnis.com/nusantara-infrastructure-2024",
        "source_name": "Bisnis Indonesia",
        "urgency": "LOW",
        "financing_implied_mn": 135.0,
        "detected_at": _ago(10),
        "deal_created": False,
        "reviewed": True,
    },
]


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

def seed_companies(db) -> dict:
    """Insert TargetCompany records; return {name: id} map."""
    company_map = {}
    for c in COMPANIES:
        existing = db.query(TargetCompany).filter_by(name=c["name"]).first()
        if existing:
            company_map[c["name"]] = existing.id
            continue
        obj = TargetCompany(**c)
        db.add(obj)
        db.flush()
        company_map[c["name"]] = obj.id
    db.commit()
    print(f"  [companies] seeded {len(company_map)} records")
    return company_map


def seed_contacts(db, company_map: dict) -> dict:
    """Insert Contact records; return {company_name -> list[contact_id]}."""
    contact_map: dict = {}
    for ct in CONTACTS:
        existing = db.query(Contact).filter_by(
            name=ct["name"], company_name=ct["company_name"]
        ).first()
        if existing:
            contact_map.setdefault(ct["company_name"], []).append(existing.id)
            continue
        cid = None
        for cname, cid_val in company_map.items():
            if cname.startswith(ct["company_name"][:12]):
                cid = cid_val
                break
        obj = Contact(
            company_id=cid,
            company_name=ct["company_name"],
            name=ct["name"],
            title=ct["title"],
            role=ct["role"],
            email=ct.get("email"),
            country=ct.get("country"),
            is_decision_maker=ct.get("is_decision_maker", False),
            priority=ct.get("priority", False),
        )
        db.add(obj)
        db.flush()
        contact_map.setdefault(ct["company_name"], []).append(obj.id)
    db.commit()
    print(f"  [contacts] seeded {sum(len(v) for v in contact_map.values())} records")
    return contact_map


def seed_deals(db, contact_map: dict) -> list:
    """Insert Deal records with scoring; return list of deal ids."""
    deal_ids = []
    for d in DEALS_RAW:
        existing = db.query(Deal).filter_by(
            company_name=d["company_name"]
        ).first()
        if existing:
            deal_ids.append(existing.id)
            continue

        scoring = score_deal(d)
        ds = score_dim_sum_feasibility(d)

        created_at = d.pop("created_at", datetime.utcnow())
        updated_at = d.pop("updated_at", datetime.utcnow())

        deal = Deal(
            **d,
            ukmc_fit_score=scoring["overall_score"],
            mandate_probability=scoring["mandate_probability"],
        )
        deal.created_at = created_at
        deal.updated_at = updated_at
        db.add(deal)
        db.flush()

        # Log creation activity
        db.add(DealActivity(
            deal_id=deal.id,
            activity_type="STAGE_CHANGE",
            description=f"Deal created in stage {deal.stage}.",
            user="System",
            created_at=created_at,
        ))

        # Attach contacts
        cname = deal.company_name
        for base_name, cids in contact_map.items():
            if cname.startswith(base_name[:12]):
                for cid in cids:
                    db.add(DealContact(deal_id=deal.id, contact_id=cid))
                break

        db.flush()
        deal_ids.append(deal.id)

    db.commit()
    print(f"  [deals] seeded {len(deal_ids)} records")
    return deal_ids


def seed_signals(db, deal_ids: list):
    """Insert IntelligenceSignal records."""
    count = 0
    converted_idx = 0  # index into deal_ids for signals with deal_created=True
    for s in SIGNALS_RAW:
        existing = db.query(IntelligenceSignal).filter_by(
            company_name=s["company_name"], headline=s["headline"]
        ).first()
        if existing:
            continue

        deal_id = None
        if s.get("deal_created") and converted_idx < len(deal_ids):
            deal_id = deal_ids[converted_idx]
            converted_idx += 1

        obj = IntelligenceSignal(
            signal_type=s["signal_type"],
            company_name=s["company_name"],
            country=s["country"],
            sector=s["sector"],
            headline=s["headline"],
            summary=s["summary"],
            source_url=s.get("source_url"),
            source_name=s.get("source_name"),
            urgency=s.get("urgency", "MEDIUM"),
            financing_implied_mn=s.get("financing_implied_mn"),
            deal_created=s.get("deal_created", False),
            deal_id=deal_id,
            reviewed=s.get("reviewed", False),
            detected_at=s.get("detected_at", datetime.utcnow()),
        )
        db.add(obj)
        count += 1

    db.commit()
    print(f"  [signals] seeded {count} records")


def seed_all(db=None):
    """Run full seed. Creates its own session if not provided."""
    own_session = db is None
    if own_session:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
    try:
        print("Seeding UKMC Deal Origination database...")
        company_map = seed_companies(db)
        contact_map = seed_contacts(db, company_map)
        deal_ids = seed_deals(db, contact_map)
        seed_signals(db, deal_ids)
        print("Done. Database seeded successfully.")
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    seed_all()
