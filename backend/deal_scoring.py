"""
UKMC Deal Scoring Engine
Scores deal opportunities on a 0-100 scale based on multiple criteria.
"""

from typing import Dict, List

SECTOR_WEIGHTS = {
    "telecom": 10,
    "data center": 10,
    "data centers": 10,
    "mining": 9,
    "nickel": 10,
    "smelting": 9,
    "smelter": 9,
    "power": 8,
    "renewable energy": 9,
    "renewables": 9,
    "logistics": 7,
    "port": 7,
    "ports": 7,
    "industrial park": 8,
    "infrastructure": 8,
    "fiber optic": 9,
    "subsea cable": 9,
    "ai infrastructure": 10,
    "battery supply": 10,
    "battery": 9,
    "oil & gas": 7,
    "manufacturing": 6,
    "real estate": 5,
    "hospitality": 4,
    "retail": 3,
    "fintech": 7,
    "healthcare": 6,
}

COUNTRY_WEIGHTS = {
    "indonesia": 10,
    "vietnam": 10,
    "hong kong": 9,
    "singapore": 9,
    "malaysia": 9,
    "thailand": 7,
    "philippines": 7,
    "uae": 8,
    "saudi arabia": 7,
    "china": 8,
    "india": 6,
    "cambodia": 5,
    "myanmar": 4,
    "laos": 4,
}

FINANCING_TYPE_WEIGHTS = {
    "dim sum bond": 10,
    "panda bond": 10,
    "usd bond": 9,
    "project finance": 9,
    "bridge financing": 8,
    "acquisition financing": 8,
    "structured finance": 8,
    "eca-backed": 9,
    "working capital": 6,
    "revolving facility": 6,
    "trade finance": 7,
    "supply chain financing": 7,
    "receivables financing": 6,
    "esg financing": 8,
    "spac / pipe": 8,
    "sblc/bg monetization": 7,
    "prepayment facility": 7,
    "infrastructure financing": 9,
}

URGENCY_WEIGHTS = {
    "HIGH": 15,
    "MEDIUM": 8,
    "LOW": 3,
}


def score_deal(deal_data: Dict) -> Dict:
    """
    Score a deal opportunity.
    Returns a dict with overall_score (0-100) and component breakdown.
    """
    scores = {}

    # 1. Sector score (0-10)
    sector = (deal_data.get("sector") or "").lower()
    sector_score = 0
    for k, v in SECTOR_WEIGHTS.items():
        if k in sector:
            sector_score = max(sector_score, v)
    scores["sector"] = sector_score

    # 2. Country score (0-10)
    country = (deal_data.get("country") or "").lower()
    country_score = 0
    for k, v in COUNTRY_WEIGHTS.items():
        if k in country:
            country_score = max(country_score, v)
    scores["country"] = country_score

    # 3. Financing type score (0-10)
    fin_type = (deal_data.get("financing_type") or "").lower()
    fin_score = 0
    for k, v in FINANCING_TYPE_WEIGHTS.items():
        if k in fin_type:
            fin_score = max(fin_score, v)
    scores["financing_type"] = fin_score

    # 4. Deal size score (0-10)
    size = deal_data.get("estimated_size_mn") or 0
    if size >= 500:
        size_score = 10
    elif size >= 200:
        size_score = 8
    elif size >= 100:
        size_score = 6
    elif size >= 50:
        size_score = 4
    elif size >= 20:
        size_score = 2
    else:
        size_score = 1
    scores["deal_size"] = size_score

    # 5. Urgency score (0-15)
    urgency = deal_data.get("urgency", "MEDIUM")
    scores["urgency"] = URGENCY_WEIGHTS.get(urgency, 5)

    # 6. China / BRI bonus (0-10)
    china_score = 0
    if deal_data.get("china_linked"):
        china_score += 5
    if deal_data.get("belt_road"):
        china_score += 5
    if deal_data.get("dim_sum_feasible"):
        china_score += 3
    scores["china_bri"] = min(china_score, 10)

    # 7. Financing complexity premium (0-5)
    complexity_score = 5 if fin_score >= 8 else (3 if fin_score >= 5 else 1)
    scores["complexity_premium"] = complexity_score

    # 8. Mandate probability factors (0-5)
    mandate_factors = 0
    if deal_data.get("source") == "referral":
        mandate_factors += 5
    elif deal_data.get("source") == "intelligence":
        mandate_factors += 3
    else:
        mandate_factors += 1
    scores["mandate_factors"] = mandate_factors

    # Weighted total -> normalize to 0-100
    raw_total = (
        scores["sector"] * 2.0
        + scores["country"] * 1.5
        + scores["financing_type"] * 2.0
        + scores["deal_size"] * 1.5
        + scores["urgency"] * 1.0
        + scores["china_bri"] * 1.5
        + scores["complexity_premium"] * 1.0
        + scores["mandate_factors"] * 0.5
    )
    # Max possible: 10*2 + 10*1.5 + 10*2 + 10*1.5 + 15*1 + 10*1.5 + 5*1 + 5*0.5
    #             = 20 + 15 + 20 + 15 + 15 + 15 + 5 + 2.5 = 107.5
    overall_score = min(round((raw_total / 107.5) * 100, 1), 100.0)

    # Mandate probability (simpler heuristic)
    mandate_prob = min(
        round((overall_score * 0.6) + (scores["mandate_factors"] * 3)), 100
    )

    return {
        "overall_score": overall_score,
        "mandate_probability": mandate_prob,
        "breakdown": scores,
    }


