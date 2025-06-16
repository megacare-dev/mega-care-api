import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import firebase_admin

# To prevent "Firebase App named "[DEFAULT]" already exists" errors during multiple test runs/sessions
# We ensure that the app is initialized only once or mock it effectively.

# Mock the firebase_admin initialization and firestore client
# This prevents actual Firebase calls during tests.

# We need to patch where these are LOOKED UP, not where they are defined.
# So, if main.py imports get_db from app.firebase_config, we patch it there.

@pytest.fixture(scope="session", autouse=True)
def mock_firebase_admin_sdk():
    """
    Mocks the firebase_admin SDK for the entire test session.
    Prevents actual initialization and network calls.
    """
    if not firebase_admin._apps: # Initialize a dummy app if none exists for other parts of SDK
        firebase_admin.initialize_app(name="pytest_dummy_app")

    # Mock the client() method from firebase_admin.firestore
    # This mock will be returned whenever firestore.client() is called.
    mock_db_client = MagicMock()
    
    # Patch 'firestore.client' within the 'app.firebase_config' module
    # as that's where it's called to set _db_client.
    with patch('app.firebase_config.firestore.client', return_value=mock_db_client):
        # Also patch initialize_app if it's causing issues, though usually mocking client is enough
        with patch('app.firebase_config.firebase_admin.initialize_app'):
            yield mock_db_client # This mock_db_client can be used by other fixtures if needed


@pytest.fixture
def db_mock(mock_firebase_admin_sdk): # Depends on the session-wide mock
    """
    Provides a fresh MagicMock for the Firestore client for each test.
    This is what will be injected into the route handlers.
    """
    return mock_firebase_admin_sdk # Return the same mock instance configured by mock_firebase_admin_sdk

@pytest.fixture
def client(db_mock):
    from app.main import app, db_dependency # Import late to use patched firebase
    app.dependency_overrides[db_dependency] = lambda: db_mock
    return TestClient(app)