MegaCare Connect API Specification

*   **Project name**: mega-care-dev
*   **Project number**: 15106852528
*   **Project ID**: mega-care-dev
*   **Github Repo**: https://github.com/megacare-dev/mega-care-api
This document provides the complete functional and technical specifications for the backend API of the MegaCare Connect application.

1. Functional Specification
This section describes what the API does from a business and user perspective.

1.1. Actors
Patient: The primary user of the LINE LIFF application. They can manage their own profile, equipment, and view their therapy data.

Clinician: A healthcare provider who monitors one or more assigned patients. They can view patient profiles and their therapy data.

System: An automated process that submits data from external sources like ResMed AirView or a data processing pipeline that analyzes CPAP SD cards.

1.2. Core Features & User Stories
User Onboarding: A new patient registers by providing their CPAP device's serial number. The system uses this serial number to find their pre-existing profile in the database and links it to their new app account.

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
from typing import Optional, Dict

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
    percentile_95th: Optional[float] = None

class PressureMap(BaseModel):
    median: Optional[float] = None
    percentile_95th: Optional[float] = None

class EventsPerHourMap(BaseModel):
    ahi: Optional[float] = None
    central_apneas: Optional[float] = None
    hypopneas: Optional[float] = None
    # ... other event types

# --- LINE Schemas ---
class LineProfile(BaseModel):
    user_id: str = Field(..., alias="userId")
    display_name: str = Field(..., alias="displayName")
    picture_url: Optional[str] = Field(None, alias="pictureUrl")

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    line_id: Optional[str] = Field(None, alias="lineId")
    display_name: str = Field(..., alias="displayName")
    title: Optional[str] = None
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    dob: date
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    location: Optional[str] = None
    status: str = "Active"
    air_view_number: Optional[str] = Field(None, alias="airViewNumber")
    monitoring_type: Optional[str] = Field(None, alias="monitoringType")
    available_data: Optional[str] = Field(None, alias="availableData")
    dealer_patient_id: Optional[str] = Field(None, alias="dealerPatientId")
    line_profile: Optional[LineProfile] = Field(None, alias="lineProfile")

    class Config:
        populate_by_name = True # Allows creating model with both alias and field name
        allow_population_by_field_name = True

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    patient_id: str = Field(..., alias="patientId")
    setup_date: datetime = Field(..., alias="setupDate")
    organisation: Optional[OrganisationMap] = None
    clinical_user: Optional[ClinicalUserMap] = Field(None, alias="clinicalUser")
    compliance: Optional[ComplianceMap] = None
    data_access: Optional[DataAccessMap] = Field(None, alias="dataAccess")

# --- Equipment Schemas ---
class DeviceBase(BaseModel):
    device_name: str = Field(..., alias="deviceName")
    serial_number: str = Field(..., alias="serialNumber")
    status: str = "Active"
    settings: Optional[Dict] = None

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    device_id: str = Field(..., alias="deviceId")
    added_date: datetime = Field(..., alias="addedDate")

class MaskBase(BaseModel):
    mask_name: str = Field(..., alias="maskName")
    size: str

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class MaskCreate(MaskBase):
    pass

class Mask(MaskBase):
    mask_id: str = Field(..., alias="maskId")
    added_date: datetime = Field(..., alias="addedDate")

class AirTubingBase(BaseModel):
    tubing_name: str = Field(..., alias="tubingName")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class AirTubingCreate(AirTubingBase):
    pass

class AirTubing(AirTubingBase):
    tubing_id: str = Field(..., alias="tubingId")
    added_date: datetime = Field(..., alias="addedDate")

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

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class DailyReportCreate(DailyReportBase):
    pass

class DailyReport(DailyReportBase):
    report_id: str = Field(..., alias="reportId") # Will be the YYYY-MM-DD date string

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


## Data Hierarchy

The database is designed with the following main collections and sub-collections:

*   **`patient_list/{patientId}`**
    *   `details/{detailId}`
    *   `prescriptions/{prescriptionId}`
*   **`devices/{deviceId}`**

---

## 1. Root Collections

### 1.1. `patient_list`

This is the main collection where each document represents a single patient, primarily containing summary data from the AirView patient list for quick filtering and display.

-   **Collection:** `patient_list`
-   **Document ID:** `airview_patient_id` (A unique ID from the AirView system)

#### Fields

