"""
Website scraper — detects new pages and content changes on company sites.
Generates `website_update` signals.

Key pages monitored:
  /pricing, /enterprise, /team, /about, /investors, /security

Strategy:
  - Checks page existence via GET (200 = exists)
  - Hashes body text to detect content changes
  - Compares against hashes stored in the last website_update signal's raw_data
"""
import hashlib
from typing import Dict, List, Optional

import httpx

MONITORED_PATHS = [
    "/pricing",
    "/enterprise",
    "/team",
    "/about",
    "/security",
    "/investors",
    "/press",
]

_HIGH_VALUE_PATHS = {"/pricing", "/enterprise", "/investors"}

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DealRadar/1.0)"}


async def _fetch_page_hash(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        r = await client.get(url, headers=_HEADERS, follow_redirects=True, timeout=12)
        if r.status_code == 200:
            # Hash visible text length + title to avoid JS noise
            text = r.text[:50_000]
            return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()
        return None
    except Exception:
        return None


async def scan_website(domain: str, previous_hashes: Dict[str, str] | None = None) -> Dict:
    """
    Scan a domain for new/changed pages.

    Returns a dict with:
      pages_found: list of currently live paths
      new_pages:   paths that appear in pages_found but not in previous_hashes
      changed:     paths whose content hash changed
      hashes:      current hash snapshot (persist in raw_data for next run)
      triggered:   True if any new high-value page or significant change
    """
    if not domain:
        return {}

    base = f"https://{domain.rstrip('/')}"
    current_hashes: Dict[str, str] = {}
    pages_found: List[str] = []

    async with httpx.AsyncClient() as client:
        for path in MONITORED_PATHS:
            h = await _fetch_page_hash(client, f"{base}{path}")
            if h:
                current_hashes[path] = h
                pages_found.append(path)

    if not current_hashes:
        return {}

    prev = previous_hashes or {}
    new_pages = [p for p in pages_found if p not in prev]
    changed = [
        p for p in pages_found
        if p in prev and prev[p] != current_hashes[p]
    ]

    # Signal is worth capturing if:
    # - any high-value page appeared (pricing, enterprise, investors)
    # - any previously-known page changed content
    triggered = (
        any(p in _HIGH_VALUE_PATHS for p in new_pages)
        or len(changed) > 0
    )

    return {
        "domain": domain,
        "pages_found": pages_found,
        "new_pages": new_pages,
        "changed": changed,
        "hashes": current_hashes,
        "triggered": triggered,
    }
