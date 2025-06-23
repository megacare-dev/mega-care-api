import logging

import firebase_admin
from google.cloud.firestore_v1.client import Client
from google.cloud import firestore

_logger = logging.getLogger(__name__)

# Global variable to hold the db client
_db_client: Client = None

def initialize_firebase_app():
    """
    Initializes the Firebase Admin SDK and the Firestore client.
    This function should be called during application startup.
    """
    global _db_client
    if not firebase_admin._apps:
        try:
            # In a GCP environment (like Cloud Run), Application Default Credentials (ADC)
            # are used automatically if the service account has the correct permissions.
            # For local development, set the GOOGLE_APPLICATION_CREDENTIALS env var.
            firebase_admin.initialize_app()
            _logger.info("Firebase Admin SDK initialized successfully using ADC.")
        except Exception as e:
            _logger.error("Firebase Admin SDK initialization error: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to initialize Firebase Admin SDK: {e}")

    _db_client = firestore.Client()
    _logger.info("Firestore client created successfully.")

def get_db() -> Client:
    """
    FastAPI dependency to get the initialized Firestore client.
    Raises a RuntimeError if the client has not been initialized.
    """
    if _db_client is None:
        # This error indicates a problem with the application's startup logic.
        raise RuntimeError("Firestore client has not been initialized. Ensure initialize_firebase_app() is called on startup.")
    return _db_client