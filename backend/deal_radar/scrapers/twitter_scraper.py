"""
Twitter/X API v2 scraper.
Requires TWITTER_BEARER_TOKEN env var.
Returns empty results gracefully when token is absent.
"""
import os
from typing import Dict, List

import httpx

from deal_radar.scoring.rules import VC_HANDLES

BEARER = os.getenv("TWITTER_BEARER_TOKEN", "")
BASE_URL = "https://api.twitter.com/2"


async def _search(query: str, max_results: int = 100) -> List[Dict]:
    if not BEARER:
        return []
    headers = {"Authorization": f"Bearer {BEARER}"}
    params = {
        "query": query,
        "max_results": min(max_results, 100),
        "tweet.fields": "created_at,author_id,text",
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{BASE_URL}/tweets/search/recent",
                headers=headers,
                params=params,
                timeout=15,
            )
            if r.status_code == 200:
                return r.json().get("data", [])
    except Exception:
        pass
    return []


async def count_founder_vc_interactions(founder_handle: str, days: int = 7) -> int:
    """Count tweets from founder that mention top VCs."""
    vc_part = " OR ".join(f"@{h}" for h in VC_HANDLES[:15])
    query = f"from:{founder_handle} ({vc_part})"
    tweets = await _search(query)
    return len(tweets)


async def get_founder_tweet_signals(founder_handle: str) -> Dict:
    count = await count_founder_vc_interactions(founder_handle)
    return {
        "founder_handle": founder_handle,
        "vc_interaction_count": count,
        "days": 7,
        "triggered": count >= 3,
    }
