import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

bearer_scheme = HTTPBearer()


async def _verify_line_token(token: str) -> str:
    """
    Verifies a LINE access token by calling the LINE API.
    
    Args:
        token: The LINE access token to verify.
        
    Returns:
        The LINE user ID (sub) if the token is valid.
        
    Raises:
        HTTPException: If the token is invalid, expired, or the LINE API returns an error.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(settings.LINE_API_VERIFY_URL, params={"access_token": token})
            response.raise_for_status() # Raise an exception for 4xx or 5xx responses
            
            data = response.json()
            line_id = data.get("sub")
            if not line_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: 'sub' field missing.")
            return line_id
        except httpx.HTTPStatusError as e:
            # LINE API returns 400 for invalid/expired tokens, 401 for invalid client_id etc.
            # We map all these to 401 Unauthorized for our API.
            detail_message = e.response.json().get("error_description", "Invalid or expired access token.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail_message)
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Network error while verifying token: {e}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during token verification: {e}")


async def get_current_line_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    FastAPI dependency that extracts the bearer token, verifies it with LINE,
    and returns the user's lineId.
    """
    token = credentials.credentials
    line_id = await _verify_line_token(token)
    return line_id