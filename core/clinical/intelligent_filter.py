"""
Intelligent Filter for Disease Detection
Filters out common conditions before flagging rare diseases
"""

from typing import List, Dict, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class IntelligentFilter:
    """
    Filters rare disease alerts by ruling out common conditions first.
    Prevents false positives from everyday illnesses.
    """
    
    def __init__(self):
        # Common conditions that can mimic rare diseases
        self.common_conditions = {
            "viral_fever": {
                "symptoms": ["fever", "fatigue", "headache", "body ache", "weakness", "loss of appetite"],
                "typical_duration": "3-7 days",
                "prevalence": 0.9
            },
            "common_cold": {
                "symptoms": ["runny nose", "sneezing", "sore throat", "cough", "fatigue", "mild fever"],
                "typical_duration": "7-10 days",
                "prevalence": 0.95
            },
            "gastroenteritis": {
                "symptoms": ["vomiting", "diarrhea", "abdominal pain", "fever", "nausea", "weakness"],
                "typical_duration": "2-5 days",
                "prevalence": 0.85
            },
            "migraine": {
                "symptoms": ["severe headache", "nausea", "vomiting", "sensitivity to light", "dizziness"],
                "typical_duration": "1-3 days",
                "prevalence": 0.7
            },
            "anxiety_disorder": {
                "symptoms": ["palpitations", "chest pain", "shortness of breath", "dizziness", "tremor", "fatigue"],
                "typical_duration": "chronic",
                "prevalence": 0.6
            },
            "iron_deficiency_anemia": {
                "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands"],
                "typical_duration": "chronic",
                "prevalence": 0.5
            },
            "seasonal_allergies": {
                "symptoms": ["runny nose", "sneezing", "itchy eyes", "congestion", "cough", "fatigue"],
                "typical_duration": "seasonal",
                "prevalence": 0.6
            },
            "acid_reflux": {
                "symptoms": ["chest pain", "heartburn", "difficulty swallowing", "regurgitation", "chronic cough"],
                "typical_duration": "chronic",
                "prevalence": 0.5
            },
            "tension_headache": {
                "symptoms": ["headache", "neck pain", "muscle tension", "fatigue", "irritability"],
                "typical_duration": "1-2 days",
                "prevalence": 0.8
            },
            "urinary_tract_infection": {
                "symptoms": ["burning urination", "frequent urination", "abdominal pain", "fever", "fatigue"],
                "typical_duration": "3-7 days",
                "prevalence": 0.6
            },
            "bronchitis": {
                "symptoms": ["cough", "chest congestion", "wheezing", "fatigue", "mild fever", "shortness of breath"],
                "typical_duration": "7-21 days",
                "prevalence": 0.5
            },
            "sinusitis": {
                "symptoms": ["facial pain", "nasal congestion", "headache", "cough", "fatigue", "fever"],
                "typical_duration": "7-14 days",
                "prevalence": 0.6
            },
            "stress_syndrome": {
                "symptoms": ["fatigue", "headache", "muscle tension", "insomnia", "irritability", "difficulty concentrating"],
                "typical_duration": "variable",
                "prevalence": 0.7
            },
            "dehydration": {
                "symptoms": ["fatigue", "dizziness", "dry mouth", "headache", "dark urine", "weakness"],
                "typical_duration": "1-2 days",
                "prevalence": 0.5
            }
        }
    
    def should_alert(self, symptoms: List[str], patient_data: Dict, 
                    base_confidence: float = 0.5) -> Tuple[bool, float, List[str]]:
        """
        Determine if rare disease alert should be triggered.
        
        Returns:
            - should_alert (bool): Whether to show the alert
            - adjusted_confidence (float): Confidence after adjustments
            - ruled_out_conditions (List[str]): Common conditions that could explain symptoms
        """
        
        # Normalize symptoms
        symptoms_lower = [s.lower().strip() for s in symptoms if s]
        symptoms_set = set(symptoms_lower)
        
        # Find common conditions that could explain symptoms
        possible_conditions = self._find_matching_conditions(symptoms_set)
        
        # Calculate unexplained symptoms
        explained_symptoms = set()
        for condition in possible_conditions:
            explained_symptoms.update(condition['matched_symptoms'])
        
        unexplained_symptoms = symptoms_set - explained_symptoms
        unexplained_ratio = len(unexplained_symptoms) / len(symptoms_set) if symptoms_set else 0
        
        # Decision logic
        should_alert = True
        adjusted_confidence = base_confidence
        
        # Rule 1: If most symptoms explained by common condition, reduce confidence
        if possible_conditions and possible_conditions[0]['match_percentage'] >= 0.7:
            adjusted_confidence *= 0.5
            if adjusted_confidence < 0.5:
                should_alert = False
        
        # Rule 2: If all symptoms are very common, reduce confidence
        if self._all_symptoms_common(symptoms_lower):
            adjusted_confidence *= 0.6
            if adjusted_confidence < 0.5:
                should_alert = False
        
        # Rule 3: Age-based adjustment for children
        age = patient_data.get('age', 30)
        if age < 5 and len(unexplained_symptoms) < 2:
            adjusted_confidence *= 0.7
        
        # Rule 4: Boost if many unexplained symptoms
        if unexplained_ratio > 0.5:
            adjusted_confidence *= 1.2
        
        # Rule 5: Pattern-based filtering
        if self._is_common_pattern(symptoms_set):
            should_alert = False
            adjusted_confidence *= 0.3
        
        # Cap confidence
        adjusted_confidence = min(adjusted_confidence, 0.95)
        
        # Get condition names
        ruled_out = [c['name'] for c in possible_conditions[:3]]
        
        logger.info(f"Filter decision: symptoms={symptoms}, "
                   f"ruled_out={ruled_out}, "
                   f"confidence={base_confidence:.2f}->{adjusted_confidence:.2f}, "
                   f"alert={should_alert}")
        
        return should_alert, adjusted_confidence, ruled_out
    
    def _find_matching_conditions(self, symptoms_set: Set[str]) -> List[Dict]:
        """Find common conditions that match the symptoms"""
        matches = []
        
        for condition_name, condition_data in self.common_conditions.items():
            condition_symptoms = set(s.lower() for s in condition_data['symptoms'])
            
            # Calculate overlap
            overlap = symptoms_set.intersection(condition_symptoms)
            if len(overlap) >= 2:  # At least 2 symptoms match
                match_percentage = len(overlap) / len(symptoms_set)
                if match_percentage >= 0.5:  # 50% or more symptoms explained
                    matches.append({
                        'name': condition_name.replace('_', ' ').title(),
                        'match_percentage': match_percentage,
                        'matched_symptoms': list(overlap),
                        'prevalence': condition_data['prevalence']
                    })
        
        # Sort by match percentage and prevalence
        matches.sort(key=lambda x: (x['match_percentage'], x['prevalence']), reverse=True)
        
        return matches
    
    def _all_symptoms_common(self, symptoms: List[str]) -> bool:
        """Check if all symptoms are very common"""
        very_common = {
            'fever', 'cough', 'fatigue', 'headache', 'pain',
            'nausea', 'vomiting', 'diarrhea', 'weakness',
            'runny nose', 'sore throat', 'congestion'
        }
        
        return all(s in very_common for s in symptoms)
    
    def _is_common_pattern(self, symptoms_set: Set[str]) -> bool:
        """Check for common symptom patterns that don't indicate rare disease"""
        common_patterns = [
            {'fever', 'cough', 'fatigue'},  # Common cold/flu
            {'nausea', 'vomiting', 'diarrhea'},  # Gastroenteritis
            {'headache', 'fatigue', 'stress'},  # Stress/tension
            {'fever', 'sore throat', 'cough'},  # Upper respiratory infection
            {'fatigue', 'weakness', 'dizziness'}  # Dehydration/anemia
        ]
        
        for pattern in common_patterns:
            if pattern.issubset(symptoms_set):
                return True
        
        return False
    
    def get_differential_diagnoses(self, symptoms: List[str]) -> List[Dict]:
        """Get list of possible common conditions for differential diagnosis"""
        symptoms_set = set(s.lower().strip() for s in symptoms if s)
        matches = self._find_matching_conditions(symptoms_set)
        
        # Format for display
        differentials = []
        for match in matches[:5]:  # Top 5
            differentials.append({
                'condition': match['name'],
                'confidence': round(match['match_percentage'], 2),
                'matched_symptoms': match['matched_symptoms'],
                'typical_duration': self.common_conditions.get(
                    match['name'].lower().replace(' ', '_'), {}
                ).get('typical_duration', 'Unknown')
            })
        
        return differentials