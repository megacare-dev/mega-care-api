# Location: app/api/v1/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Dict, List

# --- Base Schemas for Maps ---
class ComplianceMap(BaseModel):
    status: Optional[str] = None
    usage_percent: Optional[float] = None

class OrganisationMap(BaseModel):
    name: Optional[str] = None

class ClinicalUserMap(BaseModel):
    name: Optional[str] = None

class DataAccessMap(BaseModel):
    type: Optional[str] = None
    duration: Optional[str] = None

class LeakMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = Field(None, alias="95th_percentile")

class PressureMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = Field(None, alias="95th_percentile")

class EventsPerHourMap(BaseModel):
    ahi: Optional[float] = None
    central_apneas: Optional[float] = None
    hypopneas: Optional[float] = None
    # ... other event types

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    lineId: Optional[str] = None
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

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: str = Field(..., alias="patientId")
    setupDate: datetime
    organisation: Optional[OrganisationMap] = None
    clinicalUser: Optional[ClinicalUserMap] = None
    compliance: Optional[ComplianceMap] = None
    dataAccess: Optional[DataAccessMap] = None

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

# --- Equipment Schemas ---
class DeviceBase(BaseModel):
    deviceName: str
    serialNumber: str
    status: str = "Active"
    settings: Optional[Dict] = None

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: str = Field(..., alias="deviceId")
    addedDate: datetime
    
    class Config:
        allow_population_by_field_name = True
        orm_mode = True

class MaskBase(BaseModel):
    maskName: str
    size: str

class MaskCreate(MaskBase):
    pass

class Mask(MaskBase):
    id: str = Field(..., alias="maskId")
    addedDate: datetime

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

class AirTubingBase(BaseModel):
    tubingName: str

class AirTubingCreate(AirTubingBase):
    pass

class AirTubing(AirTubingBase):
    id: str = Field(..., alias="tubingId")
    addedDate: datetime

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

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

class DailyReportCreate(DailyReportBase):
    pass

class DailyReport(DailyReportBase):
    id: str = Field(..., alias="reportId") # Will be the YYYY-MM-DD date string

    class Config:
        allow_population_by_field_name = True
        orm_mode = True