import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timezone

# To test the router, we need a FastAPI app instance
from fastapi import FastAPI
from app.api.v1.endpoints import customers
from app.dependencies.auth import get_current_user

# --- Test Setup ---

# Create a minimal FastAPI app for testing purposes
app = FastAPI()
# Include the router we want to test
app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])

# Define a fake user to be returned by the mocked dependency
FAKE_USER_UID = "S1lPJz222Ih8tkm5mIKIv0c924Y2"
FAKE_USER = {"uid": FAKE_USER_UID, "email": "test@example.com"}

# This function will replace the `get_current_user` dependency
def override_get_current_user():
    return FAKE_USER

# Apply the dependency override to our test app
app.dependency_overrides[get_current_user] = override_get_current_user

# Create a TestClient for making requests to our app
client = TestClient(app)

# --- Test Cases ---

@patch('app.api.v1.endpoints.customers.firestore.client')
def test_create_customer_profile_success(mock_firestore_client):
    """
    Tests successful creation of a customer profile,
    ensuring dob (date) is converted to a datetime object for Firestore.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_customer_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_customer_ref

    # Mock the two .get() calls inside the endpoint
    mock_doc_nonexistent = MagicMock()
    mock_doc_nonexistent.exists = False
    
    mock_doc_existent = MagicMock()
    mock_doc_existent.exists = True
    mock_doc_existent.id = FAKE_USER_UID
    # This is the data we expect to be returned from the DB after creation
    # Firestore returns datetime objects for Timestamps
    expected_db_data = {
        "displayName": "Paripol Live Test 1",
        "firstName": "Paripol",
        "lastName": "Tester",
        "dob": datetime(1992, 5, 20, 0, 0),
        "status": "Active",
        "setupDate": datetime.now(timezone.utc) # The exact value is set in the endpoint
    }
    mock_doc_existent.to_dict.return_value = expected_db_data
    
    # The first call to .get() finds no existing profile, the second one finds the new one
    mock_customer_ref.get.side_effect = [mock_doc_nonexistent, mock_doc_existent]

    request_payload = {
        "displayName": "Paripol Live Test 1",
        "firstName": "Paripol",
        "lastName": "Tester",
        "dob": "1992-05-20",
        "status": "Active"
    }

    # Act
    response = client.post("/api/v1/customers/me", json=request_payload)

    # Assert
    assert response.status_code == 201
    
    # Verify Firestore interactions
    mock_db.collection.assert_called_once_with("customers")
    mock_db.collection.return_value.document.assert_called_once_with(FAKE_USER_UID)
    
    # This is the crucial check for the date conversion fix
    mock_customer_ref.set.assert_called_once()
    call_args, _ = mock_customer_ref.set.call_args
    data_sent_to_firestore = call_args[0]
    
    assert isinstance(data_sent_to_firestore["dob"], datetime)
    assert data_sent_to_firestore["dob"] == datetime(1992, 5, 20, 0, 0)
    assert "setupDate" in data_sent_to_firestore
    assert isinstance(data_sent_to_firestore["setupDate"], datetime)
    
    # Verify the response payload
    response_data = response.json()
    assert response_data["patientId"] == FAKE_USER_UID
    assert response_data["firstName"] == "Paripol"
    # Pydantic model `Customer` has `dob: date`, so FastAPI serializes it back to a string
    assert response_data["dob"] == "1992-05-20"
    assert "setupDate" in response_data


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_create_customer_profile_already_exists(mock_firestore_client):
    """
    Tests that a 409 Conflict is returned if the profile already exists.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_customer_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_customer_ref
    
    mock_doc_existent = MagicMock()
    mock_doc_existent.exists = True
    mock_customer_ref.get.return_value = mock_doc_existent
    
    request_payload = {
        "displayName": "Test User", "firstName": "Test", "lastName": "User",
        "dob": "2000-01-01", "status": "Active"
    }

    # Act
    response = client.post("/api/v1/customers/me", json=request_payload)

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Customer profile already exists"


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_get_my_profile_success(mock_firestore_client):
    """
    Tests successful retrieval of a customer profile.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_customer_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_customer_ref
    
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.id = FAKE_USER_UID
    db_data = {
        "displayName": "Paripol Tester", "firstName": "Paripol", "lastName": "Tester",
        "dob": datetime(1992, 5, 20, 0, 0), "status": "Active",
        "setupDate": datetime(2023, 1, 1, 12, 0, 0)
    }
    mock_doc.to_dict.return_value = db_data
    mock_customer_ref.get.return_value = mock_doc

    # Act
    response = client.get("/api/v1/customers/me")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["patientId"] == FAKE_USER_UID
    assert response_data["firstName"] == "Paripol"
    assert response_data["dob"] == "1992-05-20"
    assert response_data["setupDate"] == "2023-01-01T12:00:00"


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_get_my_profile_not_found(mock_firestore_client):
    """
    Tests that a 404 Not Found is returned if the profile does not exist.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_customer_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_customer_ref
    
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_customer_ref.get.return_value = mock_doc

    # Act
    response = client.get("/api/v1/customers/me")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer profile not found"


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_submit_daily_report_success(mock_firestore_client):
    """
    Tests successful submission of a daily report,
    ensuring reportDate (date) is converted to a datetime object for Firestore.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_report_ref = MagicMock()
    mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_report_ref
    
    report_date_str = "2023-10-26"
    report_datetime_obj = datetime(2023, 10, 26, 0, 0)
    
    request_payload = {
        "reportDate": report_date_str,
        "usageHours": 8.5,
        "leak": {"median": 5.0, "95th_percentile": 20.0},
        "pressure": {"median": 8.0, "95th_percentile": 12.0},
        "eventsPerHour": {"ahi": 4.2}
    }
    
    # Mock the .get() call that happens after .set()
    mock_report_snapshot = MagicMock()
    mock_report_snapshot.exists = True
    mock_report_snapshot.id = report_date_str
    mock_report_snapshot.to_dict.return_value = {
        "reportDate": report_datetime_obj,
        "usageHours": 8.5,
        "leak": {"median": 5.0, "95th_percentile": 20.0},
        "pressure": {"median": 8.0, "95th_percentile": 12.0},
        "eventsPerHour": {"ahi": 4.2}
    }
    mock_report_ref.get.return_value = mock_report_snapshot

    # Act
    response = client.post("/api/v1/customers/me/dailyReports", json=request_payload)

    # Assert
    assert response.status_code == 201
    
    # Verify Firestore interactions
    mock_db.collection.return_value.document.return_value.collection.assert_called_once_with("dailyReports")
    mock_db.collection.return_value.document.return_value.collection.return_value.document.assert_called_once_with(report_date_str)
    
    # Crucial check for the date conversion fix
    mock_report_ref.set.assert_called_once()
    call_args, _ = mock_report_ref.set.call_args
    data_sent_to_firestore = call_args[0]
    
    assert isinstance(data_sent_to_firestore["reportDate"], datetime)
    assert data_sent_to_firestore["reportDate"] == report_datetime_obj
    
    # Verify response
    response_data = response.json()
    assert response_data["reportId"] == report_date_str
    assert response_data["reportDate"] == report_date_str
    assert response_data["usageHours"] == 8.5


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_add_device_success(mock_firestore_client):
    """Tests successful addition of a device to a customer's profile."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_device_subcollection = MagicMock()
    mock_device_ref = MagicMock()

    # Path: db.collection("customers").document(FAKE_USER_UID).collection("devices")
    mock_db.collection.return_value.document.return_value.collection.return_value = mock_device_subcollection
    # The endpoint calls .add(), which returns a tuple (update_time, document_reference)
    mock_device_subcollection.add.return_value = (datetime.now(timezone.utc), mock_device_ref)

    request_payload = {
        "deviceName": "AirSense 10",
        "serialNumber": "SN123456789",
        "status": "Active"
    }

    # Mock the .get() call that happens after creation
    mock_device_snapshot = MagicMock()
    mock_device_snapshot.exists = True
    mock_device_snapshot.id = "new-device-id"
    mock_device_snapshot.to_dict.return_value = {
        **request_payload,
        "addedDate": datetime.now(timezone.utc)
    }
    mock_device_ref.get.return_value = mock_device_snapshot

    # Act
    response = client.post("/api/v1/customers/me/devices", json=request_payload)

    # Assert
    assert response.status_code == 201

    # Verify Firestore interactions
    mock_db.collection.return_value.document.assert_called_with(FAKE_USER_UID)
    mock_db.collection.return_value.document.return_value.collection.assert_called_with("devices")

    # Verify data was added to the subcollection
    mock_device_subcollection.add.assert_called_once()
    call_args, _ = mock_device_subcollection.add.call_args
    data_sent_to_firestore = call_args[0]
    assert data_sent_to_firestore["deviceName"] == "AirSense 10"
    assert "addedDate" in data_sent_to_firestore
    assert isinstance(data_sent_to_firestore["addedDate"], datetime)

    # Verify response
    response_data = response.json()
    assert response_data["deviceId"] == "new-device-id"
    assert response_data["deviceName"] == "AirSense 10"
    assert "addedDate" in response_data