def score_dim_sum_feasibility(deal_data: Dict) -> Dict:
    """
    Evaluate feasibility of Dim Sum Bond issuance.
    Returns feasibility dict with yes/no, confidence, and notes.
    """
    points = 0
    notes: List[str] = []

    # China-linked revenue
    if deal_data.get("china_linked"):
        points += 20
        notes.append("China-linked revenue/operations supports CNH investor appetite.")

    # BRI exposure
    if deal_data.get("belt_road"):
        points += 15
        notes.append("Belt & Road project — Chinese policy bank interest likely.")

    # Country
    country = (deal_data.get("country") or "").lower()
    if country in ["hong kong", "singapore"]:
        points += 15
        notes.append(
            f"{deal_data.get('country')} treasury centre supports offshore RMB structure."
        )
    elif country in ["indonesia", "malaysia", "vietnam", "thailand"]:
        points += 10
        notes.append(
            f"{deal_data.get('country')} — active Dim Sum market for ASEAN corporates."
        )

    # Sector
    sector = (deal_data.get("sector") or "").lower()
    high_appetite = [
        "telecom", "data center", "infrastructure", "power",
        "mining", "port", "logistics", "nickel",
    ]
    if any(s in sector for s in high_appetite):
        points += 15
        notes.append(
            f"{deal_data.get('sector')} sector has proven CNH investor demand."
        )

    # Deal size
    size = deal_data.get("estimated_size_mn") or 0
    if 100 <= size <= 1000:
        points += 20
        notes.append(
            f"Issuance size (~USD {size}M) is within typical Dim Sum market range."
        )
    elif size < 100:
        points += 5
        notes.append("Issuance size may be below typical Dim Sum minimum (~RMB 500M).")
    elif size > 1000:
        points += 15
        notes.append(
            "Large issuance — may require multi-tranche or syndicated approach."
        )

    # Financing type
    fin_type = (deal_data.get("financing_type") or "").lower()
    if "dim sum" in fin_type or "panda" in fin_type:
        points += 15
        notes.append("Financing type explicitly suited for offshore RMB market.")

    feasible = points >= 40
    confidence = min(round(points), 100)

    return {
        "feasible": feasible,
        "confidence_pct": confidence,
        "notes": notes,
        "estimated_size_rmb_bn": round((size * 7.2) / 1000, 2) if size else None,
        "likely_tenor": (
            "3Y" if size < 200 else ("5Y" if size < 500 else "5-7Y")
        ),
        "recommended_listing": "HKEX" if points >= 50 else "SGX or HKEX",
        "recommended_bookrunners": _suggest_bookrunners(deal_data),
    }


def _suggest_bookrunners(deal_data: Dict) -> List[str]:
    bookrunners: List[str] = []
    if deal_data.get("china_linked") or deal_data.get("belt_road"):
        bookrunners += [
            "CITIC Securities", "CICC", "Haitong International", "China Merchants Bank"
        ]
    country = (deal_data.get("country") or "").lower()
    if country in ["indonesia", "malaysia", "thailand", "vietnam", "philippines"]:
        bookrunners += ["CIMB", "Maybank IB", "RHB IB", "OCBC", "DBS"]
    if not bookrunners:
        bookrunners = ["HSBC", "Standard Chartered", "Deutsche Bank", "Citigroup"]
    return list(dict.fromkeys(bookrunners))[:5]  # dedupe, max 5
