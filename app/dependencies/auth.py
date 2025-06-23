import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Reusable HTTP client to improve performance by reusing connections
http_client = httpx.AsyncClient()

# Scheme for bearer token authentication
bearer_scheme = HTTPBearer(description="LINE Access Token")

async def verify_line_token(token: str) -> str:
    """
    Verifies the LINE access token against LINE's verification API.
    Returns the user's lineId (subject) if the token is valid.
    """
    try:
        # The form data to be sent to LINE API
        form_data = {"access_token": token, "client_id": settings.LINE_CHANNEL_ID}
        
        response = await http_client.post(settings.LINE_API_VERIFY_URL, data=form_data)
        
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        
        data = response.json()
        
        # According to LINE docs, 'sub' is the user ID.
        if "sub" not in data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: 'sub' field missing."
            )
            
        return data["sub"]

    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("error_description", "Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"An unexpected error occurred during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify authentication credentials."
        )

async def get_current_line_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """FastAPI dependency that secures an endpoint by verifying the Bearer token."""
    return await verify_line_token(credentials.credentials)