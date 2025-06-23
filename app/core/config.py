import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings.
    Values are loaded from environment variables.
    For local development, you can use a .env file.
    """
    PROJECT_ID: str = "your-gcp-project-id"
    LINE_CHANNEL_ID: str = "your-line-channel-id"

    # Firestore settings
    FIRESTORE_CUSTOMERS_COLLECTION: str = "customers"
    FIRESTORE_DEVICES_SUBCOLLECTION: str = "devices"
    FIRESTORE_REPORTS_SUBCOLLECTION: str = "reports"

    # LINE API settings
    LINE_API_VERIFY_URL: str = "https://api.line.me/oauth2/v2.1/verify"


# Create a single instance to be used across the application
settings = Settings()