"""Tests for scoring/rules.py — the most critical module in the system."""
import pytest
from deal_radar.scoring.rules import (
    RESONANCE_BONUS,
    RESONANCE_THRESHOLD,
    SIGNAL_WEIGHTS,
    classify_score,
    compute_score,
)


# ── compute_score ─────────────────────────────────────────────────────────────

def test_empty_signals_is_zero():
    assert compute_score([]) == 0


def test_single_signal_no_resonance():
    score = compute_score(["hire_finance_ir"])
    assert score == SIGNAL_WEIGHTS["hire_finance_ir"]


def test_two_signals_no_resonance():
    signals = ["hire_finance_ir", "github_commit_spike"]
    expected = SIGNAL_WEIGHTS["hire_finance_ir"] + SIGNAL_WEIGHTS["github_commit_spike"]
    assert compute_score(signals) == expected


def test_three_signals_resonance_applied():
    signals = ["hire_finance_ir", "github_commit_spike", "founder_vc_interact"]
    base = sum(SIGNAL_WEIGHTS[s] for s in signals)
    assert compute_score(signals) == base + RESONANCE_BONUS


def test_resonance_threshold_is_three():
    assert RESONANCE_THRESHOLD == 3


def test_duplicate_signals_deduped_before_scoring():
    # Three instances of same type = 1 unique → no resonance
    score = compute_score(["github_commit_spike"] * 3)
    assert score == SIGNAL_WEIGHTS["github_commit_spike"]


def test_dedup_counts_toward_resonance():
    # 2 dupes + 2 unique = 3 unique total → resonance fires
    signals = ["github_commit_spike", "github_commit_spike",
               "hire_finance_ir", "founder_vc_interact"]
    unique_base = (
        SIGNAL_WEIGHTS["github_commit_spike"]
        + SIGNAL_WEIGHTS["hire_finance_ir"]
        + SIGNAL_WEIGHTS["founder_vc_interact"]
    )
    assert compute_score(signals) == unique_base + RESONANCE_BONUS


def test_score_capped_at_100():
    all_signals = list(SIGNAL_WEIGHTS.keys())
    assert compute_score(all_signals) == 100


def test_unknown_signal_type_ignored():
    score = compute_score(["hire_finance_ir", "totally_made_up_signal"])
    assert score == SIGNAL_WEIGHTS["hire_finance_ir"]


def test_all_weights_are_positive():
    assert all(w > 0 for w in SIGNAL_WEIGHTS.values())


# ── classify_score ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected_level", [
    (100, "HIGH"),
    (80,  "HIGH"),
    (79,  "MEDIUM"),
    (60,  "MEDIUM"),
    (59,  "LOW"),
    (40,  "LOW"),
    (39,  "NOISE"),
    (0,   "NOISE"),
])
def test_classify_band_boundaries(score, expected_level):
    result = classify_score(score)
    assert result["level"] == expected_level, f"score={score} expected {expected_level}, got {result['level']}"


def test_classify_returns_required_keys():
    result = classify_score(75)
    assert {"level", "emoji", "label", "action"} == set(result.keys())


def test_high_priority_has_red_emoji():
    assert classify_score(85)["emoji"] == "🔴"


def test_medium_priority_has_yellow_emoji():
    assert classify_score(65)["emoji"] == "🟡"


# ── Calibration v1 regression guard ──────────────────────────────────────────

CALIBRATION_CASES = {
    # Cases that were MISSED in v0 (score 55 → now 60+)
    "Modal":       (["hire_infra_burst", "github_commit_spike", "pr_activity_surge"], 60),
    "Pinecone":    (["hire_finance_ir", "team_expansion", "website_update"],          60),
    "Together AI": (["github_commit_spike", "hire_infra_burst", "team_expansion"],    60),
    "LangChain":   (["github_commit_spike", "pr_activity_surge", "team_expansion"],   60),
    "Ideogram":    (["github_commit_spike", "website_update", "team_expansion"],      60),
    # High-confidence cases must stay HIGH
    "Perplexity A":  (["github_commit_spike", "founder_vc_interact", "pr_activity_surge", "hire_finance_ir"], 80),
    "Anthropic":     (["hire_finance_ir", "hire_infra_burst", "team_expansion", "github_commit_spike"], 80),
}

@pytest.mark.parametrize("company,signals_min", [
    (name, (sigs, minimum))
    for name, (sigs, minimum) in CALIBRATION_CASES.items()
])
def test_calibration_v1_regression(company, signals_min):
    signals, minimum = signals_min
    score = compute_score(signals)
    assert score >= minimum, (
        f"{company}: score {score} < {minimum}. "
        "Calibration regression — check SIGNAL_WEIGHTS."
    )
