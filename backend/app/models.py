import datetime as dt

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="staff")  # staff | admin
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    meter_number = Column(String, unique=True, index=True, nullable=False)
    address = Column(String, nullable=False)
    ward = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    records = relationship("ConsumptionRecord", back_populates="household")
    alerts = relationship("Alert", back_populates="household")


class ConsumptionRecord(Base):
    __tablename__ = "consumption_records"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    month = Column(String, nullable=False)  # e.g. "2026-06"
    purchase_rand = Column(Float, nullable=False)
    consumption_kwh = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    household = relationship("Household", back_populates="records")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    alert_type = Column(String, nullable=False)  # "usage_risk" | "sensor_tamper"
    message = Column(String, nullable=False)
    severity = Column(String, default="medium")  # low | medium | high
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    household = relationship("Household", back_populates="alerts")