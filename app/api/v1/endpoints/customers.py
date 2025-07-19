from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Dict
from datetime import datetime, date, timezone
import logging
from firebase_admin import firestore

from app.api.v1 import schemas
from app.dependencies.auth import get_current_user

router = APIRouter()

# Basic logging configuration
logging.basicConfig(level=logging.INFO)

@router.post("/me", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
def create_customer_profile(
    *,
    customer_in: schemas.CustomerCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new customer profile for the authenticated user.
    The Firestore document ID will be the user's Firebase UID.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    logging.info(f"Attempting to create profile for user UID: {user_uid}")

    customer_ref = db.collection("customers").document(user_uid)

    if customer_ref.get().exists:
        logging.warning(f"Profile for user UID: {user_uid} already exists.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer profile already exists"
        )

    customer_data = customer_in.model_dump()
    customer_data["setupDate"] = datetime.now(timezone.utc)

    # Convert date object to datetime object for Firestore compatibility
    if isinstance(customer_data.get("dob"), date):
        customer_data["dob"] = datetime.combine(customer_data["dob"], datetime.min.time())

    logging.info(f"Data to be written for UID {user_uid}: {customer_data}")

    try:
        write_result = customer_ref.set(customer_data)
        logging.info(f"Successfully wrote data for UID {user_uid} at {write_result.update_time}")
    except Exception as e:
        logging.error(f"Failed to write to Firestore for UID {user_uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create customer profile in database."
        )

    new_customer_doc = customer_ref.get()
    if not new_customer_doc.exists:
        logging.error(f"Data for UID {user_uid} was not found immediately after write.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer profile after creation."
        )

    response_data = new_customer_doc.to_dict()
    response_data["patientId"] = new_customer_doc.id

    return response_data


@router.get("/me", response_model=schemas.Customer)
def get_my_profile(current_user: Dict = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    logging.info(f"Attempting to retrieve profile for user UID: {user_uid}")
    customer_ref = db.collection("customers").document(user_uid)

    try:
        doc = customer_ref.get()
    except Exception as e:
        logging.error(f"Failed to query Firestore for UID {user_uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not query customer profile from database."
        )

    if not doc.exists:
        logging.warning(f"Profile for user UID: {user_uid} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")

    logging.info(f"Successfully retrieved profile for UID: {user_uid}")
    response_data = doc.to_dict()
    response_data["patientId"] = doc.id
    return response_data


@router.post("/me/devices", response_model=schemas.Device, status_code=status.HTTP_201_CREATED)
def add_a_device(
    *,
    device_in: schemas.DeviceCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Add a new device to the authenticated patient's profile.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    devices_ref = db.collection("customers").document(user_uid).collection("devices")

    device_data = device_in.model_dump()
    device_data["addedDate"] = datetime.now(timezone.utc)

    # .add() creates a new document with an auto-generated ID
    update_time, new_device_ref = devices_ref.add(device_data)

    # To return the full object including the new ID, we fetch the document we just created
    new_device_doc = new_device_ref.get()
    response_data = new_device_doc.to_dict()
    response_data["deviceId"] = new_device_doc.id

    return response_data


@router.get("/me/devices", response_model=List[schemas.Device])
def get_my_devices(current_user: Dict = Depends(get_current_user)):
    """
    Retrieve a list of all devices for the authenticated patient.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    devices_ref = db.collection("customers").document(user_uid).collection("devices")
    
    devices = []
    # stream() is an efficient way to iterate over all documents in a collection
    for doc in devices_ref.stream():
        device_data = doc.to_dict()
        device_data["deviceId"] = doc.id
        devices.append(device_data)
        
    return devices


@router.post("/me/masks", response_model=schemas.Mask, status_code=status.HTTP_201_CREATED)
def add_a_mask(
    *,
    mask_in: schemas.MaskCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Add a new mask to the authenticated patient's profile.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    masks_ref = db.collection("customers").document(user_uid).collection("masks")

    mask_data = mask_in.model_dump()
    mask_data["addedDate"] = datetime.now(timezone.utc)

    _update_time, new_mask_ref = masks_ref.add(mask_data)

    new_mask_doc = new_mask_ref.get()
    response_data = new_mask_doc.to_dict()
    response_data["maskId"] = new_mask_doc.id

    return response_data


@router.get("/me/masks", response_model=List[schemas.Mask])
def get_my_masks(current_user: Dict = Depends(get_current_user)):
    """
    Retrieve a list of all masks for the authenticated patient.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    masks_ref = db.collection("customers").document(user_uid).collection("masks")
    
    masks = []
    for doc in masks_ref.stream():
        mask_data = doc.to_dict()
        mask_data["maskId"] = doc.id
        masks.append(mask_data)
        
    return masks


@router.post("/me/airTubing", response_model=schemas.AirTubing, status_code=status.HTTP_201_CREATED)
def add_air_tubing(
    *,
    tubing_in: schemas.AirTubingCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Add new air tubing to the authenticated patient's profile.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    tubing_ref = db.collection("customers").document(user_uid).collection("airTubing")

    tubing_data = tubing_in.model_dump()
    tubing_data["addedDate"] = datetime.now(timezone.utc)

    _update_time, new_tubing_ref = tubing_ref.add(tubing_data)

    new_tubing_doc = new_tubing_ref.get()
    response_data = new_tubing_doc.to_dict()
    response_data["tubingId"] = new_tubing_doc.id

    return response_data


@router.get("/me/airTubing", response_model=List[schemas.AirTubing])
def get_my_air_tubing(current_user: Dict = Depends(get_current_user)):
    """
    Retrieve a list of all air tubing for the authenticated patient.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    tubing_ref = db.collection("customers").document(user_uid).collection("airTubing")
    
    tubes = []
    for doc in tubing_ref.stream():
        tubing_data = doc.to_dict()
        tubing_data["tubingId"] = doc.id
        tubes.append(tubing_data)
        
    return tubes


@router.post("/me/dailyReports", response_model=schemas.DailyReport, status_code=status.HTTP_201_CREATED)
def submit_daily_report(
    *,
    report_in: schemas.DailyReportCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Submit a daily therapy report. The document ID will be the report date (YYYY-MM-DD).
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    report_id = report_in.reportDate.strftime('%Y-%m-%d')
    report_ref = db.collection("customers").document(user_uid).collection("dailyReports").document(report_id)

    report_data = report_in.model_dump()
    # Convert date object to datetime object for Firestore compatibility
    if isinstance(report_data.get("reportDate"), date):
        report_data["reportDate"] = datetime.combine(report_data["reportDate"], datetime.min.time())

    report_ref.set(report_data)

    # Fetch the document back to ensure a consistent response and confirm the write.
    new_report_doc = report_ref.get()
    if not new_report_doc.exists:
        logging.error(f"Data for report {report_id} was not found immediately after write for UID {user_uid}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report after creation."
        )

    response_data = new_report_doc.to_dict()
    response_data["reportId"] = new_report_doc.id
    return response_data


@router.get("/me/dailyReports", response_model=List[schemas.DailyReport])
def get_my_daily_reports(
    limit: int = Query(30, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """
    Retrieve a list of recent daily reports, ordered by most recent.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    reports_ref = db.collection("customers").document(user_uid).collection("dailyReports")

    query = reports_ref.order_by("reportDate", direction=firestore.Query.DESCENDING).limit(limit)
    
    reports = []
    for doc in query.stream():
        report_data = doc.to_dict()
        report_data["reportId"] = doc.id
        reports.append(report_data)
        
    return reports