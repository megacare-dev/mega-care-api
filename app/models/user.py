from pydantic import BaseModel, Field

class LinkAccountRequest(BaseModel):
    """
    Request body for linking a LINE account with a CPAP serial number.
    """
    serialNumber: str = Field(..., description="CPAP Serial Number to link.")

class UserStatusResponse(BaseModel):
    """
    Response body for checking user account link status.
    """
    isLinked: bool = Field(..., description="True if the user's LINE account is linked, False otherwise.")