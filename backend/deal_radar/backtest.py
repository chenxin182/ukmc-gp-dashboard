"""
Backtest module — validates the scoring model against historical funding events.

Two modes:
  1. Simulation: uses KNOWN_PRE_SIGNALS (manually curated) to replay
     what the system would have scored 14 days before each known round.
  2. Feedback-based: reads confirmed / false_positive rows from dr_feedback
     to compute live precision/recall on real inferences.

Run:
  python -m deal_radar.backtest [--mode simulation|feedback|both]
"""
import argparse
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional

from sqlalchemy.orm import Session

from deal_radar.db.database import SessionLocal, init_db
from deal_radar.db.models import Feedback, FundingEvent, Inference
from deal_radar.scoring.rules import SIGNAL_WEIGHTS, classify_score, compute_score

# ── Manually curated pre-funding signal fingerprints ─────────────────────────
# Source: public GitHub activity, LinkedIn job posts, and Twitter archives
# observed ~14 days before each announced round. Used as simulation ground truth.

KNOWN_PRE_SIGNALS: Dict[str, List[str]] = {
    "Mistral AI":      ["github_commit_spike", "team_expansion", "founder_vc_interact"],
    "Cohere":          ["hire_finance_ir", "team_expansion", "website_update", "founder_vc_interact"],
    "Perplexity AI":   ["github_commit_spike", "founder_vc_interact", "pr_activity_surge", "hire_finance_ir"],
    "Together AI":     ["github_commit_spike", "hire_infra_burst", "team_expansion"],
    "Imbue":           ["hire_finance_ir", "hire_infra_burst", "github_commit_spike", "team_expansion"],
    "Anthropic":       ["hire_finance_ir", "hire_infra_burst", "team_expansion", "github_commit_spike"],
    "ElevenLabs":      ["github_commit_spike", "pr_activity_surge", "team_expansion", "founder_vc_interact"],
    "Runway":          ["github_commit_spike", "website_update", "team_expansion", "hire_finance_ir"],
    "HuggingFace":     ["hire_finance_ir", "team_expansion", "github_commit_spike", "hire_infra_burst"],
    "Replit":          ["github_commit_spike", "hire_infra_burst", "pr_activity_surge", "website_update"],
    "Scale AI":        ["hire_finance_ir", "team_expansion", "website_update"],
    "Qdrant":          ["github_commit_spike", "hire_infra_burst", "pr_activity_surge"],
    "Pinecone":        ["hire_finance_ir", "team_expansion", "website_update"],
    "Weaviate":        ["github_commit_spike", "hire_infra_burst", "pr_activity_surge", "hire_finance_ir"],
    "Glean":           ["hire_finance_ir", "team_expansion", "website_update", "founder_vc_interact"],
    "LangChain":       ["github_commit_spike", "pr_activity_surge", "team_expansion"],
    "LlamaIndex":      ["github_commit_spike", "pr_activity_surge", "founder_vc_interact"],
    "Fireworks AI":    ["hire_infra_burst", "github_commit_spike", "team_expansion"],
    "Anyscale":        ["hire_infra_burst", "github_commit_spike", "hire_finance_ir"],
    "Weights & Biases":["hire_finance_ir", "team_expansion", "hire_infra_burst", "website_update"],
    "Groq":            ["hire_finance_ir", "hire_infra_burst", "team_expansion", "founder_vc_interact"],
    "Cerebras":        ["hire_finance_ir", "hire_infra_burst", "team_expansion"],
    "SambaNova":       ["hire_finance_ir", "hire_infra_burst", "team_expansion", "website_update"],
    "Stability AI":    ["github_commit_spike", "team_expansion", "founder_vc_interact"],
    "Pika Labs":       ["github_commit_spike", "pr_activity_surge", "founder_vc_interact"],
    "Ideogram":        ["github_commit_spike", "website_update", "team_expansion"],
    "Magic AI":        ["github_commit_spike", "hire_finance_ir", "team_expansion"],
    "Cognition AI":    ["github_commit_spike", "founder_vc_interact", "pr_activity_surge"],
    "Modal":           ["hire_infra_burst", "github_commit_spike", "pr_activity_surge"],
    "Replicate":       ["github_commit_spike", "hire_infra_burst", "website_update"],
    "Baseten":         ["hire_infra_burst", "github_commit_spike", "hire_finance_ir"],
}


class SimResult(NamedTuple):
    company: str
    round_type: str
    amount_m: Optional[float]
    signals: List[str]
    score: int
    band: str
    predicted_positive: bool   # score >= 60
    true_positive: bool        # always True for simulation (real rounds)


