import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()

async def get_current_line_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Authenticates the LINE access token and returns the user's LINE ID.
    """
    line_access_token = credentials.credentials
    
    # Verify the LINE access token with LINE API
    # https://developers.line.biz/en/docs/line-login/verify-access-token/
    verify_url = settings.LINE_API_VERIFY_URL
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(verify_url, params={"access_token": line_access_token})
            response.raise_for_status() # Raise an exception for 4xx or 5xx responses
            
            data = response.json()
            
            # Check if the token is valid and belongs to the correct channel
            if data.get("client_id") != settings.LINE_CHANNEL_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid LINE Channel ID for the provided token."
                )
            
            return data.get("sub") # 'sub' field contains the LINE user ID
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"LINE API verification failed: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Network error during LINE API verification: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials: {e}")