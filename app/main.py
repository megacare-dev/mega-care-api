from fastapi import FastAPI, HTTPException, status, Depends, Request
from typing import List
from contextlib import asynccontextmanager
from google.cloud.firestore_v1.client import Client
from google.cloud.exceptions import NotFound

from app.models import (
    Customer, CustomerCreate, CustomerUpdate,
    Device, DeviceCreate
)
from app.firebase_config import initialize_firebase_app, get_db
import firebase_admin.firestore # For SERVER_TIMESTAMP
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    initialize_firebase_app()
    print("Firebase Admin SDK initialized successfully via lifespan event.")
    yield
    # Code to run on shutdown (if any)
    print("Application shutdown.")

app = FastAPI(title="Mega Care API", lifespan=lifespan)

# Dependency to get DB client
def db_dependency() -> Client:
    return get_db()

@app.get("/")
async def read_root(request: Request):
    print(f"Handling request: {request.url.path}")
    return "Hello World from Cloud Run with FastAPI!\n"

# --- Customers CRUD ---

@app.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: CustomerCreate, db: Client = Depends(db_dependency)):
    try:
        customer_dict = customer_data.model_dump(exclude_unset=True)
        
        # Handle server-side timestamp for setupDate if not provided
        if customer_data.setupDate is None and 'setupDate' not in customer_dict : # Check if client explicitly sent null vs not sending field
             customer_dict['setupDate'] = firebase_admin.firestore.SERVER_TIMESTAMP

        doc_ref = db.collection("customers").document()
        doc_ref.set(customer_dict)
        
        # Fetch the created document to get server-generated fields like timestamps
        created_doc = doc_ref.get()
        return Customer(id=created_doc.id, **created_doc.to_dict())

    except HTTPException: # Re-raise HTTPException to let FastAPI handle it
        raise
    except Exception as e:
        print(f"Error creating customer: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create customer: {str(e)}")

@app.get("/customers", response_model=List[Customer])
def get_all_customers(db: Client = Depends(db_dependency)):
    try:
        customers_ref = db.collection("customers")
        docs = customers_ref.stream() # Use stream() for async iteration if available
        customers = [Customer(id=doc.id, **doc.to_dict()) for doc in docs]
        return customers
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting customers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customers")

@app.get("/customers/{patient_id}", response_model=Customer)
def get_customer_by_id(patient_id: str, db: Client = Depends(db_dependency)):
    try:
        doc_ref = db.collection("customers").document(patient_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return Customer(id=doc.id, **doc.to_dict())
    except HTTPException: # Let FastAPI handle its own HTTPExceptions
        raise
    except Exception as e:
        print(f"Error getting customer by ID {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customer")

@app.put("/customers/{patient_id}", response_model=Customer)
def update_customer(patient_id: str, customer_update_data: CustomerUpdate, db: Client = Depends(db_dependency)):
    try:
        doc_ref = db.collection("customers").document(patient_id)
        # Check if document exists before attempting update
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found to update")

        update_dict = customer_update_data.model_dump(exclude_unset=True)
        if not update_dict:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

        doc_ref.set(update_dict, merge=True)
        updated_doc = doc_ref.get()
        return Customer(id=updated_doc.id, **updated_doc.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating customer {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update customer")

@app.delete("/customers/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(patient_id: str, db: Client = Depends(db_dependency)):
    try:
        doc_ref = db.collection("customers").document(patient_id)
        # Check if document exists before attempting delete
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found to delete")

        doc_ref.delete()
        return None # FastAPI will return 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting customer {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete customer")

# --- Devices Sub-collection CRUD ---

@app.post("/customers/{patient_id}/devices", response_model=Device, status_code=status.HTTP_201_CREATED)
def add_device_to_customer(patient_id: str, device_data: DeviceCreate, db: Client = Depends(db_dependency)):
    try:
        # Ensure customer exists
        customer_doc = db.collection("customers").document(patient_id).get()
        if not customer_doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        device_dict = device_data.model_dump(exclude_unset=True)
        if device_data.addedDate is None and 'addedDate' not in device_dict:
            device_dict['addedDate'] = firebase_admin.firestore.SERVER_TIMESTAMP

        devices_collection_ref = db.collection("customers").document(patient_id).collection("devices")
        doc_ref = devices_collection_ref.document()
        doc_ref.set(device_dict)
        
        created_doc = doc_ref.get()
        return Device(id=created_doc.id, **created_doc.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding device to customer {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add device")

@app.get("/customers/{patient_id}/devices", response_model=List[Device])
def get_devices_for_customer(patient_id: str, db: Client = Depends(db_dependency)):
    try:
        devices_ref = db.collection("customers").document(patient_id).collection("devices")
        docs = devices_ref.stream()
        devices = [Device(id=doc.id, **doc.to_dict()) for doc in docs]
        return devices
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting devices for customer {patient_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get devices")

# Add an __init__.py to the app folder to make it a package
# if __name__ == "__main__":
# import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))