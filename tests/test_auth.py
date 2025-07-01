import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

# The import that was failing, now pointing to the new module
from app.dependencies.auth import _verify_line_token

# A dummy token for testing purposes
FAKE_TOKEN = "fake-line-id-token"
FAKE_LINE_USER_ID = "U1234567890abcdef1234567890abcdef"


@patch('app.dependencies.auth.requests.post')
@patch('app.dependencies.auth.LINE_CHANNEL_ID', 'mock_channel_id')
def test_verify_line_token_success(mock_post):
    """
    Tests successful verification of a LINE token.
    """
    # Mock the response from LINE's API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "iss": "https://access.line.me",
        "sub": FAKE_LINE_USER_ID,
        "aud": "mock_channel_id",
    }
    mock_post.return_value = mock_response

    # Call the function
    decoded_token = _verify_line_token(FAKE_TOKEN)

    # Assertions
    assert decoded_token is not None
    assert decoded_token["sub"] == FAKE_LINE_USER_ID
    mock_post.assert_called_once()


@patch('app.dependencies.auth.requests.post')
@patch('app.dependencies.auth.LINE_CHANNEL_ID', 'mock_channel_id')
def test_verify_line_token_failure(mock_post):
    """
    Tests failed verification of a LINE token.
    """
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error_description": "invalid id_token"}
    mock_post.return_value = mock_response

    with pytest.raises(HTTPException) as excinfo:
        _verify_line_token(FAKE_TOKEN)

    assert excinfo.value.status_code == 401
    assert "invalid id_token" in excinfo.value.detail