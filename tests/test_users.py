from fastapi.testclient import TestClient
from unittest.mock import MagicMock


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
    db_mock.collection.return_value.where.assert_called_once_with(
        "lineId", "==", "MOCK_LINE_ID_FOR_TEST"
    )


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
    Tests POST /link-account successfully linking an account.
    """
    # Arrange
    # Mock for collection_group query
    mock_device_doc = MagicMock()
    mock_customer_ref = MagicMock()
    mock_device_doc.reference.parent.parent = mock_customer_ref
    db_mock.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = [
        mock_device_doc
    ]

    # Mock for customer document get()
    mock_customer_doc = MagicMock()
    mock_customer_doc.exists = True
    mock_customer_doc.to_dict.return_value = {"lineId": None}  # Account is not yet linked
    mock_customer_ref.get.return_value = mock_customer_doc

    # Act
    response = client.post(
        "/api/v1/users/link-account",
        json={"serialNumber": "VALID_SERIAL"},
        headers={"Authorization": "Bearer fake-token"},
    )

    # Assert
    assert response.status_code == 204
    mock_customer_ref.update.assert_called_once_with(
        {"lineId": "MOCK_LINE_ID_FOR_TEST"}
    )


def test_link_account_serial_not_found(client: TestClient, db_mock: MagicMock):
    """
    Tests POST /link-account when the serial number is not found.
    """
    # Arrange
    db_mock.collection_group.return_value.where.return_value.limit.return_value.stream.return_value = (
        []
    )

    # Act
    response = client.post(
        "/api/v1/users/link-account",
        json={"serialNumber": "INVALID_SERIAL"},
        headers={"Authorization": "Bearer fake-token"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Serial number not found."