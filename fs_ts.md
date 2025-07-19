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

class MaskBase(BaseModel):
    maskName: str
    size: str

class MaskCreate(MaskBase):
    pass

class Mask(MaskBase):
    id: str = Field(..., alias="maskId")
    addedDate: datetime

class AirTubingBase(BaseModel):
    tubingName: str

class AirTubingCreate(AirTubingBase):
    pass

class AirTubing(AirTubingBase):
    id: str = Field(..., alias="tubingId")
    addedDate: datetime

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

The database follows a hierarchical model with a main root collection and several nested sub-collections.

customers/{patientId}├── devices/{deviceId}├── masks/{maskId}├── airTubing/{tubingId}└── dailyReports/{reportDate}
---

## 1. Root Collection: `customers`

This is the main collection where each document represents a single patient. The document ID is the unique `patientId`.

-   **Collection:** `customers`
-   **Document ID:** `patient_id` (e.g., `ee319d58-9aeb-4af7-b156-f91540689595`)

### Fields

| Field               | Type        | Description                                       |
| ------------------- | ----------- | ------------------------------------------------- |
| `lineId`            | `string`    | The customer's LINE ID.                           |
| `displayName`       | `string`    | The customer's display name.                      |
| `title`             | `string`    | The customer's title (e.g., Mr, Mrs).             |
| `firstName`         | `string`    | The customer's first name.                        |
| `lastName`          | `string`    | The customer's last name.                         |
| `dob`               | `timestamp` | The customer's date of birth.                     |
| `location`          | `string`    | The customer's location or company.               |
| `status`            | `string`    | The customer's status (e.g., "Active").           |
| `setupDate`         | `timestamp` | The date the customer was set up.                 |
| `airViewNumber`     | `string`    | The customer's AirView number.                    |
| `monitoringType`    | `string`    | The type of monitoring (e.g., "Wireless").        |
| `availableData`     | `string`    | The duration of available data history.           |
| `dealerPatientId`   | `string`    | The patient ID from the dealer.                   |
| `organisation`      | `map`       | A map containing the organisation's name.         |
| `clinicalUser`      | `map`       | A map containing the clinical user's name.        |
| `compliance`        | `map`       | A map with compliance status and usage percentage.|
| `dataAccess`        | `map`       | A map with data access type and duration.         |

---

## 2. Sub-collections

Each customer document can contain the following sub-collections:

### 2.1. `devices`

Stores a history of CPAP devices used by the patient.

-   **Path:** `customers/{patientId}/devices/{deviceId}`

| Field          | Type        | Description                               |
| -------------- | ----------- | ----------------------------------------- |
| `deviceName`   | `string`    | The model name of the device.             |
| `serialNumber` | `string`    | The device's unique serial number.        |
| `addedDate`    | `timestamp` | The date the device was added.            |
| `status`       | `string`    | The current status of the device.         |
| `settings`     | `map`       | A map of all specific device settings.    |

### 2.2. `masks`

Stores a history of masks used by the patient.

-   **Path:** `customers/{patientId}/masks/{maskId}`

| Field      | Type        | Description                     |
| ---------- | ----------- | ------------------------------- |
| `maskName` | `string`    | The model name of the mask.     |
| `size`     | `string`    | The size of the mask.           |
| `addedDate`| `timestamp` | The date the mask was added.    |

### 2.3. `airTubing`

Stores a history of air tubing used by the patient.

-   **Path:** `customers/{patientId}/airTubing/{tubingId}`

| Field       | Type        | Description                      |
| ----------- | ----------- | -------------------------------- |
| `tubingName`| `string`    | The name of the air tubing.      |
| `addedDate` | `timestamp` | The date the tubing was added.   |

### 2.4. `dailyReports`

Stores daily report data extracted from PDFs or other sources. The document ID is the date of the report in `YYYY-MM-DD` format for easy querying.

-   **Path:** `customers/{patientId}/dailyReports/{reportDate}`

| Field                     | Type        | Description                                           |
| ------------------------- | ----------- | ----------------------------------------------------- |
| `reportDate`              | `timestamp` | The specific date of the report.                      |
| `usageHours`              | `string`    | Total usage time for the day.                         |
| `cheyneStokesRespiration` | `string`    | Duration and percentage of Cheyne-Stokes respiration. |
| `rera`                    | `number`    | Respiratory Effort-Related Arousal events.            |
| `leak`                    | `map`       | A map containing median and 95th percentile leak data.|
| `pressure`                | `map`       | A map containing median and 95th percentile pressure. |
| `eventsPerHour`           | `map`       | A map of all respiratory events per hour (AHI, etc.). |
| `deviceSnapshot`          | `map`       | A snapshot of the device settings during the report.  |

## 3. Development and Deployment

This section provides instructions for setting up the local development environment and deploying the application to Google Cloud Run.

### 3.1. Local Development Setup

Follow these steps to run the API on your local machine for development and testing.

**Prerequisites:**
- Python 3.8+
- `pip` and `venv`
- Google Cloud SDK (`gcloud` CLI) installed and authenticated.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd mega-care-api
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    (Assuming a `requirements.txt` file exists in the project root)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Firebase/Firestore Authentication:**
    To connect to Firestore from your local machine, you need to authenticate using a service account.
    a. In the Google Cloud Console, create a service account.
    b. Grant the service account the "Cloud Datastore User" or "Editor" role for your project.
    c. Create a JSON key for the service account and download it to a secure location on your computer.
    d. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the downloaded JSON key file.
    ```bash
    # For macOS/Linux (add this to your .bashrc or .zshrc for persistence)
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
    ```

5.  **Run the application:**
    Use `uvicorn` to start the local server. The `--reload` flag will automatically restart the server when code changes are detected.
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://1227.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

### 3.2. Deployment to Google Cloud Run

Deployment is automated using Google Cloud Build, as defined in `cloudbuild.yaml`.

**Prerequisites:**
- A Google Cloud Project with billing enabled.
- The following APIs enabled: Cloud Build API, Cloud Run Admin API, Artifact Registry API.
- Your Google Cloud user account must have permissions to submit builds (e.g., "Cloud Build Editor" role).

**Deployment Steps:**

1.  **Ensure your `gcloud` CLI is configured for the correct project:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

2.  **Submit the build:**
    From the root directory of the project, run the following command. This will trigger Cloud Build to execute the steps in `cloudbuild.yaml`.
    ```bash
    gcloud builds submit --config cloudbuild.yaml .
    ```