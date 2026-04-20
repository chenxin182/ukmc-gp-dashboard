import io
from datetime import datetime
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from calculations import calculate_emissions, get_factors
from database import engine, get_db
from models import ActivityData, Base, Company, EmissionRecord
from report_generator import generate_pdf_report

# Initialise DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ESG Carbon Accounting API",
    description="Carbon emissions calculation and PDF reporting for Singapore & Malaysia SMEs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ActivityInput(BaseModel):
    energy_type: str
    consumption: float
    unit: str = ""


class CalculateRequest(BaseModel):
    company_name: str
    country: str = "Singapore"
    activities: List[ActivityInput]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "ESG Carbon Accounting API", "docs": "/docs", "version": "1.0.0"}


@app.get("/api/factors")
def list_factors():
    """Return all available emission factors."""
    return get_factors()


@app.get("/api/companies")
def list_companies(db: Session = Depends(get_db)):
    """Return all saved companies."""
    rows = db.query(Company).order_by(Company.created_at.desc()).all()
    return [
        {"id": c.id, "name": c.name, "country": c.country, "created_at": c.created_at}
        for c in rows
    ]


@app.post("/api/calculate")
def calculate(request: CalculateRequest, db: Session = Depends(get_db)):
    """
    Calculate Scope 1 & 2 GHG emissions from a list of activity data.
    Persists the result to SQLite and returns the full calculation detail.
    """
    try:
        result = calculate_emissions(
            request.company_name, request.country, request.activities
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Upsert company
    company = db.query(Company).filter_by(name=request.company_name).first()
    if not company:
        company = Company(name=request.company_name, country=request.country)
        db.add(company)
        db.flush()

    # Persist emission record
    record = EmissionRecord(
        company_id=company.id,
        total_emissions=result["total_emissions"],
        scope1_emissions=result["scope1_emissions"],
        scope2_emissions=result["scope2_emissions"],
    )
    db.add(record)
    db.flush()

    for d in result["details"]:
        db.add(ActivityData(
            record_id=record.id,
            energy_type=d["energy_type"],
            consumption=d["consumption"],
            unit=d["unit"],
            emission_factor=d["emission_factor"],
            emissions=d["emissions"],
            scope=d["scope"],
        ))

    db.commit()
    return result


@app.post("/api/report")
def generate_report(request: CalculateRequest):
    """
    Calculate emissions and return a PDF report as a binary stream.
    """
    try:
        result = calculate_emissions(
            request.company_name, request.country, request.activities
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    pdf_bytes = generate_pdf_report(request.company_name, request.country, result)
    filename = (
        f"carbon_report_{request.company_name.replace(' ', '_')}"
        f"_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
