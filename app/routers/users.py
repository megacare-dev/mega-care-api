from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import firestore
from app.dependencies.auth import get_current_line_id
from app.firebase_config import get_db
from app.models.user import UserStatusResponse, LinkAccountRequest
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/status", response_model=UserStatusResponse, summary="Check user account link status")
async def get_user_status(
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    """
    Checks if the current LINE user's account is linked to a patient record.
    Requires a valid LINE access token in the Authorization header.
    """
    customers_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION)
    
    # Query for a customer document where 'lineId' field matches the current line_id
    query = customers_ref.where("lineId", "==", line_id).limit(1)
    docs = query.stream()
    
    is_linked = False
    for doc in docs:
        is_linked = True
        break # Found at least one linked account
    
    return UserStatusResponse(isLinked=is_linked)

@router.post("/link-account", summary="Link LINE account with CPAP serial number")
async def link_account(
    request: LinkAccountRequest,
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    """
    Links the current LINE user's account (`lineId`) with a patient record
    by finding a device with the provided `serialNumber`.
    
    If successful, updates the corresponding customer document with the `lineId`.
    """
    devices_ref = db.collection_group(settings.FIRESTORE_DEVICES_SUBCOLLECTION)
    
    # Find the device by serial number
    device_query = devices_ref.where("serialNumber", "==", request.serialNumber).limit(1)
    device_docs = list(device_query.stream())
    
    if not device_docs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found or invalid serial number.")
    
    device_doc = device_docs[0]
    customer_ref = device_doc.reference.parent.parent # Get the parent customer document reference
    
    # Update the customer document with the lineId
    customer_ref.update({"lineId": line_id})
    
    return {"message": "Account linked successfully."}