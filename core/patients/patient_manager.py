"""
Patient Manager Service
Handles all patient CRUD operations with clean separation of concerns
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

from core.patients.patient_model import Patient, PatientCreate, PatientUpdate
from data.db.json_adapter import JSONAdapter

logger = logging.getLogger(__name__)


class PatientManager:
    """Manages patient data operations"""
    
    def __init__(self, data_adapter: JSONAdapter):
        self.db = data_adapter
        
    def create_patient(self, patient_data: PatientCreate) -> Dict:
        """
        Create a new patient with validation
        """
        # Check for duplicate mobile
        existing = self.find_by_mobile(patient_data.mobile)
        if existing:
            return {
                "success": False,
                "message": "Patient with this mobile number already exists",
                "existing_patient": existing
            }
        
        # Create patient object
        patient = Patient(
            id=self._generate_patient_id(),
            name=patient_data.name,
            age=patient_data.age,
            sex=patient_data.sex,
            mobile=patient_data.mobile,
            blood_group=patient_data.blood_group,
            address=patient_data.address,
            registration_date=datetime.now().isoformat(),
            visits=[],
            symptom_tracking={},
            admissions=[]
        )
        
        # Save to database
        self.db.save_patient(patient.dict())
        
        return {
            "success": True,
            "patient_id": patient.id,
            "message": "Patient registered successfully"
        }
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient by ID"""
        return self.db.load_patient(patient_id)
    
    def update_patient(self, patient_id: str, updates: PatientUpdate) -> Dict:
        """Update patient information"""
        patient_data = self.get_patient(patient_id)
        if not patient_data:
            return {"success": False, "message": "Patient not found"}
        
        # Update only provided fields
        update_dict = updates.dict(exclude_unset=True)
        patient_data.update(update_dict)
        
        # Save changes
        self.db.save_patient(patient_data)
        
        return {
            "success": True,
            "message": "Patient updated successfully"
        }
    
    def delete_patient(self, patient_id: str) -> Dict:
        """Delete patient record"""
        if not self.get_patient(patient_id):
            return {"success": False, "message": "Patient not found"}
        
        self.db.delete_patient(patient_id)
        return {"success": True, "message": "Patient deleted successfully"}
    
    def get_all_patients(self) -> List[Dict]:
        """Get all patients with summary info"""
        patients = []
        
        for patient_data in self.db.get_all_patients():
            patients.append({
                'id': patient_data['id'],
                'name': patient_data['name'],
                'age': patient_data.get('age'),
                'sex': patient_data.get('sex'),
                'mobile': patient_data.get('mobile'),
                'registration_date': patient_data.get('registration_date'),
                'visit_count': len(patient_data.get('visits', [])),
                'last_visit': patient_data.get('visits', [{}])[-1].get('timestamp') 
                             if patient_data.get('visits') else None
            })
        
        # Sort by registration date (newest first)
        patients.sort(key=lambda x: x.get('registration_date', ''), reverse=True)
        return patients
    
    def search_patients(self, search_term: str) -> List[Dict]:
        """Search patients by name or mobile"""
        results = []
        search_term = search_term.lower()
        
        for patient_data in self.db.get_all_patients():
            name = patient_data.get('name', '').lower()
            mobile = patient_data.get('mobile', '').lower()
            
            if search_term in name or search_term in mobile:
                results.append({
                    'id': patient_data['id'],
                    'name': patient_data['name'],
                    'mobile': patient_data['mobile'],
                    'age': patient_data.get('age'),
                    'sex': patient_data.get('sex')
                })
        
        return results
    
    def find_by_mobile(self, mobile: str) -> Optional[Dict]:
        """Find patient by mobile number"""
        for patient_data in self.db.get_all_patients():
            if patient_data.get('mobile') == mobile:
                return patient_data
        return None
    
    def _generate_patient_id(self) -> str:
        """Generate unique patient ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"P{timestamp}"