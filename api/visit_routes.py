"""
Visit API Routes
Handles all visit-related endpoints for Streamlit
"""

from typing import Dict, List
import logging

from core.visits.visit_manager import VisitManager
from core.ai.gpt_engine import GPTEngine
from data.db.json_adapter import JSONAdapter

logger = logging.getLogger(__name__)

# Initialize services
db = JSONAdapter()
visit_manager = VisitManager(db)
gpt_engine = GPTEngine()


def save_visit(patient_id: str, visit_data: Dict) -> Dict:
    """Save a new visit"""
    try:
        return visit_manager.create_visit(patient_id, visit_data)
    except Exception as e:
        logger.error(f"Error saving visit: {e}")
        return {
            "success": False,
            "message": "Failed to save visit"
        }


def save_consultation(patient_id: str, visit_id: str, consultation_data: Dict) -> Dict:
    """Save consultation results (summary, prescription)"""
    try:
        return visit_manager.update_consultation(patient_id, visit_id, consultation_data)
    except Exception as e:
        logger.error(f"Error saving consultation: {e}")
        return {
            "success": False,
            "message": "Failed to save consultation"
        }


def get_patient_visits(patient_id: str) -> List[Dict]:
    """Get all visits for a patient"""
    try:
        return visit_manager.get_patient_visits(patient_id)
    except Exception as e:
        logger.error(f"Error getting visits: {e}")
        return []


def delete_patient_visit(patient_id: str, visit_id: str) -> Dict:
    """Delete a specific visit"""
    try:
        return visit_manager.delete_visit(patient_id, visit_id)
    except Exception as e:
        logger.error(f"Error deleting visit: {e}")
        return {
            "success": False,
            "message": "Failed to delete visit"
        }


def generate_clinical_summary(symptoms_text: str, patient_data: Dict = None, 
                            include_prescription: bool = True, 
                            format_type: str = "SOAP") -> Dict:
    """Generate AI clinical summary"""
    try:
        return gpt_engine.generate_summary(
            symptoms_text, 
            patient_data, 
            include_prescription, 
            format_type
        )
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return {
            "success": False,
            "summary": "Unable to generate summary",
            "prescription": "",
            "error": str(e)
        }


def check_longitudinal_risks(patient_id: str) -> Dict:
    """Check for longitudinal health risks"""
    try:
        patient_data = db.load_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found", "risks": []}
        
        risks = []
        
        # Get disease alerts from latest visit
        visits = patient_data.get('visits', [])
        if visits:
            latest_visit = visits[-1]
            if 'disease_alerts' in latest_visit:
                for alert in latest_visit['disease_alerts']:
                    risks.append({
                        'type': 'rare_disease',
                        'condition': alert['disease'],
                        'confidence': alert['confidence'],
                        'severity': alert.get('severity', 'moderate'),
                        'message': alert['message'],
                        'action': f"Consider testing: {', '.join(alert.get('suggested_tests', [])[:2])}"
                    })
        
        # Add other risk checks here (cancer screening, vitals trends, etc.)
        
        return {
            "success": True,
            "patient_id": patient_id,
            "risks": risks,
            "risk_count": len(risks),
            "high_risk_count": len([r for r in risks if r.get('severity') == 'high'])
        }
        
    except Exception as e:
        logger.error(f"Error checking risks: {e}")
        return {
            "success": False,
            "message": "Failed to check risks",
            "risks": []
        }