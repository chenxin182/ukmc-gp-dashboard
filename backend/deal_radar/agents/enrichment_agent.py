"""
Enrichment Agent — runs daily at 02:00 UTC.
Clusters recent signals per company and computes signal density windows.
"""
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Signal


def compute_signal_density(db: Session, company_id: int, window_days: int) -> Dict:
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    signals: List[Signal] = (
        db.query(Signal)
        .filter(Signal.company_id == company_id, Signal.captured_at >= cutoff)
        .all()
    )

    by_type: Dict[str, int] = {}
    for s in signals:
        by_type[s.signal_type] = by_type.get(s.signal_type, 0) + 1

    return {
        "total": len(signals),
        "by_type": by_type,
        "unique_types": list(by_type.keys()),
        "window_days": window_days,
    }


def run_enrichment_agent(db: Session) -> List[Dict]:
    companies: List[Company] = db.query(Company).all()
    report = []

    for company in companies:
        d14 = compute_signal_density(db, company.id, 14)
        d30 = compute_signal_density(db, company.id, 30)
        company.updated_at = datetime.utcnow()

        entry = {
            "company_id": company.id,
            "name": company.name,
            "density_14d": d14,
            "density_30d": d30,
        }
        report.append(entry)
        print(
            f"[EnrichmentAgent] {company.name}: "
            f"{d14['total']} signals (14d) | {d30['total']} (30d) | "
            f"types={d14['unique_types']}"
        )

    db.commit()
    return report
