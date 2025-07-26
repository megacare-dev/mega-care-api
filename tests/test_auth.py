import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

# To test the router, we need a FastAPI app instance
from fastapi import FastAPI
from app.api.v1.endpoints import auth

# --- Test Setup ---

# Create a minimal FastAPI app for testing purposes
app = FastAPI()
# Include the router we want to test
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

# Create a TestClient for making requests to our app
client = TestClient(app)

# --- Mocks and Fake Data ---
FAKE_LINE_USER_ID = "U1234567890abcdef1234567890abcdef"
FAKE_FIREBASE_UID = "firebase-uid-for-existing-user"
FAKE_LINE_CHANNEL_ID = "fake_channel_id"
FAKE_DISPLAY_NAME = "Test User"
FAKE_PICTURE_URL = "http://example.com/pic.jpg"
FAKE_EMAIL = "test@example.com"
FAKE_ID_TOKEN = "fake.id.token"
FAKE_FIREBASE_TOKEN = "fake.firebase.custom.token"

# This is what we expect jwt.decode to return
DECODED_ID_TOKEN = {
    "iss": "https://access.line.me",
    "sub": FAKE_LINE_USER_ID,
    "aud": FAKE_LINE_CHANNEL_ID,
    "exp": 1678886400,
    "iat": 1678882800,
    "name": FAKE_DISPLAY_NAME,
    "picture": FAKE_PICTURE_URL,
    "email": FAKE_EMAIL,
}

# Common setup for mocks in a fixture to avoid repetition
@pytest.fixture
def mock_line_api_flow():
    with patch('app.api.v1.endpoints.auth.httpx.AsyncClient') as mock_httpx_client, \
         patch('app.api.v1.endpoints.auth.jwt.decode') as mock_jwt_decode, \
         patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', FAKE_LINE_CHANNEL_ID), \
         patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_channel_secret'):
        
        # Mock LINE API call
        mock_line_response = MagicMock()
        mock_line_response.status_code = 200
        mock_line_response.json.return_value = {"id_token": FAKE_ID_TOKEN}
        mock_async_client_instance = AsyncMock()
        mock_async_client_instance.post.return_value = mock_line_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_async_client_instance

        # Mock JWT decoding. The test doesn't need to verify the signature,
        # just that the function is called and returns the expected payload.
        mock_jwt_decode.return_value = DECODED_ID_TOKEN
        
        yield mock_httpx_client, mock_jwt_decode

# --- Test Cases ---

@patch('app.api.v1.endpoints.auth.auth.create_custom_token')
@patch('app.api.v1.endpoints.auth.firestore.client')
def test_line_login_existing_user_success(mock_firestore_client, mock_create_token, mock_line_api_flow):
    """
    Tests the successful login flow where a user with a matching lineId
    already exists in the 'customers' collection.
    """
    # Arrange
    # 1. Mock Firestore to find an existing user
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_query = MagicMock()
    mock_db.collection.return_value.where.return_value.limit.return_value = mock_query

    mock_customer_doc = MagicMock()
    mock_customer_doc.id = FAKE_FIREBASE_UID # The doc ID is the Firebase UID
    mock_query.stream.return_value = [mock_customer_doc]

    # 2. Mock Firebase token creation
    mock_create_token.return_value = FAKE_FIREBASE_TOKEN

    request_payload = {
        "authorization_code": "some_auth_code",
        "redirect_uri": "http://localhost/callback"
    }

    response = client.post("/api/v1/auth/line", json=request_payload)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "login_success"
    assert response_data["firebase_token"] == FAKE_FIREBASE_TOKEN
    assert response_data["line_profile"] is None

    # Assert Firestore and Firebase Auth interactions
    mock_db.collection.assert_called_once_with("customers")
    mock_db.collection.return_value.where.assert_called_once_with("lineId", "==", FAKE_LINE_USER_ID)
    # Assert that custom claims are now being passed
    expected_claims = {'provider': 'line', 'line_user_id': FAKE_LINE_USER_ID}
    mock_create_token.assert_called_once_with(FAKE_FIREBASE_UID, expected_claims)


@patch('app.api.v1.endpoints.auth.auth.create_custom_token')
@patch('app.api.v1.endpoints.auth.firestore.client')
def test_line_login_new_user_registration_required(mock_firestore_client, mock_create_token, mock_line_api_flow):
    """
    Tests the registration flow where no user with a matching lineId
    is found, requiring the client to proceed with registration.
    """
    # Arrange
    # 1. Mock Firestore to find NO user
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_query = MagicMock()
    mock_db.collection.return_value.where.return_value.limit.return_value = mock_query
    mock_query.stream.return_value = [] # No documents found

    request_payload = {
        "authorization_code": "some_auth_code",
        "redirect_uri": "http://localhost/callback"
    }

    # Act
    response = client.post("/api/v1/auth/line", json=request_payload)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "registration_required"
    assert response_data["firebase_token"] is None
    
    line_profile = response_data["line_profile"]
    assert line_profile is not None
    assert line_profile["line_user_id"] == FAKE_LINE_USER_ID
    assert line_profile["display_name"] == FAKE_DISPLAY_NAME
    assert line_profile["picture_url"] == FAKE_PICTURE_URL
    assert line_profile["email"] == FAKE_EMAIL

    # Assert that no Firebase token was created
    mock_create_token.assert_not_called()