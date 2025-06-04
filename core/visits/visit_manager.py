"""
Visit Manager Service
Handles all visit-related operations with symptom tracking
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
import logging

from data.db.json_adapter import JSONAdapter
from core.clinical.symptom_analyzer import SymptomAnalyzer
from core.clinical.disease_detector import DiseaseDetectionEngine
from core.clinical.vitals_validator import VitalsValidator

logger = logging.getLogger(__name__)


class VisitManager:
    """Manages patient visits and consultations"""
    
    def __init__(self, data_adapter: JSONAdapter):
        self.db = data_adapter
        self.symptom_analyzer = SymptomAnalyzer()
        self.vitals_validator = VitalsValidator()
        
        # Initialize disease detector with config paths
        disease_config = "data/config/rare_diseases_comprehensive.json"
        symptom_scores = "data/config/symptom_severity_scores.json"
        
        # Check if configs exist, use watchlist as fallback
        if not os.path.exists(disease_config):
            disease_config = "data/config/disease_watchlist.json"
            
        self.disease_detector = DiseaseDetectionEngine(disease_config, symptom_scores)
    
    def create_visit(self, patient_id: str, visit_data: Dict) -> Dict:
        """
        Create a new visit for a patient
        """
        patient_data = self.db.load_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found"}
        
        # Generate visit ID and timestamp
        visit_data['visit_id'] = self._generate_visit_id()
        visit_data['timestamp'] = datetime.now().isoformat()
        
        # Validate vitals if present
        vitals_validation = None
        if 'vitals' in visit_data and visit_data['vitals']:
            vitals_validation = self.vitals_validator.validate_vitals(
                visit_data['vitals'],
                patient_data.get('age', 30),
                patient_data.get('sex', 'unknown')
            )
            visit_data['vitals_validation'] = vitals_validation
        
        # Extract symptoms from chief complaint
        symptoms = []
        if visit_data.get('chief_complaint'):
            symptoms = self.symptom_analyzer.extract_symptoms(visit_data['chief_complaint'])
            visit_data['extracted_symptoms'] = symptoms
        
        # Update symptom tracking
        if symptoms:
            self._update_symptom_tracking(patient_data, symptoms, visit_data['timestamp'])
        
        # Add visit to patient record
        if 'visits' not in patient_data:
            patient_data['visits'] = []
        patient_data['visits'].append(visit_data)
        
        # Run disease detection with error handling
        disease_alerts = []
        try:
            disease_alerts = self.disease_detector.detect_rare_diseases(
                patient_data,
                current_symptoms=symptoms,
                visit_date=visit_data['timestamp']
            )
            
            if disease_alerts:
                visit_data['disease_alerts'] = disease_alerts
                logger.info(f"Detected {len(disease_alerts)} disease alerts for patient {patient_id}")
                
        except Exception as e:
            logger.error(f"Disease detection failed for patient {patient_id}: {e}")
            # Continue without disease alerts - don't fail the entire visit
            visit_data['disease_detection_error'] = str(e)
        
        # Save updated patient data
        self.db.save_patient(patient_data)
        
        return {
            "success": True,
            "message": "Visit saved successfully",
            "visit_id": visit_data['visit_id'],
            "vitals_validation": vitals_validation,
            "disease_alerts": disease_alerts
        }
    
    def update_consultation(self, patient_id: str, visit_id: str, 
                          consultation_data: Dict) -> Dict:
        """
        Update visit with consultation results (summary, prescription, etc.)
        """
        patient_data = self.db.load_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found"}
        
        # Find the visit
        visit_index = None
        for i, visit in enumerate(patient_data.get('visits', [])):
            if visit.get('visit_id') == visit_id:
                visit_index = i
                break
        
        if visit_index is None:
            return {"success": False, "message": "Visit not found"}
        
        # Update visit with consultation data
        visit = patient_data['visits'][visit_index]
        visit.update({
            'summary': consultation_data.get('summary', ''),
            'prescription': consultation_data.get('prescription', ''),
            'consultation_timestamp': datetime.now().isoformat(),
            'format_type': consultation_data.get('format_type', 'SOAP')
        })
        
        # Extract symptoms from summary for better tracking
        if consultation_data.get('summary'):
            try:
                new_symptoms = self.symptom_analyzer.extract_symptoms(
                    consultation_data['summary']
                )
                if new_symptoms:
                    # Merge with existing symptoms
                    existing_symptoms = visit.get('extracted_symptoms', [])
                    all_symptoms = list(set(existing_symptoms + new_symptoms))
                    visit['extracted_symptoms'] = all_symptoms
                    
                    # Update tracking
                    self._update_symptom_tracking(
                        patient_data, new_symptoms, visit['timestamp']
                    )
            except Exception as e:
                logger.error(f"Failed to extract symptoms from summary: {e}")
        
        # Re-run disease detection with updated data
        all_symptoms = visit.get('extracted_symptoms', [])
        try:
            disease_alerts = self.disease_detector.detect_rare_diseases(
                patient_data,
                current_symptoms=all_symptoms,
                visit_date=visit['timestamp']
            )
            
            if disease_alerts:
                visit['disease_alerts'] = disease_alerts
        except Exception as e:
            logger.error(f"Disease detection failed during consultation update: {e}")
            # Keep any existing disease alerts
            disease_alerts = visit.get('disease_alerts', [])
        
        # Save updated data
        self.db.save_patient(patient_data)
        
        return {
            "success": True,
            "message": "Consultation saved successfully",
            "disease_alerts": disease_alerts,
            "prescription_warnings": []  # TODO: Add drug checker
        }
    
    def get_patient_visits(self, patient_id: str) -> List[Dict]:
        """Get all visits for a patient"""
        patient_data = self.db.load_patient(patient_id)
        if not patient_data:
            return []
        
        visits = patient_data.get('visits', [])
        
        # Sort by timestamp (newest first)
        visits.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return visits
    
    def get_visit(self, patient_id: str, visit_id: str) -> Optional[Dict]:
        """Get a specific visit"""
        patient_data = self.db.load_patient(patient_id)
        if not patient_data:
            return None
        
        for visit in patient_data.get('visits', []):
            if visit.get('visit_id') == visit_id:
                return visit
        
        return None
    
    def delete_visit(self, patient_id: str, visit_id: str) -> Dict:
        """Delete a specific visit"""
        patient_data = self.db.load_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found"}
        
        # Find and remove the visit
        original_count = len(patient_data.get('visits', []))
        patient_data['visits'] = [
            v for v in patient_data.get('visits', []) 
            if v.get('visit_id') != visit_id
        ]
        
        if len(patient_data['visits']) < original_count:
            # Visit was deleted, rebuild symptom tracking
            self._rebuild_symptom_tracking(patient_data)
            self.db.save_patient(patient_data)
            return {"success": True, "message": "Visit deleted successfully"}
        else:
            return {"success": False, "message": "Visit not found"}
    
    def _update_symptom_tracking(self, patient_data: Dict, symptoms: List[str], 
                               visit_date: str):
        """
        Update symptom tracking with deduplication per visit
        """
        if 'symptom_tracking' not in patient_data:
            patient_data['symptom_tracking'] = {}
        
        # Normalize visit date to date string (remove time)
        visit_date_str = visit_date.split('T')[0] if 'T' in visit_date else visit_date
        
        # Get unique symptoms for this visit (case-insensitive)
        unique_symptoms = set()
        for symptom in symptoms:
            if isinstance(symptom, str) and symptom.strip():
                normalized = symptom.strip().lower()
                unique_symptoms.add(normalized)
        
        # Update tracking - each symptom appears only ONCE per date
        for symptom in unique_symptoms:
            if symptom not in patient_data['symptom_tracking']:
                patient_data['symptom_tracking'][symptom] = []
            
            # Only add if not already tracked for this date
            existing_dates = [
                entry['date'] for entry in patient_data['symptom_tracking'][symptom]
            ]
            if visit_date_str not in existing_dates:
                patient_data['symptom_tracking'][symptom].append({
                    'date': visit_date_str,
                    'visit_date': visit_date  # Keep full timestamp
                })
    
    def _rebuild_symptom_tracking(self, patient_data: Dict):
        """Rebuild symptom tracking after visit deletion"""
        patient_data['symptom_tracking'] = {}
        
        # Re-process all remaining visits
        for visit in patient_data.get('visits', []):
            symptoms = visit.get('extracted_symptoms', [])
            if symptoms:
                self._update_symptom_tracking(
                    patient_data, symptoms, visit['timestamp']
                )
    
    def _generate_visit_id(self) -> str:
        """Generate unique visit ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"V{timestamp}"
    
    def get_visit_statistics(self, patient_id: str) -> Dict:
        """Get statistics about patient visits"""
        patient_data = self.db.load_patient(patient_id)
        if not patient_data:
            return {"total_visits": 0}
        
        visits = patient_data.get('visits', [])
        
        # Calculate statistics
        total_visits = len(visits)
        visits_with_alerts = len([v for v in visits if v.get('disease_alerts')])
        
        # Get date range
        if visits:
            timestamps = [v.get('timestamp', '') for v in visits]
            timestamps.sort()
            first_visit = timestamps[0].split('T')[0] if timestamps[0] else None
            last_visit = timestamps[-1].split('T')[0] if timestamps[-1] else None
        else:
            first_visit = last_visit = None
        
        return {
            'total_visits': total_visits,
            'visits_with_alerts': visits_with_alerts,
            'first_visit': first_visit,
            'last_visit': last_visit,
            'alert_rate': round(visits_with_alerts / total_visits * 100, 1) if total_visits > 0 else 0
        }