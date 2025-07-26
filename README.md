This repository contains the backend API for the MegaCare Connect application, built with FastAPI and Google Firestore.

## 1. Functional Overview

The API serves two primary actors:
*   **Patient**: The user of the LINE LIFF application. They can manage their profile, equipment, and view therapy data.
*   **Clinician**: A healthcare provider who monitors assigned patients.

### Core Features
*   **User Onboarding & Profile Management**: Patients can register and manage their personal information.
*   **Equipment Management**: Patients can track their CPAP devices, masks, and tubing.
*   **Data Reporting & Retrieval**: Patients and external systems can submit daily therapy reports. Patients and clinicians can retrieve historical data.

## 2. Technical Specification

*   **Framework**: FastAPI
*   **Database**: Google Cloud Firestore
*   **Authentication**: Firebase Authentication (ID Tokens)

### API Access
*   **Base URL**: The API is hosted on Google Cloud Run.
*   **Authentication**: All endpoints are protected and require a `Bearer` token in the `Authorization` header.
    ```
    Authorization: Bearer <Firebase_ID_Token>
    ```

### Data Structure
The database uses a hierarchical model centered around a `customers` collection. Each patient document contains their profile data and sub-collections for their `devices`, `masks`, `airTubing`, and `dailyReports`.

For a detailed schema and data hierarchy, please refer to `fs_ts.md`.

## 3. Development and Deployment

### Local Development Setup

**Prerequisites:**
- Python 3.8+
- `pip` and `venv`
- Google Cloud SDK (`gcloud` CLI)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/megacare-dev/mega-care-api.git
    cd mega-care-api
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Firestore Authentication:**
    a. Create a service account in the Google Cloud Console with the "Cloud Datastore User" role.
    b. Download the JSON key file.
    c. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the key file.
    ```bash
    # macOS/Linux
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
    ```

5.  **Run the application:**
    Use `uvicorn` to start the local server with auto-reload.
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.
    Interactive documentation (Swagger UI) is at `http://127.0.0.1:8000/docs`.

### Deployment to Google Cloud Run

Deployment is handled via Google Cloud Build using the `cloudbuild.yaml` configuration.

1.  **Set your project in gcloud:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

2.  **Submit the build:**
    From the project root, run:
    ```bash
    gcloud builds submit --config cloudbuild.yaml .

Test Local
uvicorn app.main:app --reload   
    ```
