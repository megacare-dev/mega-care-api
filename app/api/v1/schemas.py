# Location: app/api/v1/schemas.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Dict, List

# --- Base Schemas for Maps ---
class ComplianceMap(BaseModel):
    status: Optional[str] = None
    usage_percent: Optional[float] = None
    model_config = ConfigDict(populate_by_name=True)

class OrganisationMap(BaseModel):
    name: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

class ClinicalUserMap(BaseModel):
    name: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

class DataAccessMap(BaseModel):
    type: Optional[str] = None
    duration: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

class LeakMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = Field(None, alias="95th_percentile")
    model_config = ConfigDict(populate_by_name=True)

class PressureMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = Field(None, alias="95th_percentile")
    model_config = ConfigDict(populate_by_name=True)

class EventsPerHourMap(BaseModel):
    ahi: Optional[float] = None
    central_apneas: Optional[float] = None
    hypopneas: Optional[float] = None
    model_config = ConfigDict(populate_by_name=True)

# --- LINE Schemas ---
class LineUserProfile(BaseModel):
    user_id: str = Field(..., alias="userId")
    display_name: Optional[str] = Field(None, alias="displayName")
    picture_url: Optional[str] = Field(None, alias="pictureUrl")
    status_message: Optional[str] = Field(None, alias="statusMessage")
    email: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    line_id: Optional[str] = Field(None, alias="lineId")
    firebase_uid: Optional[str] = Field(None, alias="firebaseUid", description="The user's unique Firebase UID, linked after onboarding.")
    display_name: str = Field(..., alias="displayName")
    title: Optional[str] = None
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    dob: Optional[date] = None
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    location: Optional[str] = None
    status: str = "Active"
    air_view_number: Optional[str] = Field(None, alias="airViewNumber")
    monitoring_type: Optional[str] = Field(None, alias="monitoringType")
    available_data: Optional[str] = Field(None, alias="availableData")
    dealer_patient_id: Optional[str] = Field(None, alias="dealerPatientId")
    line_profile: Optional[LineUserProfile] = Field(None, alias="lineProfile")
    model_config = ConfigDict(populate_by_name=True)

class CustomerProfilePayload(BaseModel):
    """Payload for creating or updating a customer profile with optional fields."""
    line_id: Optional[str] = Field(None, alias="lineId")
    display_name: Optional[str] = Field(None, alias="displayName")
    title: Optional[str] = None
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    dob: Optional[date] = None
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    location: Optional[str] = None
    status: Optional[str] = None
    air_view_number: Optional[str] = Field(None, alias="airViewNumber")
    monitoring_type: Optional[str] = Field(None, alias="monitoringType")
    available_data: Optional[str] = Field(None, alias="availableData")
    dealer_patient_id: Optional[str] = Field(None, alias="dealerPatientId")
    line_profile: Optional[LineUserProfile] = Field(None, alias="lineProfile")
    model_config = ConfigDict(populate_by_name=True)

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    patient_id: str = Field(..., alias="patientId")
    setup_date: datetime = Field(..., alias="setupDate")
    organisation: Optional[OrganisationMap] = None
    clinical_user: Optional[ClinicalUserMap] = Field(None, alias="clinicalUser")
    compliance: Optional[ComplianceMap] = None
    data_access: Optional[DataAccessMap] = Field(None, alias="dataAccess")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Equipment Schemas ---
class DeviceBase(BaseModel):
    device_name: str = Field(..., alias="deviceName")
    serial_number: str = Field(..., alias="serialNumber")
    device_number: str = Field(..., alias="deviceNumber", min_length=3, max_length=3, description="The device's unique 3-digit device number (DN).")
    status: str = "Active"
    settings: Optional[Dict] = None
    model_config = ConfigDict(populate_by_name=True)

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    device_id: str = Field(..., alias="deviceId")
    added_date: datetime = Field(..., alias="addedDate")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class DeviceLinkRequest(BaseModel):
    serial_number: str = Field(..., alias="serialNumber", description="The device's unique serial number (SN).")
    device_number: str = Field(..., alias="deviceNumber", min_length=3, max_length=3, description="The device's unique 3-digit device number (DN).")
    model_config = ConfigDict(populate_by_name=True)

class MaskBase(BaseModel):
    mask_name: str = Field(..., alias="maskName")
    size: str
    model_config = ConfigDict(populate_by_name=True)

class MaskCreate(MaskBase):
    pass

class Mask(MaskBase):
    mask_id: str = Field(..., alias="maskId")
    added_date: datetime = Field(..., alias="addedDate")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class AirTubingBase(BaseModel):
    tubing_name: str = Field(..., alias="tubingName")
    model_config = ConfigDict(populate_by_name=True)

class AirTubingCreate(AirTubingBase):
    pass

class AirTubing(AirTubingBase):
    tubing_id: str = Field(..., alias="tubingId")
    added_date: datetime = Field(..., alias="addedDate")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Report Schemas ---
class DailyReportBase(BaseModel):
    report_date: date = Field(..., alias="reportDate")
    usage_hours: float = Field(..., alias="usageHours")
    cheyne_stokes_respiration: Optional[str] = Field(None, alias="cheyneStokesRespiration")
    rera: Optional[float] = None
    leak: LeakMap
    pressure: PressureMap
    events_per_hour: EventsPerHourMap = Field(..., alias="eventsPerHour")
    device_snapshot: Optional[Dict] = Field(None, alias="deviceSnapshot")
    model_config = ConfigDict(populate_by_name=True)

class DailyReportCreate(DailyReportBase):
    pass

class DailyReport(DailyReportBase):
    report_id: str = Field(..., alias="reportId") # Will be the YYYY-MM-DD date string
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)