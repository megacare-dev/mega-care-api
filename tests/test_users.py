from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from google.cloud.firestore_v1.base_query import FieldFilter


def test_get_user_status_linked(client: TestClient, db_mock: MagicMock):
    """
    Tests GET /status when the user's lineId is found in Firestore.
    """
    # Arrange
    mock_query_result = [MagicMock()]  # A non-empty list means a document was found
    db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = (
        mock_query_result
    )

    # Act
    response = client.get(
        "/api/v1/users/status", headers={"Authorization": "Bearer fake-token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"isLinked": True}
    # Verify the database was queried correctly
    where_mock = db_mock.collection.return_value.where
    where_mock.assert_called_once()
    call_args, call_kwargs = where_mock.call_args
    filter_arg = call_kwargs.get("filter")
    assert isinstance(filter_arg, FieldFilter)
    assert filter_arg.field_path == "lineId"
    assert filter_arg.op_string == "=="
    assert filter_arg.value == "MOCK_LINE_ID_FOR_TEST"


def test_get_user_status_not_linked(client: TestClient, db_mock: MagicMock):
    """
    Tests GET /status when the user's lineId is NOT found in Firestore.
    """
    # Arrange
    db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = (
        []
    )  # Empty list means not found

    # Act
    response = client.get(
        "/api/v1/users/status", headers={"Authorization": "Bearer fake-token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"isLinked": False}


def test_link_account_success(client: TestClient, db_mock: MagicMock):
    """
    Tests POST /link-account when a valid, unlinked serial number is provided.
    Expects 204 No Content and Firestore update.
    """
    # Arrange
    test_serial_number = "TESTSN123"
    mock_line_id = "MOCK_LINE_ID_FOR_TEST"

    # Mock a device document found by serial number
    mock_device_doc = MagicMock()
    mock_device_doc.id = "device_id_1"

    # Mock the parent customer document for the device
    mock_customer_doc = MagicMock()
    mock_customer_doc.id = "customer_id_1"
    mock_customer_doc.to_dict.return_value = {"patientId": "patient_id_1", "lineId": None} # Initially unlinked

    # Configure the device document's parent reference to return the mock customer document
    # Correct path: device -> devices (collection) -> customer (document)
    mock_device_doc.reference.parent.parent.get.return_value = mock_customer_doc

    # Mock the collection_group query for devices
    db_mock.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = [
        mock_device_doc
    ]

    # Act
    response = client.post(
        "/api/v1/users/link-account",
        headers={"Authorization": f"Bearer fake-token"},
        json={"serialNumber": test_serial_number},
    )

    # Assert
    assert response.status_code == 204
    # Verify Firestore interactions
    db_mock.collection_group.assert_called_once_with("devices")
    db_mock.collection_group.return_value.where.assert_called_once()
    # Check the filter arguments for the where clause
    where_args, where_kwargs = db_mock.collection_group.return_value.where.call_args
    filter_arg = where_kwargs.get("filter")
    assert isinstance(filter_arg, FieldFilter)
    assert filter_arg.field_path == "serialNumber"
    assert filter_arg.op_string == "=="
    assert filter_arg.value == test_serial_number

    mock_device_doc.reference.parent.parent.get.assert_called_once()  # Ensure customer doc was fetched
    mock_device_doc.reference.parent.parent.update.assert_called_once_with({"lineId": mock_line_id})  # Ensure lineId was updated on the correct reference


def test_link_account_serial_not_found(client: TestClient, db_mock: MagicMock):
    """
    Tests POST /link-account when the provided serial number is not found.
    Expects 404 Not Found.
    """
    # Arrange
    test_serial_number = "NONEXISTENTSN"
    db_mock.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = []

    # Act
    response = client.post(
        "/api/v1/users/link-account",
        headers={"Authorization": f"Bearer fake-token"},
        json={"serialNumber": test_serial_number},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Device with serial number '{test_serial_number}' not found."


def test_link_account_already_linked_by_another_user(client: TestClient, db_mock: MagicMock):
    """
    Tests POST /link-account when the device is already linked to another user.
    Expects 409 Conflict.
    """
    # Arrange
    test_serial_number = "ALREADY_LINKED_SN"
    
    # Mock a device document found by serial number
    mock_device_doc = MagicMock()
    mock_device_doc.id = "device_id_2"

    # Mock the parent customer document, which already has a different lineId
    mock_customer_doc = MagicMock()
    mock_customer_doc.id = "customer_id_2"
    mock_customer_doc.to_dict.return_value = {"patientId": "patient_id_2", "lineId": "ANOTHER_USERS_LINE_ID"}

    # Configure the device document's parent reference
    mock_device_doc.reference.parent.parent.get.return_value = mock_customer_doc

    # Mock the collection_group query
    db_mock.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = [
        mock_device_doc
    ]

    # Act
    response = client.post(
        "/api/v1/users/link-account",
        headers={"Authorization": f"Bearer fake-token"},
        json={"serialNumber": test_serial_number},
    )

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "This device is already linked to another account."