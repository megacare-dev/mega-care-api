from typing import Dict, Any, Tuple
from app.models.report import Analysis, AnalysisItem

def analyze_report_data(raw_data: Dict[str, Any]) -> Tuple[Analysis, str]:
    """
    Analyzes raw report data and generates analysis and recommendations.

    This is a placeholder for the actual business logic. In a real-world
    scenario, this function would contain complex rules to evaluate the data.
    """
    # Example placeholder logic:
    usage_hours = raw_data.get("usage_hours", 0)
    leak_rate = raw_data.get("leak_rate", 0)

    # Analyze usage
    if usage_hours >= 4:
        usage_status = "normal"
        usage_text = f"ใช้งาน {usage_hours:.1f} ชั่วโมง ถือว่าดี"
        usage_recommendation = "รักษามาตรฐานการใช้งานต่อไป"
    else:
        usage_status = "low"
        usage_text = f"ใช้งาน {usage_hours:.1f} ชั่วโมง น้อยกว่าที่แนะนำ"
        usage_recommendation = "พยายามใช้งานให้นานกว่า 4 ชั่วโมงต่อคืน"

    # Analyze leak
    if leak_rate <= 24:
        leak_status = "normal"
        leak_text = f"อัตราการรั่ว {leak_rate:.1f} L/min อยู่ในเกณฑ์ดี"
        leak_recommendation = "หน้ากากของคุณพอดีแล้ว"
    else:
        leak_status = "high"
        leak_text = f"อัตราการรั่ว {leak_rate:.1f} L/min สูงกว่าปกติ"
        leak_recommendation = "ตรวจสอบการใส่หน้ากากและความพอดี หรือปรึกษาผู้เชี่ยวชาญ"

    analysis = Analysis(
        usage=AnalysisItem(status=usage_status, text=usage_text, recommendation=usage_recommendation),
        leak=AnalysisItem(status=leak_status, text=leak_text, recommendation=leak_recommendation),
    )

    # Overall recommendation
    overall_recommendation = "โดยรวมแล้วการใช้งานของคุณดี โปรดรักษามาตรฐานนี้ไว้"
    if usage_status == "low" or leak_status == "high":
        overall_recommendation = "มีบางประเด็นที่ควรปรับปรุง โปรดดูคำแนะนำในแต่ละหัวข้อ"

    return analysis, overall_recommendation