| Field                   | Type        | Description                                                                        |
| ----------------------- | ----------- | ---------------------------------------------------------------------------------- |
| `airviewId`             | `string`    | The patient's ID in the AirView system (same as the document ID).                    |
| `name`                  | `string`    | The patient's name as displayed in AirView.                                        |
| `location`              | `string`    | The branch or location the patient belongs to (denormalized for filtering).        |
| `monitoringType`        | `string`    | The type of data monitoring (e.g., "Wireless monitoring", or `null`).              |
| `note`                  | `string`    | Additional notes (or `null`).                                                      |
| `availableData`         | `string`    | The duration of available data history (e.g., "6 months").                         |
| `isCompliant`           | `boolean`   | `true` if the patient has met compliance criteria.                                 |
| `last30DaysCompliance`  | `number`    | The compliance percentage over the last 30 days.                                   |
| `lastUpdatedSourceText` | `string`    | The text indicating the last update from AirView (e.g., "Yesterday").              |
| `shouldExtract`         | `boolean`   | `true` if this patient's detailed data should be extracted in the next sync cycle. |
| `lastUpdated`           | `timestamp` | The server timestamp of when this record was last synced by our system.            |

### 1.2. `devices`

This collection tracks individual CPAP devices to manage their link status with patients and prevent duplicate linking.

-   **Collection:** `devices`
-   **Document ID:** `auto_generated_uuid`

#### Fields

| Field          | Type        | Description                                                              |
| -------------- | ----------- | ------------------------------------------------------------------------ |
| `serialNumber` | `string`    | The unique serial number of the device (an index should be created).     |
| `patientId`    | `string`    | The `airview_patient_id` of the patient this device is linked to.        |
| `status`       | `string`    | The current status of the device (e.g., "linked", "unlinked").           |
| `linkedAt`     | `timestamp` | The timestamp when the device was last linked to a patient.              |
| `unlinkedAt`   | `timestamp` | The timestamp when the device was unlinked (if applicable).              |
| `createdAt`    | `timestamp` | The timestamp when this device record was first created in our system.   |
| `updatedAt`    | `timestamp` | The timestamp of the last update to this record.                         |

---

## 2. Sub-collections

Each `patient_list` document can contain the following sub-collections:

### 2.1. `details`

Stores the comprehensive details for a patient, typically scraped from the patient's detail page in AirView. There is usually only one document per patient in this sub-collection.

-   **Path:** `patient_list/{patientId}/details/{detailId}`

#### Fields

| Field              | Type | Description                                             |
| ------------------ | ---- | ------------------------------------------------------- |
| `personalInfo`     | `map`| A map containing the patient's personal information.    |
| `airviewInfo`      | `map`| A map containing data related to the AirView system.    |
| `organizationInfo` | `map`| A map containing information about the caring organization. |
| `system`           | `map`| A map containing system-generated metadata.             |

### 2.2. `prescriptions`

Stores a history of prescriptions and device settings for the patient.

-   **Path:** `patient_list/{patientId}/prescriptions/{prescriptionId}`

#### Fields

| Field        | Type | Description                                                              |
| ------------ | ---- | ------------------------------------------------------------------------ |
| `patientId`  | `string` | The patient's UUID (denormalized for client-side convenience).         |
| `device`     | `map`| A map containing information about the prescribed device.              |
| `settings`   | `map`| A map containing the therapy settings.                                 |
| `climate`    | `map`| A map containing climate control settings.                             |
| `monitoring` | `map`| A map containing data access and monitoring settings.                  |
| `mask`       | `map`| A map containing information about the mask for this prescription.     |
| `airTubing`  | `map`| A map containing information about the air tubing for this prescription. |
| `system`     | `map`| A map containing system-generated metadata.                            |

---

## 3. Firebase Authentication (`users`)

User management for the Admin Portal is handled by Firebase Authentication. A `users` collection in Firestore is not required unless additional user-specific data, such as roles (`admin`, `viewer`), needs to be stored. The user's Firebase UID serves as the unique identifier.

---
## 4. Deprecated Collections

The following collections are deprecated and their data models have been moved into the structure described above:

*   **`customers`**: Replaced by `patient_list`.
*   **`patient_details`**: Replaced by the `details` sub-collection under `patient_list`.
*   **`prescriptions`**: Replaced by the `prescriptions` sub-collection under `patient_list`.