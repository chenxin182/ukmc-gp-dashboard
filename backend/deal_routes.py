"""
UKMC Deal Origination System — API Routes
FastAPI router for deal management, intelligence signals, contacts, and analytics.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from database import get_db
from deal_models import (
    Contact, Deal, DealActivity, DealContact,
    IntelligenceSignal, TargetCompany,
)
from deal_scoring import score_deal, score_dim_sum_feasibility

router = APIRouter(prefix="/api", tags=["origination"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class DealContactIn(BaseModel):
    name: str
    title: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None


class DealCreate(BaseModel):
    company_name: str
    country: Optional[str] = None
    sector: Optional[str] = None
    company_description: Optional[str] = None
    financing_type: Optional[str] = None
    estimated_size_mn: Optional[float] = None
    currency: Optional[str] = "USD"
    purpose: Optional[str] = None
    tenor: Optional[str] = None
    urgency: Optional[str] = "MEDIUM"
    stage: Optional[str] = "DISCOVERY"
    why_suitable: Optional[str] = None
    financing_angle: Optional[str] = None
    potential_lenders: Optional[str] = None
    chinese_counterparties: Optional[str] = None
    dim_sum_feasible: Optional[bool] = False
    dim_sum_notes: Optional[str] = None
    dim_sum_size_mn: Optional[float] = None
    dim_sum_tenor: Optional[str] = None
    dim_sum_investor_appeal: Optional[str] = None
    entry_strategy: Optional[str] = None
    competitive_landscape: Optional[str] = None
    objections: Optional[str] = None
    political_considerations: Optional[str] = None
    next_action: Optional[str] = None
    next_action_detail: Optional[str] = None
    source: Optional[str] = "manual"
    source_url: Optional[str] = None
    intelligence_summary: Optional[str] = None
    priority: Optional[str] = "NORMAL"
    china_linked: Optional[bool] = False
    belt_road: Optional[bool] = False
    contacts: Optional[List[DealContactIn]] = []


class DealUpdate(DealCreate):
    company_name: Optional[str] = None


class StageChange(BaseModel):
    stage: str


class ContactCreate(BaseModel):
    name: str
    title: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    company_name: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    is_decision_maker: Optional[bool] = False
    is_gatekeeper: Optional[bool] = False
    priority: Optional[bool] = False


class SignalCreate(BaseModel):
    signal_type: str
    company_name: str
    country: Optional[str] = None
    sector: Optional[str] = None
    headline: str
    summary: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    urgency: Optional[str] = "MEDIUM"
    financing_implied_mn: Optional[float] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _deal_to_dict(d: Deal) -> dict:
    return {
        "id": d.id,
        "company_name": d.company_name,
        "country": d.country,
        "sector": d.sector,
        "company_description": d.company_description,
        "financing_type": d.financing_type,
        "estimated_size_mn": d.estimated_size_mn,
        "currency": d.currency,
        "purpose": d.purpose,
        "tenor": d.tenor,
        "urgency": d.urgency,
        "stage": d.stage,
        "ukmc_fit_score": d.ukmc_fit_score,
        "mandate_probability": d.mandate_probability,
        "why_suitable": d.why_suitable,
        "financing_angle": d.financing_angle,
        "potential_lenders": d.potential_lenders,
        "chinese_counterparties": d.chinese_counterparties,
        "dim_sum_feasible": d.dim_sum_feasible,
        "dim_sum_notes": d.dim_sum_notes,
        "dim_sum_size_mn": d.dim_sum_size_mn,
        "dim_sum_tenor": d.dim_sum_tenor,
        "dim_sum_investor_appeal": d.dim_sum_investor_appeal,
        "entry_strategy": d.entry_strategy,
        "competitive_landscape": d.competitive_landscape,
        "objections": d.objections,
        "political_considerations": d.political_considerations,
        "next_action": d.next_action,
        "next_action_detail": d.next_action_detail,
        "source": d.source,
        "source_url": d.source_url,
        "intelligence_summary": d.intelligence_summary,
        "is_active": d.is_active,
        "priority": d.priority,
        "china_linked": d.china_linked,
        "belt_road": d.belt_road,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        "contacts": [_contact_to_dict(c) for c in d.contacts],
        "activities": [_activity_to_dict(a) for a in d.activities],
    }


def _contact_to_dict(c) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "title": c.title,
        "role": c.role,
        "email": c.email,
        "phone": c.phone,
        "linkedin": c.linkedin,
        "notes": c.notes,
    }


def _activity_to_dict(a: DealActivity) -> dict:
    return {
        "id": a.id,
        "activity_type": a.activity_type,
        "description": a.description,
        "user": a.user,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _signal_to_dict(s: IntelligenceSignal) -> dict:
    return {
        "id": s.id,
        "signal_type": s.signal_type,
        "company_name": s.company_name,
        "country": s.country,
        "sector": s.sector,
        "headline": s.headline,
        "summary": s.summary,
        "source_url": s.source_url,
        "source_name": s.source_name,
        "urgency": s.urgency,
        "financing_implied_mn": s.financing_implied_mn,
        "deal_created": s.deal_created,
        "deal_id": s.deal_id,
        "reviewed": s.reviewed,
        "detected_at": s.detected_at.isoformat() if s.detected_at else None,
    }


def _apply_scoring(deal: Deal, data: dict) -> None:
    scoring = score_deal(data)
    deal.ukmc_fit_score = scoring["overall_score"]
    deal.mandate_probability = scoring["mandate_probability"]

    ds = score_dim_sum_feasibility(data)
    if not deal.dim_sum_feasible:
        deal.dim_sum_feasible = ds["feasible"]
    if not deal.dim_sum_notes:
        deal.dim_sum_notes = " ".join(ds["notes"])
    if not deal.dim_sum_tenor:
        deal.dim_sum_tenor = ds["likely_tenor"]


VALID_STAGES = ["DISCOVERY", "RESEARCH", "ANALYSIS", "OUTREACH",
                "PROPOSAL", "MANDATE", "CLOSED", "LOST"]


# ── Deal Routes ───────────────────────────────────────────────────────────────

@router.get("/deals")
def list_deals(
    q: Optional[str] = None,
    stage: Optional[str] = None,
    country: Optional[str] = None,
    sector: Optional[str] = None,
    urgency: Optional[str] = None,
    is_active: Optional[bool] = True,
    sort: Optional[str] = "score",   # score | updated | size | urgency
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Deal)

    if is_active is not None:
        query = query.filter(Deal.is_active == is_active)
    if stage:
        query = query.filter(Deal.stage == stage.upper())
    if country:
        query = query.filter(Deal.country.ilike(f"%{country}%"))
    if sector:
        query = query.filter(Deal.sector.ilike(f"%{sector}%"))
    if urgency:
        query = query.filter(Deal.urgency == urgency.upper())
    if q:
        query = query.filter(
            or_(
                Deal.company_name.ilike(f"%{q}%"),
                Deal.sector.ilike(f"%{q}%"),
                Deal.financing_type.ilike(f"%{q}%"),
                Deal.purpose.ilike(f"%{q}%"),
            )
        )

    sort_map = {
        "score":   desc(Deal.ukmc_fit_score),
        "updated": desc(Deal.updated_at),
        "size":    desc(Deal.estimated_size_mn),
        "urgency": desc(Deal.urgency),
    }
    query = query.order_by(sort_map.get(sort, desc(Deal.ukmc_fit_score)))

    total = query.count()
    deals = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "deals": [_deal_to_dict(d) for d in deals],
    }


@router.get("/deals/{deal_id}")
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _deal_to_dict(deal)


@router.post("/deals", status_code=201)
def create_deal(payload: DealCreate, db: Session = Depends(get_db)):
    data = payload.dict(exclude={"contacts"})
    deal = Deal(**{k: v for k, v in data.items() if hasattr(Deal, k)})
    _apply_scoring(deal, payload.dict())
    db.add(deal)
    db.flush()

    for c in (payload.contacts or []):
        db.add(DealContact(deal_id=deal.id, **c.dict()))

    db.add(DealActivity(
        deal_id=deal.id,
        activity_type="STAGE_CHANGE",
        description=f"Deal created at stage {deal.stage}. UKMC Fit Score: {deal.ukmc_fit_score:.0f}/100.",
    ))
    db.commit()
    db.refresh(deal)
    return _deal_to_dict(deal)


@router.put("/deals/{deal_id}")
def update_deal(deal_id: int, payload: DealUpdate, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    data = payload.dict(exclude_none=True, exclude={"contacts"})
    for k, v in data.items():
        if hasattr(deal, k):
            setattr(deal, k, v)

    deal.updated_at = datetime.utcnow()
    _apply_scoring(deal, {
        "sector": deal.sector, "country": deal.country,
        "financing_type": deal.financing_type, "estimated_size_mn": deal.estimated_size_mn,
        "urgency": deal.urgency, "china_linked": deal.china_linked,
        "belt_road": deal.belt_road, "dim_sum_feasible": deal.dim_sum_feasible,
        "source": deal.source,
    })

    db.add(DealActivity(deal_id=deal.id, activity_type="NOTE", description="Deal details updated."))
    db.commit()
    db.refresh(deal)
    return _deal_to_dict(deal)


@router.delete("/deals/{deal_id}", status_code=204)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.is_active = False
    deal.updated_at = datetime.utcnow()
    db.commit()


@router.post("/deals/{deal_id}/stage")
def change_stage(deal_id: int, payload: StageChange, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    stage = payload.stage.upper()
    if stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    old = deal.stage
    deal.stage = stage
    deal.updated_at = datetime.utcnow()
    db.add(DealActivity(
        deal_id=deal.id,
        activity_type="STAGE_CHANGE",
        description=f"Stage advanced: {old} → {stage}",
    ))
    db.commit()
    return {"id": deal.id, "stage": deal.stage}


# ── Pipeline Stats ────────────────────────────────────────────────────────────

@router.get("/pipeline/stats")
def pipeline_stats(db: Session = Depends(get_db)):
    active = db.query(Deal).filter(Deal.is_active == True)

    by_stage = {}
    for row in active.with_entities(Deal.stage, func.count()).group_by(Deal.stage).all():
        by_stage[row[0]] = row[1]

    by_country = {}
    for row in active.with_entities(Deal.country, func.count()).group_by(Deal.country).all():
        if row[0]:
            by_country[row[0]] = row[1]

    by_sector = {}
    for row in active.with_entities(Deal.sector, func.count()).group_by(Deal.sector).all():
        if row[0]:
            by_sector[row[0]] = row[1]

    by_priority = {}
    for row in active.with_entities(Deal.priority, func.count()).group_by(Deal.priority).all():
        if row[0]:
            by_priority[row[0]] = row[1]

    total_pipeline = db.query(func.sum(Deal.estimated_size_mn)).filter(
        Deal.is_active == True
    ).scalar() or 0

    dim_sum_pool = db.query(func.sum(Deal.estimated_size_mn)).filter(
        Deal.is_active == True, Deal.dim_sum_feasible == True
    ).scalar() or 0

    unreviewed = db.query(IntelligenceSignal).filter(
        IntelligenceSignal.reviewed == False
    ).count()

    high_urgency = active.filter(Deal.urgency == "HIGH").count()
    china_linked = active.filter(Deal.china_linked == True).count()
    belt_road    = active.filter(Deal.belt_road == True).count()
    dim_sum_cnt  = active.filter(Deal.dim_sum_feasible == True).count()

    return {
        "active_deals":        active.count(),
        "total_deals":         db.query(Deal).count(),
        "total_pipeline_mn":   round(total_pipeline, 1),
        "dim_sum_pool_mn":     round(dim_sum_pool, 1),
        "by_stage":            by_stage,
        "by_country":          by_country,
        "by_sector":           by_sector,
        "by_priority":         by_priority,
        "unreviewed_signals":  unreviewed,
        "high_urgency":        high_urgency,
        "china_linked":        china_linked,
        "belt_road":           belt_road,
        "dim_sum_feasible":    dim_sum_cnt,
    }


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    deals = db.query(Deal).filter(Deal.is_active == True).all()

    # Score distribution buckets
    buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    for d in deals:
        s = d.ukmc_fit_score or 0
        if s <= 25:
            buckets["0-25"] += 1
        elif s <= 50:
            buckets["26-50"] += 1
        elif s <= 75:
            buckets["51-75"] += 1
        else:
            buckets["76-100"] += 1

    score_dist = [{"range": k, "count": v} for k, v in buckets.items()]

    # Pipeline by financing type
    fin_type_data = {}
    for d in deals:
        ft = d.financing_type or "Other"
        if ft not in fin_type_data:
            fin_type_data[ft] = {"count": 0, "size_mn": 0}
        fin_type_data[ft]["count"] += 1
        fin_type_data[ft]["size_mn"] += d.estimated_size_mn or 0

    fin_type_list = sorted(
        [{"type": k, **v} for k, v in fin_type_data.items()],
        key=lambda x: x["size_mn"], reverse=True
    )[:10]

    # Deals created in last 30 days (by week)
    weekly = []
    for i in range(4, -1, -1):
        week_start = datetime.utcnow() - timedelta(weeks=i + 1)
        week_end   = datetime.utcnow() - timedelta(weeks=i)
        count = db.query(Deal).filter(
            Deal.created_at >= week_start,
            Deal.created_at < week_end,
        ).count()
        weekly.append({
            "week": f"W-{i}" if i > 0 else "This week",
            "count": count,
        })

    # Top deals by score
    top = db.query(Deal).filter(Deal.is_active == True).order_by(
        desc(Deal.ukmc_fit_score)
    ).limit(5).all()

    return {
        "score_distribution": score_dist,
        "by_financing_type":  fin_type_list,
        "weekly_new_deals":   weekly,
        "top_deals": [
            {
                "company_name": d.company_name,
                "country": d.country,
                "sector": d.sector,
                "ukmc_fit_score": d.ukmc_fit_score,
                "mandate_probability": d.mandate_probability,
                "estimated_size_mn": d.estimated_size_mn,
                "financing_type": d.financing_type,
            }
            for d in top
        ],
    }


# ── Signals ───────────────────────────────────────────────────────────────────

@router.get("/signals")
def list_signals(
    urgency: Optional[str] = None,
    signal_type: Optional[str] = None,
    country: Optional[str] = None,
    reviewed: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(IntelligenceSignal).order_by(desc(IntelligenceSignal.detected_at))

    if urgency:
        query = query.filter(IntelligenceSignal.urgency == urgency.upper())
    if signal_type:
        query = query.filter(IntelligenceSignal.signal_type == signal_type.upper())
    if country:
        query = query.filter(IntelligenceSignal.country.ilike(f"%{country}%"))
    if reviewed is not None and reviewed != "":
        query = query.filter(IntelligenceSignal.reviewed == (reviewed.lower() == "true"))

    signals = query.limit(limit).all()
    return {"signals": [_signal_to_dict(s) for s in signals]}


@router.post("/signals", status_code=201)
def create_signal(payload: SignalCreate, db: Session = Depends(get_db)):
    sig = IntelligenceSignal(**payload.dict())
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return _signal_to_dict(sig)


@router.post("/signals/{signal_id}/convert")
def convert_signal(signal_id: int, db: Session = Depends(get_db)):
    sig = db.query(IntelligenceSignal).filter(IntelligenceSignal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    deal_data = {
        "company_name": sig.company_name,
        "country":      sig.country,
        "sector":       sig.sector,
        "source":       "intelligence",
        "source_url":   sig.source_url,
        "intelligence_summary": f"[{sig.signal_type}] {sig.headline}\n\n{sig.summary or ''}",
        "urgency":      sig.urgency,
        "estimated_size_mn": sig.financing_implied_mn,
        "china_linked": False,
        "belt_road":    False,
        "dim_sum_feasible": False,
    }

    deal = Deal(**deal_data)
    _apply_scoring(deal, deal_data)
    db.add(deal)
    db.flush()

    db.add(DealActivity(
        deal_id=deal.id,
        activity_type="SIGNAL_LINKED",
        description=f"Deal auto-created from intelligence signal: {sig.headline}",
    ))

    sig.deal_created = True
    sig.deal_id = deal.id
    sig.reviewed = True
    db.commit()
    db.refresh(deal)
    return _deal_to_dict(deal)


# ── Contacts ──────────────────────────────────────────────────────────────────

@router.get("/contacts")
def list_contacts(
    q: Optional[str] = None,
    country: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).order_by(Contact.name)

    if q:
        query = query.filter(
            or_(
                Contact.name.ilike(f"%{q}%"),
                Contact.company_name.ilike(f"%{q}%"),
                Contact.title.ilike(f"%{q}%"),
            )
        )
    if country:
        query = query.filter(Contact.country.ilike(f"%{country}%"))
    if role:
        query = query.filter(Contact.role == role.upper())

    contacts = query.limit(limit).all()
    return {
        "contacts": [
            {
                "id": c.id,
                "name": c.name,
                "title": c.title,
                "role": c.role,
                "email": c.email,
                "phone": c.phone,
                "linkedin": c.linkedin,
                "company_name": c.company_name,
                "country": c.country,
                "notes": c.notes,
                "is_decision_maker": c.is_decision_maker,
                "is_gatekeeper": c.is_gatekeeper,
                "priority": c.priority,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in contacts
        ]
    }


@router.post("/contacts", status_code=201)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(**payload.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"id": contact.id, "name": contact.name}


# ── Intelligence Engine ───────────────────────────────────────────────────────

# Curated real-world financing signal templates for demo/scan simulation
_SIGNAL_TEMPLATES = [
    {
        "signal_type": "EXPANSION",
        "company_name": "Smartfren Telecom",
        "country": "Indonesia",
        "sector": "Telecom",
        "headline": "Smartfren accelerates 5G rollout across Java — funding gap estimated at USD 400M",
        "summary": "Indonesian telco Smartfren is pushing aggressive 5G spectrum deployment across Java and Sumatra, having acquired 2.3GHz spectrum in the latest SDPPI auction. Capital expenditure requirements for 2025-2026 are estimated at IDR 6 trillion (~USD 380M), with current cash reserves insufficient. The company is actively seeking bridge financing or project finance.",
        "source_name": "Bisnis Indonesia",
        "urgency": "HIGH",
        "financing_implied_mn": 380.0,
    },
    {
        "signal_type": "SMELTER",
        "company_name": "PT Gunbuster Nickel Industry",
        "country": "Indonesia",
        "sector": "Mining / Nickel",
        "headline": "GNI Morowali smelter Phase 3 expansion requires USD 600M project financing",
        "summary": "PT Gunbuster Nickel Industry, backed by Chinese investors including Tsingshan Group, is expanding its RKEF (Rotary Kiln Electric Furnace) nickel smelting capacity in Morowali Industrial Park, Central Sulawesi. Phase 3 adds 4 new RKEF lines. EPC contractor is Sinosteel. Off-take agreement with Chinese stainless steel producers provides revenue visibility. UKMC Dim Sum bond angle: strong Chinese sponsor/EPC, IDR-denominated revenue converted to USD.",
        "source_name": "Mining Indonesia",
        "urgency": "HIGH",
        "financing_implied_mn": 600.0,
    },
    {
        "signal_type": "DATA_CENTER",
        "company_name": "VNG Corporation",
        "country": "Vietnam",
        "sector": "Data Centers",
        "headline": "VNG seeks USD 300M for new data center campus in Ho Chi Minh City",
        "summary": "Vietnam's leading internet company VNG Corporation is planning a 50MW hyperscale data center campus in Thu Duc City, Ho Chi Minh City. The project requires USD 280-320M in project financing. VNG has signed an MOU with Alibaba Cloud for co-location services, providing revenue visibility. Chinese tech linkage makes this a strong Dim Sum bond candidate.",
        "source_name": "Vietnam Investment Review",
        "urgency": "HIGH",
        "financing_implied_mn": 300.0,
    },
    {
        "signal_type": "RENEWABLE",
        "company_name": "Super Energy Corporation",
        "country": "Thailand",
        "sector": "Renewable Energy",
        "headline": "Super Energy 500MW solar portfolio seeks project bond refinancing in 2025",
        "summary": "Thailand's Super Energy Corporation has a maturing project loan portfolio across 12 solar projects (combined 500MW). The 7-year construction loans totaling ~THB 15B (~USD 430M) are due in mid-2026. The company is exploring USD bond issuance or Baht bond, given the stable feed-in-tariff revenue from the Thai government. ESG certification is in progress.",
        "source_name": "Bangkok Post",
        "urgency": "HIGH",
        "financing_implied_mn": 430.0,
    },
    {
        "signal_type": "INFRASTRUCTURE",
        "company_name": "IGB REIT",
        "country": "Malaysia",
        "sector": "Logistics / Ports",
        "headline": "Johor-Singapore special economic zone creates USD 2B infrastructure financing pipeline",
        "summary": "The newly launched Johor-Singapore Special Economic Zone (JSSEZ) has triggered a wave of infrastructure investment in southern Johor. Multiple port, logistics, and industrial park operators are seeking financing for expansion. Malaysian sovereign wealth fund Khazanah Nasional is anchor investor. Chinese manufacturers are relocating operations to the zone, creating strong BRI-linked deal flow.",
        "source_name": "The Edge Malaysia",
        "urgency": "MEDIUM",
        "financing_implied_mn": 500.0,
    },
    {
        "signal_type": "REFINANCING",
        "company_name": "Masan Group",
        "country": "Vietnam",
        "sector": "Mining / Nickel",
        "headline": "Masan High-Tech Materials seeks USD 200M refinancing for Nui Phao tungsten mine",
        "summary": "Masan High-Tech Materials, owner of the Nui Phao polymetallic mine — the world's largest tungsten producer outside China — has USD 200M in syndicated loans maturing in Q3 2026. The company is exploring USD bond issuance or Dim Sum bond given strong Chinese offtake relationships with Xiamen Tungsten. Revenue is predominantly USD-denominated from Chinese buyers.",
        "source_name": "DealStreetAsia",
        "urgency": "MEDIUM",
        "financing_implied_mn": 200.0,
    },
    {
        "signal_type": "ACQUISITION",
        "company_name": "Axiata Group",
        "country": "Malaysia",
        "sector": "Telecom",
        "headline": "Axiata evaluates USD 700M acquisition financing for XL Axiata-Smartfren merger",
        "summary": "Axiata Group is evaluating bridge financing for a potential merger between PT XL Axiata and Smartfren Telecom to create Indonesia's third-largest telco. The merged entity would require significant post-merger integration capex and potential debt refinancing. Axiata's Malaysian holding structure and Chinese shareholder (Khazanah) creates a Dim Sum issuance pathway.",
        "source_name": "Reuters",
        "urgency": "MEDIUM",
        "financing_implied_mn": 700.0,
    },
    {
        "signal_type": "BOND_MATURITY",
        "company_name": "Lippo Karawaci",
        "country": "Indonesia",
        "sector": "Real Estate",
        "headline": "Lippo Karawaci USD 280M bond matures 2026 — refinancing urgently required",
        "summary": "Indonesian property developer Lippo Karawaci has USD 280M in offshore USD bonds maturing in June 2026. The company, which has significant retail and hospital assets, is under pressure to refinance as domestic capital markets remain constrained. UKMC angle: structured refinancing with asset-backed security or offshore bond with partial collateral.",
        "source_name": "Bloomberg",
        "urgency": "HIGH",
        "financing_implied_mn": 280.0,
    },
    {
        "signal_type": "INFRASTRUCTURE",
        "company_name": "Manila Electric Company (Meralco)",
        "country": "Philippines",
        "sector": "Power / Energy",
        "headline": "Meralco PowerGen requires PHP 60B (~USD 1B) for coal-to-gas transition financing",
        "summary": "Manila Electric Company's generation arm MGen is accelerating its coal-to-LNG/renewable transition, requiring approximately PHP 55-65 billion in capital over 2025-2028. Projects include LNG terminal at Batangas and 600MW combined cycle gas turbine. Strong ESG/green financing angle. Philippine government's Just Energy Transition Partnership (JETP) commitment provides policy tailwind.",
        "source_name": "BusinessWorld Philippines",
        "urgency": "MEDIUM",
        "financing_implied_mn": 1000.0,
    },
    {
        "signal_type": "DATA_CENTER",
        "company_name": "ST Telemedia Global Data Centres",
        "country": "Singapore",
        "sector": "Data Centers",
        "headline": "STT GDC expands Southeast Asia data center portfolio — USD 800M financing needed",
        "summary": "ST Telemedia Global Data Centres (STT GDC), backed by Singapore state investor Temasek, is expanding its AI-ready data center portfolio across Singapore, Indonesia, India and Malaysia. The company needs USD 700-900M for new build projects in Batam (Indonesia) and KL. Chinese hyperscalers (Alibaba, ByteDance) are anchor tenants, making Dim Sum bond issuance an attractive option.",
        "source_name": "The Business Times",
        "urgency": "MEDIUM",
        "financing_implied_mn": 800.0,
    },
]


@router.post("/intelligence/run")
def run_intelligence(db: Session = Depends(get_db)):
    """
    Simulate an intelligence scan — in production this would call
    web scraping pipelines, news APIs, and exchange announcement feeds.
    For now it inserts curated real-world signal templates that are not yet in DB.
    """
    existing_headlines = {
        s.headline for s in db.query(IntelligenceSignal.headline).all()
    }

    new_signals = []
    for tmpl in _SIGNAL_TEMPLATES:
        if tmpl["headline"] not in existing_headlines:
            sig = IntelligenceSignal(**tmpl)
            db.add(sig)
            new_signals.append(sig)

    db.commit()

    high_urgency = sum(1 for s in new_signals if s.urgency == "HIGH")

    return {
        "new_signals": len(new_signals),
        "high_urgency": high_urgency,
        "message": f"Scan complete. {len(new_signals)} new signals added, {high_urgency} high urgency.",
    }
