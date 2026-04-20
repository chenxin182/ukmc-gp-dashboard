from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    country = Column(String, default="Singapore")
    created_at = Column(DateTime, default=datetime.utcnow)

    records = relationship("EmissionRecord", back_populates="company")


class EmissionRecord(Base):
    __tablename__ = "emission_records"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    total_emissions = Column(Float, nullable=False)
    scope1_emissions = Column(Float, nullable=False)
    scope2_emissions = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="records")
    activities = relationship("ActivityData", back_populates="record")


class ActivityData(Base):
    __tablename__ = "activity_data"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("emission_records.id"), nullable=False)
    energy_type = Column(String, nullable=False)
    consumption = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    emission_factor = Column(Float, nullable=False)
    emissions = Column(Float, nullable=False)
    scope = Column(Integer, nullable=False)

    record = relationship("EmissionRecord", back_populates="activities")
