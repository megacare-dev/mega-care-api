from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from app.dependencies.auth import get_current_line_id
from app.dependencies.database import get_db
from app.core.config import settings
from app.models.equipment import EquipmentListResponse

router = APIRouter(prefix="/equipment", tags=["equipment"])

@router.get("/", response_model=EquipmentListResponse, summary="Get equipment list for the linked user")
async def get_equipment_list(
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    """
    Retrieves the list of equipment (devices) associated with the current LINE user.
    """
    # 1. Find the customer document by lineId
    customers_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION)
    customer_query = customers_ref.where(filter=FieldFilter("lineId", "==", line_id)).limit(1)
    customer_docs = list(customer_query.stream())

    if not customer_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No linked customer profile found for the provided token."
        )
    
    customer_doc = customer_docs[0]
    
    # 2. Query the 'devices' subcollection for that customer
    devices_ref = customer_doc.reference.collection(settings.FIRESTORE_DEVICES_SUBCOLLECTION)
    device_docs = devices_ref.stream()
    
    equipment_list = [doc.to_dict() for doc in device_docs]
    
    return EquipmentListResponse(devices=equipment_list)