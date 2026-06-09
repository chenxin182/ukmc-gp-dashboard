"""
Signal Agent — runs every 6 hours.
Iterates the watchlist, hits each scraper, and writes raw signals to DB.
Deduplication: skips a signal if the same type was already captured for
the same company within the last DEDUP_WINDOW_HOURS hours.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Signal
from deal_radar.scrapers.github_scraper import get_commit_activity, get_pr_activity
from deal_radar.scrapers.job_scraper import scan_company_jobs
from deal_radar.scrapers.rss_scraper import scan_for_company_news
from deal_radar.scrapers.twitter_scraper import get_founder_tweet_signals

COMMIT_SPIKE_THRESHOLD = 200.0   # % growth needed to flag as signal
DEDUP_WINDOW_HOURS = 6           # skip if identical signal seen within this window


def _is_duplicate(db: Session, company_id: int, signal_type: str) -> bool:
    """Return True if the same signal type was captured recently."""
    cutoff = datetime.utcnow() - timedelta(hours=DEDUP_WINDOW_HOURS)
    return (
        db.query(Signal)
        .filter(
            Signal.company_id == company_id,
            Signal.signal_type == signal_type,
            Signal.captured_at >= cutoff,
        )
        .first()
        is not None
    )


def _add_signal(
    db: Session,
    company_id: int,
    signal_type: str,
    source_url: str,
    raw: dict,
    skip_dedup: bool = False,
) -> Optional[Signal]:
    if not skip_dedup and _is_duplicate(db, company_id, signal_type):
        return None

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
    skipped = 0

    for company in companies:
        print(f"[SignalAgent] ▶ {company.name}")

        # ── GitHub ───────────────────────────────────────────────────────────
        if company.github_org:
            commit_data = await get_commit_activity(company.github_org)
            if commit_data and commit_data.get("growth_pct", 0) >= COMMIT_SPIKE_THRESHOLD:
                sig = _add_signal(
                    db, company.id, "github_commit_spike",
                    f"https://github.com/{company.github_org}",
                    commit_data,
                )
                if sig:
                    new_signals.append(sig)
                else:
                    skipped += 1

            pr_data = await get_pr_activity(company.github_org)
            if pr_data and pr_data.get("surge"):
                sig = _add_signal(
                    db, company.id, "pr_activity_surge",
                    f"https://github.com/{company.github_org}",
                    pr_data,
                )
                if sig:
                    new_signals.append(sig)
                else:
                    skipped += 1

        # ── Job boards ────────────────────────────────────────────────────────
        job_hits = await scan_company_jobs(
            company.name,
            greenhouse_token=company.greenhouse_token,
            lever_slug=company.lever_slug,
        )
        for job in job_hits:
            sig = _add_signal(
                db, company.id, job["signal_type"],
                job.get("url", ""),
                job,
            )
            if sig:
                new_signals.append(sig)
            else:
                skipped += 1

        # ── RSS / news ────────────────────────────────────────────────────────
        news_items = await scan_for_company_news(company.name, company.domain)
        for item in news_items:
            # News items deduplicate by URL rather than by type (multiple news ok)
            existing_url = (
                db.query(Signal)
                .filter(
                    Signal.company_id == company.id,
                    Signal.signal_type == "news",
                    Signal.source_url == item.get("link", ""),
                )
                .first()
            )
            if existing_url:
                skipped += 1
                continue
            sig = _add_signal(
                db, company.id, "news",
                item.get("link", ""),
                item,
                skip_dedup=True,  # URL dedup handled above
            )
            if sig:
                new_signals.append(sig)

        # ── Twitter ───────────────────────────────────────────────────────────
        handle = company.founder_twitter or company.twitter_handle
        if handle:
            tw = await get_founder_tweet_signals(handle)
            if tw.get("triggered"):
                sig = _add_signal(
                    db, company.id, "founder_vc_interact",
                    f"https://twitter.com/{handle}",
                    tw,
                )
                if sig:
                    new_signals.append(sig)
                else:
                    skipped += 1

    db.commit()
    print(f"[SignalAgent] ✓ {len(new_signals)} new signals | {skipped} deduplicated.")
    return new_signals
