"""Tests for backtest simulation — verifies recall stays above 95% after any weight change."""
import pytest
from pathlib import Path

from deal_radar.backtest import _run_simulation, suggest_weight_adjustments
from deal_radar.db.database import SessionLocal, init_db
from deal_radar.db.models import FundingEvent
from deal_radar.db.seed import CSV_PATH, import_funding_events


@pytest.fixture(scope="module")
def seeded_db():
    """In-memory SQLite DB seeded with funding events."""
    import os
    os.environ["DEAL_RADAR_DB_URL"] = "sqlite:///:memory:"
    init_db()
    db = SessionLocal()
    import_funding_events(db, CSV_PATH)
    yield db
    db.close()


def test_csv_exists():
    assert CSV_PATH.exists(), f"funding_events.csv not found at {CSV_PATH}"


def test_csv_has_records(seeded_db):
    count = seeded_db.query(FundingEvent).count()
    assert count >= 40, f"Expected ≥40 funding events, got {count}"


def test_simulation_produces_results(seeded_db):
    results = _run_simulation(seeded_db)
    assert len(results) > 0, "No simulation results — KNOWN_PRE_SIGNALS may be empty"


def test_simulation_recall_at_least_95_pct(seeded_db):
    results = _run_simulation(seeded_db)
    hits = [r for r in results if r.predicted_positive]
    recall = len(hits) / len(results) if results else 0
    assert recall >= 0.95, (
        f"Recall {recall:.1%} below 95% threshold. "
        f"Missed: {[r.company for r in results if not r.predicted_positive]}"
    )


def test_no_score_exceeds_100(seeded_db):
    results = _run_simulation(seeded_db)
    over = [r for r in results if r.score > 100]
    assert not over, f"Score > 100: {[(r.company, r.score) for r in over]}"


def test_no_negative_scores(seeded_db):
    results = _run_simulation(seeded_db)
    neg = [r for r in results if r.score < 0]
    assert not neg


def test_suggestions_structure(seeded_db):
    results = _run_simulation(seeded_db)
    missed = [r for r in results if not r.predicted_positive]
    if missed:
        suggestions = suggest_weight_adjustments(results)
        assert "weight_suggestions" in suggestions or "message" in suggestions


def test_high_confidence_rounds_score_above_80(seeded_db):
    """Rounds with 4+ curated signals should score HIGH."""
    from deal_radar.backtest import KNOWN_PRE_SIGNALS
    from deal_radar.scoring.rules import compute_score
    multi_signal = {
        name: sigs
        for name, sigs in KNOWN_PRE_SIGNALS.items()
        if len(sigs) >= 4
    }
    for company, signals in multi_signal.items():
        score = compute_score(signals)
        assert score >= 80, f"{company} with {signals} scored only {score}/100"
