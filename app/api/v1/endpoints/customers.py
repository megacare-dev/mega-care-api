from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import List, Dict
from datetime import datetime

from app.api.v1 import schemas
from app.api.v1.deps import get_current_user

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
    user_uid = current_user["uid"]
    # TODO: Implement Firestore logic
    # 1. Check if a document with ID `user_uid` already exists in 'customers'.
    # 2. If it exists, raise HTTPException 409 Conflict.
    # 3. Create a new customer document in Firestore with ID `user_uid`.
    #    - Convert `customer_in` to a dict.
    #    - Add `setupDate` = datetime.utcnow().
    #    - Save to `customers/{user_uid}`.
    # 4. Fetch the newly created document and return it as a `schemas.Customer`.
    print(f"Creating profile for user: {user_uid} with data: {customer_in.dict()}")
    # Placeholder response:
    return {**customer_in.dict(), "patientId": user_uid, "setupDate": datetime.utcnow()}


@router.get("/me", response_model=schemas.Customer)
def get_my_profile(current_user: Dict = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user.
    """
    user_uid = current_user["uid"]
    # TODO: Implement Firestore logic
    # 1. Fetch the document `customers/{user_uid}`.
    # 2. If not found, raise HTTPException 404 Not Found.
    # 3. Return the document data, mapped to `schemas.Customer`.
    print(f"Fetching profile for user: {user_uid}")
    raise HTTPException(status_code=501, detail="Not Implemented")


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