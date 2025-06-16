from fastapi.testclient import TestClient
from unittest.mock import MagicMock, ANY
from datetime import datetime, timezone
from app.models import Customer, Device # Import your Pydantic models

# Test the root endpoint
def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == '"Hello World from Cloud Run with FastAPI!\\n"' # FastAPI returns JSON encoded string

# --- Test Customers CRUD ---

def test_create_customer(client: TestClient, db_mock: MagicMock):
    # Mock Firestore document reference and its methods
    mock_doc_ref = MagicMock()
    mock_created_doc_snapshot = MagicMock()
    mock_created_doc_snapshot.id = "new_customer_id"
    
    # Sample data that matches CustomerCreate and the expected to_dict() from snapshot
    customer_data_payload = {
        "firstName": "Test",
        "lastName": "User",
        "email": "test.user@example.com",
        # Add other required fields from CustomerCreate
    }
    # This is what doc_ref.get().to_dict() would return
    firestore_doc_data = {**customer_data_payload, "setupDate": datetime.now(timezone.utc)} 

    mock_created_doc_snapshot.to_dict.return_value = firestore_doc_data
    mock_doc_ref.get.return_value = mock_created_doc_snapshot

    db_mock.collection.return_value.document.return_value = mock_doc_ref

    response = client.post("/customers", json=customer_data_payload)

    assert response.status_code == 201
    created_customer = response.json()
    assert created_customer["id"] == "new_customer_id"
    assert created_customer["firstName"] == "Test"
    db_mock.collection.assert_called_once_with("customers")
    mock_doc_ref.set.assert_called_once()
    # Check if setupDate was handled (either client-provided or SERVER_TIMESTAMP placeholder)
    # The actual value of SERVER_TIMESTAMP is tricky to assert directly without more complex mocking
    # So we check that the field was part of the set call
    args, kwargs = mock_doc_ref.set.call_args
    assert 'setupDate' in args[0] or 'setupDate' in kwargs.get('data', {})


def test_get_all_customers(client: TestClient, db_mock: MagicMock):
    mock_doc1 = MagicMock()
    mock_doc1.id = "cust1"
    mock_doc1.to_dict.return_value = {"firstName": "Customer", "lastName": "One"}

    mock_doc2 = MagicMock()
    mock_doc2.id = "cust2"
    mock_doc2.to_dict.return_value = {"firstName": "Customer", "lastName": "Two"}

    db_mock.collection.return_value.stream.return_value = [mock_doc1, mock_doc2]

    response = client.get("/customers")
    assert response.status_code == 200
    customers = response.json()
    assert len(customers) == 2
    assert customers[0]["id"] == "cust1"
    assert customers[1]["firstName"] == "Customer"

def test_get_customer_by_id_found(client: TestClient, db_mock: MagicMock):
    patient_id = "existing_customer"
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.id = patient_id
    mock_doc_snapshot.to_dict.return_value = {"firstName": "Existing", "lastName": "Customer"}

    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot

    response = client.get(f"/customers/{patient_id}")
    assert response.status_code == 200
    customer = response.json()
    assert customer["id"] == patient_id
    assert customer["firstName"] == "Existing"

