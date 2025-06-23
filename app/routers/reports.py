from fastapi import APIRouter, Depends, HTTPException, status, Query
from firebase_admin import firestore
from app.dependencies.auth import get_current_line_id
from app.firebase_config import get_db
from app.models.report import ReportDetailResponse
from app.core.config import settings
from app.services.report_analyzer import ReportAnalyzerService
from typing import Optional

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/latest", summary="Get the latest report for the linked user")
async def get_latest_report(
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    # TODO: Implement logic to find patientId from line_id,
    # then query the 'reports' subcollection for the latest report.
    # This will involve querying customers collection for line_id, then getting subcollection.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet.")

@router.get("/{reportDate}", response_model=ReportDetailResponse, summary="Get a specific daily report and analysis")
async def get_report_by_date(
    reportDate: str, # e.g., "YYYY-MM-DD"
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    # TODO: Implement logic to find patientId from line_id,
    # then query the 'reports' subcollection for the specific reportDate.
    # Use ReportAnalyzerService to process raw data into analysis and overallRecommendation.
    analyzer = ReportAnalyzerService()
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet.")