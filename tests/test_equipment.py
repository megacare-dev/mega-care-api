from fastapi.testclient import TestClient
from unittest.mock import MagicMock

def test_get_equipment_success(client: TestClient, db_mock: MagicMock):
    """
    Tests successful retrieval of a user's equipment.
    """
    # Arrange
    # 1. Mock finding the customer by lineId
    mock_customer_doc = MagicMock()
    mock_customer_doc.id = "customer_123"
    db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = [mock_customer_doc]

    # 2. Mock finding devices in the sub-collection
    mock_device_doc_1 = MagicMock()
    mock_device_doc_1.to_dict.return_value = {"serialNumber": "SN1", "model": "AirSense 10"}
    mock_device_doc_2 = MagicMock()
    mock_device_doc_2.to_dict.return_value = {"serialNumber": "SN2", "model": "AirSense 11"}
    
    mock_devices_collection_ref = MagicMock()
    mock_devices_collection_ref.stream.return_value = [mock_device_doc_1, mock_device_doc_2]
    
    db_mock.collection.return_value.document.return_value.collection.return_value = mock_devices_collection_ref

    # Act
    response = client.get("/api/v1/equipment", headers={"Authorization": "Bearer fake-token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert len(data["devices"]) == 2
    assert data["devices"][0]["serialNumber"] == "SN1"
    assert data["devices"][1]["model"] == "AirSense 11"

def test_get_equipment_no_linked_account(client: TestClient, db_mock: MagicMock):
    """
    Tests case where the lineId is not linked to any customer.
    """
    # Arrange
    db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = []

    # Act
    response = client.get("/api/v1/equipment", headers={"Authorization": "Bearer fake-token"})

    # Assert
    assert response.status_code == 404
    assert "No linked customer profile found" in response.json()["detail"]