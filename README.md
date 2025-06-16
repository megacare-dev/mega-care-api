# mega-care-api
Mega Care API
test# Firestore Data Structure for CPAP Customer Management

This document outlines the data structure used in Firestore to store customer information, their CPAP devices, and daily reports. The structure is designed to be scalable and query-efficient.

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

