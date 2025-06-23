from pydantic import BaseModel
from typing import List

class Equipment(BaseModel):
    serialNumber: str
    model: str

class EquipmentListResponse(BaseModel):
    devices: List[Equipment]