"""
Inference Agent — runs daily at 06:00 UTC.
Scores each company on 14-day signals and writes Inference rows.
"""
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Inference, Signal
from deal_radar.scoring.embeddings import find_best_match
from deal_radar.scoring.rules import classify_score, compute_score

MIN_SCORE_TO_PERSIST = 40


def _build_reasoning(
    company_name: str,
    signals: List[Signal],
    score: int,
    event_type: str,
    similarity: float,
) -> str:
    summaries = []
    for s in signals:
        rd = s.raw_data or {}
        if s.signal_type == "github_commit_spike":
            summaries.append(f"GitHub commits +{rd.get('growth_pct', 0):.0f}%")
        elif s.signal_type == "hire_finance_ir":
            title = rd.get("title", "财务/IR职位")
            summaries.append(f"招聘 {title}")
        elif s.signal_type == "founder_vc_interact":
            n = rd.get("vc_interaction_count", 0)
            summaries.append(f"创始人与VC互动 {n} 次（7天内）")
        elif s.signal_type == "pr_activity_surge":
            summaries.append(f"PR活动激增（近14d {rd.get('recent_14d_prs', '?')} vs 前14d {rd.get('prior_14d_prs', '?')}）")
        elif s.signal_type == "news":
            summaries.append(f"媒体报道：{rd.get('title', '')[:50]}")
        else:
            summaries.append(s.signal_type)

    band = classify_score(score)
    sig_text = "；".join(summaries)
    return (
        f"{company_name} 在过去14天触发信号：{sig_text}。"
        f"信号组合与历史{event_type}案例相似度 {similarity:.0%}，"
        f"综合评分 {score}/100（{band['label']}）。"
    )


def run_inference_agent(db: Session) -> List[Inference]:
    cutoff = datetime.utcnow() - timedelta(days=14)
    companies: List[Company] = db.query(Company).all()
    new_inferences: List[Inference] = []

    for company in companies:
        signals_14d: List[Signal] = (
            db.query(Signal)
            .filter(Signal.company_id == company.id, Signal.captured_at >= cutoff)
            .all()
        )
        if not signals_14d:
            continue

        signal_types = [s.signal_type for s in signals_14d]
        score = compute_score(signal_types)
        if score < MIN_SCORE_TO_PERSIST:
            continue

        match = find_best_match(signal_types)
        event_type = match["event_type"]
        similarity = match["similarity"]

        reasoning = _build_reasoning(company.name, signals_14d, score, event_type, similarity)

        inf = Inference(
            company_id=company.id,
            event_type=event_type,
            confidence_score=float(score),
            reasoning=reasoning,
            triggered_signals=[s.id for s in signals_14d],
            created_at=datetime.utcnow(),
        )
        db.add(inf)
        new_inferences.append(inf)
        band = classify_score(score)
        print(f"[InferenceAgent] {band['emoji']} {company.name}: {score}/100 → {event_type}")

    db.commit()
    print(f"[InferenceAgent] ✓ {len(new_inferences)} inferences created.")
    return new_inferences