def test_get_customer_by_id_not_found(client: TestClient, db_mock: MagicMock):
    patient_id = "non_existent_customer"
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False

    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot

    response = client.get(f"/customers/{patient_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"

def test_update_customer_found(client: TestClient, db_mock: MagicMock):
    patient_id = "customer_to_update"
    update_data = {"firstName": "Updated", "notes": "Some new notes"}

    mock_existing_doc_snapshot = MagicMock()
    mock_existing_doc_snapshot.exists = True

    mock_updated_doc_snapshot = MagicMock()
    mock_updated_doc_snapshot.id = patient_id
    mock_updated_doc_snapshot.to_dict.return_value = {**update_data, "lastName": "OriginalLastName"} # Simulate other fields

    mock_doc_ref = MagicMock()
    # Simulate the get() calls: first for existence check, second after update
    mock_doc_ref.get.side_effect = [mock_existing_doc_snapshot, mock_updated_doc_snapshot]

    db_mock.collection.return_value.document.return_value = mock_doc_ref

    response = client.put(f"/customers/{patient_id}", json=update_data)
    assert response.status_code == 200
    updated_customer = response.json()
    assert updated_customer["firstName"] == "Updated"
    assert updated_customer["notes"] == "Some new notes"
    mock_doc_ref.set.assert_called_once_with(update_data, merge=True)

def test_update_customer_not_found(client: TestClient, db_mock: MagicMock):
    patient_id = "non_existent_customer_for_update"
    update_data = {"firstName": "Updated"}

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot

    response = client.put(f"/customers/{patient_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found to update"

def test_update_customer_no_data(client: TestClient, db_mock: MagicMock):
    patient_id = "customer_no_update_data"
    
    mock_doc_snapshot = MagicMock() # For the existence check
    mock_doc_snapshot.exists = True
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot

    response = client.put(f"/customers/{patient_id}", json={}) # Empty update data
    assert response.status_code == 400
    assert response.json()["detail"] == "No update data provided"


def test_delete_customer_found(client: TestClient, db_mock: MagicMock):
    patient_id = "customer_to_delete"
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot

    response = client.delete(f"/customers/{patient_id}")
    assert response.status_code == 204 # No content
    db_mock.collection.return_value.document.return_value.delete.assert_called_once()

def test_delete_customer_not_found(client: TestClient, db_mock: MagicMock):
    patient_id = "non_existent_customer_for_delete"
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot

    response = client.delete(f"/customers/{patient_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found to delete"

# --- Test Devices Sub-collection CRUD ---

def test_add_device_to_customer(client: TestClient, db_mock: MagicMock):
    patient_id = "existing_customer_for_device"
    device_payload = {"deviceName": "CPAP AirSense", "serialNumber": "SN123"}

    # Mock customer existence check
    mock_customer_doc = MagicMock()
    mock_customer_doc.exists = True
    db_mock.collection.return_value.document.return_value.get.return_value = mock_customer_doc

    # Mock device creation
    mock_device_doc_ref = MagicMock()
    mock_created_device_snapshot = MagicMock()
    mock_created_device_snapshot.id = "new_device_id"
    
    # This is what doc_ref.get().to_dict() would return for the device
    firestore_device_data = {**device_payload, "addedDate": datetime.now(timezone.utc)}
    mock_created_device_snapshot.to_dict.return_value = firestore_device_data
    mock_device_doc_ref.get.return_value = mock_created_device_snapshot

    # Mock the subcollection document reference
    db_mock.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_device_doc_ref

    response = client.post(f"/customers/{patient_id}/devices", json=device_payload)
    
    assert response.status_code == 201
    created_device = response.json()
    assert created_device["id"] == "new_device_id"
    assert created_device["deviceName"] == "CPAP AirSense"
    mock_device_doc_ref.set.assert_called_once()
    args, kwargs = mock_device_doc_ref.set.call_args
    assert 'addedDate' in args[0] or 'addedDate' in kwargs.get('data', {})

def test_add_device_to_customer_customer_not_found(client: TestClient, db_mock: MagicMock):
    patient_id = "non_existent_customer_for_device"
    device_payload = {"deviceName": "Test Device", "serialNumber": "SN000"}

    mock_customer_doc = MagicMock()
    mock_customer_doc.exists = False
    db_mock.collection.return_value.document.return_value.get.return_value = mock_customer_doc

    response = client.post(f"/customers/{patient_id}/devices", json=device_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"

def test_get_devices_for_customer(client: TestClient, db_mock: MagicMock):
    patient_id = "customer_with_devices"
    mock_device_doc1 = MagicMock()
    mock_device_doc1.id = "dev1"
    mock_device_doc1.to_dict.return_value = {"deviceName": "Device A", "serialNumber": "SNA"}

    mock_device_doc2 = MagicMock()
    mock_device_doc2.id = "dev2"
    mock_device_doc2.to_dict.return_value = {"deviceName": "Device B", "serialNumber": "SNB"}

    db_mock.collection.return_value.document.return_value.collection.return_value.stream.return_value = [mock_device_doc1, mock_device_doc2]

    response = client.get(f"/customers/{patient_id}/devices")
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) == 2
    assert devices[0]["id"] == "dev1"
    assert devices[1]["deviceName"] == "Device B"