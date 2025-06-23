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
    # as that's where it's called.
    with patch('app.dependencies.database.firestore.client', return_value=mock_db_client):
        # Also patch initialize_app if it's causing issues, though usually mocking client is enough
        with patch('app.dependencies.database.firebase_admin.initialize_app'):
            yield mock_db_client # This mock_db_client can be used by other fixtures if needed


@pytest.fixture
def db_mock(): # No longer depends on mock_firebase_admin_sdk for its return value
    """
    Provides a fresh MagicMock for the Firestore client for each test.
    This is what will be injected into the route handlers via dependency_overrides.
    """
    # The session-scoped mock_firebase_admin_sdk has already patched
    # firebase_admin.initialize_app and firestore.client at their lookup points.
    # This db_mock is specifically for being injected via app.dependency_overrides.
    # Each test gets a new, clean MagicMock instance.
    return MagicMock()

@pytest.fixture
def client(db_mock):
    from app.main import app # Import late to use patched firebase
    from app.dependencies.database import db_dependency
    from app.dependencies.auth import get_current_line_id
    
    # Override the db_dependency to use the fresh db_mock for this test
    app.dependency_overrides[db_dependency] = lambda: db_mock
    # Override the auth dependency to bypass the actual LINE API call
    # and return a consistent mock line_id for testing purposes.
    app.dependency_overrides[get_current_line_id] = lambda: "MOCK_LINE_ID_FOR_TEST"
    
    test_client = TestClient(app)
    yield test_client
    
    # Clean up dependency overrides after the test
    app.dependency_overrides.clear()