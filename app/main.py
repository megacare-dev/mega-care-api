from fastapi import FastAPI, HTTPException, status, Depends, Request
from typing import List
from contextlib import asynccontextmanager
from google.cloud.firestore_v1.client import Client
from google.cloud.exceptions import NotFound

from app.models import (
    Customer, CustomerCreate, CustomerUpdate
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

    except HTTPException:
        raise # Re-raise HTTPException to be handled by FastAPI
    except Exception as e:
        print(f"UNEXPECTED Error creating customer: {type(e).__name__} - {str(e)}")
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
        print(f"UNEXPECTED Error getting customers: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customers")

@app.get("/customers/{patient_id}", response_model=Customer)
def get_customer_by_id(patient_id: str, db: Client = Depends(db_dependency)):
    try:
        doc_ref = db.collection("customers").document(patient_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return Customer(id=doc.id, **doc.to_dict())
    except HTTPException:
        raise
    except NotFound as e: # Specifically catch Firestore's NotFound
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in Firestore") from e
    except Exception as e:
        print(f"UNEXPECTED Error getting customer by ID {patient_id}: {type(e).__name__} - {str(e)}")
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
    except NotFound as e: # Specifically catch Firestore's NotFound
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in Firestore for update") from e
    except Exception as e:
        print(f"UNEXPECTED Error updating customer {patient_id}: {type(e).__name__} - {str(e)}")
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
    except NotFound as e: # Specifically catch Firestore's NotFound
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in Firestore for delete") from e
    except Exception as e:
        print(f"UNEXPECTED Error deleting customer {patient_id}: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete customer")

# Add an __init__.py to the app folder to make it a package
# if __name__ == "__main__":
# import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))