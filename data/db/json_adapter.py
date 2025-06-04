"""
JSON Database Adapter
Handles all file I/O operations for patient data
Future: Can be swapped with SQL adapter without changing business logic
"""

import os
import json
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class JSONAdapter:
    """
    Adapter for JSON file-based storage.
    Implements a clean interface that can be replaced with SQL later.
    """
    
    def __init__(self, data_dir: str = "data/patients"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def save_patient(self, patient_data: Dict) -> bool:
        """Save patient data to JSON file"""
        try:
            patient_id = patient_data['id']
            filepath = self.data_dir / f"{patient_id}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(patient_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved patient {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving patient: {e}")
            return False
    
    def load_patient(self, patient_id: str) -> Optional[Dict]:
        """Load patient data from JSON file"""
        try:
            filepath = self.data_dir / f"{patient_id}.json"
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading patient {patient_id}: {e}")
            return None
    
    def delete_patient(self, patient_id: str) -> bool:
        """Delete patient JSON file"""
        try:
            filepath = self.data_dir / f"{patient_id}.json"
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted patient {patient_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting patient {patient_id}: {e}")
            return False
    
    def get_all_patients(self) -> List[Dict]:
        """Get all patient records"""
        patients = []
        
        try:
            for filepath in self.data_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        patient_data = json.load(f)
                        patients.append(patient_data)
                except Exception as e:
                    logger.warning(f"Error reading {filepath}: {e}")
                    continue
            
            return patients
            
        except Exception as e:
            logger.error(f"Error getting all patients: {e}")
            return []
    
    def patient_exists(self, patient_id: str) -> bool:
        """Check if patient exists"""
        filepath = self.data_dir / f"{patient_id}.json"
        return filepath.exists()
    
    def get_patient_count(self) -> int:
        """Get total number of patients"""
        return len(list(self.data_dir.glob("*.json")))
    
    def get_database_size_mb(self) -> float:
        """Get total size of all patient files in MB"""
        total_size = 0
        
        for filepath in self.data_dir.glob("*.json"):
            total_size += filepath.stat().st_size
        
        return round(total_size / (1024 * 1024), 2)
    
    def backup_patient(self, patient_id: str) -> bool:
        """Create backup of patient data"""
        try:
            patient_data = self.load_patient(patient_id)
            if not patient_data:
                return False
            
            backup_dir = self.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{patient_id}_{timestamp}.json"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(patient_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created backup for patient {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def load_config(self, config_name: str) -> Dict:
        """Load configuration file from data/config"""
        try:
            config_path = Path("data/config") / f"{config_name}.json"
            
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_name}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading config {config_name}: {e}")
            return {}
    
    def save_config(self, config_name: str, config_data: Dict) -> bool:
        """Save configuration file"""
        try:
            config_dir = Path("data/config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            config_path = config_dir / f"{config_name}.json"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved config {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config {config_name}: {e}")
            return False