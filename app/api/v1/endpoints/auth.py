import os
import httpx
import jwt
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import auth, firestore

router = APIRouter()

# --- Schemas ---

class LineLoginRequest(BaseModel):
    authorization_code: str = Field(..., description="The authorization code from LINE Login.")
    redirect_uri: str = Field(..., description="The redirect URI used in the initial login request.")

class LineProfileResponse(BaseModel):
    line_user_id: str = Field(..., description="The user's unique ID from LINE.")
    display_name: str | None = Field(None, description="The user's display name from their LINE profile.")
    picture_url: str | None = Field(None, description="URL of the user's profile image from LINE.")
    email: str | None = Field(None, description="The user's email address from LINE.")

class LineLoginResponse(BaseModel):
    status: str = Field(..., description="Either 'login_success' or 'registration_required'.")
    firebase_token: str | None = Field(default=None, description="The Firebase custom token, present on successful login.")
    line_profile: LineProfileResponse | None = Field(default=None, description="The user's LINE profile, present if registration is required.")

# --- Environment Variables ---
# These should be set in your deployment environment (e.g., Cloud Run environment variables)
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

@router.post("/line", response_model=LineLoginResponse)
async def line_login(payload: LineLoginRequest):
    """
    Handles the LINE login/register flow.

    1.  Receives an authorization code from the client.
    2.  Exchanges the code for a LINE access token and ID token.
    3.  Verifies the ID token and extracts the LINE User ID.
    4.  Searches the `customers` collection in Firestore for a matching `lineId`.
    5.  If a user is found, it returns a Firebase Custom Token for login.
    6.  If no user is found, it returns a 'registration_required' status with the user's LINE profile data, signaling the client to proceed to a registration screen.
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
        id_token = line_data.get("id_token")
        if not id_token:
            raise ValueError("id_token not found in LINE response")
        
        # Security Best Practice: Verify the ID token's signature and claims.
        # This ensures the token is authentic, was issued by LINE for your channel,
        # and has not expired.
        decoded_id_token = jwt.decode(
            id_token,
            LINE_CHANNEL_SECRET,
            algorithms=["HS256"],
            audience=LINE_CHANNEL_ID,
            issuer="https://access.line.me"
        )
        line_user_id = decoded_id_token.get("sub")
        if not line_user_id:
            raise ValueError("LINE User ID (sub) not found in ID token.")
        
        display_name = decoded_id_token.get("name")
        picture_url = decoded_id_token.get("picture")
        email = decoded_id_token.get("email")

    except Exception as e:
        logging.error(f"Failed to decode or process LINE ID token: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token from LINE.")

    # 4. Search the `customers` collection for a matching `lineId`.
    db = firestore.client()
    customers_ref = db.collection("customers")
    # Note: This query requires a Firestore index on the 'lineId' field.
    query = customers_ref.where(filter=FieldFilter("lineId", "==", line_user_id)).limit(1)
    
    try:
        docs = list(query.stream())
        if docs:
            # 5. If user exists (Login Flow)
            customer_doc = docs[0]
            firebase_uid = customer_doc.id # The document ID is the Firebase UID

            logging.info(f"Found existing customer profile for LINE ID {line_user_id} with Firebase UID {firebase_uid}. Proceeding with login.")
            
            # 6. Generate a Firebase Custom Token for that user.
            try:
                # Add custom claims to identify the login provider in the Firebase token
                developer_claims = {'provider': 'line', 'line_user_id': line_user_id}
                custom_token = auth.create_custom_token(firebase_uid, developer_claims)
                return LineLoginResponse(status="login_success", firebase_token=custom_token)
            except Exception as e:
                logging.error(f"Firebase custom token creation failed for UID {firebase_uid}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate authentication token.")
        else:
            # 7. If user does not exist (Registration Flow)
            logging.info(f"No customer profile found for LINE ID {line_user_id}. Signaling for registration.")
            
            line_profile_data = LineProfileResponse(
                line_user_id=line_user_id,
                display_name=display_name,
                picture_url=picture_url,
                email=email
            )
            
            return LineLoginResponse(status="registration_required", line_profile=line_profile_data)
    except Exception as e:
        logging.error(f"Firestore query or processing failed for LINE login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred during the login process."
        )


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

        # Security Best Practice: Verify the ID token's signature and claims.
        decoded_id_token = jwt.decode(
            id_token,
            LINE_CHANNEL_SECRET,
            algorithms=["HS256"],
            audience=LINE_CHANNEL_ID,
            issuer="https://access.line.me"
        )

        line_user_id = decoded_id_token.get("sub")
        if not line_user_id:
            raise ValueError("LINE User ID (sub) not found in ID token.")

        return LineProfileResponse(
            line_user_id=line_user_id,
            display_name=decoded_id_token.get("name"),
            picture_url=decoded_id_token.get("picture"),
            email=decoded_id_token.get("email")
        )
    except Exception as e:
        logging.error(f"Failed to decode or process LINE ID token: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token from LINE.")