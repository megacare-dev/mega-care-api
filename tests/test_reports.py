from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from google.cloud import firestore

# Mock data for a report
MOCK_RAW_DATA = {"usage_hours": 8.2, "leak_rate": 10.5, "ahi": 4.1}
MOCK_REPORT_DOC_ID = "2023-10-27"

def setup_customer_find_mock(db_mock: MagicMock):
    """Helper to mock the customer lookup part. Returns the db_mock and the mocked customer document."""
    mock_customer_doc = MagicMock()
    mock_customer_doc.id = "customer_123"
    # This mock is for the _find_customer_ref helper
    db_mock.collection.return_value.where.return_value.limit.return_value.stream.return_value = [mock_customer_doc]
    return db_mock, mock_customer_doc

def test_get_report_by_date_success(client: TestClient, db_mock: MagicMock):
    """
    Tests successful retrieval of a report by a specific date.
    """
    # Arrange
    db_mock, mock_customer_doc = setup_customer_find_mock(db_mock)

    mock_report_doc = MagicMock()
    mock_report_doc.exists = True # Ensure the document is considered existing
    mock_report_doc.to_dict.return_value = {"rawData": MOCK_RAW_DATA} # Ensure to_dict returns a *real* dict
    
    mock_customer_doc.reference.collection.return_value.document.return_value.get.return_value = mock_report_doc

    # Act
    response = client.get(f"/api/v1/reports/{MOCK_REPORT_DOC_ID}", headers={"Authorization": "Bearer fake-token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["rawData"] == MOCK_RAW_DATA
    assert data["analysis"]["usage"]["status"] == "normal"
    assert "overallRecommendation" in data

def test_get_report_by_date_not_found(client: TestClient, db_mock: MagicMock):
    """
    Tests case where a report for a specific date is not found.
    """
    # Arrange
    db_mock, mock_customer_doc = setup_customer_find_mock(db_mock)

    mock_report_doc = MagicMock()
    mock_report_doc.exists = False
    
    mock_customer_doc.reference.collection.return_value.document.return_value.get.return_value = mock_report_doc

    # Act
    response = client.get(f"/api/v1/reports/{MOCK_REPORT_DOC_ID}", headers={"Authorization": "Bearer fake-token"})

    # Assert
    assert response.status_code == 404
    assert f"Report for date {MOCK_REPORT_DOC_ID} not found" in response.json()["detail"]

def test_get_latest_report_success(client: TestClient, db_mock: MagicMock):
    """
    Tests successful retrieval of the latest report.
    """
    # Arrange
    db_mock, mock_customer_doc = setup_customer_find_mock(db_mock)

    mock_latest_report_doc = MagicMock()
    mock_latest_report_doc.to_dict.return_value = {"rawData": MOCK_RAW_DATA} # Ensure to_dict returns a *real* dict

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_latest_report_doc]
    mock_customer_doc.reference.collection.return_value.order_by.return_value.limit.return_value = mock_query

    # Act
    response = client.get("/api/v1/reports/latest", headers={"Authorization": "Bearer fake-token"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["rawData"] == MOCK_RAW_DATA
    assert data["analysis"]["leak"]["status"] == "normal"

def test_get_latest_report_no_reports_found(client: TestClient, db_mock: MagicMock):
    """
    Tests case where no reports exist for the user.
    """
    # Arrange
    db_mock, mock_customer_doc = setup_customer_find_mock(db_mock)
    
    mock_query = MagicMock()
    mock_query.stream.return_value = [] # No documents returned
    mock_customer_doc.reference.collection.return_value.order_by.return_value.limit.return_value = mock_query

    # Act
    response = client.get("/api/v1/reports/latest", headers={"Authorization": "Bearer fake-token"})

    # Assert
    assert response.status_code == 404
    assert "No reports found for this user" in response.json()["detail"]