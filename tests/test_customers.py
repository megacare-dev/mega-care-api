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
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])

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
        "createDate": datetime.now(timezone.utc), # The exact value is set in the endpoint
        "lineProfile": None
    }
    mock_doc_existent.to_dict.return_value = expected_db_data
    
    # The first call to .get() finds no existing profile, the second one finds the new one
    mock_customer_ref.get.side_effect = [mock_doc_nonexistent, mock_doc_existent]

    request_payload = {
        "display_name": "Paripol Live Test 1",
        "first_name": "Paripol",
        "last_name": "Tester",
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
    assert data_sent_to_firestore["dob"] == datetime(1992, 5, 20, 0, 0) # type: ignore
    assert "createDate" in data_sent_to_firestore # type: ignore
    assert isinstance(data_sent_to_firestore["createDate"], datetime) # type: ignore
    
    # Verify the response payload
    response_data = response.json()
    assert response_data["patient_id"] == FAKE_USER_UID
    assert response_data["first_name"] == "Paripol"
    # Pydantic model `Customer` has `dob: date`, so FastAPI serializes it back to a string
    assert response_data["dob"] == "1992-05-20"
    assert "create_date" in response_data


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_update_customer_profile_success(mock_firestore_client):
    """
    Tests that an existing profile is successfully updated (upsert)
    and returns a 200 OK status.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_customer_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_customer_ref

    # Mock that the document *already exists*
    mock_doc_existent_before = MagicMock()
    mock_doc_existent_before.exists = True

    mock_doc_existent_after = MagicMock()
    mock_doc_existent_after.exists = True
    mock_doc_existent_after.id = FAKE_USER_UID

    updated_db_data = {
        "displayName": "Paripol Live Test Updated", # Updated
        "firstName": "Paripol", "lastName": "Tester", "dob": datetime(1992, 5, 20, 0, 0),
        "status": "Active", "createDate": datetime(2023, 1, 1, 0, 0), # Should not be changed by update
        "lineProfile": None
    }
    mock_doc_existent_after.to_dict.return_value = updated_db_data

    mock_customer_ref.get.side_effect = [mock_doc_existent_before, mock_doc_existent_after]

    request_payload = {
        "display_name": "Paripol Live Test Updated",
        "first_name": "Paripol",
        "last_name": "Tester",
        "dob": "1992-05-20",
        "status": "Active"
    }

    # Act
    response = client.post("/api/v1/customers/me", json=request_payload)

    # Assert
    assert response.status_code == 200 # Should be 200 OK for an update

    mock_customer_ref.set.assert_called_once()
    call_args, call_kwargs = mock_customer_ref.set.call_args
    data_sent_to_firestore = call_args[0]

    assert "createDate" not in data_sent_to_firestore # createDate should not be added on update
    assert call_kwargs.get("merge") is True # Should be called with merge=True

    response_data = response.json()
    assert response_data["display_name"] == "Paripol Live Test Updated"
    assert response_data["patient_id"] == FAKE_USER_UID


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
        "createDate": datetime(2023, 1, 1, 12, 0, 0),
        "lineProfile": None
    }
    mock_doc.to_dict.return_value = db_data
    mock_customer_ref.get.return_value = mock_doc

    # Act
    response = client.get("/api/v1/customers/me")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["patient_id"] == FAKE_USER_UID
    assert response_data["first_name"] == "Paripol"
    assert response_data["dob"] == "1992-05-20"
    assert response_data["create_date"] == "2023-01-01T12:00:00"


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
        "report_date": report_date_str,
        "usage_hours": 8.5,
        "leak": {"median": 5.0, "95th_percentile": 20.0},
        "pressure": {"median": 8.0, "95th_percentile": 12.0},
        "events_per_hour": {"ahi": 4.2}
    }
    
    # Mock the .get() call that happens after .set()
    mock_report_snapshot = MagicMock()
    mock_report_snapshot.exists = True
    mock_report_snapshot.id = report_date_str
    mock_report_snapshot.to_dict.return_value = {
        "reportDate": report_datetime_obj, # type: ignore
        "usageHours": 8.5, # type: ignore
        "leak": {"median": 5.0, "95th_percentile": 20.0},
        "pressure": {"median": 8.0, "95th_percentile": 12.0},
        "eventsPerHour": {"ahi": 4.2} # type: ignore
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
    
    assert isinstance(data_sent_to_firestore["reportDate"], datetime) # type: ignore
    assert data_sent_to_firestore["reportDate"] == report_datetime_obj # type: ignore
    
    # Verify response
    response_data = response.json()
    assert response_data["report_id"] == report_date_str
    assert response_data["report_date"] == report_date_str
    assert response_data["usage_hours"] == 8.5


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
        "device_name": "AirSense 10",
        "serial_number": "SN123456789",
        "status": "Active"
    }

    # Mock the .get() call that happens after creation
    mock_device_snapshot = MagicMock()
    mock_device_snapshot.exists = True
    mock_device_snapshot.id = "new-device-id"
    mock_device_snapshot.to_dict.return_value = {
        "deviceName": "AirSense 10", "serialNumber": "SN123456789", "status": "Active",
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
    assert data_sent_to_firestore["deviceName"] == "AirSense 10" # type: ignore
    assert "addedDate" in data_sent_to_firestore # type: ignore
    assert isinstance(data_sent_to_firestore["addedDate"], datetime) # type: ignore

    # Verify response
    response_data = response.json()
    assert response_data["device_id"] == "new-device-id"
    assert response_data["device_name"] == "AirSense 10"
    assert "added_date" in response_data

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
    assert response_data[0]["device_id"] == "device-id-1"
    assert response_data[0]["device_name"] == "AirSense 10"
    assert response_data[1]["device_id"] == "device-id-2"
    assert response_data[1]["device_name"] == "AirSense 11"
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

    request_payload = {"mask_name": "AirFit P10", "size": "M"}

    mock_mask_snapshot = MagicMock()
    mock_mask_snapshot.exists = True
    mock_mask_snapshot.id = "new-mask-id"
    mock_mask_snapshot.to_dict.return_value = {"maskName": "AirFit P10", "size": "M", "addedDate": datetime.now(timezone.utc)}
    mock_mask_ref.get.return_value = mock_mask_snapshot

    # Act
    response = client.post("/api/v1/customers/me/masks", json=request_payload)

    # Assert
    assert response.status_code == 201
    mock_db.collection.return_value.document.return_value.collection.assert_called_with("masks")
    response_data = response.json()
    assert response_data["mask_id"] == "new-mask-id"
    assert response_data["mask_name"] == "AirFit P10"


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_link_device_success_no_patient_id_field(mock_firestore_client):
    """
    Tests successful linking of a device by finding a pre-existing profile
    in Firestore and merging it into the current user's profile. This test
    verifies the case where the device document does NOT have a 'patientId' field.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db

    # --- Mocking the Collection Group Query ---
    PRE_EXISTING_PATIENT_ID = "patient-abc-123"
    pre_existing_patient_data = {
        "displayName": "John Firestore", "firstName": "John", "lastName": "Firestore",
        "dob": datetime(1985, 6, 15, 0, 0), "status": "Active",
        "createDate": datetime(2023, 1, 1)
    }
    mock_pre_existing_customer_doc = MagicMock()
    mock_pre_existing_customer_doc.exists = True
    mock_pre_existing_customer_doc.to_dict.return_value = pre_existing_patient_data
    mock_pre_existing_customer_ref = MagicMock()
    mock_pre_existing_customer_ref.id = PRE_EXISTING_PATIENT_ID
    mock_pre_existing_customer_ref.get.return_value = mock_pre_existing_customer_doc

    # Mock the Firestore document hierarchy: customer_ref -> devices_collection_ref -> device_doc_ref
    mock_devices_collection_ref = MagicMock()
    mock_devices_collection_ref.parent = mock_pre_existing_customer_ref

    # Device data WITHOUT 'patientId' field
    mock_device_data = {"serialNumber": "SN123456789"}
    mock_device_doc = MagicMock()
    mock_device_doc.id = "device-doc-id"
    mock_device_doc.reference.parent = mock_devices_collection_ref
    mock_device_doc.to_dict.return_value = mock_device_data
    mock_db.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = [mock_device_doc]

    # --- Mocking the Firestore collection calls ---
    mock_customers_collection = MagicMock()
    mock_patients_collection = MagicMock()

    def collection_side_effect(name):
        if name == "customers":
            return mock_customers_collection
        if name == "patients":
            return mock_patients_collection
        return MagicMock()
    mock_db.collection.side_effect = collection_side_effect

    # --- Mocking the Update/Get of the Current User's Profile ---
    mock_current_user_customer_ref = MagicMock()
    mock_customers_collection.document.return_value = mock_current_user_customer_ref

    final_merged_data = {
        **pre_existing_patient_data, "lineId": FAKE_USER_UID,
        "patientId": None,  # The device doc has no patientId, so this becomes None in the merge
        "lineProfile": None
    }
    mock_updated_doc = MagicMock()
    mock_updated_doc.exists = True
    mock_updated_doc.id = FAKE_USER_UID
    mock_updated_doc.to_dict.return_value = final_merged_data
    mock_current_user_customer_ref.get.return_value = mock_updated_doc

    request_payload = {"serial_number": "SN123456789", "device_number": "DN987654321"}

    # Act
    response = client.post("/api/v1/customers/me/link-device", json=request_payload)

    # Assert
    assert response.status_code == 200
    mock_db.collection_group.assert_called_once_with("devices")
    mock_db.collection_group.return_value.where.assert_called_once_with("serialNumber", "==", "SN123456789")

    # Assert that the copy to 'patients' collection DID NOT happen
    mock_patients_collection.document.assert_not_called()

    mock_customers_collection.document.assert_called_once_with(FAKE_USER_UID)

    mock_current_user_customer_ref.set.assert_called_once()
    call_args, call_kwargs = mock_current_user_customer_ref.set.call_args
    data_sent_to_firestore = call_args[0]

    assert data_sent_to_firestore["firstName"] == "John" # type: ignore

    assert data_sent_to_firestore["patientId"] is None # type: ignore
    assert call_kwargs.get("merge") is True

    response_data = response.json()
    assert response_data["patient_id"] == FAKE_USER_UID
    assert response_data["first_name"] == "John"
    assert response_data["dob"] == "1985-06-15"
    assert "create_date" in response_data


@patch('app.api.v1.endpoints.customers.firestore.client')
def test_link_device_copies_to_patients_collection(mock_firestore_client):
    """
    Tests that linking a device correctly copies the pre-existing profile
    to the 'patients' collection when the device doc has a 'patientId' field.
    """
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db

    # --- Mocking the Collection Group Query ---
    PRE_EXISTING_PATIENT_ID = "patient-abc-123"
    DEVICE_PATIENT_ID_FIELD = "new-patient-doc-id-from-device" # The ID for the new doc in 'patients'

    pre_existing_patient_data = {
        "displayName": "John Firestore", "firstName": "John", "lastName": "Firestore",
        "dob": datetime(1985, 6, 15, 0, 0), "status": "Active",
        "createDate": datetime(2023, 1, 1)
    }
    mock_pre_existing_customer_doc = MagicMock()
    mock_pre_existing_customer_doc.exists = True
    mock_pre_existing_customer_doc.to_dict.return_value = pre_existing_patient_data
    mock_pre_existing_customer_ref = MagicMock()
    mock_pre_existing_customer_ref.id = PRE_EXISTING_PATIENT_ID
    mock_pre_existing_customer_ref.get.return_value = mock_pre_existing_customer_doc

    mock_devices_collection_ref = MagicMock()
    mock_devices_collection_ref.parent = mock_pre_existing_customer_ref

    # This is the key part: the device document now has a 'patientId'
    mock_device_data = {"serialNumber": "SN123456789", "patientId": DEVICE_PATIENT_ID_FIELD}
    mock_device_doc = MagicMock()
    mock_device_doc.reference.parent = mock_devices_collection_ref
    mock_device_doc.to_dict.return_value = mock_device_data
    mock_device_doc.id = "device-doc-id"

    mock_db.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = [mock_device_doc]

    # --- Mocking the Firestore collection calls ---
    mock_customers_collection = MagicMock()
    mock_patients_collection = MagicMock()

    def collection_side_effect(name):
        if name == "customers":
            return mock_customers_collection
        if name == "patients":
            return mock_patients_collection
        return MagicMock() # Default mock for other collections
    mock_db.collection.side_effect = collection_side_effect

    # --- Mocking the Update/Get of the Current User's Profile ---
    mock_current_user_customer_ref = MagicMock()
    mock_customers_collection.document.return_value = mock_current_user_customer_ref

    final_merged_data = {
        **pre_existing_patient_data,
        "lineId": FAKE_USER_UID,
        "patientId": DEVICE_PATIENT_ID_FIELD,
        "lineProfile": None
    }
    mock_updated_doc = MagicMock()
    mock_updated_doc.exists = True
    mock_updated_doc.id = FAKE_USER_UID
    mock_updated_doc.to_dict.return_value = final_merged_data
    mock_current_user_customer_ref.get.return_value = mock_updated_doc

    # --- Mocking the set call on the 'patients' collection ---
    mock_new_patient_doc_ref = MagicMock()
    mock_patients_collection.document.return_value = mock_new_patient_doc_ref

    request_payload = {"serial_number": "SN123456789", "device_number": "DN987654321"}

    # Act
    response = client.post("/api/v1/customers/me/link-device", json=request_payload)

    # Assert
    assert response.status_code == 200

    # Assert the copy to 'patients' collection
    mock_patients_collection.document.assert_called_once_with(DEVICE_PATIENT_ID_FIELD)

    # The endpoint adds the 'customerId' (the logged-in user's UID) to the
    # pre-existing data before copying it to the 'patients' collection.
    expected_data_for_patients_collection = pre_existing_patient_data.copy()
    expected_data_for_patients_collection["customerId"] = FAKE_USER_UID
    mock_new_patient_doc_ref.set.assert_called_once_with(expected_data_for_patients_collection, merge=True)

    # Assert the merge to 'customers' collection still happened
    mock_customers_collection.document.assert_called_once_with(FAKE_USER_UID)
    mock_current_user_customer_ref.set.assert_called_once()

@patch('app.api.v1.endpoints.customers.firestore.client')
def test_link_device_not_found_in_firestore(mock_firestore_client):
    """Tests 404 when the device SN is not found in Firestore."""
    # Arrange
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_db.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = []
    request_payload = {"serial_number": "INVALID_SN", "device_number": "INVALID_DN"}

    # Act
    response = client.post("/api/v1/customers/me/link-device", json=request_payload)

    # Assert
    assert response.status_code == 404
    assert "No patient record found" in response.json()["detail"]