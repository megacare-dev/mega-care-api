from pydantic import BaseModel, Field
from typing import Dict, Any

class AnalysisItem(BaseModel):
    """
    Represents the analysis for a single metric (e.g., usage, leak).
    """
    status: str = Field(..., description="Status of the metric, e.g., 'normal', 'high', 'low'")
    text: str = Field(..., description="A descriptive text for the metric's value and status.")
    recommendation: str = Field(..., description="A specific recommendation based on the metric's status.")

class Analysis(BaseModel):
    """
    Contains the analysis for all relevant metrics from the report.
    """
    usage: AnalysisItem
    leak: AnalysisItem
    # Note: Can be extended with other metrics like 'ahi' in the future
    # ahi: AnalysisItem

class ReportDetailResponse(BaseModel):
    """
    The complete response model for the daily report detail endpoint.
    """
    rawData: Dict[str, Any] = Field(..., description="The raw data from the device report.")
    analysis: Analysis = Field(..., description="The processed analysis of the raw data.")
    overallRecommendation: str = Field(..., description="A summary recommendation for the user based on the overall analysis.")