import os
from typing import Dict

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# This dependency is specific to LINE Login verification.
security = HTTPBearer()

LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_API_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"


def _verify_line_token(token: str) -> Dict:
    """
    Internal function to verify a LINE access token.
    Communicates with the LINE Platform.
    """
    if not LINE_CHANNEL_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINE_CHANNEL_ID is not configured on the server.",
        )

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"id_token": token, "client_id": LINE_CHANNEL_ID}

    response = requests.post(LINE_API_VERIFY_URL, headers=headers, data=data)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid LINE token: {response.json().get('error_description', 'Verification failed')}",
        )

    return response.json()


def get_current_line_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get the current user's LINE ID from a bearer token.
    Verifies the token and returns the user's LINE ID ('sub').
    """
    try:
        token = credentials.credentials
        decoded_token = _verify_line_token(token)
        line_user_id = decoded_token.get("sub")
        if not line_user_id:
            raise HTTPException(status_code=401, detail="LINE user ID not found in token")
        return line_user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )