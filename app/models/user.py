from pydantic import BaseModel, Field

class UserStatusResponse(BaseModel):
    """
    Response body for checking user account link status.
    """
    isLinked: bool = Field(..., description="True if the user's LINE account is linked, False otherwise.")

class LinkAccountRequest(BaseModel):
    """
    Request body for linking a LINE account to a patient record via serial number.
    """
    serialNumber: str = Field(..., description="The CPAP device serial number to link.")