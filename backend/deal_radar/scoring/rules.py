from typing import Dict, List

SIGNAL_WEIGHTS: Dict[str, int] = {
    "hire_finance_ir": 25,      # CFO / VP Finance / IR Manager
    "hire_infra_burst": 15,     # DevOps / SRE / Platform surge
    "github_commit_spike": 15,  # commit growth > 200 %
    "founder_vc_interact": 20,  # founder @ top-VC on Twitter
    "website_update": 5,        # pricing / enterprise page added
    "pr_activity_surge": 10,    # PR velocity increase
    "team_expansion": 10,       # headcount growing fast
}

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
    """Weighted sum of unique signal types, with resonance bonus."""
    unique = list(dict.fromkeys(signal_types))   # preserve order, dedupe
    raw = sum(SIGNAL_WEIGHTS.get(s, 0) for s in unique)
    if len(unique) >= RESONANCE_THRESHOLD:
        raw += RESONANCE_BONUS
    return min(raw, 100)


def classify_score(score: int) -> Dict:
    for level, (lo, hi, emoji, label, action) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return {"level": level, "emoji": emoji, "label": label, "action": action}
    return {"level": "NOISE", "emoji": "⚪", "label": "忽略", "action": "无需跟进"}
