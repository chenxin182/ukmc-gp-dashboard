"""Unit tests for scraper utilities — no live HTTP, all logic-level."""
import pytest

from deal_radar.scrapers.job_scraper import _classify_job
from deal_radar.scrapers.rss_scraper import _is_funding_related, _matches_company
from deal_radar.scrapers.website_scraper import _HIGH_VALUE_PATHS, MONITORED_PATHS


# ── Job scraper ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("title,expected", [
    ("VP Finance",                 "hire_finance_ir"),
    ("Chief Financial Officer",    "hire_finance_ir"),
    ("Investor Relations Manager", "hire_finance_ir"),
    ("Head of FP&A",               "hire_finance_ir"),
    ("DevOps Engineer",            "hire_infra_burst"),
    ("Senior SRE",                 "hire_infra_burst"),
    ("MLOps Engineer",             "hire_infra_burst"),
    ("Platform Engineering Lead",  "hire_infra_burst"),
    ("Software Engineer",          None),
    ("Marketing Manager",          None),
    ("Product Designer",           None),
])
def test_classify_job(title, expected):
    assert _classify_job(title) == expected


def test_classify_job_case_insensitive():
    assert _classify_job("vp finance") == "hire_finance_ir"
    assert _classify_job("DEVOPS ENGINEER") == "hire_infra_burst"


# ── RSS scraper ────────────────────────────────────────────────────────────────

def test_is_funding_related_raises_on_keyword():
    item = {"title": "Startup raises $50M Series A", "description": ""}
    assert _is_funding_related(item) is True


def test_is_funding_related_ignores_unrelated():
    item = {"title": "New product launch", "description": "Exciting features released today."}
    assert _is_funding_related(item) is False


def test_matches_company_by_name():
    item = {"title": "Mistral AI raises €600M", "description": ""}
    assert _matches_company(item, "Mistral AI", None) is True


def test_matches_company_by_domain_slug():
    item = {"title": "mistral raises new round", "description": ""}
    assert _matches_company(item, "Mistral AI", "mistral.ai") is True


def test_does_not_match_unrelated():
    item = {"title": "OpenAI raises billions", "description": ""}
    assert _matches_company(item, "Mistral AI", "mistral.ai") is False


# ── Website scraper ───────────────────────────────────────────────────────────

def test_high_value_paths_subset_of_monitored():
    assert _HIGH_VALUE_PATHS.issubset(set(MONITORED_PATHS))


def test_pricing_is_high_value():
    assert "/pricing" in _HIGH_VALUE_PATHS


def test_enterprise_is_high_value():
    assert "/enterprise" in _HIGH_VALUE_PATHS


def test_monitored_paths_start_with_slash():
    assert all(p.startswith("/") for p in MONITORED_PATHS)
