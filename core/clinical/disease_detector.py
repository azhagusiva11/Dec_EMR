"""
Rare Disease Detection Engine
Implements longitudinal pattern recognition with false positive prevention
FIXED VERSION - Handles both list and dict formats
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set, Optional
import logging

from core.clinical.intelligent_filter import IntelligentFilter
from core.clinical.symptom_analyzer import SymptomAnalyzer

logger = logging.getLogger(__name__)


class DiseaseDetectionEngine:
    """
    Detects rare diseases based on longitudinal symptom patterns.
    Key features:
    - Minimum 2 visits, 7+ days requirement
    - Symptom deduplication per visit
    - Intelligent filtering of common conditions
    - Confidence-based alerting
    """
    
    def __init__(self, disease_config_path: str, symptom_scores_path: str):
        self.diseases = self._load_disease_config(disease_config_path)
        self.symptom_scores = self._load_symptom_scores(symptom_scores_path)
        self.intelligent_filter = IntelligentFilter()
        self.symptom_analyzer = SymptomAnalyzer()
        
    def detect_rare_diseases(self, patient_data: Dict, 
                           current_symptoms: List[str] = None,
                           visit_date: str = None) -> List[Dict]:
        """
        Main detection method with all safety checks
        """
        disease_alerts = []
        symptom_tracking = patient_data.get('symptom_tracking', {})
        
        # FIX: Handle both list and dict formats
        if isinstance(self.diseases, list):
            # Convert list to dict on the fly
            diseases_dict = {}
            for disease in self.diseases:
                if isinstance(disease, dict) and 'name' in disease:
                    key = disease['name'].lower().replace(' ', '_').replace("'", "")
                    diseases_dict[key] = disease
            diseases_to_check = diseases_dict
        else:
            diseases_to_check = self.diseases
        
        # Analyze each disease
        for disease_id, config in diseases_to_check.items():
            alert = self._check_disease_pattern(
                disease_id, config, symptom_tracking, visit_date
            )
            
            if alert:
                # Apply intelligent filtering
                should_alert, adjusted_confidence, ruled_out = \
                    self.intelligent_filter.should_alert(
                        alert['matched_symptoms'],
                        patient_data,
                        alert['confidence']
                    )
                
                if should_alert:
                    alert['confidence'] = adjusted_confidence
                    alert['ruled_out_conditions'] = ruled_out
                    disease_alerts.append(alert)
                else:
                    logger.info(f"Filtered out {config['name']}: {ruled_out}")
        
        # Sort by confidence
        disease_alerts.sort(key=lambda x: x['confidence'], reverse=True)
        return disease_alerts
    
    def _check_disease_pattern(self, disease_id: str, config: Dict,
                              symptom_tracking: Dict, visit_date: str) -> Optional[Dict]:
        """
        Check if patient matches disease pattern
        """
        # Extract parameters - handle both old and new config formats
        if 'symptoms' in config:
            # Handle both nested symptoms (dict with categories) and flat list
            if isinstance(config['symptoms'], dict):
                # Flatten categorized symptoms
                required_symptoms = set()
                for category, symptoms in config['symptoms'].items():
                    if isinstance(symptoms, list):
                        required_symptoms.update(s.lower() for s in symptoms)
            elif isinstance(config['symptoms'], list):
                required_symptoms = set(s.lower() for s in config['symptoms'])
            else:
                required_symptoms = set()
        else:
            required_symptoms = set()
            
        min_matches = config.get('min_matches', config.get('min_symptoms', 3))
        time_window = config.get('time_window_days', 365)
        min_visits = config.get('min_visits_required', 2)
        min_timespan = config.get('min_timespan_days', 7)
        
        # Track matched symptoms
        matched_symptoms = []
        visit_dates = set()
        symptom_timeline = []
        
        # Check each symptom
        for symptom in required_symptoms:
            if symptom in symptom_tracking:
                occurrences = self._filter_by_time_window(
                    symptom_tracking[symptom], visit_date, time_window
                )
                
                if occurrences:
                    matched_symptoms.append(symptom)
                    for occ in occurrences:
                        visit_dates.add(occ['date'])
                        symptom_timeline.append({
                            'symptom': symptom,
                            'date': occ['date']
                        })
        
        # Check minimum requirements
        if len(matched_symptoms) < min_matches:
            return None
        
        visit_count = len(visit_dates)
        if visit_count < min_visits:
            logger.debug(f"{config['name']}: Only {visit_count} visits, need {min_visits}")
            return None
        
        # Calculate timespan
        if visit_dates:
            sorted_dates = sorted(visit_dates)
            first_date = datetime.fromisoformat(sorted_dates[0])
            last_date = datetime.fromisoformat(sorted_dates[-1])
            days_span = (last_date - first_date).days
            
            if days_span < min_timespan:
                logger.debug(f"{config['name']}: Span {days_span} days, need {min_timespan}")
                return None
        else:
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            matched_symptoms, list(required_symptoms),
            visit_count, days_span, config
        )
        
        # Determine severity
        severity = self._determine_severity(confidence, matched_symptoms)
        
        # Create alert
        return {
            'disease_id': disease_id,
            'disease': config['name'],
            'confidence': confidence,
            'matched_symptoms': matched_symptoms,
            'matched_count': len(matched_symptoms),
            'required_count': min_matches,
            'visit_count': visit_count,
            'days_span': days_span,
            'severity': severity,
            'timeline': sorted(symptom_timeline, key=lambda x: x['date']),
            'suggested_tests': config.get('suggested_tests', config.get('diagnostic_tests', [])),
            'specialists': config.get('specialists', [config.get('specialist', 'Specialist')]),
            'icd_code': config.get('icd_code', config.get('icd10', '')),
            'message': self._generate_alert_message(
                config['name'], matched_symptoms, visit_count, days_span, confidence
            )
        }
    
    def _filter_by_time_window(self, occurrences: List[Dict], 
                              visit_date: str, window_days: int) -> List[Dict]:
        """Filter symptom occurrences by time window"""
        if not visit_date:
            return occurrences
        
        recent = []
        current_date = datetime.fromisoformat(visit_date.split('T')[0])
        
        for occ in occurrences:
            try:
                symptom_date = datetime.fromisoformat(occ['date'])
                days_diff = (current_date - symptom_date).days
                if 0 <= days_diff <= window_days:
                    recent.append(occ)
            except:
                continue
        
        return recent
    
    def _calculate_confidence(self, matched_symptoms: List[str],
                            required_symptoms: List[str],
                            visit_count: int, days_span: int,
                            config: Dict) -> float:
        """
        Multi-factor confidence calculation
        """
        # Base: symptom match ratio (max 0.5)
        match_ratio = len(matched_symptoms) / len(required_symptoms) if required_symptoms else 0
        base_confidence = match_ratio * 0.5
        
        # Visit spread bonus (max 0.2)
        visit_bonus = min(0.2, (visit_count - 1) * 0.05)
        
        # Time span bonus (max 0.2)
        time_bonus = min(0.2, days_span / 150)
        
        # Symptom rarity bonus (max 0.1)
        rarity_scores = [
            self.symptom_scores.get(s, {}).get('rarity_score', 0.3)
            for s in matched_symptoms
        ]
        avg_rarity = sum(rarity_scores) / len(rarity_scores) if rarity_scores else 0.3
        rarity_bonus = avg_rarity * 0.1
        
        # High-confidence symptom bonus
        high_conf_bonus = 0
        if config.get('confidence_boost_symptoms'):
            for symptom in config['confidence_boost_symptoms']:
                if symptom.lower() in matched_symptoms:
                    high_conf_bonus += 0.05
        
        # Total confidence
        confidence = (base_confidence + visit_bonus + time_bonus + 
                     rarity_bonus + high_conf_bonus)
        
        return min(confidence, 0.95)
    
    def _determine_severity(self, confidence: float, 
                           matched_symptoms: List[str]) -> str:
        """Determine alert severity level"""
        # Get average symptom severity
        severity_scores = [
            self.symptom_scores.get(s, {}).get('rarity_score', 0.3)
            for s in matched_symptoms
        ]
        avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 0.3
        
        if confidence >= 0.8 and avg_severity > 0.6:
            return "high"
        elif confidence >= 0.6:
            return "moderate"
        else:
            return "low"
    
    def _generate_alert_message(self, disease_name: str, symptoms: List[str],
                               visit_count: int, days_span: int, 
                               confidence: float) -> str:
        """Generate clinical alert message"""
        symptom_list = ', '.join(symptoms[:3])
        if len(symptoms) > 3:
            symptom_list += f" (+{len(symptoms) - 3} more)"
        
        return (
            f"Potential {disease_name} detected ({confidence*100:.0f}% confidence). "
            f"Pattern: {symptom_list} across {visit_count} visits over {days_span} days. "
            f"Consider specialist evaluation and recommended tests."
        )
    
    def _load_disease_config(self, path: str) -> Dict:
        """Load disease configuration - FIXED to handle both formats"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different possible formats
                if isinstance(data, dict):
                    if 'diseases' in data:
                        diseases = data['diseases']
                        # If diseases is a list, convert to dict
                        if isinstance(diseases, list):
                            diseases_dict = {}
                            for disease in diseases:
                                if isinstance(disease, dict) and 'name' in disease:
                                    key = disease['name'].lower().replace(' ', '_').replace("'", "")
                                    diseases_dict[key] = disease
                            return diseases_dict
                        else:
                            return diseases
                    else:
                        # Direct dict format
                        return data
                elif isinstance(data, list):
                    # Direct list format - convert to dict
                    diseases_dict = {}
                    for disease in data:
                        if isinstance(disease, dict) and 'name' in disease:
                            key = disease['name'].lower().replace(' ', '_').replace("'", "")
                            diseases_dict[key] = disease
                    return diseases_dict
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Failed to load disease config: {e}")
            return {}
    
    def _load_symptom_scores(self, path: str) -> Dict:
        """Load symptom severity scores"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load symptom scores: {e}")
            return {}