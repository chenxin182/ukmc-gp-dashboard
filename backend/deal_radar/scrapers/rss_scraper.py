import xml.etree.ElementTree as ET
from typing import Dict, List

import httpx

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://news.ycombinator.com/rss",
    "https://36kr.com/feed",
]

_FUNDING_KEYWORDS = [
    "raises", "funding", "series a", "series b", "series c",
    "seed round", "investment", "venture", "backed", "valuation",
    "round", "fundraise", "capital", "融资", "投资", "轮",
]


async def _fetch_feed(url: str) -> List[Dict]:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(url, timeout=15, headers={"User-Agent": "DealRadar/1.0"})
            if r.status_code != 200:
                return []
        root = ET.fromstring(r.text)
        items = []
        for item in root.iter("item"):
            items.append({
                "title": item.findtext("title", ""),
                "link": item.findtext("link", ""),
                "pub_date": item.findtext("pubDate", ""),
                "description": item.findtext("description", ""),
                "source": url,
            })
        return items
    except Exception:
        return []


def _is_funding_related(item: Dict) -> bool:
    text = (item.get("title", "") + " " + item.get("description", "")).lower()
    return any(kw in text for kw in _FUNDING_KEYWORDS)


def _matches_company(item: Dict, company_name: str, domain: str | None) -> bool:
    text = (item.get("title", "") + " " + item.get("description", "")).lower()
    if company_name.lower() in text:
        return True
    if domain:
        slug = domain.replace("www.", "").split(".")[0]
        if slug and slug in text:
            return True
    return False


async def scan_for_company_news(company_name: str, domain: str | None = None) -> List[Dict]:
    results = []
    for feed_url in RSS_FEEDS:
        items = await _fetch_feed(feed_url)
        for item in items:
            if _matches_company(item, company_name, domain) and _is_funding_related(item):
                item["matched_company"] = company_name
                results.append(item)
    return results
