from fastapi.testclient import TestClient
from unittest.mock import MagicMock, ANY
from datetime import datetime, timezone
from app.models import Customer # Import your Pydantic models

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
        "location": "Test Location",
        "status": "Active",
        "organisation": {"name": "Test Org"},
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
    mock_doc1.to_dict.return_value = {"firstName": "Customer", "lastName": "One", "status": "Active"}

    mock_doc2 = MagicMock()
    mock_doc2.id = "cust2"
    mock_doc2.to_dict.return_value = {"firstName": "Customer", "lastName": "Two", "status": "Inactive"}

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
    mock_doc_snapshot.to_dict.return_value = {"firstName": "Existing", "lastName": "Customer", "location": "Main Street"}

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

def test_get_customer_by_line_id_found(client: TestClient, db_mock: MagicMock):
    target_line_id = "line_user_123"
    customer_doc_id = "customer_for_line_id_test"
    customer_data = {
        "firstName": "Line",
        "lastName": "User",
        "lineId": target_line_id,
        "status": "Active",
        "location": "Digital World"
    }

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.id = customer_doc_id
    mock_doc_snapshot.to_dict.return_value = customer_data

    # Mock the Firestore query chain: collection -> where -> limit -> stream
    mock_query_after_limit = MagicMock()
    mock_query_after_limit.stream.return_value = [mock_doc_snapshot] # stream() returns an iterable

    mock_query_after_where = MagicMock()
    mock_query_after_where.limit.return_value = mock_query_after_limit

    db_mock.collection.return_value.where.return_value = mock_query_after_where

    response = client.get(f"/customers/line/{target_line_id}")

    assert response.status_code == 200
    customer = response.json()
    assert customer["id"] == customer_doc_id
    assert customer["lineId"] == target_line_id
    assert customer["firstName"] == "Line"
    db_mock.collection.assert_called_once_with("customers")
    db_mock.collection.return_value.where.assert_called_once_with("lineId", "==", target_line_id)
    mock_query_after_where.limit.assert_called_once_with(1)
    mock_query_after_limit.stream.assert_called_once()

def test_get_customer_by_line_id_not_found(client: TestClient, db_mock: MagicMock):
    target_line_id = "non_existent_line_id"

    mock_query_after_limit = MagicMock()
    mock_query_after_limit.stream.return_value = [] # stream() returns an empty iterable
    mock_query_after_where = MagicMock()
    mock_query_after_where.limit.return_value = mock_query_after_limit
    db_mock.collection.return_value.where.return_value = mock_query_after_where
    response = client.get(f"/customers/line/{target_line_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found with that lineId"

def test_update_customer_found(client: TestClient, db_mock: MagicMock):
    patient_id = "customer_to_update"
    update_data = {"firstName": "Updated", "location": "New Location"}

    mock_existing_doc_snapshot = MagicMock()
    mock_existing_doc_snapshot.exists = True

    mock_updated_doc_snapshot = MagicMock()
    mock_updated_doc_snapshot.id = patient_id
    mock_updated_doc_snapshot.to_dict.return_value = {**update_data, "lastName": "OriginalLastName", "status": "Active"} # Simulate other fields

    mock_doc_ref = MagicMock()
    # Simulate the get() calls: first for existence check, second after update
    mock_doc_ref.get.side_effect = [mock_existing_doc_snapshot, mock_updated_doc_snapshot]

    db_mock.collection.return_value.document.return_value = mock_doc_ref

    response = client.put(f"/customers/{patient_id}", json=update_data)
    assert response.status_code == 200
    updated_customer = response.json()
    assert updated_customer["firstName"] == "Updated"
    assert updated_customer["location"] == "New Location"
    mock_doc_ref.set.assert_called_once_with(update_data, merge=True)


def test_update_customer_no_data(client: TestClient, db_mock: MagicMock):
    # This test was previously combined or misplaced.
    # Assuming the intent was to test the "no data" scenario for updates.
    patient_id = "customer_no_update_data"
    
    mock_doc_snapshot = MagicMock() # For the existence check
    mock_doc_snapshot.exists = True
    
    # The update_customer route calls .get() once for existence check.
    # If it then proceeds, it calls .set() and then .get() again.
    # For this test, we only care about the first .get() and the subsequent 400.
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot 

    response = client.put(f"/customers/{patient_id}", json={}) # Empty update data
    assert response.status_code == 400
    assert response.json()["detail"] == "No update data provided"

def test_update_customer_not_found(client: TestClient, db_mock: MagicMock):
    patient_id = "non_existent_customer_for_update"
    update_data = {"firstName": "Updated"}

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False
    
    # The update_customer route calls .get() once for existence check.
    # If not found, it raises HTTPException(404).
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot 

    response = client.put(f"/customers/{patient_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found to update"

def test_delete_customer_found(client: TestClient, db_mock: MagicMock):
    patient_id = "customer_to_delete"
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True

    # The delete_customer route calls .get() once for existence check.
    # If found, it calls .delete().
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    db_mock.collection.return_value.document.return_value = mock_doc_ref

    response = client.delete(f"/customers/{patient_id}")
    assert response.status_code == 204 # No content
    db_mock.collection.return_value.document.return_value.delete.assert_called_once()

def test_delete_customer_not_found(client: TestClient, db_mock: MagicMock):
    patient_id = "non_existent_customer_for_delete"
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False

    # The delete_customer route calls .get() once for existence check.
    # If not found, it raises HTTPException(404).
    db_mock.collection.return_value.document.return_value.get.return_value = mock_doc_snapshot 

    response = client.delete(f"/customers/{patient_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found to delete"