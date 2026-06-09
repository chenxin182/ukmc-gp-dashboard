"""
Seed script: imports historical funding events from data/funding_events.csv
and optionally adds demo watchlist companies.
Run: python -m deal_radar.db.seed
"""
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Allow running as a module from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deal_radar.db.database import SessionLocal, init_db
from deal_radar.db.models import Company, FundingEvent

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "funding_events.csv"

DEMO_WATCHLIST = [
    {
        "name": "Mistral AI",
        "domain": "mistral.ai",
        "github_org": "mistralai",
        "sector": "AI / LLM",
        "stage": "series_b",
    },
    {
        "name": "Cohere",
        "domain": "cohere.com",
        "github_org": "cohere-ai",
        "sector": "AI / NLP",
        "stage": "series_c",
    },
    {
        "name": "Together AI",
        "domain": "together.ai",
        "github_org": "togethercomputer",
        "sector": "AI / Infrastructure",
        "stage": "series_a",
    },
    {
        "name": "Perplexity AI",
        "domain": "perplexity.ai",
        "github_org": "perplexity-ai",
        "sector": "AI / Search",
        "stage": "series_b",
    },
    {
        "name": "Imbue",
        "domain": "imbue.com",
        "github_org": "imbue-ai",
        "sector": "AI / Reasoning",
        "stage": "series_b",
    },
]


def import_funding_events(db, csv_path: Path) -> int:
    if not csv_path.exists():
        print(f"[Seed] CSV not found: {csv_path}")
        return 0

    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                date = datetime.strptime(row["announced_date"].strip(), "%Y-%m-%d")
            except ValueError:
                continue

            amount = float(row["amount_usd"]) if row.get("amount_usd", "").strip() else None
            event = FundingEvent(
                company_name=row["company_name"].strip(),
                round_type=row["round_type"].strip(),
                amount_usd=amount,
                announced_date=date,
                source_url=row.get("source_url", "").strip(),
                verified=True,
            )
            db.add(event)
            count += 1

    db.commit()
    return count


def seed_demo_watchlist(db) -> int:
    count = 0
    for data in DEMO_WATCHLIST:
        existing = db.query(Company).filter_by(name=data["name"]).first()
        if not existing:
            db.add(Company(**data))
            count += 1
    db.commit()
    return count


if __name__ == "__main__":
    print("[Seed] Initialising database...")
    init_db()
    db = SessionLocal()

    n_events = import_funding_events(db, CSV_PATH)
    print(f"[Seed] Imported {n_events} funding events.")

    n_companies = seed_demo_watchlist(db)
    print(f"[Seed] Added {n_companies} demo watchlist companies.")

    db.close()
    print("[Seed] Done.")
