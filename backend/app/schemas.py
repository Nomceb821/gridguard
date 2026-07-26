import datetime as dt

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HouseholdCreate(BaseModel):
    meter_number: str
    address: str
    ward: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class HouseholdOut(HouseholdCreate):
    id: int

    class Config:
        from_attributes = True


class ConsumptionCreate(BaseModel):
    month: str
    purchase_rand: float
    consumption_kwh: float


class ConsumptionOut(ConsumptionCreate):
    id: int
    household_id: int
    risk_score: float | None = None
    created_at: dt.datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    household_id: int
    alert_type: str
    message: str
    severity: str
    resolved: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


class RiskResult(BaseModel):
    household_id: int
    risk_score: float
    flagged: bool