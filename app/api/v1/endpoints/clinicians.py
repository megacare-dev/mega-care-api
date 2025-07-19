from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Dict

from firebase_admin import firestore
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
    db = firestore.client()

    # 1. Fetch the clinician's document from a `clinicians` collection.
    clinician_ref = db.collection("clinicians").document(clinician_uid)
    clinician_doc = clinician_ref.get()

    if not clinician_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinician profile not found")

    # 2. Get the `assignedPatients` array of patient UIDs.
    assigned_patient_uids = clinician_doc.to_dict().get("assignedPatients", [])
    if not assigned_patient_uids:
        return []

    # 3. For each patient UID, fetch the corresponding document from the `customers` collection.
    # Note: This is an N+1 query and can be inefficient.
    # Firestore's `in` operator is limited to 10 items per query. For larger lists,
    # multiple queries or data denormalization would be necessary.
    patients = []
    for patient_uid in assigned_patient_uids:
        customer_doc = db.collection("customers").document(patient_uid).get()
        if customer_doc.exists:
            customer_data = customer_doc.to_dict()
            customer_data["patientId"] = customer_doc.id
            patients.append(customer_data)
    
    return patients

@router.get("/patients/{patientId}", response_model=schemas.Customer)
def get_patient_profile(
    patientId: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Retrieves the profile for a specific patient, verifying that the clinician
    is authorized to view this patient.
    """
    clinician_uid = current_user["uid"]
    db = firestore.client()

    # 1. Verify the clinician is authorized to view this patient's data.
    clinician_ref = db.collection("clinicians").document(clinician_uid)
    clinician_doc = clinician_ref.get()

    if not clinician_doc.exists or patientId not in clinician_doc.to_dict().get("assignedPatients", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this patient's profile"
        )

    # 2. Fetch the patient's document from the `customers` collection.
    customer_ref = db.collection("customers").document(patientId)
    customer_doc = customer_ref.get()

    if not customer_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    response_data = customer_doc.to_dict()
    response_data["patientId"] = customer_doc.id
    return response_data

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
    db = firestore.client()

    # 1. Verify the clinician is authorized to view this patient's data.
    clinician_ref = db.collection("clinicians").document(clinician_uid)
    clinician_doc = clinician_ref.get()

    if not clinician_doc.exists or patientId not in clinician_doc.to_dict().get("assignedPatients", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this patient's reports"
        )

    # 2. Fetch reports from `customers/{patientId}/dailyReports`.
    reports_ref = db.collection("customers").document(patientId).collection("dailyReports")
    
    query = reports_ref.order_by("reportDate", direction=firestore.Query.DESCENDING).limit(limit)

    # 3. Return the list of reports.
    reports = []
    for doc in query.stream():
        report_data = doc.to_dict()
        report_data["reportId"] = doc.id
        reports.append(report_data)

    if not reports:
        # It's better to return an empty list than a 404 if the patient exists but has no reports.
        return []
        
    return reports