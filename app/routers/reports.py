from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1.client import Client
from google.cloud import firestore

from app.dependencies.auth import get_current_line_id
from app.dependencies.database import db_dependency
from app.core.config import settings
from app.models.report import ReportDetailResponse
from app.services.report_analyzer import analyze_report_data

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
    dependencies=[Depends(get_current_line_id)]
)

async def get_customer_id_from_line_id(line_id: str, db: Client) -> str:
    """Helper function to get customer ID from a line ID to avoid code duplication."""
    customers_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION)
    query = customers_ref.where("lineId", "==", line_id).limit(1)
    customer_docs = list(query.stream())
    if not customer_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No linked customer profile found for this LINE account."
        )
    return customer_docs[0].id

@router.get("/latest", response_model=ReportDetailResponse)
async def get_latest_report(
    line_id: str = Depends(get_current_line_id),
    db: Client = Depends(db_dependency)
):
    """
    Retrieves the most recent report for the current user.
    """
    try:
        customer_id = await get_customer_id_from_line_id(line_id, db)
        
        reports_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION).document(customer_id).collection(settings.FIRESTORE_REPORTS_SUBCOLLECTION)
        # Assuming report documents are named with 'YYYY-MM-DD', we can sort by name descending.
        query = reports_ref.order_by(firestore.Client.field_path.document_id(), direction=firestore.Query.DESCENDING).limit(1)
        report_docs = list(query.stream())

        if not report_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reports found for this user."
            )
        
        latest_report_data = report_docs[0].to_dict()
        raw_data = latest_report_data.get("rawData", {})

        analysis, overall_recommendation = analyze_report_data(raw_data)

        return ReportDetailResponse(
            rawData=raw_data,
            analysis=analysis,
            overallRecommendation=overall_recommendation
        )
    except Exception as e:
        print(f"Error retrieving latest report for line_id {line_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the latest report."
        )


@router.get("/{report_date}", response_model=ReportDetailResponse)
async def get_report_by_date(
    report_date: str, # e.g., "2023-10-27"
    line_id: str = Depends(get_current_line_id),
    db: Client = Depends(db_dependency)
):
    """
    Retrieves a specific daily report by date for the current user.
    """
    try:
        customer_id = await get_customer_id_from_line_id(line_id, db)

        report_ref = db.collection(settings.FIRESTORE_CUSTOMERS_COLLECTION).document(customer_id).collection(settings.FIRESTORE_REPORTS_SUBCOLLECTION).document(report_date)
        report_doc = report_ref.get()

        if not report_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report for date {report_date} not found."
            )
        
        report_data = report_doc.to_dict()
        raw_data = report_data.get("rawData", {})

        analysis, overall_recommendation = analyze_report_data(raw_data)

        return ReportDetailResponse(
            rawData=raw_data,
            analysis=analysis,
            overallRecommendation=overall_recommendation
        )
    except Exception as e:
        print(f"Error retrieving report for date {report_date} and line_id {line_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the report."
        )