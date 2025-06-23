from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AnalysisDetail(BaseModel):
    """
    Model for individual analysis sections (e.g., usage, leak, AHI).
    """
    status: str = Field(..., description="Status of the analysis (e.g., 'normal', 'high', 'low').")
    text: str = Field(..., description="Descriptive text for the analysis.")
    recommendation: str = Field(..., description="Recommendation based on the analysis.")

class ReportDetailResponse(BaseModel):
    """
    Response body for fetching a daily report and its analysis.
    """
    rawData: Dict[str, Any] = Field(..., description="Raw data fetched from Firestore for the specific report date.")
    analysis: Dict[str, AnalysisDetail] = Field(
        ...,
        description="Detailed analysis for various metrics (e.g., 'usage', 'leak', 'ahi').",
        example={
            "usage": {"status": "normal", "text": "Usage is good.", "recommendation": "Keep it up."},
            "leak": {"status": "high", "text": "High leak detected.", "recommendation": "Check mask fit."}
        }
    )
    overallRecommendation: str = Field(
        ...,
        description="Overall summary recommendation for the report.",
        example="Overall, your therapy is effective, but pay attention to mask leaks."
    )