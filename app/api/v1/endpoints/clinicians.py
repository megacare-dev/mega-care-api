from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Dict

from app.api.v1 import schemas
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/patients", response_model=List[schemas.Customer])
def get_assigned_patients(current_user: Dict = Depends(get_current_user)):
    """
    Retrieves a list of summary profiles for all patients assigned to the
    authenticated clinician.
    """
    clinician_uid = current_user["uid"]
    # TODO: Implement Firestore logic
    # 1. Fetch the clinician's document (e.g., from a `clinicians` collection).
    # 2. Get the `assignedPatients` array of patient UIDs.
    # 3. For each patient UID, fetch the corresponding document from the `customers` collection.
    # 4. Return the list of customer documents, mapped to `List[schemas.Customer]`.
    # Note: This could be inefficient. Consider denormalizing patient summary data
    # into the clinician's document or using a separate collection for assignments.
    print(f"Fetching patients for clinician: {clinician_uid}")
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/patients/{patientId}/dailyReports", response_model=List[schemas.DailyReport])
def get_patient_daily_reports(
    patientId: str,
    limit: int = Query(30, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """
    Retrieves recent daily reports for a specific patient assigned to the clinician.
    """
    clinician_uid = current_user["uid"]
    # TODO: Implement Firestore logic
    # 1. Verify the clinician is authorized to view this patient's data.
    #    - Fetch clinician's doc, check if `patientId` is in `assignedPatients`.
    #    - If not authorized, raise HTTPException 403 Forbidden.
    # 2. Fetch reports from `customers/{patientId}/dailyReports`.
    #    - Order by `reportDate` descending.
    #    - Apply the `limit`.
    # 3. Return the list of reports, mapped to `List[schemas.DailyReport]`.
    print(f"Clinician {clinician_uid} fetching reports for patient {patientId}")
    raise HTTPException(status_code=501, detail="Not Implemented")