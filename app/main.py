import os
import logging
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, customers, clinicians

# --- Logging Configuration ---
# Configure logging at the application's entry point.
# Cloud Run will automatically handle log output to Cloud Logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Firebase Admin SDK Initialization ---
# It's crucial to initialize the app only once.
# Use GOOGLE_APPLICATION_CREDENTIALS environment variable for security.
# In Cloud Run, this is handled automatically if the service account is set.
try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': os.getenv('GOOGLE_CLOUD_PROJECT'),
        })
except Exception as e:
    logging.error(f"Could not initialize Firebase Admin SDK: {e}")
    # Depending on the use case, you might want to exit the application
    # if Firebase connection is essential for all operations.

app = FastAPI(
    title="MegaCare Connect API",
    description="Backend API for the MegaCare Connect application.",
    version="1.0.0"
)

# --- Custom Exception Handler for Validation Errors ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Log detailed validation errors for 422 Unprocessable Entity responses.
    This helps in debugging client-side requests that are malformed.
    """
    error_details = exc.errors()
    logging.error(f"422 Unprocessable Entity. Request: {request.method} {request.url}. Errors: {error_details}")

    # Return the default FastAPI response structure for validation errors.
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )

# --- CORS Middleware ---
# This allows the frontend application (e.g., LINE LIFF) to make requests to this API.
origins = [
    "https://mega-care-connect-service-15106852528.asia-southeast1.run.app",
    # For local development and testing
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500", # Example for VS Code Live Server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers, including Authorization
)

app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(clinicians.router, prefix="/api/v1/clinician", tags=["Clinicians"])

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to MegaCare Connect API"}