"""
Job-board scrapers using public APIs (no auth required).
Supported: Greenhouse, Lever.
"""
from typing import Dict, List, Optional

import httpx

from deal_radar.scoring.rules import JOB_KEYWORDS_FINANCE, JOB_KEYWORDS_INFRA


def _classify_job(title: str) -> Optional[str]:
    t = title.upper()
    if any(kw.upper() in t for kw in JOB_KEYWORDS_FINANCE):
        return "hire_finance_ir"
    if any(kw.upper() in t for kw in JOB_KEYWORDS_INFRA):
        return "hire_infra_burst"
    return None


async def _fetch_greenhouse(token: str) -> List[Dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=15)
            if r.status_code == 200:
                return r.json().get("jobs", [])
    except Exception:
        pass
    return []


async def _fetch_lever(slug: str) -> List[Dict]:
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return []


async def scan_company_jobs(
    company_name: str,
    greenhouse_token: Optional[str] = None,
    lever_slug: Optional[str] = None,
) -> List[Dict]:
    results = []

    if greenhouse_token:
        for job in await _fetch_greenhouse(greenhouse_token):
            title = job.get("title", "")
            sig = _classify_job(title)
            if sig:
                results.append({
                    "title": title,
                    "signal_type": sig,
                    "url": job.get("absolute_url", ""),
                    "source": "greenhouse",
                    "company": company_name,
                })

    if lever_slug:
        for job in await _fetch_lever(lever_slug):
            title = job.get("text", "")
            sig = _classify_job(title)
            if sig:
                results.append({
                    "title": title,
                    "signal_type": sig,
                    "url": job.get("hostedUrl", ""),
                    "source": "lever",
                    "company": company_name,
                })

    return results
