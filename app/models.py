from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# Note: firebase_admin.firestore.SERVER_TIMESTAMP is a sentinel value, not a type for Pydantic.
# We'll handle its assignment in the route logic if needed for default creation/update times by Firestore server.
# For Pydantic, datetime is appropriate for fields that will hold timestamps.

class CustomerBase(BaseModel):
    lineId: Optional[str] = None
    displayName: Optional[str] = None
    title: Optional[str] = None
    firstName: Optional[str] = None # Assuming these can be optional based on common use cases
    lastName: Optional[str] = None  # Make them non-optional if they are always required
    dob: Optional[datetime] = None # Pydantic will parse ISO strings to datetime
    location: Optional[str] = None
    status: Optional[str] = None # e.g., "Active"
    setupDate: Optional[datetime] = None # Pydantic will parse ISO strings to datetime
    airViewNumber: Optional[str] = None
    monitoringType: Optional[str] = None
    availableData: Optional[str] = None
    dealerPatientId: Optional[str] = None
    organisation: Optional[Dict[str, Any]] = Field(default_factory=dict) # e.g., {"name": "Org Name"}
    clinicalUser: Optional[Dict[str, Any]] = Field(default_factory=dict) # e.g., {"name": "User Name"}
    compliance: Optional[Dict[str, Any]] = Field(default_factory=dict)   # e.g., {"status": "Compliant", "usagePercentage": 90}
    dataAccess: Optional[Dict[str, Any]] = Field(default_factory=dict)    # e.g., {"type": "Full", "duration": "30 days"}


class CustomerCreate(CustomerBase): # For creating new customers (input)
    # If setupDate should default to server time on creation and not provided by client:
    # setupDate: Optional[datetime] = None # Client can override, or we set SERVER_TIMESTAMP in route
    pass

class CustomerUpdate(BaseModel): # For updating customers (all fields optional)
    lineId: Optional[str] = None
    displayName: Optional[str] = None
    title: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    dob: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None
    setupDate: Optional[datetime] = None
    airViewNumber: Optional[str] = None
    monitoringType: Optional[str] = None
    availableData: Optional[str] = None
    dealerPatientId: Optional[str] = None
    organisation: Optional[Dict[str, Any]] = None
    clinicalUser: Optional[Dict[str, Any]] = None
    compliance: Optional[Dict[str, Any]] = None
    dataAccess: Optional[Dict[str, Any]] = None

class Customer(CustomerBase): # For responses (output, includes ID)
    id: str