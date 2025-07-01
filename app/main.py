import os
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI

from app.api.v1.endpoints import customers, clinicians

# --- Firebase Admin SDK Initialization ---
# It's crucial to initialize the app only once.
# Use GOOGLE_APPLICATION_CREDENTIALS environment variable for security.
# In Cloud Run, this is handled automatically if the service account is set.
try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': os.getenv('GCP_PROJECT'),
        })
except Exception as e:
    print(f"Could not initialize Firebase Admin SDK: {e}")
    # Depending on the use case, you might want to exit the application
    # if Firebase connection is essential for all operations.

app = FastAPI(
    title="MegaCare Connect API",
    description="Backend API for the MegaCare Connect application.",
    version="1.0.0"
)

app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(clinicians.router, prefix="/api/v1/clinician", tags=["Clinicians"])

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to MegaCare Connect API"}