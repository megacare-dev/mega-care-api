MegaCare Connect API Specification
This document provides the complete functional and technical specifications for the backend API of the MegaCare Connect application.

1. Functional Specification
This section describes what the API does from a business and user perspective.

1.1. Actors
Patient: The primary user of the mobile app. They can manage their own profile, equipment, and view their therapy data.

Clinician: A healthcare provider who monitors one or more assigned patients. They can view patient profiles and their therapy data.

System: An automated process that might submit data (e.g., from a data processing pipeline that analyzes CPAP SD cards).

1.2. Core Features & User Stories
User Onboarding: A new patient can register and create their profile immediately after signing up with Firebase Authentication.

Profile Management: A patient can view and update their personal information (e.g., display name, date of birth).

Equipment Management: A patient can add and view the history of their CPAP devices, masks, and tubing to keep their profile current.

Data Reporting: A patient or an external system can submit a daily therapy report containing key metrics like usage hours, AHI, and leak data.

Data Retrieval (Patient): A patient can retrieve their historical therapy reports and compliance data to track their progress over time.

Data Retrieval (Clinician): A clinician can retrieve a list of their assigned patients and view the complete profile and report history for any of them to provide effective care.

1.3. Data Entities
Customer: Represents a single patient, containing their profile information.

Device: Represents a CPAP device assigned to a patient.

Mask: Represents a mask used by a patient.

AirTubing: Represents air tubing used by a patient.

DailyReport: A record of a single day's therapy session, containing usage, AHI, leak data, etc.

2. Technical Specification (API Reference)
This section describes how the API is built and provides the detailed contract for each endpoint.

2.1. General Information
Base URL: Your Cloud Run service URL. Example: https://megacare-connect-backend-xxxxxxxx-as.a.run.app/api/v1

API Version: The API is versioned with /v1 in the URL path.

Authentication: All endpoints require an Authorization header with a Firebase Auth ID Token. The backend will verify this token for every request to identify and authenticate the user.

Format: Authorization: Bearer <Firebase_ID_Token>

2.2. Pydantic Schemas
These schemas define the data structures for API requests and responses. They will be used by FastAPI for automatic data validation and serialization.

# Location: app/api/v1/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

# --- Base Schemas for Maps ---
class ComplianceMap(BaseModel):
    status: Optional[str] = None
    usage_percent: Optional[float] = None

class LeakMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = None

class PressureMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = None

class EventsPerHourMap(BaseModel):
    ahi: Optional[float] = None
    central_apneas: Optional[float] = None
    hypopneas: Optional[float] = None
    # ... other event types

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    lineId: Optional[str] = None
    displayName: str
    firstName: str
    lastName: str
    dob: date
    status: str = "Active"

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: str = Field(..., alias="patientId")
    setupDate: datetime
    compliance: Optional[ComplianceMap] = None

# --- Equipment Schemas ---
class DeviceBase(BaseModel):
    deviceName: str
    serialNumber: str
    status: str = "Active"

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: str = Field(..., alias="deviceId")
    addedDate: datetime

# --- Report Schemas ---
class DailyReportBase(BaseModel):
    reportDate: date
    usageHours: float
    leak: LeakMap
    pressure: PressureMap
    eventsPerHour: EventsPerHourMap

class DailyReportCreate(DailyReportBase):
    pass

class DailyReport(DailyReportBase):
    id: str = Field(..., alias="reportId") # Will be the YYYY-MM-DD date string

2.3. API Endpoints
Customer Endpoints
Create Customer Profile

Description: Creates a new customer profile. This should be called once after a user signs up. The Firestore document ID will be the user's Firebase UID.

Endpoint: POST /customers/me

Request Body: CustomerCreate

Response (201 Created): Customer

Get My Profile

Description: Retrieves the profile of the currently authenticated user (patient or clinician).

Endpoint: GET /customers/me

Response (200 OK): Customer

Equipment Endpoints
Add a Device

Description: Adds a new device to the authenticated patient's profile.

Endpoint: POST /customers/me/devices

Request Body: DeviceCreate

Response (201 Created): Device

Get My Devices

Description: Retrieves a list of all devices for the authenticated patient.

Endpoint: GET /customers/me/devices

Response (200 OK): list[Device]

(Similar endpoints can be created for masks and airTubing)

Report Endpoints
Submit Daily Report

Description: Submits a daily therapy report for the authenticated patient. The Firestore document ID will be the report date in YYYY-MM-DD format.

Endpoint: POST /customers/me/dailyReports

Request Body: DailyReportCreate

Response (201 Created): DailyReport

Get My Daily Reports

Description: Retrieves a list of recent daily reports for the authenticated patient, ordered by most recent.

Endpoint: GET /customers/me/dailyReports

Query Parameters: limit: int = 30

Response (200 OK): list[DailyReport]

Clinician Endpoints
Get Assigned Patients

Description: Retrieves a list of summary profiles for all patients assigned to the authenticated clinician. (Requires the clinician's Firestore document to have an assignedPatients array of patient UIDs).

Endpoint: GET /clinician/patients

Response (200 OK): list[Customer]

Get Patient's Daily Reports

Description: Retrieves recent daily reports for a specific patient assigned to the clinician. The API must verify that the clinician is authorized to view this patient's data.

Endpoint: GET /clinician/patients/{patientId}/dailyReports

Path Parameter: patientId: str (The Firebase UID of the patient)

Query Parameters: limit: int = 30

Response (200 OK): list[DailyReport]