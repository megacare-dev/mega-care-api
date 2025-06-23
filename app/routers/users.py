from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1.client import Client

from app.dependencies.auth import get_current_line_id
from app.dependencies.database import db_dependency
from app.models.user import LinkAccountRequest, UserStatusResponse
from app.core.config import settings

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
)

@router.get("/status", response_model=UserStatusResponse)
async def get_user_status(
    line_id: str = Depends(get_current_line_id),
    db: Client = Depends(db_dependency)
):
    """
    Checks if the current user's LINE account is linked to a customer profile.
    """
    try:
        customers_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION)
        query = customers_ref.where("lineId", "==", line_id).limit(1)
        docs = list(query.stream())

        return UserStatusResponse(isLinked=bool(docs))
    except Exception as e:
        print(f"Error checking user status for line_id {line_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking user status."
        )

@router.post("/link-account", status_code=status.HTTP_204_NO_CONTENT)
async def link_account(
    request_body: LinkAccountRequest,
    line_id: str = Depends(get_current_line_id),
    db: Client = Depends(db_dependency)
):
    """
    Links a user's LINE account to a customer profile using a device serial number.
    """
    serial_number = request_body.serialNumber
    try:
        device_query = db.collection_group(settings.FIRESTORE_DEVICES_SUBCOLLECTION).where("serialNumber", "==", serial_number).limit(1)
        device_docs = list(device_query.stream())

        if not device_docs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serial number not found.")

        device_doc = device_docs[0]
        customer_ref = device_doc.reference.parent.parent
        customer_doc = customer_ref.get()

        if not customer_doc.exists or customer_doc.to_dict().get("lineId"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account is already linked or invalid.")

        customer_ref.update({"lineId": line_id})

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error linking account for serial {serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the account linking process."
        )