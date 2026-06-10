import os
from datetime import datetime, timedelta
from typing import Dict, List

import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BASE_URL = "https://api.github.com"
_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    **({"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}


async def _get(client: httpx.AsyncClient, path: str, params: Dict = None) -> dict | list | None:
    try:
        r = await client.get(f"{BASE_URL}{path}", headers=_HEADERS, params=params or {}, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


async def list_org_repos(org: str) -> List[Dict]:
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"/orgs/{org}/repos", {"sort": "pushed", "per_page": 10})
        return data if isinstance(data, list) else []


async def get_commit_activity(org: str) -> Dict:
    """
    Returns commit spike signal data.
    Compares commits in the most recent 14 days vs the prior 14 days.
    """
    repos = await list_org_repos(org)
    if not repos:
        return {}

    repo_name = repos[0]["name"]
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"/repos/{org}/{repo_name}/stats/commit_activity")

    if not isinstance(data, list) or len(data) < 4:
        return {}

    recent_2w = sum(w["total"] for w in data[-2:])
    prior_2w = sum(w["total"] for w in data[-4:-2])

    if prior_2w == 0:
        growth_pct = 200.0 if recent_2w > 0 else 0.0
    else:
        growth_pct = ((recent_2w - prior_2w) / prior_2w) * 100

    return {
        "org": org,
        "repo": repo_name,
        "recent_2w_commits": recent_2w,
        "prior_2w_commits": prior_2w,
        "growth_pct": round(growth_pct, 1),
    }


async def get_pr_activity(org: str) -> Dict:
    repos = await list_org_repos(org)
    if not repos:
        return {}

    repo_name = repos[0]["name"]
    cutoff_14d = datetime.utcnow() - timedelta(days=14)
    cutoff_28d = datetime.utcnow() - timedelta(days=28)

    async with httpx.AsyncClient() as client:
        data = await _get(
            client,
            f"/repos/{org}/{repo_name}/pulls",
            {"state": "all", "per_page": 100, "sort": "updated"},
        )

    if not isinstance(data, list):
        return {}

    recent = sum(1 for pr in data if (pr.get("created_at") or "") >= cutoff_14d.isoformat())
    prior = sum(
        1 for pr in data
        if cutoff_28d.isoformat() <= (pr.get("created_at") or "") < cutoff_14d.isoformat()
    )

    return {
        "org": org,
        "repo": repo_name,
        "recent_14d_prs": recent,
        "prior_14d_prs": prior,
        "surge": recent > max(prior * 1.5, 1),
    }


async def get_contributor_count(org: str) -> Dict:
    repos = await list_org_repos(org)
    contributors: set = set()

    async with httpx.AsyncClient() as client:
        for repo in repos[:5]:
            data = await _get(client, f"/repos/{org}/{repo['name']}/contributors", {"per_page": 50})
            if isinstance(data, list):
                for c in data:
                    contributors.add(c.get("login", ""))

    return {"org": org, "unique_contributors": len(contributors)}
