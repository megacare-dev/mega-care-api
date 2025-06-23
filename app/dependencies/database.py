from google.cloud.firestore_v1.client import Client
from google.cloud import firestore
import firebase_admin

# Global variable to hold the db client
_db_client: Client = None

def initialize_firebase_app():
    """
    Initializes the Firebase Admin SDK.
    In a GCP environment (like Cloud Run), the project is inferred automatically.
    """
    global _db_client
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
        print("Firebase Admin SDK initialized.")
    _db_client = firestore.client()
    print("Firestore client created successfully.")

def get_db() -> Client:
    """
    Returns the initialized Firestore client.
    Raises an exception if the client is not initialized.
    """
    if _db_client is None:
        raise RuntimeError("Firestore client has not been initialized. Ensure lifespan event ran.")
    return _db_client

# This function will be used as a FastAPI dependency
def db_dependency() -> Client:
    return get_db()