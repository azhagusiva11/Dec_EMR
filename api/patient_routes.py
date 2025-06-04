"""
Patient API Routes
Clean separation between Streamlit UI and business logic
"""

from typing import Dict, List
import logging

from core.patients.patient_manager import PatientManager
from core.patients.patient_model import PatientCreate, PatientUpdate
from core.clinical.vitals_validator import VitalsValidator
from data.db.json_adapter import JSONAdapter

logger = logging.getLogger(__name__)

# Initialize services
db = JSONAdapter()
patient_manager = PatientManager(db)
vitals_validator = VitalsValidator()


def register_patient(patient_data: Dict) -> Dict:
    """
    Register new patient with validation
    """
    try:
        # Validate and create patient model
        patient_create = PatientCreate(**patient_data)
        
        # Validate vitals if provided
        vitals_validation = None
        if 'vitals' in patient_data and patient_data['vitals']:
            vitals_validation = vitals_validator.validate_vitals(
                patient_data['vitals'],
                patient_create.age,
                patient_create.sex
            )
            
            # Add validation to response
            if vitals_validation['status'] != 'normal':
                logger.warning(f"Abnormal vitals during registration: {vitals_validation}")
        
        # Create patient
        result = patient_manager.create_patient(patient_create)
        
        # Add vitals validation to response
        if vitals_validation:
            result['vitals_validation'] = vitals_validation
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "message": f"Validation error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error registering patient: {e}")
        return {
            "success": False,
            "message": "Failed to register patient"
        }


def get_all_patients() -> List[Dict]:
    """Get all patients with summary info"""
    try:
        return patient_manager.get_all_patients()
    except Exception as e:
        logger.error(f"Error getting patients: {e}")
        return []


def get_patient_data(patient_id: str) -> Dict:
    """Get complete patient data"""
    try:
        patient = patient_manager.get_patient(patient_id)
        if patient:
            return patient
        return None
    except Exception as e:
        logger.error(f"Error getting patient {patient_id}: {e}")
        return None


def update_patient_data(patient_id: str, updates: Dict) -> Dict:
    """Update patient information"""
    try:
        patient_update = PatientUpdate(**updates)
        return patient_manager.update_patient(patient_id, patient_update)
    except ValueError as e:
        return {
            "success": False,
            "message": f"Validation error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error updating patient: {e}")
        return {
            "success": False,
            "message": "Failed to update patient"
        }


def search_patients(search_term: str) -> List[Dict]:
    """Search patients by name or mobile"""
    try:
        return patient_manager.search_patients(search_term)
    except Exception as e:
        logger.error(f"Error searching patients: {e}")
        return []


def delete_patient(patient_id: str) -> Dict:
    """Delete patient record"""
    try:
        return patient_manager.delete_patient(patient_id)
    except Exception as e:
        logger.error(f"Error deleting patient: {e}")
        return {
            "success": False,
            "message": "Failed to delete patient"
        }


def export_patient_data(patient_id: str, format: str = 'json') -> Dict:
    """Export patient data in specified format"""
    try:
        patient = patient_manager.get_patient(patient_id)
        if not patient:
            return {
                "success": False,
                "message": "Patient not found"
            }
        
        if format == 'json':
            return {
                "success": True,
                "data": patient,
                "format": "json"
            }
        
        # Add more formats as needed (CSV, PDF, etc.)
        return {
            "success": False,
            "message": f"Unsupported format: {format}"
        }
        
    except Exception as e:
        logger.error(f"Error exporting patient data: {e}")
        return {
            "success": False,
            "message": "Failed to export patient data"
        }


def get_patient_statistics() -> Dict:
    """Get overall patient statistics"""
    try:
        patients = patient_manager.get_all_patients()
        
        # Calculate statistics
        total_patients = len(patients)
        age_groups = {'0-18': 0, '19-40': 0, '41-60': 0, '60+': 0}
        gender_distribution = {'male': 0, 'female': 0, 'other': 0}
        
        for patient in patients:
            # Age groups
            age = patient.get('age', 0)
            if age <= 18:
                age_groups['0-18'] += 1
            elif age <= 40:
                age_groups['19-40'] += 1
            elif age <= 60:
                age_groups['41-60'] += 1
            else:
                age_groups['60+'] += 1
            
            # Gender
            sex = patient.get('sex', 'other').lower()
            if sex in gender_distribution:
                gender_distribution[sex] += 1
        
        return {
            'total_patients': total_patients,
            'age_distribution': age_groups,
            'gender_distribution': gender_distribution,
            'database_size_mb': db.get_database_size_mb()
        }
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return {
            'total_patients': 0,
            'age_distribution': {},
            'gender_distribution': {},
            'database_size_mb': 0
        }