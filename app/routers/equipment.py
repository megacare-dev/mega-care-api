from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import firestore
from app.dependencies.auth import get_current_line_id
from app.firebase_config import get_db
from app.core.config import settings

router = APIRouter(prefix="/equipment", tags=["equipment"])

@router.get("/", summary="Get equipment list for the linked user")
async def get_equipment_list(
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    """
    Retrieves the list of equipment (devices) associated with the current LINE user.
    """
    # TODO: Implement logic to find patientId from line_id, then query the 'devices' subcollection.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet.")