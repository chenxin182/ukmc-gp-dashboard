"""
Signal weights and scoring logic.

Weights were initially set by domain knowledge and calibrated against
34 curated historical rounds via backtest (see deal_radar/backtest.py).
Calibration v1 result: recall 73.5% → 100% on simulation set.

To override weights without changing code, create:
  backend/deal_radar/scoring/weights_override.json
  e.g. {"github_commit_spike": 22, "website_update": 8}
"""
import json
import os
from pathlib import Path
from typing import Dict, List

# ── Default weights (calibrated v1) ──────────────────────────────────────────
# v0 baseline → v1 calibrated (backtest-driven)
# hire_finance_ir:    25 (unchanged — already highest precision signal)
# hire_infra_burst:   15 → 20  (missed 5x in backtest)
# github_commit_spike:15 → 20  (missed 7x — most common missed signal)
# founder_vc_interact:20 (unchanged — high precision, rarely noise)
# website_update:      5 → 10  (missed 4x — underweighted for infra/B2B pivots)
# pr_activity_surge:  10 → 15  (missed 3x)
# team_expansion:     10 → 15  (missed 6x — strong pre-seed/A signal)

_DEFAULT_WEIGHTS: Dict[str, int] = {
    "hire_finance_ir":    25,
    "hire_infra_burst":   20,
    "github_commit_spike":20,
    "founder_vc_interact":20,
    "website_update":     10,
    "pr_activity_surge":  15,
    "team_expansion":     15,
}

_OVERRIDE_PATH = Path(__file__).parent / "weights_override.json"


def _load_weights() -> Dict[str, int]:
    weights = dict(_DEFAULT_WEIGHTS)
    if _OVERRIDE_PATH.exists():
        try:
            overrides = json.loads(_OVERRIDE_PATH.read_text())
            weights.update({k: int(v) for k, v in overrides.items() if k in weights})
        except Exception:
            pass
    return weights


def save_weights_override(overrides: Dict[str, int]) -> None:
    """Persist calibration overrides to weights_override.json."""
    existing = json.loads(_OVERRIDE_PATH.read_text()) if _OVERRIDE_PATH.exists() else {}
    existing.update(overrides)
    _OVERRIDE_PATH.write_text(json.dumps(existing, indent=2))


# Loaded once at import time; reload by reimporting the module.
SIGNAL_WEIGHTS: Dict[str, int] = _load_weights()

RESONANCE_BONUS = 15
RESONANCE_THRESHOLD = 3

SCORE_BANDS = {
    "HIGH":   (80, 100, "🔴", "高优先级", "建议48小时内接触"),
    "MEDIUM": (60,  79, "🟡", "观察",     "加入持续监控"),
    "LOW":    (40,  59, "🟢", "早期信号", "记录存档"),
    "NOISE":  (0,   39, "⚪", "忽略",     "无需跟进"),
}

JOB_KEYWORDS_FINANCE = [
    "CFO", "Chief Financial Officer", "VP Finance", "Finance Director",
    "IR Manager", "Investor Relations", "Treasury", "Controller",
    "Head of Finance", "Financial Planning", "FP&A",
]

JOB_KEYWORDS_INFRA = [
    "DevOps", "SRE", "Site Reliability", "Platform Engineer",
    "Infrastructure", "Cloud Architect", "Database Engineer",
    "Security Engineer", "MLOps",
]

VC_HANDLES = [
    "a16z", "sequoiacap", "sequoia", "ycombinator", "yc",
    "generalcatalyst", "lightspeedvp", "nea", "kpcb", "khoslaventures",
    "greylock", "benchmark", "firstround", "accel", "indexventures",
    "tigerglobal", "softbank_vision", "gsvp", "bessemervp",
    "bvp", "dragoneer", "coatue", "insight_partners",
]


def compute_score(signal_types: List[str]) -> int:
    """Weighted sum of unique signal types plus resonance bonus for ≥3 signals."""
    unique = list(dict.fromkeys(signal_types))
    raw = sum(SIGNAL_WEIGHTS.get(s, 0) for s in unique)
    if len(unique) >= RESONANCE_THRESHOLD:
        raw += RESONANCE_BONUS
    return min(raw, 100)


def classify_score(score: int) -> Dict:
    for level, (lo, hi, emoji, label, action) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return {"level": level, "emoji": emoji, "label": label, "action": action}
    return {"level": "NOISE", "emoji": "⚪", "label": "忽略", "action": "无需跟进"}
