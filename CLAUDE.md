# UKMC GP Dashboard

Two-module platform: **ESG Carbon Accounting** + **Deal Radar** (pre-funding signal intelligence).

## Quick Start

```bash
cd backend
pip install -r requirements.txt

# Seed DB: 50 historical AI funding events + 5 demo watchlist companies
python -m deal_radar.db.seed

# Start API server (port 8000)
uvicorn main:app --reload --port 8000

# Frontend (port 5173)
cd ../frontend && npm install && npm run dev
```

Or with Docker:

```bash
cp backend/.env.example backend/.env   # fill in API keys
docker-compose up -d
```

## Project Structure

```
backend/
├── deal_radar/
│   ├── agents/
│   │   ├── signal_agent.py      — every 6h: GitHub/jobs/RSS/Twitter/website
│   │   ├── enrichment_agent.py  — 02:00 UTC: signal density per company
│   │   ├── inference_agent.py   — 06:00 UTC: score + pattern match → Inference
│   │   └── delivery_agent.py    — 08:00 UTC: email/Feishu/Slack digest
│   ├── scrapers/
│   │   ├── github_scraper.py    — commit spike, PR surge, contributor growth
│   │   ├── job_scraper.py       — Greenhouse + Lever public APIs
│   │   ├── rss_scraper.py       — TechCrunch/VB/HN/36kr keyword filter
│   │   ├── twitter_scraper.py   — founder × VC interaction count
│   │   └── website_scraper.py   — page hash change detection
│   ├── scoring/
│   │   ├── rules.py             — SIGNAL_WEIGHTS, compute_score(), classify_score()
│   │   └── embeddings.py        — pattern match vs historical rounds
│   ├── db/
│   │   ├── models.py            — 5 SQLAlchemy tables (dr_*)
│   │   ├── database.py          — engine + get_db()
│   │   └── seed.py              — CSV import + demo watchlist
│   ├── api/router.py            — 20 FastAPI endpoints under /dr/*
│   ├── backtest.py              — simulation + weight calibration
│   ├── cli.py                   — management CLI
│   └── scheduler.py             — APScheduler cron wiring
├── tests/
│   ├── test_scoring.py          — 20+ scoring unit tests
│   ├── test_backtest.py         — recall regression tests
│   └── test_scrapers.py         — scraper utility tests
├── data/funding_events.csv      — 50 AI rounds 2022-2024 (ground truth)
├── Dockerfile
└── requirements.txt

frontend/src/components/DealRadar/
├── DealRadarPage.jsx     — tabbed layout (情报 / 监控列表 / 回测)
├── InferenceCard.jsx     — score badge + signal chips + feedback
├── WatchlistPanel.jsx    — company list + signal history drawer
├── AddCompanyModal.jsx   — add company form
├── BacktestPanel.jsx     — recall table + weight suggestions
├── ScoreBadge.jsx
└── SignalChip.jsx
```

## Development Workflow

```bash
# 1. Add a company to watch
python -m deal_radar.cli companies add "Acme AI" \
  --github acme-ai --domain acme.ai --sector "AI / Agents"

# 2. Manually inject a signal (for testing without API keys)
python -m deal_radar.cli signals inject 1 github_commit_spike
python -m deal_radar.cli signals inject 1 hire_finance_ir
python -m deal_radar.cli signals inject 1 founder_vc_interact

# 3. Run inference
python -m deal_radar.cli inference run

# 4. Preview digest
python -m deal_radar.cli digest preview

# 5. Run full pipeline
python -m deal_radar.cli signals run    # requires GITHUB_TOKEN
python -m deal_radar.cli inference run

# 6. Backtest + calibrate
python -m deal_radar.cli backtest
python -m deal_radar.cli calibrate      # writes scoring/weights_override.json

# 7. Run tests
cd backend && pytest tests/ -v
```

## Environment Variables

Copy `backend/.env.example` → `backend/.env`:

| Variable | Purpose | Required |
|----------|---------|----------|
| `GITHUB_TOKEN` | GitHub API (60 → 5000 req/hr) | Recommended |
| `TWITTER_BEARER_TOKEN` | Twitter v2 VC interaction signal | Optional |
| `SMTP_USER` / `SMTP_PASS` | Email digest | Optional |
| `FEISHU_WEBHOOK_URL` | Feishu bot card | Optional |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook | Optional |
| `DEAL_RADAR_DB_URL` | DB connection (default: SQLite) | Optional |

## Scoring Logic

| Signal | Weight | Detection |
|--------|--------|-----------|
| `hire_finance_ir` | **25** | Job titles: CFO/VP Finance/IR Manager |
| `hire_infra_burst` | **20** | Job titles: DevOps/SRE/MLOps |
| `github_commit_spike` | **20** | Commit growth > 200% (14d vs prior 14d) |
| `founder_vc_interact` | **20** | Founder tweets @ top VCs (≥3 in 7d) |
| `pr_activity_surge` | **15** | PR count growth > 50% |
| `team_expansion` | **15** | Contributor count growth ≥ 20% |
| `website_update` | **10** | New /pricing /enterprise /investors page |

**Resonance bonus**: +15 when ≥3 unique signal types fire together.

Score bands: 🔴 80-100 (HIGH — 48h contact) · 🟡 60-79 (MEDIUM — monitor) · 🟢 40-59 (LOW — archive)

Weights are calibrated against 34 historical AI company rounds; backtest recall = 100%.
Override locally: `backend/deal_radar/scoring/weights_override.json` (gitignored).

## API Reference — Deal Radar (/dr/*)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dr/companies` | Watchlist |
| POST | `/dr/companies` | Add company |
| DELETE | `/dr/companies/{id}` | Remove company |
| POST | `/dr/companies/{id}/signals` | Inject signal manually |
| GET | `/dr/inferences` | All inferences (filterable by days/score) |
| GET | `/dr/inferences/today` | Last 24h inferences |
| POST | `/dr/feedback/{id}` | Label outcome (confirmed/false_positive) |
| GET | `/dr/signals/{company_id}` | Raw signals for company |
| GET | `/dr/backtest/simulation` | Recall metrics + per-round detail |
| GET | `/dr/digest/preview` | Preview daily digest |
| POST | `/dr/run/signals` | Trigger Signal Agent |
| POST | `/dr/run/inference` | Trigger Inference Agent |
| POST | `/dr/score` | Score arbitrary signal list |

Full Swagger docs: `http://localhost:8000/docs`

## Database Schema

Five tables (all prefixed `dr_`):

- `dr_companies` — watchlist (GitHub org, domain, job board tokens)
- `dr_signals` — raw captured signals with JSON payload
- `dr_inferences` — scored predictions with reasoning
- `dr_funding_events` — 50-round ground truth CSV for backtesting
- `dr_feedback` — human-labelled outcomes for precision tracking

Default: SQLite (`deal_radar.db`). Switch to Postgres/pgvector by setting `DEAL_RADAR_DB_URL`.
