import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies.auth import _verify_line_token, get_current_line_id
from app.core.config import settings

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@patch("app.dependencies.auth.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_verify_line_token_success(mock_get):
    """
    Tests successful token verification should return the lineId ('sub').
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "sub": "U1234567890abcdef1234567890ab",
        "client_id": settings.LINE_CHANNEL_ID,
    }
    # raise_for_status() does nothing on success
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    token = "valid_access_token"

    # Act
    line_id = await _verify_line_token(token)

    # Assert
    assert line_id == "U1234567890abcdef1234567890ab"
    mock_get.assert_awaited_once_with(
        settings.LINE_API_VERIFY_URL,
        params={"access_token": token},
    )


@patch("app.dependencies.auth.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_verify_line_token_http_error(mock_get):
    """
    Tests that an HTTPException(401) is raised for HTTP errors from LINE API.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "error": "invalid_request",
        "error_description": "Invalid access token.",
    }
    # Configure raise_for_status to raise an HTTPStatusError
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized", request=MagicMock(), response=mock_response
    )
    mock_get.return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await _verify_line_token("invalid_access_token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid access token."


@patch("app.dependencies.auth.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_verify_line_token_missing_sub(mock_get):
    """
    Tests that an HTTPException(401) is raised if 'sub' field is missing.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"client_id": settings.LINE_CHANNEL_ID}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await _verify_line_token("token_with_missing_sub")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token payload: 'sub' field missing."


# --- Tests for get_current_line_id dependency ---


@patch("app.dependencies.auth._verify_line_token", new_callable=AsyncMock)
async def test_get_current_line_id_success(mock_verify):
    """
    Tests that get_current_line_id successfully returns a line_id
    when given valid credentials.
    """
    # Arrange
    mock_verify.return_value = "U1234567890"
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake_token")

    # Act
    line_id = await get_current_line_id(mock_credentials)

    # Assert
    assert line_id == "U1234567890"
    mock_verify.assert_awaited_once_with("fake_token")


@patch("app.dependencies.auth._verify_line_token", new_callable=AsyncMock)
async def test_get_current_line_id_verification_fails(mock_verify):
    """
    Tests that get_current_line_id propagates HTTPException from _verify_line_token.
    """
    # Arrange
    mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid Token")
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_line_id(mock_credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid Token"