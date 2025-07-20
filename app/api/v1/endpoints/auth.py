import os
import httpx
import jwt
import logging
from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel, Field
from firebase_admin import auth

router = APIRouter()

# --- Schemas ---

class LineLoginRequest(BaseModel):
    authorization_code: str = Field(..., description="The authorization code from LINE Login.")
    redirect_uri: str = Field(..., description="The redirect URI used in the initial login request.")

class FirebaseCustomTokenResponse(BaseModel):
    firebase_token: str = Field(..., description="The Firebase custom token for the client to sign in with.")

class LineProfileResponse(BaseModel):
    line_user_id: str = Field(..., description="The user's unique ID from LINE.")
    display_name: str | None = Field(None, description="The user's display name from their LINE profile.")
    picture_url: str | None = Field(None, description="URL of the user's profile image from LINE.")

# --- Environment Variables ---
# These should be set in your deployment environment (e.g., Cloud Run environment variables)
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

@router.post("/line", response_model=FirebaseCustomTokenResponse)
async def line_login(payload: LineLoginRequest):
    """
    Exchanges a LINE authorization code for a Firebase Custom Token.

    1.  Receives an authorization code from the client.
    2.  Exchanges the code for a LINE access token and ID token.
    3.  Verifies the ID token and extracts the LINE User ID.
    4.  Finds or creates a user in Firebase Authentication based on the LINE User ID.
    5.  Generates a Firebase Custom Token for that user.
    6.  Returns the Firebase Custom Token to the client.
    """
    if not LINE_CHANNEL_ID or not LINE_CHANNEL_SECRET:
        logging.error("LINE Channel ID or Secret is not configured on the server.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is not configured."
        )

    # 2. Exchange code for tokens
    token_payload = {
        "grant_type": "authorization_code",
        "code": payload.authorization_code,
        "redirect_uri": payload.redirect_uri,
        "client_id": LINE_CHANNEL_ID,
        "client_secret": LINE_CHANNEL_SECRET,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(LINE_TOKEN_URL, data=token_payload)
            response.raise_for_status()
            line_data = response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('error_description', 'Unknown LINE API error')
            logging.error(f"LINE token exchange failed: {e.response.status_code} - {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange LINE authorization code: {error_detail}"
            )

    # 3. Decode ID token and get LINE User ID (sub)
    try:
        # Since we just received the token from a direct server-to-server call,
        # we can decode it without signature verification for simplicity.
        # A full implementation might verify the signature using the channel secret.
        id_token = line_data.get("id_token")
        if not id_token:
            raise ValueError("id_token not found in LINE response")
        
        decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})
        line_user_id = decoded_id_token.get("sub")
        if not line_user_id:
            raise ValueError("LINE User ID (sub) not found in ID token.")
        
        display_name = decoded_id_token.get("name")
        picture_url = decoded_id_token.get("picture")

    except Exception as e:
        logging.error(f"Failed to decode or process LINE ID token: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token from LINE.")

    # 4. Find or create Firebase user
    try:
        firebase_user = auth.get_user(line_user_id)
        logging.info(f"Found existing Firebase user for LINE ID: {line_user_id}")
    except auth.UserNotFoundError:
        logging.info(f"Creating new Firebase user for LINE ID: {line_user_id}")
        firebase_user = auth.create_user(
            uid=line_user_id,
            display_name=display_name,
            photo_url=picture_url
        )
    except Exception as e:
        logging.error(f"Firebase user lookup/creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process user account.")

    # 5. Generate Firebase Custom Token
    try:
        custom_token = auth.create_custom_token(firebase_user.uid)
    except Exception as e:
        logging.error(f"Firebase custom token creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate authentication token.")

    return FirebaseCustomTokenResponse(firebase_token=custom_token)


@router.post("/line/profile", response_model=LineProfileResponse)
async def get_line_profile(payload: LineLoginRequest):
    """
    Exchanges a LINE authorization code for the user's LINE profile data.
    This endpoint does NOT create or interact with a Firebase user.
    """
    if not LINE_CHANNEL_ID or not LINE_CHANNEL_SECRET:
        logging.error("LINE Channel ID or Secret is not configured on the server.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is not configured."
        )

    # Exchange code for tokens
    token_payload = {
        "grant_type": "authorization_code",
        "code": payload.authorization_code,
        "redirect_uri": payload.redirect_uri,
        "client_id": LINE_CHANNEL_ID,
        "client_secret": LINE_CHANNEL_SECRET,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(LINE_TOKEN_URL, data=token_payload)
            response.raise_for_status()
            line_data = response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('error_description', 'Unknown LINE API error')
            logging.error(f"LINE token exchange failed: {e.response.status_code} - {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange LINE authorization code: {error_detail}"
            )

    # Decode ID token and get LINE User profile
    try:
        id_token = line_data.get("id_token")
        if not id_token:
            raise ValueError("id_token not found in LINE response")

        decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})

        line_user_id = decoded_id_token.get("sub")
        if not line_user_id:
            raise ValueError("LINE User ID (sub) not found in ID token.")

        return LineProfileResponse(line_user_id=line_user_id, display_name=decoded_id_token.get("name"), picture_url=decoded_id_token.get("picture"))
    except Exception as e:
        logging.error(f"Failed to decode or process LINE ID token: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token from LINE.")