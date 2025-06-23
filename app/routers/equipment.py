from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1.client import Client

from app.dependencies.auth import get_current_line_id
from app.dependencies.database import db_dependency
from app.core.config import settings
from app.models.equipment import EquipmentResponse, Device

router = APIRouter(
    prefix="/api/v1/equipment",
    tags=["Equipment"],
    dependencies=[Depends(get_current_line_id)] # Secure all routes in this router
)

@router.get("", response_model=EquipmentResponse)
async def get_user_equipment(
    line_id: str = Depends(get_current_line_id),
    db: Client = Depends(db_dependency)
):
    """
    Retrieves the list of devices associated with the current user.
    """
    try:
        # 1. Find the customer document using the line_id
        customers_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION)
        query = customers_ref.where("lineId", "==", line_id).limit(1)
        customer_docs = list(query.stream())

        if not customer_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No linked customer profile found for this LINE account."
            )
        
        customer_id = customer_docs[0].id

        # 2. Retrieve devices from the sub-collection
        devices_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION).document(customer_id).collection(settings.FIRESTORE_DEVICES_SUBCOLLECTION)
        device_docs = devices_ref.stream()

        devices_list = [Device.model_validate(doc.to_dict()) for doc in device_docs]

        return EquipmentResponse(devices=devices_list)
    except Exception as e:
        print(f"Error retrieving equipment for line_id {line_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching equipment data."
        )