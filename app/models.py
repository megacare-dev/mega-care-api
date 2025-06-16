from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# Note: firebase_admin.firestore.SERVER_TIMESTAMP is a sentinel value, not a type for Pydantic.
# We'll handle its assignment in the route logic if needed for default creation/update times by Firestore server.
# For Pydantic, datetime is appropriate for fields that will hold timestamps.

class DeviceSettings(BaseModel):
    # Define your device settings fields here
    # Example:
    mode: Optional[str] = None
    pressure: Optional[int] = None
    # Add other settings as per your original DeviceSettings interface

class DeviceBase(BaseModel):
    deviceName: str
    serialNumber: str
    addedDate: Optional[datetime] = None # Pydantic will parse ISO strings to datetime
    status: Optional[str] = "active"
    settings: Optional[DeviceSettings | Dict[str, Any]] = Field(default_factory=dict)

class DeviceCreate(DeviceBase): # For creating new devices (input)
    pass

class Device(DeviceBase): # For responses (output, includes ID)
    id: str

class CustomerBase(BaseModel):
    lineId: Optional[str] = None
    displayName: Optional[str] = None
    title: Optional[str] = None
    firstName: str
    lastName: str
    dob: Optional[datetime] = None # Pydantic will parse ISO strings to datetime
    gender: Optional[str] = None
    hn: Optional[str] = None # Hospital Number
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    setupDate: Optional[datetime] = None # Pydantic will parse ISO strings to datetime
    physician: Optional[str] = None
    technician: Optional[str] = None
    branch: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)

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
    # ... include all other fields from CustomerBase as Optional ...
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class Customer(CustomerBase): # For responses (output, includes ID)
    id: str