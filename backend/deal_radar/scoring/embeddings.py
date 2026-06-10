"""
Embedding-based similarity matching against historical funding patterns.
Falls back to keyword overlap when sentence-transformers is not installed.
"""
from typing import Dict, List

# Canonical pre-funding signal fingerprints derived from historical cases
HISTORICAL_PATTERNS: Dict[str, List[str]] = {
    "series_a": [
        "hire_finance_ir github_commit_spike founder_vc_interact team_expansion",
        "hire_finance_ir pr_activity_surge founder_vc_interact website_update",
        "github_commit_spike hire_finance_ir hire_infra_burst founder_vc_interact",
        "hire_finance_ir team_expansion founder_vc_interact website_update",
    ],
    "seed": [
        "github_commit_spike team_expansion pr_activity_surge",
        "hire_infra_burst github_commit_spike website_update",
        "team_expansion github_commit_spike founder_vc_interact",
        "github_commit_spike pr_activity_surge website_update",
    ],
    "series_b": [
        "hire_finance_ir hire_infra_burst team_expansion founder_vc_interact",
        "hire_finance_ir github_commit_spike team_expansion website_update",
    ],
    "acquisition": [
        "hire_finance_ir website_update news",
        "hire_finance_ir team_expansion news website_update",
    ],
    "pivot": [
        "hire_infra_burst github_commit_spike website_update",
        "github_commit_spike website_update pr_activity_surge",
    ],
}

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    _model: SentenceTransformer | None = None

    def _get_model() -> SentenceTransformer:
        global _model
        if _model is None:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        return _model

    def find_best_match(signal_types: List[str]) -> Dict:
        model = _get_model()
        query_text = " ".join(sorted(signal_types))
        query_emb = model.encode([query_text])[0]

        best_score = 0.0
        best_event = "unknown"

        for event, patterns in HISTORICAL_PATTERNS.items():
            pattern_embs = model.encode(patterns)
            norms = np.linalg.norm(pattern_embs, axis=1) * np.linalg.norm(query_emb)
            sims = np.dot(pattern_embs, query_emb) / np.where(norms == 0, 1, norms)
            max_sim = float(sims.max())
            if max_sim > best_score:
                best_score = max_sim
                best_event = event

        return {"event_type": best_event, "similarity": round(best_score, 3), "method": "embedding"}

except ImportError:

    def find_best_match(signal_types: List[str]) -> Dict:  # type: ignore[misc]
        query_set = set(signal_types)
        best_score = 0.0
        best_event = "unknown"

        for event, patterns in HISTORICAL_PATTERNS.items():
            for pattern in patterns:
                pattern_set = set(pattern.split())
                if not pattern_set:
                    continue
                overlap = len(query_set & pattern_set) / len(pattern_set)
                if overlap > best_score:
                    best_score = overlap
                    best_event = event

        return {"event_type": best_event, "similarity": round(best_score, 3), "method": "keyword"}
