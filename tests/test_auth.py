import pytest
import httpx
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException

from app.dependencies.auth import verify_line_token
from app.core.config import settings

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@patch("app.dependencies.auth.http_client.post", new_callable=AsyncMock)
async def test_verify_line_token_success(mock_post):
    """
    Tests successful token verification should return the lineId ('sub').
    """
    # Arrange
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "sub": "U1234567890abcdef1234567890ab",
        "client_id": settings.LINE_CHANNEL_ID,
    }
    # raise_for_status() does nothing on success
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    token = "valid_access_token"

    # Act
    line_id = await verify_line_token(token)

    # Assert
    assert line_id == "U1234567890abcdef1234567890ab"
    mock_post.assert_awaited_once_with(
        settings.LINE_API_VERIFY_URL,
        data={"access_token": token, "client_id": settings.LINE_CHANNEL_ID},
    )


@patch("app.dependencies.auth.http_client.post", new_callable=AsyncMock)
async def test_verify_line_token_http_error(mock_post):
    """
    Tests that an HTTPException(401) is raised for HTTP errors from LINE API.
    """
    # Arrange
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "error": "invalid_request",
        "error_description": "Invalid access token.",
    }
    # Configure raise_for_status to raise an HTTPStatusError
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized", request=AsyncMock(), response=mock_response
    )
    mock_post.return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await verify_line_token("invalid_access_token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid access token."


@patch("app.dependencies.auth.http_client.post", new_callable=AsyncMock)
async def test_verify_line_token_missing_sub(mock_post):
    """
    Tests that an HTTPException(401) is raised if 'sub' field is missing.
    """
    # Arrange
    mock_response = AsyncMock()
    mock_response.json.return_value = {"client_id": settings.LINE_CHANNEL_ID}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await verify_line_token("token_with_missing_sub")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token payload: 'sub' field missing."