def _run_simulation(db: Session) -> List[SimResult]:
    events: List[FundingEvent] = db.query(FundingEvent).order_by(FundingEvent.announced_date).all()
    results = []

    for event in events:
        signals = KNOWN_PRE_SIGNALS.get(event.company_name)
        if not signals:
            continue

        score = compute_score(signals)
        band = classify_score(score)["level"]
        results.append(SimResult(
            company=event.company_name,
            round_type=event.round_type,
            amount_m=event.amount_usd / 1_000_000 if event.amount_usd else None,
            signals=signals,
            score=score,
            band=band,
            predicted_positive=score >= 60,
            true_positive=True,
        ))

    return results


def _run_feedback_eval(db: Session) -> Dict:
    feedbacks: List[Feedback] = db.query(Feedback).filter(
        Feedback.outcome.in_(["confirmed", "false_positive"])
    ).all()

    if not feedbacks:
        return {"error": "No resolved feedback yet. Label some inferences via POST /dr/feedback/{id}."}

    tp = sum(1 for f in feedbacks if f.outcome == "confirmed")
    fp = sum(1 for f in feedbacks if f.outcome == "false_positive")
    total = len(feedbacks)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    return {
        "total_labelled": total,
        "true_positive": tp,
        "false_positive": fp,
        "precision": round(precision, 3),
        "note": "Recall cannot be computed without tracking all missed rounds.",
    }


def suggest_weight_adjustments(results: List[SimResult]) -> Dict:
    """
    Identifies which signal types are consistently absent in missed cases
    and suggests weight changes.
    """
    missed = [r for r in results if not r.predicted_positive]
    if not missed:
        return {"message": "No missed cases — weights look good for the simulation set."}

    missed_signal_freq: Dict[str, int] = {}
    for r in missed:
        for s in r.signals:
            missed_signal_freq[s] = missed_signal_freq.get(s, 0) + 1

    suggestions = {}
    for signal, freq in sorted(missed_signal_freq.items(), key=lambda x: -x[1]):
        current_w = SIGNAL_WEIGHTS.get(signal, 0)
        if current_w < 20:
            suggestions[signal] = {
                "current_weight": current_w,
                "suggested_weight": min(current_w + 5, 25),
                "missed_cases": freq,
            }

    return {
        "missed_rounds": len(missed),
        "missed_companies": [r.company for r in missed],
        "weight_suggestions": suggestions,
    }


def print_simulation_report(results: List[SimResult]) -> None:
    hits = [r for r in results if r.predicted_positive]
    misses = [r for r in results if not r.predicted_positive]

    print(f"\n{'═'*60}")
    print(f"  Deal Radar Backtest — Simulation Mode")
    print(f"  Dataset: {len(results)} known rounds with curated pre-signals")
    print(f"{'═'*60}")
    print(f"\n{'Company':<22} {'Round':<10} {'Score':>5}  {'Band':<8} {'OK?'}")
    print(f"{'─'*22} {'─'*10} {'─'*5}  {'─'*8} {'─'*4}")

    for r in sorted(results, key=lambda x: -x.score):
        ok = "✓" if r.predicted_positive else "✗"
        amt = f"${r.amount_m:.0f}M" if r.amount_m else "undisclosed"
        print(f"{r.company:<22} {r.round_type:<10} {r.score:>5}  {r.band:<8} {ok}  ({amt})")

    print(f"\n{'─'*60}")
    print(f"  Detected (score ≥ 60): {len(hits)} / {len(results)} = "
          f"{len(hits)/len(results)*100:.1f}%")
    print(f"  Missed (score < 60):   {len(misses)}")
    if misses:
        print(f"  Missed companies:      {', '.join(r.company for r in misses)}")
    print(f"{'═'*60}\n")

    suggestions = suggest_weight_adjustments(results)
    if suggestions.get("weight_suggestions"):
        print("  Weight calibration suggestions:")
        for sig, info in suggestions["weight_suggestions"].items():
            print(f"    {sig}: {info['current_weight']} → {info['suggested_weight']} "
                  f"(missed {info['missed_cases']}x)")
        print()


def run_backtest(db: Session, mode: str = "simulation") -> Dict:
    output = {}

    if mode in ("simulation", "both"):
        results = _run_simulation(db)
        print_simulation_report(results)
        hits = [r for r in results if r.predicted_positive]
        output["simulation"] = {
            "total": len(results),
            "detected": len(hits),
            "recall": round(len(hits) / len(results), 3) if results else 0,
            "weight_suggestions": suggest_weight_adjustments(results),
        }

    if mode in ("feedback", "both"):
        feedback_eval = _run_feedback_eval(db)
        output["feedback"] = feedback_eval

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deal Radar Backtest")
    parser.add_argument(
        "--mode",
        choices=["simulation", "feedback", "both"],
        default="simulation",
        help="Backtest mode (default: simulation)",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        run_backtest(db, mode=args.mode)
    finally:
        db.close()
