from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Device(BaseModel):
    """
    Represents a single CPAP device.
    Corresponds to documents in the 'devices' sub-collection.
    """
    serialNumber: str
    model: str
    lastSync: Optional[datetime] = None

class EquipmentResponse(BaseModel):
    """Response model for the equipment list endpoint."""
    devices: List[Device]