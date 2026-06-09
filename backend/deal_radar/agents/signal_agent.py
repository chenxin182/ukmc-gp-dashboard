"""
Signal Agent — runs every 6 hours.
Iterates the watchlist, hits each scraper, and writes raw signals to DB.
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Signal
from deal_radar.scrapers.github_scraper import get_commit_activity, get_pr_activity
from deal_radar.scrapers.job_scraper import scan_company_jobs
from deal_radar.scrapers.rss_scraper import scan_for_company_news
from deal_radar.scrapers.twitter_scraper import get_founder_tweet_signals

COMMIT_SPIKE_THRESHOLD = 200.0  # percent growth to flag as signal


def _add_signal(db: Session, company_id: int, signal_type: str, source_url: str, raw: dict) -> Signal:
    sig = Signal(
        company_id=company_id,
        signal_type=signal_type,
        source_url=source_url,
        raw_data=raw,
        captured_at=datetime.utcnow(),
    )
    db.add(sig)
    return sig


async def run_signal_agent(db: Session) -> List[Signal]:
    companies: List[Company] = db.query(Company).all()
    new_signals: List[Signal] = []

    for company in companies:
        print(f"[SignalAgent] ▶ {company.name}")

        # ── GitHub ──────────────────────────────────────────────────────────
        if company.github_org:
            commit_data = await get_commit_activity(company.github_org)
            if commit_data and commit_data.get("growth_pct", 0) >= COMMIT_SPIKE_THRESHOLD:
                new_signals.append(_add_signal(
                    db, company.id, "github_commit_spike",
                    f"https://github.com/{company.github_org}",
                    commit_data,
                ))

            pr_data = await get_pr_activity(company.github_org)
            if pr_data and pr_data.get("surge"):
                new_signals.append(_add_signal(
                    db, company.id, "pr_activity_surge",
                    f"https://github.com/{company.github_org}",
                    pr_data,
                ))

        # ── Job boards ───────────────────────────────────────────────────────
        job_hits = await scan_company_jobs(
            company.name,
            greenhouse_token=company.greenhouse_token,
            lever_slug=company.lever_slug,
        )
        for job in job_hits:
            new_signals.append(_add_signal(
                db, company.id, job["signal_type"],
                job.get("url", ""),
                job,
            ))

        # ── RSS / news ───────────────────────────────────────────────────────
        news_items = await scan_for_company_news(company.name, company.domain)
        for item in news_items:
            new_signals.append(_add_signal(
                db, company.id, "news",
                item.get("link", ""),
                item,
            ))

        # ── Twitter ──────────────────────────────────────────────────────────
        handle = company.founder_twitter or company.twitter_handle
        if handle:
            tw = await get_founder_tweet_signals(handle)
            if tw.get("triggered"):
                new_signals.append(_add_signal(
                    db, company.id, "founder_vc_interact",
                    f"https://twitter.com/{handle}",
                    tw,
                ))

    db.commit()
    print(f"[SignalAgent] ✓ {len(new_signals)} new signals captured.")
    return new_signals
