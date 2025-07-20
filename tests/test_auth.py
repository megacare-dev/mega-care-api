import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
import httpx

# The function to test
from app.dependencies.auth import get_current_user
# --- New setup for testing the auth router ---
from fastapi import FastAPI
from app.api.v1.endpoints import auth as auth_router

app = FastAPI()
app.include_router(auth_router.router, prefix="/api/v1/auth")
# We need to mock the firebase auth module
from firebase_admin import auth

# A dummy token for testing purposes
FAKE_TOKEN = "fake-firebase-id-token"
FAKE_DECODED_TOKEN = {"uid": "some_firebase_uid", "email": "user@example.com"}

client = TestClient(app)


@patch('app.dependencies.auth.auth.verify_id_token')
def test_get_current_user_success(mock_verify_id_token):
    """
    Tests successful verification of a Firebase ID token.
    """
    # Arrange
    mock_verify_id_token.return_value = FAKE_DECODED_TOKEN
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=FAKE_TOKEN)

    # Act
    user = get_current_user(credentials)

    # Assertions
    assert user == FAKE_DECODED_TOKEN
    mock_verify_id_token.assert_called_once_with(FAKE_TOKEN)


@patch('app.dependencies.auth.auth.verify_id_token')
def test_get_current_user_invalid_token(mock_verify_id_token):
    """
    Tests that an HTTPException is raised for an invalid token.
    """
    # Arrange
    mock_verify_id_token.side_effect = auth.InvalidIdTokenError("The token is invalid.")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        get_current_user(credentials)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid Firebase ID token" in excinfo.value.detail


@patch('app.dependencies.auth.auth.verify_id_token')
def test_get_current_user_generic_exception(mock_verify_id_token):
    """
    Tests that a generic exception during verification raises an HTTPException.
    """
    # Arrange
    mock_verify_id_token.side_effect = Exception("A generic error occurred.")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=FAKE_TOKEN)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        get_current_user(credentials)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authentication credentials" in excinfo.value.detail


# --- New Tests for LINE Login Endpoint ---

FAKE_LINE_USER_ID = "U1234567890abcdef1234567890abcdef"
FAKE_LINE_ID_TOKEN_PAYLOAD = {
    "iss": "https://access.line.me",
    "sub": FAKE_LINE_USER_ID,
    "aud": "1234567890",
    "exp": 1504169092,
    "iat": 1504165492,
    "name": "Test User",
    "picture": "http://example.com/pic.jpg"
}
FAKE_ENCODED_LINE_ID_TOKEN = "fake.encoded.id_token"
FAKE_FIREBASE_CUSTOM_TOKEN = "fake-firebase-custom-token"

