import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timezone
from google.cloud.firestore_v1.query import Query
# To test the router, we need a FastAPI app instance
from fastapi import FastAPI
from app.api.v1.endpoints import clinicians
from app.dependencies.auth import get_current_user

# --- Test Setup ---

# Create a minimal FastAPI app for testing purposes
app = FastAPI()
# Include the router we want to test
app.include_router(clinicians.router, prefix="/api/v1/clinician", tags=["clinicians"])

# Define fake user IDs to be returned by the mocked dependency and used in data
FAKE_CLINICIAN_UID = "clinician-abc-123"
FAKE_PATIENT_UID_1 = "patient-def-456"
FAKE_PATIENT_UID_2 = "patient-ghi-789"

FAKE_CLINICIAN_USER = {"uid": FAKE_CLINICIAN_UID, "email": "clinician@example.com"}

# This function will replace the `get_current_user` dependency
def override_get_current_user():
    return FAKE_CLINICIAN_USER

# Apply the dependency override to our test app
app.dependency_overrides[get_current_user] = override_get_current_user

# Create a TestClient for making requests to our app
client = TestClient(app)

# --- Test Cases ---

@patch('app.api.v1.endpoints.clinicians.firestore.client')
def test_get_assigned_patients_success(mock_firestore_client):
    """Tests successful retrieval of assigned patients for a clinician."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db

    # Mock clinician document and reference
    mock_clinician_doc = MagicMock()
    mock_clinician_doc.exists = True
    mock_clinician_doc.to_dict.return_value = {"assignedPatients": [FAKE_PATIENT_UID_1, FAKE_PATIENT_UID_2]}
    mock_clinician_ref = MagicMock()
    mock_clinician_ref.get.return_value = mock_clinician_doc

    # Mock patient documents and references
    mock_patient_doc_1 = MagicMock()
    mock_patient_doc_1.exists = True
    mock_patient_doc_1.id = FAKE_PATIENT_UID_1
    mock_patient_doc_1.to_dict.return_value = {
        "displayName": "Patient One",
        "firstName": "Patient",
        "lastName": "One",
        "dob": datetime(1990, 1, 1),
        "setupDate": datetime.now(),
        "status": "Active"
    }
    mock_patient_ref_1 = MagicMock()
    mock_patient_ref_1.get.return_value = mock_patient_doc_1

    mock_patient_doc_2 = MagicMock()
    mock_patient_doc_2.exists = True
    mock_patient_doc_2.id = FAKE_PATIENT_UID_2
    mock_patient_doc_2.to_dict.return_value = {
        "displayName": "Patient Two",
        "firstName": "Patient", "lastName": "Two", "dob": datetime(1991, 2, 2), "setupDate": datetime.now(), "status": "Active"
    }
    mock_patient_ref_2 = MagicMock()
    mock_patient_ref_2.get.return_value = mock_patient_doc_2

    # Firestore call routing
    def collection_router(collection_name):
        if collection_name == "clinicians":
            mock_collection = MagicMock()
            mock_collection.document.return_value = mock_clinician_ref
            return mock_collection
        elif collection_name == "customers":
            mock_collection = MagicMock()
            def document_router(doc_id):
                if doc_id == FAKE_PATIENT_UID_1: return mock_patient_ref_1
                if doc_id == FAKE_PATIENT_UID_2: return mock_patient_ref_2
                return MagicMock()
            mock_collection.document.side_effect = document_router
            return mock_collection
    mock_db.collection.side_effect = collection_router

    # Act
    response = client.get("/api/v1/clinician/patients")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["patient_id"] == FAKE_PATIENT_UID_1
    assert response_data[0]["first_name"] == "Patient"
    assert response_data[1]["patient_id"] == FAKE_PATIENT_UID_2
    assert response_data[1]["last_name"] == "Two"

@patch('app.api.v1.endpoints.clinicians.firestore.client')
def test_get_assigned_patients_clinician_not_found(mock_firestore_client):
    """Tests 404 when the clinician profile does not exist."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_clinician_doc = MagicMock()
    mock_clinician_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_clinician_doc

    # Act
    response = client.get("/api/v1/clinician/patients")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Clinician profile not found"

