"""
Signal Agent — runs every 6 hours.
Iterates the watchlist, hits each scraper, and writes raw signals to DB.

Deduplication strategy:
  - Generic signals (github_commit_spike, pr_activity_surge, founder_vc_interact,
    hire_*): skip if same type captured in the last DEDUP_WINDOW_HOURS hours.
  - news: deduplicate by source URL (same article never stored twice).
  - website_update: compare current page hashes vs last stored hashes.
  - team_expansion: only fire if contributor count grew ≥ TEAM_GROWTH_PCT.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Signal
from deal_radar.scrapers.github_scraper import (
    get_commit_activity,
    get_contributor_count,
    get_pr_activity,
)
from deal_radar.scrapers.job_scraper import scan_company_jobs
from deal_radar.scrapers.rss_scraper import scan_for_company_news
from deal_radar.scrapers.twitter_scraper import get_founder_tweet_signals
from deal_radar.scrapers.website_scraper import scan_website

COMMIT_SPIKE_THRESHOLD = 200.0   # % growth needed to flag github_commit_spike
TEAM_GROWTH_PCT = 20.0           # % contributor growth to flag team_expansion
DEDUP_WINDOW_HOURS = 6           # generic dedup window


# ── Deduplication helpers ─────────────────────────────────────────────────────

def _is_duplicate(db: Session, company_id: int, signal_type: str) -> bool:
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


def _last_signal(db: Session, company_id: int, signal_type: str) -> Optional[Signal]:
    return (
        db.query(Signal)
        .filter(Signal.company_id == company_id, Signal.signal_type == signal_type)
        .order_by(Signal.captured_at.desc())
        .first()
    )


def _news_url_exists(db: Session, company_id: int, url: str) -> bool:
    return (
        db.query(Signal)
        .filter(
            Signal.company_id == company_id,
            Signal.signal_type == "news",
            Signal.source_url == url,
        )
        .first()
        is not None
    )


# ── Signal writer ─────────────────────────────────────────────────────────────

def _write(
    db: Session,
    company_id: int,
    signal_type: str,
    source_url: str,
    raw: dict,
) -> Signal:
    sig = Signal(
        company_id=company_id,
        signal_type=signal_type,
        source_url=source_url,
        raw_data=raw,
        captured_at=datetime.utcnow(),
    )
    db.add(sig)
    return sig


# ── Per-signal logic ──────────────────────────────────────────────────────────

async def _check_github(db: Session, company: Company, new_signals: List, skipped: List):
    if not company.github_org:
        return

    # commit spike
    if not _is_duplicate(db, company.id, "github_commit_spike"):
        data = await get_commit_activity(company.github_org)
        if data and data.get("growth_pct", 0) >= COMMIT_SPIKE_THRESHOLD:
            new_signals.append(_write(
                db, company.id, "github_commit_spike",
                f"https://github.com/{company.github_org}", data,
            ))
        elif data:
            skipped.append("github_commit_spike")
    else:
        skipped.append("github_commit_spike")

    # PR surge
    if not _is_duplicate(db, company.id, "pr_activity_surge"):
        pr = await get_pr_activity(company.github_org)
        if pr and pr.get("surge"):
            new_signals.append(_write(
                db, company.id, "pr_activity_surge",
                f"https://github.com/{company.github_org}", pr,
            ))
    else:
        skipped.append("pr_activity_surge")

    # Team expansion — compare against last stored count
    last_team_sig = _last_signal(db, company.id, "team_expansion")
    prev_count = (last_team_sig.raw_data or {}).get("unique_contributors", 0) if last_team_sig else 0
    contrib_data = await get_contributor_count(company.github_org)
    current_count = contrib_data.get("unique_contributors", 0)

    if current_count > 0 and (
        prev_count == 0
        or (current_count - prev_count) / prev_count * 100 >= TEAM_GROWTH_PCT
    ):
        # Only write if we have a meaningful growth — skip first-ever capture if no prev
        if prev_count > 0:
            new_signals.append(_write(
                db, company.id, "team_expansion",
                f"https://github.com/{company.github_org}",
                {**contrib_data, "prev_count": prev_count,
                 "growth_pct": round((current_count - prev_count) / prev_count * 100, 1)},
            ))
        else:
            # First capture — just record the baseline (no signal yet)
            _write(
                db, company.id, "team_expansion",
                f"https://github.com/{company.github_org}",
                {**contrib_data, "prev_count": 0, "baseline": True},
            )


async def _check_jobs(db: Session, company: Company, new_signals: List, skipped: List):
    hits = await scan_company_jobs(
        company.name,
        greenhouse_token=company.greenhouse_token,
        lever_slug=company.lever_slug,
    )
    for job in hits:
        if _is_duplicate(db, company.id, job["signal_type"]):
            skipped.append(job["signal_type"])
        else:
            new_signals.append(_write(
                db, company.id, job["signal_type"], job.get("url", ""), job,
            ))


async def _check_news(db: Session, company: Company, new_signals: List, skipped: List):
    items = await scan_for_company_news(company.name, company.domain)
    for item in items:
        url = item.get("link", "")
        if _news_url_exists(db, company.id, url):
            skipped.append("news")
        else:
            new_signals.append(_write(db, company.id, "news", url, item))


async def _check_twitter(db: Session, company: Company, new_signals: List, skipped: List):
    handle = company.founder_twitter or company.twitter_handle
    if not handle:
        return
    if _is_duplicate(db, company.id, "founder_vc_interact"):
        skipped.append("founder_vc_interact")
        return
    tw = await get_founder_tweet_signals(handle)
    if tw.get("triggered"):
        new_signals.append(_write(
            db, company.id, "founder_vc_interact",
            f"https://twitter.com/{handle}", tw,
        ))


async def _check_website(db: Session, company: Company, new_signals: List, skipped: List):
    if not company.domain:
        return

    last_sig = _last_signal(db, company.id, "website_update")
    prev_hashes = (last_sig.raw_data or {}).get("hashes") if last_sig else None

    result = await scan_website(company.domain, prev_hashes)
    if not result:
        return

    if result.get("triggered"):
        new_signals.append(_write(
            db, company.id, "website_update",
            f"https://{company.domain}", result,
        ))
    elif result.get("hashes") and not prev_hashes:
        # First baseline scan — record without signalling
        _write(
            db, company.id, "website_update",
            f"https://{company.domain}",
            {**result, "baseline": True, "triggered": False},
        )


# ── Main entry ────────────────────────────────────────────────────────────────

async def run_signal_agent(db: Session) -> List[Signal]:
    companies: List[Company] = db.query(Company).all()
    new_signals: List[Signal] = []
    skipped: List[str] = []

    for company in companies:
        print(f"[SignalAgent] ▶ {company.name}")
        await _check_github(db, company, new_signals, skipped)
        await _check_jobs(db, company, new_signals, skipped)
        await _check_news(db, company, new_signals, skipped)
        await _check_twitter(db, company, new_signals, skipped)
        await _check_website(db, company, new_signals, skipped)

    db.commit()
    print(f"[SignalAgent] ✓ {len(new_signals)} new signals | {len(skipped)} deduplicated.")
    return new_signals
