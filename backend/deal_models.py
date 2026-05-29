"""
UKMC Deal Origination System — Database Models
SQLAlchemy ORM models for deals, companies, contacts, intelligence signals
"""

import json
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from database import Base


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Company info
    company_name = Column(String(255), index=True, nullable=False)
    country = Column(String(100))
    sector = Column(String(100))
    company_description = Column(Text)

    # Financing details
    financing_type = Column(String(100))  # Dim Sum Bond, Project Finance, etc.
    estimated_size_mn = Column(Float)  # USD millions
    currency = Column(String(10), default="USD")
    purpose = Column(String(255))
    tenor = Column(String(50))
    urgency = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW

    # Pipeline stage
    stage = Column(String(30), default="DISCOVERY")
    # DISCOVERY → RESEARCH → ANALYSIS → OUTREACH → PROPOSAL → MANDATE → CLOSED → LOST

    # Scoring
    ukmc_fit_score = Column(Float, default=0)  # 0-100
    mandate_probability = Column(Float, default=0)  # 0-100

    # Analysis
    why_suitable = Column(Text)
    financing_angle = Column(Text)
    potential_lenders = Column(Text)
    chinese_counterparties = Column(Text)

    # Dim Sum Bond
    dim_sum_feasible = Column(Boolean, default=False)
    dim_sum_notes = Column(Text)
    dim_sum_size_mn = Column(Float)
    dim_sum_tenor = Column(String(50))
    dim_sum_investor_appeal = Column(Text)

    # Strategy
    entry_strategy = Column(Text)
    competitive_landscape = Column(Text)
    objections = Column(Text)
    political_considerations = Column(Text)
    next_action = Column(String(100))
    next_action_detail = Column(Text)

    # Source
    source = Column(String(50), default="manual")  # intelligence, manual, referral
    source_url = Column(String(500))
    intelligence_summary = Column(Text)

    # Flags
    is_active = Column(Boolean, default=True)
    priority = Column(String(20), default="NORMAL")  # HIGH, NORMAL, LOW
    china_linked = Column(Boolean, default=False)
    belt_road = Column(Boolean, default=False)

    # Relationships
    contacts = relationship("DealContact", back_populates="deal", cascade="all, delete-orphan")
    activities = relationship("DealActivity", back_populates="deal", cascade="all, delete-orphan")
    signals = relationship("IntelligenceSignal", back_populates="deal")


class TargetCompany(Base):
    __tablename__ = "target_companies"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    name = Column(String(255), unique=True, index=True)
    country = Column(String(100))
    sector = Column(String(100))
    subsector = Column(String(100))
    website = Column(String(255))
    description = Column(Text)
    revenue_mn = Column(Float)
    employees = Column(Integer)
    founded = Column(Integer)
    hq_address = Column(String(500))

    # Capital markets
    listed = Column(Boolean, default=False)
    exchange = Column(String(50))
    ticker = Column(String(20))
    market_cap_mn = Column(Float)
    credit_rating = Column(String(20))

    # Ownership
    parent_company = Column(String(255))
    shareholders = Column(Text)  # JSON string

    # China / BRI exposure
    chinese_exposure = Column(Boolean, default=False)
    belt_road_exposure = Column(Boolean, default=False)
    chinese_partners = Column(Text)
    rmb_exposure = Column(Boolean, default=False)

    # Signals
    financing_signals = Column(Text)  # JSON
    last_signal_date = Column(DateTime)

    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("target_companies.id"), nullable=True)

    name = Column(String(255), index=True)
    title = Column(String(255))
    role = Column(String(50))  # CEO, CFO, TREASURY_HEAD, PROJECT_DIRECTOR, BOARD
    email = Column(String(255))
    phone = Column(String(50))
    linkedin = Column(String(255))
    company_name = Column(String(255))  # denormalized for quick display
    country = Column(String(100))
    notes = Column(Text)
    is_decision_maker = Column(Boolean, default=False)
    is_gatekeeper = Column(Boolean, default=False)
    priority = Column(Boolean, default=False)

    company = relationship("TargetCompany", back_populates="contacts")


class DealContact(Base):
    """Junction for deal <-> contacts (a contact can be on multiple deals)"""
    __tablename__ = "deal_contacts"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Inline contact details (when not linked to a Contact record)
    name = Column(String(255))
    title = Column(String(255))
    role = Column(String(50))
    email = Column(String(255))
    phone = Column(String(50))
    linkedin = Column(String(255))
    notes = Column(Text)

    deal = relationship("Deal", back_populates="contacts")


class IntelligenceSignal(Base):
    __tablename__ = "intelligence_signals"

    id = Column(Integer, primary_key=True, index=True)
    detected_at = Column(DateTime, default=datetime.utcnow)

    signal_type = Column(String(50))
    # EXPANSION, REFINANCING, CAPEX, ACQUISITION, IPO, M_A, DISTRESS,
    # SPECTRUM, INFRASTRUCTURE, SMELTER, DATA_CENTER, RENEWABLE, BOND_MATURITY

    company_name = Column(String(255), index=True)
    country = Column(String(100))
    sector = Column(String(100))
    headline = Column(String(500))
    summary = Column(Text)
    source_url = Column(String(500))
    source_name = Column(String(100))

    urgency = Column(String(20), default="MEDIUM")
    financing_implied_mn = Column(Float)

    # Action taken
    deal_created = Column(Boolean, default=False)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=True)
    reviewed = Column(Boolean, default=False)

    deal = relationship("Deal", back_populates="signals")


class DealActivity(Base):
    __tablename__ = "deal_activities"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    activity_type = Column(String(50))
    # STAGE_CHANGE, NOTE, EMAIL_SENT, MEETING, ANALYSIS_RUN, CONTACT_ADDED, SIGNAL_LINKED
    description = Column(Text)
    user = Column(String(100), default="System")
    metadata_ = Column("metadata", Text)  # JSON

    deal = relationship("Deal", back_populates="activities")
