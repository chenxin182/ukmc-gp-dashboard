"""
APScheduler configuration for all four Deal Radar agents.
Import and call start_scheduler() from the FastAPI lifespan.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from deal_radar.db.database import SessionLocal

_scheduler: AsyncIOScheduler | None = None


def _sync_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def _job_signal():
    from deal_radar.agents.signal_agent import run_signal_agent
    db = SessionLocal()
    try:
        await run_signal_agent(db)
    finally:
        db.close()


def _job_enrichment():
    from deal_radar.agents.enrichment_agent import run_enrichment_agent
    db = SessionLocal()
    try:
        run_enrichment_agent(db)
    finally:
        db.close()


def _job_inference():
    from deal_radar.agents.inference_agent import run_inference_agent
    db = SessionLocal()
    try:
        run_inference_agent(db)
    finally:
        db.close()


def _job_delivery():
    from deal_radar.agents.delivery_agent import run_delivery_agent
    db = SessionLocal()
    try:
        run_delivery_agent(db)
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Signal Agent — every 6 hours
    _scheduler.add_job(_job_signal, "interval", hours=6, id="signal_agent", replace_existing=True)

    # Enrichment Agent — daily 02:00 UTC
    _scheduler.add_job(_job_enrichment, "cron", hour=2, minute=0, id="enrichment_agent", replace_existing=True)

    # Inference Agent — daily 06:00 UTC
    _scheduler.add_job(_job_inference, "cron", hour=6, minute=0, id="inference_agent", replace_existing=True)

    # Delivery Agent — daily 08:00 UTC
    _scheduler.add_job(_job_delivery, "cron", hour=8, minute=0, id="delivery_agent", replace_existing=True)

    _scheduler.start()
    print("[Scheduler] Deal Radar agents scheduled.")
    return _scheduler


def stop_scheduler():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[Scheduler] Stopped.")
