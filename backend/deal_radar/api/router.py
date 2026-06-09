from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from deal_radar.db.database import get_db
from deal_radar.db.models import Company, Feedback, FundingEvent, Inference, Signal
from deal_radar.scoring.rules import classify_score, compute_score

router = APIRouter(prefix="/dr", tags=["deal-radar"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    github_org: Optional[str] = None
    twitter_handle: Optional[str] = None
    founder_twitter: Optional[str] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[str] = None
    sector: Optional[str] = None
    greenhouse_token: Optional[str] = None
    lever_slug: Optional[str] = None


class CompanyOut(BaseModel):
    id: int
    name: str
    domain: Optional[str]
    github_org: Optional[str]
    twitter_handle: Optional[str]
    stage: Optional[str]
    sector: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InferenceOut(BaseModel):
    id: int
    company_id: int
    company_name: str
    event_type: str
    confidence_score: float
    priority: str
    emoji: str
    reasoning: str
    triggered_signals: list
    created_at: datetime


class FeedbackCreate(BaseModel):
    outcome: str   # confirmed | false_positive | pending
    notes: Optional[str] = None


class SignalOut(BaseModel):
    id: int
    signal_type: str
    source_url: Optional[str]
    raw_data: Optional[dict]
    captured_at: datetime


class ScoreRequest(BaseModel):
    signal_types: List[str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _inference_out(inf: Inference, db: Session) -> InferenceOut:
    company = db.get(Company, inf.company_id)
    band = classify_score(int(inf.confidence_score))
    return InferenceOut(
        id=inf.id,
        company_id=inf.company_id,
        company_name=company.name if company else "Unknown",
        event_type=inf.event_type,
        confidence_score=inf.confidence_score,
        priority=band["level"],
        emoji=band["emoji"],
        reasoning=inf.reasoning,
        triggered_signals=inf.triggered_signals or [],
        created_at=inf.created_at,
    )


# ── Company endpoints ─────────────────────────────────────────────────────────

@router.get("/companies", response_model=List[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.name).all()


@router.post("/companies", response_model=CompanyOut, status_code=201)
def add_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/companies/{company_id}", status_code=204)
def remove_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()


# ── Inference endpoints ───────────────────────────────────────────────────────

@router.get("/inferences/today", response_model=List[InferenceOut])
def get_today_inferences(min_score: int = 60, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(hours=24)
    inferences = (
        db.query(Inference)
        .filter(Inference.created_at >= cutoff, Inference.confidence_score >= min_score)
        .order_by(Inference.confidence_score.desc())
        .all()
    )
    return [_inference_out(inf, db) for inf in inferences]


@router.get("/inferences", response_model=List[InferenceOut])
def list_inferences(
    min_score: int = 0,
    days: int = 7,
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    inferences = (
        db.query(Inference)
        .filter(Inference.created_at >= cutoff, Inference.confidence_score >= min_score)
        .order_by(Inference.confidence_score.desc())
        .all()
    )
    return [_inference_out(inf, db) for inf in inferences]


@router.get("/inferences/{inference_id}", response_model=InferenceOut)
def get_inference(inference_id: int, db: Session = Depends(get_db)):
    inf = db.get(Inference, inference_id)
    if not inf:
        raise HTTPException(status_code=404, detail="Inference not found")
    return _inference_out(inf, db)


# ── Feedback endpoint ─────────────────────────────────────────────────────────

@router.post("/feedback/{inference_id}", status_code=201)
def submit_feedback(
    inference_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
):
    if payload.outcome not in {"confirmed", "false_positive", "pending"}:
        raise HTTPException(status_code=422, detail="outcome must be confirmed | false_positive | pending")
    inf = db.get(Inference, inference_id)
    if not inf:
        raise HTTPException(status_code=404, detail="Inference not found")
    fb = Feedback(
        inference_id=inference_id,
        outcome=payload.outcome,
        notes=payload.notes,
        resolved_at=datetime.utcnow() if payload.outcome != "pending" else None,
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "outcome": payload.outcome}


# ── Signal endpoints ──────────────────────────────────────────────────────────

@router.get("/signals/{company_id}", response_model=List[SignalOut])
def get_company_signals(
    company_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    if not db.get(Company, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    cutoff = datetime.utcnow() - timedelta(days=days)
    signals = (
        db.query(Signal)
        .filter(Signal.company_id == company_id, Signal.captured_at >= cutoff)
        .order_by(Signal.captured_at.desc())
        .all()
    )
    return signals


# ── Scoring utility ───────────────────────────────────────────────────────────

@router.post("/score")
def score_signals(payload: ScoreRequest):
    score = compute_score(payload.signal_types)
    band = classify_score(score)
    return {"score": score, **band}


# ── Digest preview ────────────────────────────────────────────────────────────

@router.get("/digest/preview")
def preview_digest(db: Session = Depends(get_db)):
    from deal_radar.agents.delivery_agent import generate_daily_digest
    return {"digest": generate_daily_digest(db)}


# ── Manual agent triggers (for dev / backfill) ────────────────────────────────

@router.post("/run/signals")
async def trigger_signal_agent(db: Session = Depends(get_db)):
    from deal_radar.agents.signal_agent import run_signal_agent
    signals = await run_signal_agent(db)
    return {"status": "ok", "new_signals": len(signals)}


@router.post("/run/enrichment")
def trigger_enrichment(db: Session = Depends(get_db)):
    from deal_radar.agents.enrichment_agent import run_enrichment_agent
    result = run_enrichment_agent(db)
    return {"status": "ok", "companies_processed": len(result)}


@router.post("/run/inference")
def trigger_inference(db: Session = Depends(get_db)):
    from deal_radar.agents.inference_agent import run_inference_agent
    inferences = run_inference_agent(db)
    return {"status": "ok", "inferences_created": len(inferences)}


@router.post("/run/delivery")
def trigger_delivery(db: Session = Depends(get_db)):
    from deal_radar.agents.delivery_agent import run_delivery_agent
    digest = run_delivery_agent(db)
    return {"status": "ok", "digest_chars": len(digest)}


# ── Backtest ──────────────────────────────────────────────────────────────────

@router.get("/backtest")
def run_backtest_api(
    mode: str = "simulation",
    db: Session = Depends(get_db),
):
    """
    Run backtest and return structured results.
    mode: simulation | feedback | both
    """
    if mode not in ("simulation", "feedback", "both"):
        raise HTTPException(status_code=422, detail="mode must be simulation | feedback | both")
    from deal_radar.backtest import run_backtest, _run_simulation, suggest_weight_adjustments
    return run_backtest(db, mode=mode)


@router.get("/backtest/simulation")
def backtest_simulation_detail(db: Session = Depends(get_db)):
    """Return per-company simulation results as structured JSON."""
    from deal_radar.backtest import _run_simulation, suggest_weight_adjustments
    results = _run_simulation(db)
    rows = [
        {
            "company": r.company,
            "round_type": r.round_type,
            "amount_usd_m": r.amount_m,
            "signals": r.signals,
            "score": r.score,
            "band": r.band,
            "detected": r.predicted_positive,
        }
        for r in results
    ]
    hits = [r for r in results if r.predicted_positive]
    return {
        "total": len(results),
        "detected": len(hits),
        "recall": round(len(hits) / len(results), 3) if results else 0,
        "results": rows,
        "weight_suggestions": suggest_weight_adjustments(results),
    }


# ── Funding events (backtest ground truth) ───────────────────────────────────

@router.get("/funding-events")
def list_funding_events(db: Session = Depends(get_db)):
    from deal_radar.db.models import FundingEvent
    events = db.query(FundingEvent).order_by(FundingEvent.announced_date.desc()).all()
    return [
        {
            "id": e.id,
            "company_name": e.company_name,
            "round_type": e.round_type,
            "amount_usd_m": round(e.amount_usd / 1_000_000, 1) if e.amount_usd else None,
            "announced_date": e.announced_date.date().isoformat() if e.announced_date else None,
            "source_url": e.source_url,
        }
        for e in events
    ]
