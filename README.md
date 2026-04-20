# ESG Carbon Accounting Platform — MVP

Full-stack SaaS MVP for Singapore & Malaysia SMEs to calculate carbon emissions (Scope 1 & 2) and generate GHG-compliant PDF reports.

## Project Structure

```
.
├── backend/
│   ├── main.py               # FastAPI app + all API routes
│   ├── models.py             # SQLAlchemy ORM (Company, EmissionRecord, ActivityData)
│   ├── database.py           # SQLite engine & session factory
│   ├── calculations.py       # Emission factor logic (kg → tCO₂e)
│   ├── report_generator.py   # ReportLab PDF generation
│   ├── factors.json          # Emission factor database (SG + MY)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx            # Router + global state
    │   ├── api.js             # fetch wrappers
    │   └── components/
    │       ├── DataEntry.jsx  # Page 1 — data input form
    │       ├── Dashboard.jsx  # Page 2 — charts & results
    │       └── ReportPage.jsx # Page 3 — PDF download
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

## Quick Start

### 1 — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

API: **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: **http://localhost:5173**

> Vite proxies `/api/*` → `http://localhost:8000` automatically — no CORS config needed.

---

## Emission Factors

| Energy Type | Country | Factor | Unit | Scope | Standard |
|---|---|---|---|---|---|
| `sg_electricity` | Singapore | 0.4057 kg CO₂e | /kWh | 2 | EMA 2025 |
| `sg_petrol` | Singapore | 2.296 kg CO₂e | /litre | 1 | IPCC 2006 |
| `sg_diesel` | Singapore | 2.68 kg CO₂e | /litre | 1 | IPCC 2006 |
| `my_electricity` | Malaysia | 0.585 kg CO₂e | /kWh | 2 | ST 2025 |
| `my_petrol` | Malaysia | 2.296 kg CO₂e | /litre | 1 | IPCC 2006 |
| `my_diesel` | Malaysia | 2.68 kg CO₂e | /litre | 1 | IPCC 2006 |

---

## API Reference

### POST `/api/calculate`

Calculate Scope 1 & 2 emissions and persist to SQLite.

**Request:**
```json
{
  "company_name": "Test Pte Ltd",
  "country": "Singapore",
  "activities": [
    { "energy_type": "sg_electricity", "consumption": 5000, "unit": "kWh" },
    { "energy_type": "my_diesel",      "consumption": 200,  "unit": "litres" }
  ]
}
```

**Response:**
```json
{
  "company_name": "Test Pte Ltd",
  "country": "Singapore",
  "total_emissions": 2.5645,
  "scope1_emissions": 0.536,
  "scope2_emissions": 2.0285,
  "details": [...]
}
```

### POST `/api/report`

Same request body as `/api/calculate` — returns a PDF binary stream.

### GET `/api/companies`

List all saved companies.

### GET `/api/factors`

List all emission factors from `factors.json`.

---

## Test with curl

```bash
# Calculate emissions
curl -s -X POST http://localhost:8000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Pte Ltd",
    "country": "Singapore",
    "activities": [
      {"energy_type": "sg_electricity", "consumption": 5000, "unit": "kWh"},
      {"energy_type": "my_diesel",      "consumption": 200,  "unit": "litres"}
    ]
  }' | python3 -m json.tool

# Download PDF report
curl -X POST http://localhost:8000/api/report \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Pte Ltd",
    "country": "Singapore",
    "activities": [
      {"energy_type": "sg_electricity", "consumption": 5000, "unit": "kWh"},
      {"energy_type": "my_diesel",      "consumption": 200,  "unit": "litres"}
    ]
  }' --output report.pdf && echo "PDF saved as report.pdf"
```

**Expected result:** `total_emissions ≈ 2.5645 tCO₂e`  
(Scope 2: 5000 × 0.0004057 = 2.0285 | Scope 1: 200 × 0.00268 = 0.5360)

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `""` (Vite proxy) | Override backend URL for production |

Create `frontend/.env.local` to override:
```
VITE_API_URL=http://your-backend-host:8000
```
