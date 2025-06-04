"""
Analytics and Utility API Routes - UPDATED FOR LIVE TRACKING
Handles dashboard, statistics, and utility functions
"""

import os
import json
from typing import Dict, List
import logging
from datetime import datetime, timedelta

from data.db.json_adapter import JSONAdapter

logger = logging.getLogger(__name__)

# Initialize services
db = JSONAdapter()


def get_patient_analytics() -> Dict:
    """Get overall system analytics - UPDATED FOR LIVE METRICS"""
    try:
        total_patients = 0
        total_visits = 0
        visits_today = 0
        ai_summaries_today = 0
        prescriptions_edited = 0
        api_success_count = 0
        api_fallback_count = 0
        recent_visits = []
        doctor_usage = {}
        
        # Get today's date
        today = datetime.now().date()
        
        # Process all patients
        for patient_data in db.get_all_patients():
            total_patients += 1
            visits = patient_data.get('visits', [])
            total_visits += len(visits)
            
            # Count today's visits and metrics
            for visit in visits:
                visit_date_str = visit.get('timestamp', '')
                if visit_date_str:
                    visit_date = datetime.fromisoformat(visit_date_str.split('T')[0]).date()
                    
                    # Check if visit is today
                    if visit_date == today:
                        visits_today += 1
                        
                        # Count AI summaries
                        if visit.get('summary'):
                            ai_summaries_today += 1
                            
                        # Check if prescription was edited
                        if visit.get('prescription_edited'):
                            prescriptions_edited += 1
                            
                        # Track API success/fallback
                        if visit.get('ai_success', True):
                            api_success_count += 1
                        else:
                            api_fallback_count += 1
                            
                        # Track doctor usage
                        doctor = visit.get('doctor', 'Unknown')
                        if doctor not in doctor_usage:
                            doctor_usage[doctor] = 0
                        doctor_usage[doctor] += 1
            
            # Get recent visits (last 10)
            for visit in visits[-5:]:
                recent_visits.append({
                    'patient_name': patient_data['name'],
                    'visit_date': visit.get('timestamp', 'Unknown'),
                    'doctor': visit.get('doctor', 'Unknown'),
                    'has_feedback': bool(visit.get('feedback'))
                })
        
        # Sort recent visits
        recent_visits.sort(key=lambda x: x['visit_date'], reverse=True)
        
        # Calculate rates
        prescription_edit_rate = round((prescriptions_edited / ai_summaries_today * 100), 1) if ai_summaries_today > 0 else 0
        api_success_rate = round((api_success_count / (api_success_count + api_fallback_count) * 100), 1) if (api_success_count + api_fallback_count) > 0 else 100
        
        return {
            'total_patients': total_patients,
            'total_visits': total_visits,
            'visits_today': visits_today,
            'ai_summaries_today': ai_summaries_today,
            'prescriptions_edited': prescriptions_edited,
            'prescription_edit_rate': prescription_edit_rate,
            'api_success_rate': api_success_rate,
            'recent_visits': recent_visits[:10],
            'doctor_usage': doctor_usage,
            'avg_visits_per_patient': round(total_visits / total_patients, 1) if total_patients > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {
            'total_patients': 0,
            'total_visits': 0,
            'visits_today': 0,
            'ai_summaries_today': 0,
            'prescriptions_edited': 0,
            'prescription_edit_rate': 0,
            'api_success_rate': 100,
            'recent_visits': [],
            'doctor_usage': {},
            'avg_visits_per_patient': 0
        }


def get_feedback_stats() -> Dict:
    """Get feedback statistics - UPDATED"""
    try:
        total_feedback = 0
        total_rating = 0
        thumbs_up = 0
        thumbs_down = 0
        feedback_by_doctor = {}
        
        for patient_data in db.get_all_patients():
            for visit in patient_data.get('visits', []):
                if 'feedback' in visit:
                    feedback = visit['feedback']
                    total_feedback += 1
                    
                    # Count thumbs up/down
                    if feedback.get('helpful') == True:
                        thumbs_up += 1
                    elif feedback.get('helpful') == False:
                        thumbs_down += 1
                    
                    # Count ratings
                    if 'rating' in feedback:
                        total_rating += feedback['rating']
                    
                    # Track by doctor
                    doctor = visit.get('doctor', 'Unknown')
                    if doctor not in feedback_by_doctor:
                        feedback_by_doctor[doctor] = {'total': 0, 'positive': 0}
                    feedback_by_doctor[doctor]['total'] += 1
                    if feedback.get('helpful') == True:
                        feedback_by_doctor[doctor]['positive'] += 1
        
        return {
            'total_feedback': total_feedback,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'average_rating': round(total_rating / total_feedback, 2) if total_feedback > 0 else 0,
            'satisfaction_rate': round((thumbs_up / total_feedback) * 100, 1) if total_feedback > 0 else 0,
            'feedback_by_doctor': feedback_by_doctor
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        return {
            'total_feedback': 0,
            'thumbs_up': 0,
            'thumbs_down': 0,
            'average_rating': 0,
            'satisfaction_rate': 0,
            'feedback_by_doctor': {}
        }


def save_visit_feedback(patient_id: str, visit_id: str, feedback_data: Dict) -> Dict:
    """Save feedback for a visit - NEW FUNCTION"""
    try:
        patient_data = db.load_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found"}
        
        # Find the visit
        for visit in patient_data.get('visits', []):
            if visit.get('visit_id') == visit_id:
                # Save feedback
                visit['feedback'] = {
                    'timestamp': datetime.now().isoformat(),
                    'helpful': feedback_data.get('helpful'),  # True/False for thumbs up/down
                    'rating': feedback_data.get('rating'),  # 1-5 stars
                    'comment': feedback_data.get('comment', ''),
                    'doctor': feedback_data.get('doctor', 'Unknown')
                }
                
                # Track if prescription was edited
                if 'prescription_edited' in feedback_data:
                    visit['prescription_edited'] = feedback_data['prescription_edited']
                
                # Save updated data
                db.save_patient(patient_data)
                
                return {
                    "success": True,
                    "message": "Feedback saved successfully"
                }
        
        return {"success": False, "message": "Visit not found"}
        
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        return {
            "success": False,
            "message": "Failed to save feedback"
        }


def get_doctor_performance(doctor_name: str) -> Dict:
    """Get performance metrics for a specific doctor - NEW FUNCTION"""
    try:
        visits_count = 0
        ai_summaries = 0
        prescriptions_edited = 0
        positive_feedback = 0
        total_feedback = 0
        avg_time_per_visit = []
        
        for patient_data in db.get_all_patients():
            for visit in patient_data.get('visits', []):
                if visit.get('doctor') == doctor_name:
                    visits_count += 1
                    
                    if visit.get('summary'):
                        ai_summaries += 1
                    
                    if visit.get('prescription_edited'):
                        prescriptions_edited += 1
                    
                    if 'feedback' in visit:
                        total_feedback += 1
                        if visit['feedback'].get('helpful') == True:
                            positive_feedback += 1
                    
                    # Calculate time spent (if consultation_timestamp exists)
                    if 'consultation_timestamp' in visit and 'timestamp' in visit:
                        try:
                            start = datetime.fromisoformat(visit['timestamp'])
                            end = datetime.fromisoformat(visit['consultation_timestamp'])
                            time_spent = (end - start).total_seconds() / 60  # minutes
                            if 0 < time_spent < 60:  # Reasonable consultation time
                                avg_time_per_visit.append(time_spent)
                        except:
                            pass
        
        return {
            'doctor_name': doctor_name,
            'total_visits': visits_count,
            'ai_summaries_used': ai_summaries,
            'prescriptions_edited': prescriptions_edited,
            'edit_rate': round((prescriptions_edited / ai_summaries * 100), 1) if ai_summaries > 0 else 0,
            'positive_feedback': positive_feedback,
            'total_feedback': total_feedback,
            'satisfaction_rate': round((positive_feedback / total_feedback * 100), 1) if total_feedback > 0 else 0,
            'avg_consultation_time': round(sum(avg_time_per_visit) / len(avg_time_per_visit), 1) if avg_time_per_visit else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting doctor performance: {e}")
        return {
            'doctor_name': doctor_name,
            'total_visits': 0,
            'ai_summaries_used': 0,
            'prescriptions_edited': 0,
            'edit_rate': 0,
            'positive_feedback': 0,
            'total_feedback': 0,
            'satisfaction_rate': 0,
            'avg_consultation_time': 0
        }


# Keep existing functions unchanged
def initialize_rare_disease_matrix() -> Dict:
    """Initialize or reload disease configurations"""
    try:
        # Check which config files exist
        configs_loaded = []
        disease_count = 0
        
        config_files = [
            'rare_diseases_comprehensive',
            'disease_watchlist',
            'rare_disease_matrix'
        ]
        
        for config_name in config_files:
            config_data = db.load_config(config_name)
            if config_data:
                configs_loaded.append(config_name)
                if isinstance(config_data, dict):
                    if 'diseases' in config_data:
                        disease_count += len(config_data['diseases'])
                    else:
                        disease_count += len(config_data)
        
        return {
            "success": True,
            "message": f"Loaded {disease_count} diseases from {len(configs_loaded)} config files",
            "configs_loaded": configs_loaded,
            "disease_count": disease_count
        }
        
    except Exception as e:
        logger.error(f"Error initializing disease matrix: {e}")
        return {
            "success": False,
            "message": str(e),
            "disease_count": 0
        }


def get_cancer_screening_alerts(patient_id: str = None) -> List[Dict]:
    """Get cancer screening recommendations"""
    alerts = []
    
    try:
        if patient_id:
            # Get alerts for specific patient
            patient_data = db.load_patient(patient_id)
            if patient_data:
                alerts = _check_cancer_screening_for_patient(patient_data)
        else:
            # Get alerts for all patients
            for patient_data in db.get_all_patients():
                patient_alerts = _check_cancer_screening_for_patient(patient_data)
                alerts.extend(patient_alerts)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting cancer screening alerts: {e}")
        return []


def _check_cancer_screening_for_patient(patient_data: Dict) -> List[Dict]:
    """Check cancer screening needs for a patient"""
    alerts = []
    age = patient_data.get('age', 0)
    sex = patient_data.get('sex', '').lower()
    
    # Breast cancer screening
    if sex == 'female' and age >= 40:
        alerts.append({
            'patient_id': patient_data['id'],
            'patient_name': patient_data['name'],
            'screening_type': 'Breast Cancer Screening',
            'test_recommended': 'Mammography',
            'reason': f'Recommended for women age {age}',
            'frequency': 'Annual' if age >= 45 else 'Every 2 years'
        })
    
    # Cervical cancer screening
    if sex == 'female' and 21 <= age <= 65:
        alerts.append({
            'patient_id': patient_data['id'],
            'patient_name': patient_data['name'],
            'screening_type': 'Cervical Cancer Screening',
            'test_recommended': 'Pap smear',
            'reason': f'Recommended for women age {age}',
            'frequency': 'Every 3 years (21-29), Every 5 years with HPV test (30-65)'
        })
    
    # Colorectal cancer screening
    if age >= 45:
        alerts.append({
            'patient_id': patient_data['id'],
            'patient_name': patient_data['name'],
            'screening_type': 'Colorectal Cancer Screening',
            'test_recommended': 'Colonoscopy or FIT',
            'reason': f'Recommended for adults age {age}',
            'frequency': 'Colonoscopy every 10 years or FIT annually'
        })
    
    return alerts


def save_clinician_feedback(patient_id: str, visit_id: str, feedback_data: Dict) -> Dict:
    """Save clinician feedback for a visit"""
    try:
        patient_data = db.load_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found"}
        
        # Find the visit
        for visit in patient_data.get('visits', []):
            if visit.get('visit_id') == visit_id:
                # Initialize feedback list if not exists
                if 'clinician_feedback' not in visit:
                    visit['clinician_feedback'] = []
                
                # Add feedback entry
                feedback_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'summary_accuracy': feedback_data.get('summary_accuracy', 0),
                    'prescription_appropriate': feedback_data.get('prescription_appropriate', False),
                    'disease_alert_helpful': feedback_data.get('disease_alert_helpful', False),
                    'overall_rating': feedback_data.get('overall_rating', 0),
                    'comments': feedback_data.get('comments', '')
                }
                
                visit['clinician_feedback'].append(feedback_entry)
                
                # Update edited content if provided
                if 'edited_summary' in feedback_data:
                    visit['original_summary'] = visit.get('summary', '')
                    visit['summary'] = feedback_data['edited_summary']
                    visit['summary_edited'] = True
                
                if 'edited_prescription' in feedback_data:
                    visit['original_prescription'] = visit.get('prescription', '')
                    visit['prescription'] = feedback_data['edited_prescription']
                    visit['prescription_edited'] = True
                
                # Save updated data
                db.save_patient(patient_data)
                
                return {
                    "success": True,
                    "message": "Feedback saved successfully"
                }
        
        return {"success": False, "message": "Visit not found"}
        
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        return {
            "success": False,
            "message": "Failed to save feedback"
        }


def extract_text_from_pdf(pdf_file) -> Dict:
    """Extract text from uploaded PDF"""
    try:
        # Try PyPDF2 first
        try:
            import PyPDF2
            text = ""
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return {"success": True, "text": text}
            
        except ImportError:
            # Try pdfplumber as fallback
            try:
                import pdfplumber
                text = ""
                
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                return {"success": True, "text": text}
                
            except ImportError:
                return {
                    "success": False,
                    "text": "",
                    "error": "No PDF library installed. Install PyPDF2 or pdfplumber."
                }
        
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }


def generate_referral_letter(patient_data: Dict, visit_data: Dict, disease_alert: Dict) -> str:
    """Generate referral letter text"""
    try:
        from datetime import datetime
        
        letter = f"""
Date: {datetime.now().strftime('%d-%b-%Y')}

To,
The Specialist Doctor
{', '.join(disease_alert.get('specialists', ['Concerned Specialist']))}

Subject: Referral for evaluation of suspected {disease_alert['disease']}

Dear Doctor,

I am referring {patient_data['name']}, {patient_data['age']} year old {patient_data['sex']}, 
for your expert evaluation regarding suspected {disease_alert['disease']} 
(ICD: {disease_alert.get('icd_code', 'Not specified')}).

CLINICAL PRESENTATION:
The patient has presented with the following symptoms across {disease_alert['visit_count']} visits 
over {disease_alert['days_span']} days:

{_format_symptom_timeline(disease_alert.get('timeline', []))}

CLINICAL SUMMARY:
{visit_data.get('summary', 'See attached clinical notes')}

RATIONALE FOR REFERRAL:
Our EMR's rare disease detection system identified a pattern consistent with {disease_alert['disease']} 
with {disease_alert['confidence']*100:.0f}% confidence based on longitudinal symptom tracking.

SUGGESTED INVESTIGATIONS:
{_format_list(disease_alert.get('suggested_tests', ['As per your clinical judgment']))}

I would be grateful if you could evaluate this patient and provide your expert opinion.

Thank you for your time and consideration.

Sincerely,

Dr. _________________
[Your Clinic Name]
Contact: {patient_data.get('mobile', 'Not provided')}
"""
        
        return letter
        
    except Exception as e:
        logger.error(f"Error generating referral letter: {e}")
        return "Error generating referral letter"


def _format_symptom_timeline(timeline: List[Dict]) -> str:
    """Format symptom timeline for display"""
    if not timeline:
        return "No timeline available"
    
    lines = []
    for item in timeline:
        lines.append(f"- {item['symptom'].title()}: {item['date']}")
    
    return '\n'.join(lines)


def _format_list(items: List[str]) -> str:
    """Format list items"""
    if not items:
        return "None specified"
    
    return '\n'.join(f"- {item}" for item in items)