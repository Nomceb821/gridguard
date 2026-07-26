from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.ml_model import predict_risk
from app.models import Alert, ConsumptionRecord, Household
from app.schemas import (
    ConsumptionCreate,
    ConsumptionOut,
    HouseholdCreate,
    HouseholdOut,
    RiskResult,
)
from app.alerts_service import dispatch_alert

router = APIRouter(prefix="/households", tags=["households"], dependencies=[Depends(get_current_user)])

RISK_THRESHOLD = 0.6


@router.post("", response_model=HouseholdOut)
def create_household(payload: HouseholdCreate, db: Session = Depends(get_db)):
    existing = db.query(Household).filter(Household.meter_number == payload.meter_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Meter number already exists")
    household = Household(**payload.model_dump())
    db.add(household)
    db.commit()
    db.refresh(household)
    return household


@router.get("", response_model=list[HouseholdOut])
def list_households(db: Session = Depends(get_db)):
    return db.query(Household).all()


@router.get("/{household_id}", response_model=HouseholdOut)
def get_household(household_id: int, db: Session = Depends(get_db)):
    household = db.query(Household).get(household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    return household


@router.post("/{household_id}/consumption", response_model=ConsumptionOut)
def add_consumption(household_id: int, payload: ConsumptionCreate, db: Session = Depends(get_db)):
    household = db.query(Household).get(household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    ratio = payload.purchase_rand / max(payload.consumption_kwh, 1)
    features = {
        "purchase_rand": payload.purchase_rand,
        "consumption_kwh": payload.consumption_kwh,
        "ratio": ratio,
        "consumption_3m_avg": payload.consumption_kwh,
        "purchase_3m_avg": payload.purchase_rand,
        "consumption_trend": 0,
        "ratio_trend": 0,
    }
    risk_score = predict_risk(features)

    record = ConsumptionRecord(
        household_id=household_id,
        month=payload.month,
        purchase_rand=payload.purchase_rand,
        consumption_kwh=payload.consumption_kwh,
        risk_score=risk_score,
    )
    db.add(record)

    if risk_score >= RISK_THRESHOLD:
        message = (
            f"Household {household.meter_number} ({household.address}) shows a "
            f"purchase-to-consumption pattern consistent with illegal connection "
            f"(risk score {risk_score:.2f})."
        )
        alert = Alert(household_id=household_id, alert_type="usage_risk", message=message, severity="high")
        db.add(alert)
        db.commit()
        dispatch_alert(subject="GridGuard: high-risk usage pattern", body=message)
    else:
        db.commit()

    db.refresh(record)
    return record


@router.get("/{household_id}/consumption", response_model=list[ConsumptionOut])
def list_consumption(household_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ConsumptionRecord)
        .filter(ConsumptionRecord.household_id == household_id)
        .order_by(ConsumptionRecord.month)
        .all()
    )


@router.get("/{household_id}/risk", response_model=RiskResult)
def get_latest_risk(household_id: int, db: Session = Depends(get_db)):
    record = (
        db.query(ConsumptionRecord)
        .filter(ConsumptionRecord.household_id == household_id)
        .order_by(ConsumptionRecord.created_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No consumption records for this household")
    return RiskResult(
        household_id=household_id,
        risk_score=record.risk_score or 0,
        flagged=(record.risk_score or 0) >= RISK_THRESHOLD,
    )