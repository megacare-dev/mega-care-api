import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock, call
from datetime import datetime

# To test the router, we need a FastAPI app instance
from fastapi import FastAPI
from app.api.v1.endpoints import auth
# Import the actual exception to be raised by the mock
from firebase_admin.auth import UserNotFoundError

# --- Test Setup ---

# Create a minimal FastAPI app for testing purposes
app = FastAPI()
# Include the router we want to test
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

# Create a TestClient for making requests to our app
client = TestClient(app)

# --- Mocks and Fake Data ---
FAKE_LINE_USER_ID = "U1234567890abcdef1234567890abcdef"
FAKE_DISPLAY_NAME = "Test User"
FAKE_PICTURE_URL = "http://example.com/pic.jpg"
FAKE_ID_TOKEN = "fake.id.token"
FAKE_FIREBASE_TOKEN = "fake.firebase.custom.token"

# This is what we expect jwt.decode to return
DECODED_ID_TOKEN = {
    "iss": "https://access.line.me",
    "sub": FAKE_LINE_USER_ID,
    "aud": "1234567890",
    "exp": 1678886400,
    "iat": 1678882800,
    "name": FAKE_DISPLAY_NAME,
    "picture": FAKE_PICTURE_URL,
}

# --- Test Cases ---

@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_channel_secret')
@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', 'fake_channel_id')
@patch('app.api.v1.endpoints.auth.firestore.client')
@patch('app.api.v1.endpoints.auth.auth.create_custom_token')
@patch('app.api.v1.endpoints.auth.auth.create_user')
@patch('app.api.v1.endpoints.auth.auth.get_user')
@patch('app.api.v1.endpoints.auth.jwt.decode')
@patch('app.api.v1.endpoints.auth.httpx.AsyncClient')
def test_line_login_new_user_creates_firestore_profile(
    mock_httpx_client, mock_jwt_decode, mock_get_user, mock_create_user, mock_create_token, mock_firestore_client
):
    """
    Tests that when a new user logs in via LINE, a corresponding
    customer profile is created in Firestore.
    """
    # Arrange
    # 1. Mock LINE API call
    mock_line_response = MagicMock()
    mock_line_response.status_code = 200
    mock_line_response.json.return_value = {"id_token": FAKE_ID_TOKEN}
    # httpx.AsyncClient() returns a context manager, so we mock its async enter/exit
    mock_async_client_instance = AsyncMock()
    mock_async_client_instance.post.return_value = mock_line_response
    mock_httpx_client.return_value.__aenter__.return_value = mock_async_client_instance

    # 2. Mock JWT decoding
    mock_jwt_decode.return_value = DECODED_ID_TOKEN

    # 3. Mock Firebase Auth for a NEW user
    mock_get_user.side_effect = UserNotFoundError("User not found")
    
    mock_new_user = MagicMock()
    mock_new_user.uid = FAKE_LINE_USER_ID
    mock_create_user.return_value = mock_new_user
    mock_create_token.return_value = FAKE_FIREBASE_TOKEN

    # 4. Mock Firestore client
    mock_db = MagicMock()
    mock_firestore_client.return_value = mock_db
    mock_customer_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_customer_ref

    request_payload = {
        "authorization_code": "some_auth_code",
        "redirect_uri": "http://localhost/callback"
    }

    # Act
    response = client.post("/api/v1/auth/line", json=request_payload)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"firebase_token": FAKE_FIREBASE_TOKEN}

    # Assert Firebase Auth interactions
    mock_get_user.assert_called_once_with(FAKE_LINE_USER_ID)
    mock_create_user.assert_called_once_with(
        uid=FAKE_LINE_USER_ID,
        display_name=FAKE_DISPLAY_NAME,
        photo_url=FAKE_PICTURE_URL
    )
    mock_create_token.assert_called_once_with(FAKE_LINE_USER_ID)

    # Assert Firestore interaction (THE CORE OF THIS TEST)
    mock_db.collection.assert_called_once_with("customers")
    mock_db.collection.return_value.document.assert_called_once_with(FAKE_LINE_USER_ID)
    
    mock_customer_ref.set.assert_called_once()
    call_args, _ = mock_customer_ref.set.call_args
    data_sent_to_firestore = call_args[0]
    
    assert data_sent_to_firestore["lineId"] == FAKE_LINE_USER_ID
    assert data_sent_to_firestore["displayName"] == FAKE_DISPLAY_NAME
    assert data_sent_to_firestore["status"] == "Active"
    assert "createDate" in data_sent_to_firestore
    assert isinstance(data_sent_to_firestore["createDate"], datetime)
    assert "lineProfile" in data_sent_to_firestore
    assert data_sent_to_firestore["lineProfile"]["userId"] == FAKE_LINE_USER_ID
    assert data_sent_to_firestore["lineProfile"]["displayName"] == FAKE_DISPLAY_NAME
    assert data_sent_to_firestore["lineProfile"]["pictureUrl"] == FAKE_PICTURE_URL


@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_channel_secret')
@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', 'fake_channel_id')
@patch('app.api.v1.endpoints.auth.firestore.client')
@patch('app.api.v1.endpoints.auth.auth.create_custom_token')
@patch('app.api.v1.endpoints.auth.auth.create_user')
@patch('app.api.v1.endpoints.auth.auth.get_user')
@patch('app.api.v1.endpoints.auth.jwt.decode')
@patch('app.api.v1.endpoints.auth.httpx.AsyncClient')
def test_line_login_existing_user_does_not_create_firestore_profile(
    mock_httpx_client, mock_jwt_decode, mock_get_user, mock_create_user, mock_create_token, mock_firestore_client
):
    """
    Tests that when an existing user logs in via LINE, a new
    Firestore profile is NOT created.
    """
    # Arrange
    mock_line_response = MagicMock()
    mock_line_response.status_code = 200
    mock_line_response.json.return_value = {"id_token": FAKE_ID_TOKEN}
    mock_async_client_instance = AsyncMock()
    mock_async_client_instance.post.return_value = mock_line_response
    mock_httpx_client.return_value.__aenter__.return_value = mock_async_client_instance

    mock_jwt_decode.return_value = DECODED_ID_TOKEN

    mock_existing_user = MagicMock()
    mock_existing_user.uid = FAKE_LINE_USER_ID
    mock_get_user.return_value = mock_existing_user
    mock_create_token.return_value = FAKE_FIREBASE_TOKEN

    mock_customer_ref = mock_firestore_client.return_value.collection.return_value.document.return_value

    # Act
    response = client.post("/api/v1/auth/line", json={"authorization_code": "code", "redirect_uri": "uri"})

    # Assert
    assert response.status_code == 200
    mock_get_user.assert_called_once_with(FAKE_LINE_USER_ID)
    mock_create_user.assert_not_called()
    mock_customer_ref.set.assert_not_called()