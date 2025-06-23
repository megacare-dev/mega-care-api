from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.field_path import FieldPath
from app.dependencies.auth import get_current_line_id
from app.dependencies.database import get_db
from app.models.report import ReportDetailResponse
from app.core.config import settings
from app.services.report_analyzer import ReportAnalyzerService

router = APIRouter(prefix="/reports", tags=["reports"])

async def _find_customer_ref(line_id: str, db: firestore.Client):
    """Helper function to find a customer's document reference by their line_id."""
    customers_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION)
    customer_query = customers_ref.where(filter=FieldFilter("lineId", "==", line_id)).limit(1)
    customer_docs = list(customer_query.stream())

    if not customer_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No linked customer profile found for the provided token."
        )
    return customer_docs[0].reference

@router.get("/latest", response_model=ReportDetailResponse, summary="Get the latest report for the linked user")
async def get_latest_report(
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    customer_ref = await _find_customer_ref(line_id, db)
    
    reports_ref = customer_ref.collection(settings.FIRESTORE_REPORTS_SUBCOLLECTION)
    # Order by document ID (which is the date string 'YYYY-MM-DD') descending
    latest_report_query = reports_ref.order_by(
        FieldPath.document_id(), direction=firestore.Query.DESCENDING
    ).limit(1)
    
    latest_docs = list(latest_report_query.stream())
    
    if not latest_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reports found for this user."
        )
        
    report_data = latest_docs[0].to_dict()
    raw_data = report_data.get("rawData", {})
    
    analyzer = ReportAnalyzerService()
    return analyzer.analyze_report(raw_data)

@router.get("/{reportDate}", response_model=ReportDetailResponse, summary="Get a specific daily report and analysis")
async def get_report_by_date(
    reportDate: str, # e.g., "YYYY-MM-DD"
    line_id: str = Depends(get_current_line_id),
    db: firestore.Client = Depends(get_db)
):
    customer_ref = await _find_customer_ref(line_id, db)
    report_doc_ref = customer_ref.collection(settings.FIRESTORE_REPORTS_SUBCOLLECTION).document(reportDate)
    report_doc = report_doc_ref.get()
    
    if not report_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report for date {reportDate} not found.")
        
    report_data = report_doc.to_dict()
    raw_data = report_data.get("rawData", {})
    
    analyzer = ReportAnalyzerService()
    return analyzer.analyze_report(raw_data)