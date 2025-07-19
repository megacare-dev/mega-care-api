from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Dict
from datetime import datetime
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

    customer_data = customer_in.dict()
    customer_data["setupDate"] = datetime.utcnow()
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

    device_data = device_in.dict()
    device_data["addedDate"] = datetime.utcnow()

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

# TODO: Add similar endpoints for masks and airTubing
# - POST /me/masks -> add_a_mask
# - GET /me/masks -> get_my_masks
# - POST /me/airTubing -> add_air_tubing
# - GET /me/airTubing -> get_my_air_tubing