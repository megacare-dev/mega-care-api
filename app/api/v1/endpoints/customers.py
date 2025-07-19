from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Dict
from datetime import datetime
from firebase_admin import firestore

from app.api.v1 import schemas
from app.dependencies.auth import get_current_user

router = APIRouter()

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
    customer_ref = db.collection("customers").document(user_uid)

    if customer_ref.get().exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer profile already exists"
        )

    customer_data = customer_in.dict()
    customer_data["setupDate"] = datetime.utcnow()

    customer_ref.set(customer_data)

    new_customer_doc = customer_ref.get()
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
    customer_ref = db.collection("customers").document(user_uid)
    doc = customer_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")

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
    user_uid = current_user["uid"]
    # TODO: Implement Firestore logic
    # 1. Add a new document to the sub-collection `customers/{user_uid}/devices`.
    #    - Let Firestore auto-generate the deviceId.
    #    - Convert `device_in` to a dict.
    #    - Add `addedDate` = datetime.utcnow().
    # 2. Return the new device data, including the auto-generated ID.
    print(f"Adding device for user {user_uid}: {device_in.dict()}")
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/me/devices", response_model=List[schemas.Device])
def get_my_devices(current_user: Dict = Depends(get_current_user)):
    """
    Retrieve a list of all devices for the authenticated patient.
    """
    user_uid = current_user["uid"]
    # TODO: Implement Firestore logic
    # 1. Fetch all documents from the sub-collection `customers/{user_uid}/devices`.
    # 2. Return the list of documents, mapped to `List[schemas.Device]`.
    print(f"Fetching devices for user: {user_uid}")
    raise HTTPException(status_code=501, detail="Not Implemented")

# TODO: Add similar endpoints for masks and airTubing
# - POST /me/masks -> add_a_mask
# - GET /me/masks -> get_my_masks
# - POST /me/airTubing -> add_air_tubing
# - GET /me/airTubing -> get_my_air_tubing