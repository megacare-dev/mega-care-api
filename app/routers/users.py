from fastapi import APIRouter, Depends, HTTPException, status, Response
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.dependencies.auth import get_current_line_id
from app.dependencies.database import get_db
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

    # Query for a customer document where 'lineId' matches, limiting to 1 for efficiency.
    query = customers_ref.where(filter=FieldFilter("lineId", "==", line_id)).limit(1)

    # any(query.stream()) efficiently checks for the existence of at least one document
    # without loading its data, returning True if found, False otherwise.
    return UserStatusResponse(isLinked=any(query.stream()))


@router.post(
    "/link-account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Link LINE account to a patient record",
)
async def link_account(
    request: LinkAccountRequest,
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db),
):
    """
    Links the current LINE user to a patient record by finding the device
    with the provided serial number and updating the parent customer document.
    """
    devices_ref = db.collection_group(settings.FIRESTORE_DEVICES_SUBCOLLECTION)
    device_query = devices_ref.where(
        filter=FieldFilter("serialNumber", "==", request.serialNumber)
    ).limit(1)

    try:
        device_doc = next(device_query.stream())
    except StopIteration:
        # This happens if the stream is empty
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with serial number '{request.serialNumber}' not found.",
        )

    # Correctly get the parent customer document from the subcollection structure
    # Path: customers/{customer_id}/devices/{device_id}
    # device_doc.reference.parent is the 'devices' collection
    # device_doc.reference.parent.parent is the customer document
    customer_ref = device_doc.reference.parent.parent
    customer_doc = customer_ref.get()
    customer_data = customer_doc.to_dict()

    existing_line_id = customer_data.get("lineId")

    if existing_line_id and existing_line_id != line_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This device is already linked to another account.")

    if not existing_line_id:
        customer_ref.update({"lineId": line_id})

    return Response(status_code=status.HTTP_204_NO_CONTENT)