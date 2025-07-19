import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

# The function to test
from app.dependencies.auth import get_current_user
# We need to mock the firebase auth module
from firebase_admin import auth

# A dummy token for testing purposes
FAKE_TOKEN = "fake-firebase-id-token"
FAKE_DECODED_TOKEN = {"uid": "some_firebase_uid", "email": "user@example.com"}


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