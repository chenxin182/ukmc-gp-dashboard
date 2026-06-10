from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "dr_companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    github_org = Column(String(255))
    twitter_handle = Column(String(255))
    linkedin_url = Column(String(500))
    description = Column(Text)
    stage = Column(String(50))   # seed / series_a / growth
    sector = Column(String(100))
    greenhouse_token = Column(String(255))
    lever_slug = Column(String(255))
    founder_twitter = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    signals = relationship("Signal", back_populates="company", cascade="all, delete-orphan")
    inferences = relationship("Inference", back_populates="company", cascade="all, delete-orphan")
    funding_events = relationship("FundingEvent", back_populates="company")


class Signal(Base):
    __tablename__ = "dr_signals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dr_companies.id"), nullable=False)
    signal_type = Column(String(100), nullable=False)
    # signal_type enum:
    #   hire_finance_ir | hire_infra_burst | github_commit_spike
    #   pr_activity_surge | founder_vc_interact | news | website_update
    #   team_expansion
    source_url = Column(String(500))
    raw_data = Column(JSON)
    captured_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="signals")


class Inference(Base):
    __tablename__ = "dr_inferences"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dr_companies.id"), nullable=False)
    event_type = Column(String(100))  # seed | series_a | acquisition | pivot
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text)
    triggered_signals = Column(JSON)  # list of signal IDs
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="inferences")
    feedback = relationship("Feedback", back_populates="inference", cascade="all, delete-orphan")


class FundingEvent(Base):
    """Historical ground-truth funding events used for backtesting."""
    __tablename__ = "dr_funding_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dr_companies.id"), nullable=True)
    company_name = Column(String(255), nullable=False)
    round_type = Column(String(50))  # seed | series_a | series_b | acquisition
    amount_usd = Column(Float)
    announced_date = Column(DateTime)
    source_url = Column(String(500))
    verified = Column(Boolean, default=True)
    pre_signals_14d = Column(JSON)   # signals observed 14 days before announcement
    pre_signals_30d = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="funding_events")


class Feedback(Base):
    """Human-labelled outcome for an Inference (confirmed / false_positive / pending)."""
    __tablename__ = "dr_feedback"

    id = Column(Integer, primary_key=True, index=True)
    inference_id = Column(Integer, ForeignKey("dr_inferences.id"), nullable=False)
    outcome = Column(String(50), nullable=False)  # confirmed | false_positive | pending
    notes = Column(Text)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    inference = relationship("Inference", back_populates="feedback")
