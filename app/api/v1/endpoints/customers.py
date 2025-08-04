from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Dict
from datetime import datetime, date, timezone
import logging
from google.cloud.firestore_v1.base_query import FieldFilter, And
from firebase_admin import firestore

from app.api.v1 import schemas
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/me", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
def create_customer_profile(
    *,
    customer_in: schemas.CustomerProfilePayload,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a customer profile for the authenticated user.
    This endpoint is called once after user registration to create their profile.
    It will return a 409 Conflict error if a profile already exists.
    """
    db = firestore.client()
    user_uid = current_user["uid"]
    logging.info(f"Attempting to create profile for user UID: {user_uid}")

    customer_ref = db.collection("customers").document(user_uid)
    doc = customer_ref.get()
    if doc.exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer profile already exists for this user."
        )

    # Use exclude_unset=True for partial updates.
    customer_data = customer_in.model_dump(by_alias=True, exclude_unset=True)

    # If displayName is not provided, try to construct it from first/last name.
    if 'displayName' not in customer_data and 'firstName' in customer_data and 'lastName' in customer_data:
        customer_data['displayName'] = f"{customer_data['firstName']} {customer_data['lastName']}"

    # For a new profile, we need a display name.
    if 'displayName' not in customer_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A 'displayName' or both 'firstName' and 'lastName' are required to create a profile."
        )

    customer_data["setupDate"] = datetime.now(timezone.utc)

    # Convert date object to datetime object for Firestore compatibility
    if isinstance(customer_data.get("dob"), date):
        customer_data["dob"] = datetime.combine(customer_data["dob"], datetime.min.time())

    logging.info(f"Data to be written for UID {user_uid}: {customer_data}")

    try:
        # Use set() for creation.
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve customer profile after creation.")

    response_data = new_customer_doc.to_dict()
    response_data["patientId"] = new_customer_doc.id

    return schemas.Customer.model_validate(response_data)


@router.get("/me", response_model=schemas.Customer, response_model_by_alias=False)
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
    return schemas.Customer.model_validate(response_data)


@router.post("/me/devices", response_model=schemas.Device, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
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

    device_data = device_in.model_dump(by_alias=True)
    device_data["addedDate"] = datetime.now(timezone.utc)

    # .add() creates a new document with an auto-generated ID
    update_time, new_device_ref = devices_ref.add(device_data)

    # To return the full object including the new ID, we fetch the document we just created
    new_device_doc = new_device_ref.get()
    response_data = new_device_doc.to_dict()
    response_data["deviceId"] = new_device_doc.id

    return schemas.Device.model_validate(response_data)


@router.get("/me/devices", response_model=List[schemas.Device], response_model_by_alias=False)
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
        devices.append(schemas.Device.model_validate(device_data))
        
    return devices


@router.post("/me/masks", response_model=schemas.Mask, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
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

    mask_data = mask_in.model_dump(by_alias=True)
    mask_data["addedDate"] = datetime.now(timezone.utc)

    _update_time, new_mask_ref = masks_ref.add(mask_data)

    new_mask_doc = new_mask_ref.get()
    response_data = new_mask_doc.to_dict()
    response_data["maskId"] = new_mask_doc.id

    return schemas.Mask.model_validate(response_data)


@router.get("/me/masks", response_model=List[schemas.Mask], response_model_by_alias=False)
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
        masks.append(schemas.Mask.model_validate(mask_data))
        
    return masks


@router.post("/me/airTubing", response_model=schemas.AirTubing, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
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

    tubing_data = tubing_in.model_dump(by_alias=True)
    tubing_data["addedDate"] = datetime.now(timezone.utc)

    _update_time, new_tubing_ref = tubing_ref.add(tubing_data)

    new_tubing_doc = new_tubing_ref.get()
    response_data = new_tubing_doc.to_dict()
    response_data["tubingId"] = new_tubing_doc.id

    return schemas.AirTubing.model_validate(response_data)


@router.get("/me/airTubing", response_model=List[schemas.AirTubing], response_model_by_alias=False)
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
        tubes.append(schemas.AirTubing.model_validate(tubing_data))
        
    return tubes


@router.post("/me/link-device", response_model=schemas.Customer, status_code=status.HTTP_200_OK, response_model_by_alias=False)
def link_device_to_profile(
    *,
    link_request: schemas.DeviceLinkRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Links a device (via SN) to the authenticated user's profile.

    This process involves finding a pre-existing patient profile in Firestore
    via the device's serial number. If a profile is found, its data is
    merged into the authenticated user's profile, effectively linking them.
    It also copies the found profile to a 'patients' collection if the
    device document contains a 'patientId' field.
    """
    db = firestore.client()
    user_uid = current_user["uid"]

    # 1. Find the device using a collection group query.
    # This searches all 'devices' sub-collections for a matching serial number.
    # The device must also have a status of "unlinked" to be available for linking.
    # This requires a composite index in Firestore on (serialNumber, status).
    device_query = db.collection_group("devices").where(
        filter=And([
            FieldFilter("serialNumber", "==", link_request.serial_number),
            FieldFilter("status", "==", "unlink")
        ])
    ).limit(1)
    try:
        device_docs = list(device_query.stream())
    except Exception as e:
        logging.error(f"Firestore query for device SN {link_request.serial_number} failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while searching for the device."
        )

    if not device_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patient record found for the provided Serial Number."
        )

    # 2. Get the parent customer profile from the found device.
    found_device_doc = device_docs[0]
    device_data = found_device_doc.to_dict()

    logging.info(f"Found device doc with ID: {found_device_doc.id} for SN: {link_request.serial_number}. Data: {device_data}")
    # The device doc's parent is the 'devices' collection, whose parent is the customer document.
    pre_existing_customer_ref = found_device_doc.reference.parent.parent

    # If the device is not in a sub-collection (i.e., it's in a root collection),
    # it might have a reference field to the patient.
    if not pre_existing_customer_ref:
        # The device document is not in a standard 'customers/{uid}/devices/{id}' path.
        # Check for a reference field within the device document itself.
        patient_id = device_data.get("patientId")
        if not patient_id:
            logging.error(f"Device {found_device_doc.id} is a root-level document but does not contain a patient reference field like 'patientId'.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device found, but it is not linked to any patient profile."
            )
        logging.info(f"Device is a root document. Looking up patient via 'patientId' field: {patient_id}")
        pre_existing_customer_ref = db.collection("patient_list").document(patient_id)
    pre_existing_customer_doc = pre_existing_customer_ref.get()


    if not pre_existing_customer_doc.exists:
        logging.error(f"Device {found_device_doc.id} found for SN {link_request.serial_number}, but parent customer {pre_existing_customer_ref.id} does not exist.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A device was found, but its associated patient profile is missing."
        )

    pre_existing_customer_data = pre_existing_customer_doc.to_dict()
    
    # 3. As per specification, copy the found customer document to a 'patient_list'
    # collection, using the 'patientId' from the device document as the new doc ID. 
    patient_id_from_device = device_data.get("patientId")
    if patient_id_from_device:
        try:
            # Create a separate dictionary for the 'patient_list' collection to avoid
            # mutating the original data that will be merged into the 'customers' profile.
            data_for_patients = pre_existing_customer_data.copy()
            data_for_patients["customerId"] = user_uid # This links the patient record back to the LINE user.
            logging.info(f"Copying customer profile {pre_existing_customer_doc.id} to 'patient_list' collection with ID {patient_id_from_device}")
            db.collection("patient_list").document(patient_id_from_device).set(data_for_patients, merge=True)
        except Exception as e:
            # This is treated as a non-critical error. The primary linking can still proceed.
            logging.warning(f"Could not copy profile to 'patient_list' collection for patientId {patient_id_from_device}: {e}")
    else:
        logging.info(f"Device document {found_device_doc.id} does not contain a 'patientId' field. Skipping copy to 'patient_list' collection.")

    # 4. Fetch the current user's profile to preserve key identity fields like lineProfile.
    current_user_customer_ref = db.collection("customers").document(user_uid)
    current_user_doc = current_user_customer_ref.get()
    current_user_data = current_user_doc.to_dict() if current_user_doc.exists else {}

    # 5. Manually merge data to ensure the user's LINE identity is the source of truth.
    # Start with the pre-existing data as the base.
    data_to_write = pre_existing_customer_data.copy()

    # Preserve key fields from the current user's profile (from LINE login).
    if "lineProfile" in current_user_data:
        data_to_write["lineProfile"] = current_user_data["lineProfile"]
    if "lineId" in current_user_data:
        data_to_write["lineId"] = current_user_data["lineId"]

    # Add the patientId from the device, which may link to the 'patients' collection.
    data_to_write["patientId"] = patient_id_from_device

    try:
        # Perform a full write of the constructed data. This is safer than a blind merge.
        current_user_customer_ref.set(data_to_write)
        logging.info(f"Successfully merged data from profile {pre_existing_customer_doc.id} to profile {user_uid}")
    except Exception as e:
        logging.error(f"Failed to merge Firestore data for UID {user_uid}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not link device to customer profile.")

    # Mark the original device document as linked to this customer to prevent re-linking.
    try:
        found_device_doc.reference.update({"customerId": user_uid, "status": "active"})
        logging.info(f"Successfully updated original device doc {found_device_doc.id} with customerId {user_uid}.")
    except Exception as e:
        # This is a non-critical error for the user flow, but should be logged as a warning.
        logging.warning(f"Could not update original device doc {found_device_doc.id} with customerId: {e}")


    # 6. Create a record of the linked device in the user's 'devices' sub-collection.
    # This ensures the device used for linking is now associated with the user's profile.
    try:
        # Using 'devices' collection for consistency with other endpoints like /me/devices.
        devices_ref = current_user_customer_ref.collection("devices")

        # Prepare the data for the new device document, conforming to DeviceBase + addedDate.
        # This combines data from the found device and the link request.
        new_device_data = {
            "deviceName": device_data.get("deviceName", "Unknown Device"),
            "serialNumber": link_request.serial_number,
            "deviceNumber": link_request.device_number,
            "status": device_data.get("status", "Active"),
            "settings": device_data.get("settings"),
            "addedDate": datetime.now(timezone.utc)
        }

        # Clean the dict from None values before saving to Firestore
        new_device_data_cleaned = {k: v for k, v in new_device_data.items() if v is not None}

        devices_ref.add(new_device_data_cleaned)
        logging.info(f"Successfully created a new device entry for user {user_uid} from the linking process.")
    except Exception as e:
        logging.warning(f"Could not create device entry for user {user_uid} after linking: {e}")

    # 7. Return the updated profile of the current user.
    updated_doc = current_user_customer_ref.get()
    if not updated_doc.exists:
        logging.error(f"Data for UID {user_uid} was not found immediately after merge.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve customer profile after linking.")

    response_data = updated_doc.to_dict()
    response_data["patientId"] = updated_doc.id
    return schemas.Customer.model_validate(response_data)

@router.post("/me/dailyReports", response_model=schemas.DailyReport, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
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
    report_id = report_in.report_date.strftime('%Y-%m-%d')
    report_ref = db.collection("customers").document(user_uid).collection("dailyReports").document(report_id)

    report_data = report_in.model_dump(by_alias=True)
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
    return schemas.DailyReport.model_validate(response_data)


@router.get("/me/dailyReports", response_model=List[schemas.DailyReport], response_model_by_alias=False)
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
        reports.append(schemas.DailyReport.model_validate(report_data))
        
    return reports