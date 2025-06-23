from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# --- Request Models ---

class LinkAccountRequest(BaseModel):
    serialNumber: str

# --- Response Models ---

class UserStatusResponse(BaseModel):
    isLinked: bool

# --- Firestore Data Models (for reference and internal use) ---

class Customer(BaseModel):
    id: str
    patientId: str
    firstName: str
    lastName: str
    lineId: Optional[str] = None
    setupDate: Optional[datetime] = None

class CustomerUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    lineId: Optional[str] = None