from typing import Dict, Any
from app.models.report import AnalysisDetail, ReportDetailResponse

class ReportAnalyzerService:
    """
    Service responsible for processing raw report data and generating
    analysis and overall recommendations based on business rules.
    """
    
    def analyze_report(self, raw_data: Dict[str, Any]) -> ReportDetailResponse:
        """
        Analyzes raw report data and returns structured analysis and recommendations.
        
        Args:
            raw_data: A dictionary containing raw report data from Firestore.
                      Example: {"usageHours": 6, "ahi": 2.5, "leakRate": 15}
        
        Returns:
            A ReportDetailResponse object with processed analysis and recommendations.
        """
        analysis = {}
        recommendations = []

        # Usage analysis
        usage_hours = raw_data.get("usage_hours", 0)
        if usage_hours >= 4:
            analysis["usage"] = AnalysisDetail(
                status="normal",
                text=f"Your usage of {usage_hours:.1f} hours is good.",
                recommendation="Keep up the consistent use of your therapy."
            )
        else:
            analysis["usage"] = AnalysisDetail(
                status="low",
                text=f"Your usage of {usage_hours:.1f} hours is below the recommended 4 hours.",
                recommendation="Try to use your device for at least 4 hours per night for effective therapy."
            )
            recommendations.append("Focus on increasing your usage time.")

        # Leak analysis
        leak_rate = raw_data.get("leak_rate", 0)
        if leak_rate <= 24:
            analysis["leak"] = AnalysisDetail(
                status="normal",
                text=f"Your mask leak rate of {leak_rate:.1f} L/min is within the acceptable range.",
                recommendation="Your mask fit appears to be good."
            )
        else:
            analysis["leak"] = AnalysisDetail(
                status="high",
                text=f"Your mask leak rate of {leak_rate:.1f} L/min is high.",
                recommendation="Check your mask for a proper seal. Adjust the straps or consider a different mask style if leaks persist."
            )
            recommendations.append("Pay attention to your mask fit to reduce leaks.")

        # AHI analysis (example)
        ahi = raw_data.get("ahi", 0)
        if ahi < 5:
            analysis["ahi"] = AnalysisDetail(status="normal", text=f"Your AHI of {ahi:.1f} is excellent.", recommendation="Your therapy is effectively controlling sleep apnea events.")
        else:
            analysis["ahi"] = AnalysisDetail(status="high", text=f"Your AHI of {ahi:.1f} is elevated.", recommendation="Consult with your healthcare provider to discuss these results.")
            recommendations.append("Your AHI is higher than ideal; a consultation with your provider is recommended.")

        # Overall Recommendation
        if not recommendations:
            overall_recommendation = "Excellent results! Your therapy is on track. Keep up the great work."
        else:
            overall_recommendation = "Overall, your therapy is effective, but there are areas for improvement. " + " ".join(recommendations)

        return ReportDetailResponse(
            rawData=raw_data,
            analysis=analysis,
            overallRecommendation=overall_recommendation
        )