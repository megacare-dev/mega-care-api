import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()

async def _verify_line_token(token: str) -> str:
    """
    Internal function to verify a LINE access token and return the user's LINE ID ('sub').
    Raises HTTPException on failure.
    """
    verify_url = settings.LINE_API_VERIFY_URL
    try:
        async with httpx.AsyncClient() as client:
            # Note: The official LINE docs use GET for token verification
            response = await client.get(verify_url, params={"access_token": token})
            response.raise_for_status()  # Raise an exception for 4xx or 5xx responses
            data = response.json()
    except httpx.HTTPStatusError as e:
        # Try to parse a meaningful error from LINE's response
        error_detail = e.response.json().get("error_description", f"LINE API verification failed: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Network error during LINE API verification: {e}")
    except Exception as e:
        # Catch other potential errors like JSON decoding errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not process LINE API response: {e}")

    # Perform validation *after* the network call is successful
    if data.get("client_id") != settings.LINE_CHANNEL_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid LINE Channel ID for the provided token."
        )

    line_id = data.get("sub")
    if not line_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: 'sub' field missing."
        )
    return line_id

async def get_current_line_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency that authenticates the LINE access token from the Authorization header
    and returns the user's LINE ID.
    """
    return await _verify_line_token(credentials.credentials)