@patch('app.api.v1.endpoints.clinicians.firestore.client')
def test_get_patient_profile_unauthorized(mock_firestore_client):
    """Tests 403 Forbidden when trying to access a non-assigned patient."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_clinician_doc = MagicMock()
    mock_clinician_doc.exists = True
    # This clinician is only assigned patient 1
    mock_clinician_doc.to_dict.return_value = {"assignedPatients": [FAKE_PATIENT_UID_1]}
    mock_db.collection.return_value.document.return_value.get.return_value = mock_clinician_doc

    # Act
    # The request is for a different patient ID
    response = client.get(f"/api/v1/clinician/patients/some-other-patient-id")

    # Assert
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"]

@patch('app.api.v1.endpoints.clinicians.firestore.client')
def test_get_patient_daily_reports_success(mock_firestore_client):
    """Tests successful retrieval of a specific patient's daily reports."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db

    # Mock clinician document (authorized)
    mock_clinician_doc = MagicMock()
    mock_clinician_doc.exists = True
    mock_clinician_doc.to_dict.return_value = {"assignedPatients": [FAKE_PATIENT_UID_1]}
    mock_db.collection.return_value.document.return_value.get.return_value = mock_clinician_doc

    # Mock daily reports stream
    mock_report_1 = MagicMock()
    mock_report_1.id = "2023-10-27"
    mock_report_1.to_dict.return_value = {
        "reportDate": datetime(2023, 10, 27), "usageHours": 8.0,
        "leak": {"median": 5.0},
        "pressure": {"median": 9.0},
        "eventsPerHour": {"ahi": 4.2}
    }

    mock_report_2 = MagicMock()
    mock_report_2.id = "2023-10-26"
    mock_report_2.to_dict.return_value = {
        "reportDate": datetime(2023, 10, 26),
        "usageHours": 7.5,
        "leak": {"median": 6.0},
        "pressure": {"median": 9.2},
        "eventsPerHour": {"ahi": 5.1}
    }

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_report_1, mock_report_2]
    
    mock_reports_ref = MagicMock()
    mock_reports_ref.order_by.return_value.limit.return_value = mock_query

    # Route the call to the subcollection
    mock_db.collection.return_value.document.return_value.collection.return_value = mock_reports_ref

    # Act
    response = client.get(f"/api/v1/clinician/patients/{FAKE_PATIENT_UID_1}/dailyReports?limit=5")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["report_id"] == "2023-10-27"
    assert response_data[0]["usage_hours"] == 8.0
    assert response_data[1]["report_id"] == "2023-10-26"

    # Verify query parameters were used
    mock_reports_ref.order_by.assert_called_with("reportDate", direction=Query.DESCENDING) # type: ignore
    mock_reports_ref.order_by.return_value.limit.assert_called_with(5)

@patch('app.api.v1.endpoints.clinicians.firestore.client')
def test_get_patient_daily_reports_no_reports(mock_firestore_client):
    """Tests returning an empty list when a patient has no reports."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db

    mock_clinician_doc = MagicMock()
    mock_clinician_doc.exists = True
    mock_clinician_doc.to_dict.return_value = {"assignedPatients": [FAKE_PATIENT_UID_1]}
    mock_db.collection.return_value.document.return_value.get.return_value = mock_clinician_doc

    mock_query = MagicMock()
    mock_query.stream.return_value = [] # No reports
    mock_reports_ref = MagicMock()
    mock_reports_ref.order_by.return_value.limit.return_value = mock_query
    mock_db.collection.return_value.document.return_value.collection.return_value = mock_reports_ref

    # Act
    response = client.get(f"/api/v1/clinician/patients/{FAKE_PATIENT_UID_1}/dailyReports")

    # Assert
    assert response.status_code == 200
    assert response.json() == []