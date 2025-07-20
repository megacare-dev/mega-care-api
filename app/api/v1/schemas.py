# Location: app/api/v1/schemas.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Dict, List
import re

def to_snake_case(name: str) -> str:
    """Converts a camelCase string to snake_case."""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

# --- Base Schemas for Maps ---
class ComplianceMap(BaseModel):
    status: Optional[str] = None
    usage_percent: Optional[float] = None
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class OrganisationMap(BaseModel):
    name: Optional[str] = None
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class ClinicalUserMap(BaseModel):
    name: Optional[str] = None
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class DataAccessMap(BaseModel):
    type: Optional[str] = None
    duration: Optional[str] = None
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class LeakMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = Field(None, alias="95th_percentile")
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class PressureMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = Field(None, alias="95th_percentile")
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class EventsPerHourMap(BaseModel):
    ahi: Optional[float] = None
    central_apneas: Optional[float] = None
    hypopneas: Optional[float] = None
    # ... other event types
    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    lineId: Optional[str] = None
    firebaseUid: Optional[str] = Field(None, description="The user's unique Firebase UID, linked after onboarding.")
    displayName: str
    title: Optional[str] = None
    firstName: str
    lastName: str
    dob: date
    location: Optional[str] = None
    status: str = "Active"
    airViewNumber: Optional[str] = None
    monitoringType: Optional[str] = None
    availableData: Optional[str] = None
    dealerPatientId: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True
    )

class CustomerProfilePayload(BaseModel):
    """Payload for creating or updating a customer profile with optional fields."""
    lineId: Optional[str] = None
    displayName: Optional[str] = None
    title: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    dob: Optional[date] = None
    location: Optional[str] = None
    status: Optional[str] = None
    airViewNumber: Optional[str] = None
    monitoringType: Optional[str] = None
    availableData: Optional[str] = None
    dealerPatientId: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True
    )

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    patientId: str
    setupDate: datetime
    organisation: Optional[OrganisationMap] = None
    clinicalUser: Optional[ClinicalUserMap] = None
    compliance: Optional[ComplianceMap] = None
    dataAccess: Optional[DataAccessMap] = None

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True,
        from_attributes=True
    )

# --- Equipment Schemas ---
class DeviceBase(BaseModel):
    deviceName: str
    serialNumber: str
    status: str = "Active"
    settings: Optional[Dict] = None

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True
    )

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    deviceId: str
    addedDate: datetime
    
    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True,
        from_attributes=True
    )

class DeviceLinkRequest(BaseModel):
    serialNumber: str = Field(..., description="The device's unique serial number (SN).")
    deviceNumber: str = Field(..., description="The device's unique device number (DN).")

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True
    )


class MaskBase(BaseModel):
    maskName: str
    size: str

    model_config = ConfigDict(alias_generator=to_snake_case, populate_by_name=True)

class MaskCreate(MaskBase):
    pass

class Mask(MaskBase):
    maskId: str
    addedDate: datetime

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True,
        from_attributes=True
    )

class AirTubingBase(BaseModel):
    tubingName: str

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True
    )

class AirTubingCreate(AirTubingBase):
    pass

class AirTubing(AirTubingBase):
    tubingId: str
    addedDate: datetime

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True,
        from_attributes=True
    )

# --- Report Schemas ---
class DailyReportBase(BaseModel):
    reportDate: date
    usageHours: float
    cheyneStokesRespiration: Optional[str] = None
    rera: Optional[float] = None
    leak: LeakMap
    pressure: PressureMap
    eventsPerHour: EventsPerHourMap
    deviceSnapshot: Optional[Dict] = None

    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True
    )

class DailyReportCreate(DailyReportBase):
    pass

class DailyReport(DailyReportBase):
    reportId: str # Will be the YYYY-MM-DD date string
    
    model_config = ConfigDict(
        alias_generator=to_snake_case,
        populate_by_name=True,
        from_attributes=True
    )