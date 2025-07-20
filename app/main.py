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
    Custom handler to log detailed validation errors for 422 responses.
    This helps in debugging malformed client-side requests.
    The actual response is delegated back to FastAPI's default handler
    to ensure it's processed correctly by middleware like CORS.
    """
    error_details = exc.errors()
    logging.error(f"422 Unprocessable Entity. Request: {request.method} {request.url}. Errors: {error_details}")

    # By calling the default handler, we ensure the response format is
    # consistent and that it passes through the middleware chain correctly.
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request, exc)

# --- CORS Middleware ---
# To allow any origin to access your API, you can use a wildcard "*".
# This is often used for public APIs or during development to avoid CORS issues.
#
# IMPORTANT: According to the CORS specification, when `allow_origins` is set to a
# wildcard ("*"), `allow_credentials` must be set to `False`. Your application uses
# a bearer token for authentication, which is passed in a header and is not
# affected by this `allow_credentials` setting (which primarily relates to cookies).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers, including Authorization
)

app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(clinicians.router, prefix="/api/v1/clinician", tags=["Clinicians"])

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to MegaCare Connect API"}