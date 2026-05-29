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
from database import engine, get_db, SessionLocal
from models import ActivityData, Base as EsgBase, Company, EmissionRecord
from deal_models import Base as DealBase
from deal_routes import router as deal_router
from report_generator import generate_pdf_report

# Initialise all DB tables on startup
EsgBase.metadata.create_all(bind=engine)
DealBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="UKMC International — Deal Origination & ESG Platform",
    description="AI-powered deal origination, pipeline management, and ESG carbon reporting.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register origination router
app.include_router(deal_router)


# ── Auto-seed on first launch ─────────────────────────────────────────────────

def _needs_seed(db: Session) -> bool:
    from deal_models import Deal
    return db.query(Deal).count() == 0


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        if _needs_seed(db):
            from seed_data import seed_all
            seed_all(db)
    finally:
        db.close()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ActivityInput(BaseModel):
    energy_type: str
    consumption: float
    unit: str = ""


class CalculateRequest(BaseModel):
    company_name: str
    country: str = "Singapore"
    activities: List[ActivityInput]


# ── ESG Routes ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "UKMC International — Deal Origination & ESG Platform",
        "docs": "/docs",
        "version": "2.0.0",
        "modules": ["deal-origination", "esg-carbon"],
    }


@app.get("/api/factors")
def list_factors():
    return get_factors()


@app.get("/api/esg/companies")
def list_esg_companies(db: Session = Depends(get_db)):
    rows = db.query(Company).order_by(Company.created_at.desc()).all()
    return [
        {"id": c.id, "name": c.name, "country": c.country, "created_at": c.created_at}
        for c in rows
    ]


@app.post("/api/calculate")
def calculate(request: CalculateRequest, db: Session = Depends(get_db)):
    try:
        result = calculate_emissions(request.company_name, request.country, request.activities)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    company = db.query(Company).filter_by(name=request.company_name).first()
    if not company:
        company = Company(name=request.company_name, country=request.country)
        db.add(company)
        db.flush()

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
    try:
        result = calculate_emissions(request.company_name, request.country, request.activities)
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