@patch('app.api.v1.endpoints.customers.firestore.client')
def test_get_my_devices_success(mock_firestore_client):
    """Tests successful retrieval of a list of devices."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_device_subcollection = MagicMock()

    mock_db.collection.return_value.document.return_value.collection.return_value = mock_device_subcollection

    # Mock two device documents being returned
    device1_data = { "deviceName": "AirSense 10", "serialNumber": "SN1", "status": "Active", "addedDate": datetime(2023, 1, 1) }
    device2_data = { "deviceName": "AirSense 11", "serialNumber": "SN2", "status": "Inactive", "addedDate": datetime(2023, 6, 1) }

    mock_doc1 = MagicMock()
    mock_doc1.id = "device-id-1"
    mock_doc1.to_dict.return_value = device1_data

    mock_doc2 = MagicMock()
    mock_doc2.id = "device-id-2"
    mock_doc2.to_dict.return_value = device2_data

    mock_device_subcollection.stream.return_value = [mock_doc1, mock_doc2]

    # Act
    response = client.get("/api/v1/customers/me/devices")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["deviceId"] == "device-id-1"
    assert response_data[0]["deviceName"] == "AirSense 10"
    assert response_data[1]["deviceId"] == "device-id-2"
    assert response_data[1]["deviceName"] == "AirSense 11"
    assert response_data[1]["status"] == "Inactive"

@patch('app.api.v1.endpoints.customers.firestore.client')
def test_add_mask_success(mock_firestore_client):
    """Tests successful addition of a mask."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_mask_subcollection = MagicMock()
    mock_mask_ref = MagicMock()
    mock_db.collection.return_value.document.return_value.collection.return_value = mock_mask_subcollection
    # The endpoint calls .add(), which returns a tuple (update_time, document_reference)
    mock_mask_subcollection.add.return_value = (datetime.now(timezone.utc), mock_mask_ref)

    request_payload = {"maskName": "AirFit P10", "size": "M"}

    mock_mask_snapshot = MagicMock()
    mock_mask_snapshot.exists = True
    mock_mask_snapshot.id = "new-mask-id"
    mock_mask_snapshot.to_dict.return_value = {**request_payload, "addedDate": datetime.now(timezone.utc)}
    mock_mask_ref.get.return_value = mock_mask_snapshot

    # Act
    response = client.post("/api/v1/customers/me/masks", json=request_payload)

    # Assert
    assert response.status_code == 201
    mock_db.collection.return_value.document.return_value.collection.assert_called_with("masks")
    response_data = response.json()
    assert response_data["maskId"] == "new-mask-id"
    assert response_data["maskName"] == "AirFit P10"