@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_secret')
@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', 'fake_id')
@patch('app.api.v1.endpoints.auth.httpx.AsyncClient')
@patch('app.api.v1.endpoints.auth.jwt.decode')
@patch('app.api.v1.endpoints.auth.auth')
def test_line_login_new_user_success(mock_firebase_auth, mock_jwt_decode, mock_async_client):
    """
    Tests successful LINE login flow for a new user.
    - Exchanges auth code for LINE token.
    - Decodes LINE ID token.
    - Finds no existing Firebase user.
    - Creates a new Firebase user.
    - Creates and returns a Firebase custom token.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id_token": FAKE_ENCODED_LINE_ID_TOKEN, "access_token": "some_access_token"}
    mock_async_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

    mock_jwt_decode.return_value = FAKE_LINE_ID_TOKEN_PAYLOAD

    mock_firebase_auth.UserNotFoundError = auth.UserNotFoundError
    mock_firebase_auth.get_user.side_effect = mock_firebase_auth.UserNotFoundError("User not found")
    
    mock_new_user = MagicMock()
    mock_new_user.uid = FAKE_LINE_USER_ID
    mock_firebase_auth.create_user.return_value = mock_new_user
    
    mock_firebase_auth.create_custom_token.return_value = FAKE_FIREBASE_CUSTOM_TOKEN

    request_payload = {"authorization_code": "some-auth-code", "redirect_uri": "https://example.com/callback"}

    # Act
    response = client.post("/api/v1/auth/line", json=request_payload)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"firebase_token": FAKE_FIREBASE_CUSTOM_TOKEN}

    mock_jwt_decode.assert_called_once_with(FAKE_ENCODED_LINE_ID_TOKEN, options={"verify_signature": False})
    mock_firebase_auth.get_user.assert_called_once_with(FAKE_LINE_USER_ID)
    mock_firebase_auth.create_user.assert_called_once_with(
        uid=FAKE_LINE_USER_ID,
        display_name=FAKE_LINE_ID_TOKEN_PAYLOAD["name"],
        photo_url=FAKE_LINE_ID_TOKEN_PAYLOAD["picture"]
    )
    mock_firebase_auth.create_custom_token.assert_called_once_with(FAKE_LINE_USER_ID)


@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_secret')
@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', 'fake_id')
@patch('app.api.v1.endpoints.auth.httpx.AsyncClient')
@patch('app.api.v1.endpoints.auth.jwt.decode')
@patch('app.api.v1.endpoints.auth.auth')
def test_line_login_existing_user_success(mock_firebase_auth, mock_jwt_decode, mock_async_client):
    """
    Tests successful LINE login flow for an existing user.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id_token": FAKE_ENCODED_LINE_ID_TOKEN}
    mock_async_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

    mock_jwt_decode.return_value = FAKE_LINE_ID_TOKEN_PAYLOAD

    mock_existing_user = MagicMock()
    mock_existing_user.uid = FAKE_LINE_USER_ID
    mock_firebase_auth.get_user.return_value = mock_existing_user
    mock_firebase_auth.create_custom_token.return_value = FAKE_FIREBASE_CUSTOM_TOKEN

    request_payload = {"authorization_code": "some-auth-code", "redirect_uri": "https://example.com/callback"}

    # Act
    response = client.post("/api/v1/auth/line", json=request_payload)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"firebase_token": FAKE_FIREBASE_CUSTOM_TOKEN}
    mock_firebase_auth.create_user.assert_not_called()


@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_secret')
@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', 'fake_id')
@patch('app.api.v1.endpoints.auth.httpx.AsyncClient')
def test_line_login_line_api_fails(mock_async_client):
    """
    Tests that a 400 is returned if the LINE API call fails.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "invalid_grant", "error_description": "invalid authorization code"}
    mock_http_error = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)
    mock_async_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=mock_http_error)

    # Act
    response = client.post("/api/v1/auth/line", json={"authorization_code": "invalid-code", "redirect_uri": "https://example.com/callback"})

    # Assert
    assert response.status_code == 400
    assert "invalid authorization code" in response.json()["detail"]


@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_SECRET', 'fake_secret')
@patch('app.api.v1.endpoints.auth.LINE_CHANNEL_ID', 'fake_id')
@patch('app.api.v1.endpoints.auth.httpx.AsyncClient')
@patch('app.api.v1.endpoints.auth.jwt.decode')
def test_get_line_profile_success(mock_jwt_decode, mock_async_client):
    """
    Tests successful retrieval of a LINE profile from an authorization code.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id_token": FAKE_ENCODED_LINE_ID_TOKEN, "access_token": "some_access_token"}
    mock_async_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

    mock_jwt_decode.return_value = FAKE_LINE_ID_TOKEN_PAYLOAD

    request_payload = {"authorization_code": "some-auth-code", "redirect_uri": "https://example.com/callback"}

    # Act
    response = client.post("/api/v1/auth/line/profile", json=request_payload)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["line_user_id"] == FAKE_LINE_USER_ID
    assert response_data["display_name"] == FAKE_LINE_ID_TOKEN_PAYLOAD["name"]
    assert response_data["picture_url"] == FAKE_LINE_ID_TOKEN_PAYLOAD["picture"]
    mock_jwt_decode.assert_called_once_with(FAKE_ENCODED_LINE_ID_TOKEN, options={"verify_signature": False})