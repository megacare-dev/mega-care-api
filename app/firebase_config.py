import firebase_admin
from firebase_admin import firestore
import os

_db_client = None

def initialize_firebase_app():
    global _db_client
    if not firebase_admin._apps:
        try:
            # For Cloud Run, ADC will be used if no credentials are provided
            # and the service account has the right permissions.
            # For local dev, set GOOGLE_APPLICATION_CREDENTIALS env var.
            # projectId = os.getenv("GCLOUD_PROJECT", "mega-care-dev") # Not needed if ADC works
            firebase_admin.initialize_app()
            print("Firebase Admin SDK initialized successfully using ADC.")
        except Exception as e:
            print(f"Firebase Admin SDK initialization error: {e}")
            raise RuntimeError(f"Failed to initialize Firebase Admin SDK: {e}")
    
    _db_client = firestore.client()

def get_db():
    if _db_client is None:
        raise RuntimeError("Firestore client not initialized. Call initialize_firebase_app() during application startup.")
    return _db_client