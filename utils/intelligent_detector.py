"""
Intelligent Disease Detector - Fixed Version
Filters out common conditions before flagging rare diseases.
Prevents false positives from everyday illnesses.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
import logging

logger = logging.getLogger(__name__)

class IntelligentDiseaseDetector:
    """
    Filters rare disease alerts by ruling out common conditions first.
    Only alerts when symptoms cannot be explained by common illnesses.
    """
    
    def __init__(self):
        self.common_conditions = self._load_common_conditions()
        self.symptom_severity = self._load_symptom_severity()
        
    def _load_common_conditions(self):
        """Load common conditions database."""
        # Comprehensive list of common conditions that can mimic rare diseases
        return {
            "viral_fever": {
                "symptoms": ["fever", "fatigue", "headache", "body ache", "weakness", "loss of appetite"],
                "duration_days": 3-7,
                "prevalence": 0.9
            },
            "common_cold": {
                "symptoms": ["runny nose", "sneezing", "sore throat", "cough", "fatigue", "mild fever"],
                "duration_days": 7-10,
                "prevalence": 0.95
            },
            "gastroenteritis": {
                "symptoms": ["vomiting", "diarrhea", "abdominal pain", "fever", "nausea", "weakness"],
                "duration_days": 2-5,
                "prevalence": 0.85
            },
            "migraine": {
                "symptoms": ["severe headache", "nausea", "vomiting", "sensitivity to light", "dizziness"],
                "duration_days": 1-3,
                "prevalence": 0.7
            },
            "anxiety_disorder": {
                "symptoms": ["palpitations", "chest pain", "shortness of breath", "dizziness", "tremor", "fatigue"],
                "duration_days": "chronic",
                "prevalence": 0.6
            },
            "iron_deficiency_anemia": {
                "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands"],
                "duration_days": "chronic",
                "prevalence": 0.5
            },
            "seasonal_allergies": {
                "symptoms": ["runny nose", "sneezing", "itchy eyes", "congestion", "cough", "fatigue"],
                "duration_days": "seasonal",
                "prevalence": 0.6
            },
            "acid_reflux": {
                "symptoms": ["chest pain", "heartburn", "difficulty swallowing", "regurgitation", "chronic cough"],
                "duration_days": "chronic",
                "prevalence": 0.5
            },
            "tension_headache": {
                "symptoms": ["headache", "neck pain", "muscle tension", "fatigue", "irritability"],
                "duration_days": 1-2,
                "prevalence": 0.8
            },
            "urinary_tract_infection": {
                "symptoms": ["burning urination", "frequent urination", "abdominal pain", "fever", "fatigue"],
                "duration_days": 3-7,
                "prevalence": 0.6
            },
            "bronchitis": {
                "symptoms": ["cough", "chest congestion", "wheezing", "fatigue", "mild fever", "shortness of breath"],
                "duration_days": 7-21,
                "prevalence": 0.5
            },
            "sinusitis": {
                "symptoms": ["facial pain", "nasal congestion", "headache", "cough", "fatigue", "fever"],
                "duration_days": 7-14,
                "prevalence": 0.6
            },
            "food_poisoning": {
                "symptoms": ["vomiting", "diarrhea", "abdominal cramps", "fever", "weakness", "dehydration"],
                "duration_days": 1-3,
                "prevalence": 0.4
            },
            "muscle_strain": {
                "symptoms": ["muscle pain", "stiffness", "weakness", "swelling", "limited movement"],
                "duration_days": 3-7,
                "prevalence": 0.7
            },
            "viral_gastritis": {
                "symptoms": ["nausea", "vomiting", "abdominal pain", "loss of appetite", "fatigue"],
                "duration_days": 2-5,
                "prevalence": 0.6
            },
            "stress_syndrome": {
                "symptoms": ["fatigue", "headache", "muscle tension", "insomnia", "irritability", "difficulty concentrating"],
                "duration_days": "variable",
                "prevalence": 0.7
            },
            "dehydration": {
                "symptoms": ["fatigue", "dizziness", "dry mouth", "headache", "dark urine", "weakness"],
                "duration_days": 1-2,
                "prevalence": 0.5
            },
            "hypoglycemia": {
                "symptoms": ["tremor", "sweating", "palpitations", "confusion", "weakness", "dizziness"],
                "duration_days": "acute",
                "prevalence": 0.3
            },
            "orthostatic_hypotension": {
                "symptoms": ["dizziness", "lightheadedness", "weakness", "blurred vision", "fatigue"],
                "duration_days": "chronic",
                "prevalence": 0.4
            },
            "vitamin_d_deficiency": {
                "symptoms": ["fatigue", "bone pain", "muscle weakness", "muscle aches", "mood changes"],
                "duration_days": "chronic",
                "prevalence": 0.6
            }
        }
    
    def _load_symptom_severity(self):
        """Load symptom severity scores."""
        try:
            with open('data/symptom_severity_scores.json', 'r') as f:
                return json.load(f)
        except:
            # Fallback to basic scoring
            return {
                "fever": {"rarity_score": 0.1},
                "fatigue": {"rarity_score": 0.15},
                "pain": {"rarity_score": 0.1},
                "headache": {"rarity_score": 0.15},
                "nausea": {"rarity_score": 0.2},
                "vomiting": {"rarity_score": 0.2},
                "cough": {"rarity_score": 0.1},
                "weakness": {"rarity_score": 0.2}
            }
    
    def should_alert(self, symptoms: List[str], patient_data: Dict, confidence: float = 0.5) -> Tuple[bool, float, List[str]]:
        """
        Determine if rare disease alert should be triggered after ruling out common conditions.
        
        Returns:
            - should_alert (bool): Whether to show the alert
            - adjusted_confidence (float): Confidence after adjustments
            - ruled_out_conditions (List[str]): Common conditions that could explain symptoms
        """
        
        # Normalize symptoms
        symptoms_lower = [s.lower().strip() for s in symptoms if s]
        symptoms_set = set(symptoms_lower)
        
        # Check which common conditions could explain these symptoms
        possible_conditions = []
        explained_symptoms = set()
        
        for condition_name, condition_data in self.common_conditions.items():
            condition_symptoms = set(s.lower() for s in condition_data['symptoms'])
            
            # Calculate overlap
            overlap = symptoms_set.intersection(condition_symptoms)
            if len(overlap) >= 2:  # At least 2 symptoms match
                match_percentage = len(overlap) / len(symptoms_set)
                if match_percentage >= 0.5:  # 50% or more symptoms explained
                    possible_conditions.append({
                        'name': condition_name,
                        'match_percentage': match_percentage,
                        'matched_symptoms': list(overlap)
                    })
                    explained_symptoms.update(overlap)
        
        # Sort by match percentage
        possible_conditions.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Calculate how many symptoms are NOT explained by common conditions
        unexplained_symptoms = symptoms_set - explained_symptoms
        unexplained_ratio = len(unexplained_symptoms) / len(symptoms_set) if symptoms_set else 0
        
        # Calculate average rarity score of symptoms
        total_rarity = 0
        rarity_count = 0
        for symptom in symptoms_lower:
            if symptom in self.symptom_severity:
                total_rarity += self.symptom_severity[symptom].get('rarity_score', 0.3)
                rarity_count += 1
        
        avg_rarity = total_rarity / rarity_count if rarity_count > 0 else 0.3
        
        # Decision logic
        should_alert = True
        adjusted_confidence = confidence
        
        # Rule 1: If most symptoms are explained by common conditions, reduce confidence
        if possible_conditions and possible_conditions[0]['match_percentage'] >= 0.7:
            adjusted_confidence *= 0.5  # Halve confidence
            if adjusted_confidence < 0.5:
                should_alert = False
        
        # Rule 2: If symptoms are all very common (low rarity), reduce confidence
        if avg_rarity < 0.25:  # All common symptoms
            adjusted_confidence *= 0.6
            if adjusted_confidence < 0.5:
                should_alert = False
        
        # Rule 3: If patient is young and symptoms are non-specific, be more conservative
        age = patient_data.get('age', 30)
        if age < 5 and avg_rarity < 0.4:
            adjusted_confidence *= 0.7
        
        # Rule 4: Boost confidence if many symptoms are unexplained
        if unexplained_ratio > 0.5:
            adjusted_confidence *= 1.2
        
        # Rule 5: If only common symptoms like fever + fatigue, don't alert
        common_only = all(
            self.symptom_severity.get(s, {}).get('rarity_score', 1.0) < 0.3 
            for s in symptoms_lower
        )
        if common_only and len(symptoms_set) < 4:
            should_alert = False
            adjusted_confidence *= 0.4
        
        # Cap confidence at 0.95
        adjusted_confidence = min(adjusted_confidence, 0.95)
        
        # Extract condition names for return
        ruled_out = [c['name'] for c in possible_conditions[:3]]  # Top 3 matches
        
        # Log decision
        logger.info(f"IntelligentDetector: symptoms={symptoms}, "
                   f"possible_common={ruled_out}, "
                   f"confidence={confidence:.2f}->{adjusted_confidence:.2f}, "
                   f"alert={should_alert}")
        
        return should_alert, adjusted_confidence, ruled_out
    
    def suggest_common_differentials(self, symptoms: List[str]) -> List[Dict]:
        """
        Suggest common differential diagnoses to consider.
        """
        symptoms_lower = [s.lower().strip() for s in symptoms if s]
        symptoms_set = set(symptoms_lower)
        
        differentials = []
        
        for condition_name, condition_data in self.common_conditions.items():
            condition_symptoms = set(s.lower() for s in condition_data['symptoms'])
            overlap = symptoms_set.intersection(condition_symptoms)
            
            if len(overlap) >= 2:
                score = len(overlap) / len(condition_symptoms)
                differentials.append({
                    'condition': condition_name.replace('_', ' ').title(),
                    'confidence': round(score, 2),
                    'matched_symptoms': list(overlap),
                    'prevalence': condition_data['prevalence']
                })
        
        # Sort by confidence and prevalence
        differentials.sort(key=lambda x: (x['confidence'], x['prevalence']), reverse=True)
        
        return differentials[:5]  # Top 5 differentials
    
    def is_symptom_pattern_concerning(self, symptom_timeline: List[Dict]) -> bool:
        """
        Check if the pattern of symptoms over time is concerning.
        """
        if not symptom_timeline:
            return False
        
        # Check for progressive worsening
        symptom_counts = {}
        for entry in symptom_timeline:
            date = entry.get('date', '')
            symptom = entry.get('symptom', '').lower()
            
            if symptom not in symptom_counts:
                symptom_counts[symptom] = []
            symptom_counts[symptom].append(date)
        
        # Look for concerning patterns
        concerning_patterns = 0
        
        # Pattern 1: Increasing number of symptoms over time
        unique_dates = sorted(set(date for dates in symptom_counts.values() for date in dates))
        if len(unique_dates) >= 3:
            symptoms_per_date = {}
            for symptom, dates in symptom_counts.items():
                for date in dates:
                    if date not in symptoms_per_date:
                        symptoms_per_date[date] = set()
                    symptoms_per_date[date].add(symptom)
            
            counts = [len(symptoms_per_date[date]) for date in unique_dates]
            if counts[-1] > counts[0] * 1.5:  # 50% increase
                concerning_patterns += 1
        
        # Pattern 2: High-severity symptoms appearing
        high_severity_symptoms = [
            s for s in symptom_counts.keys() 
            if self.symptom_severity.get(s, {}).get('rarity_score', 0) > 0.6
        ]
        if high_severity_symptoms:
            concerning_patterns += 1
        
        # Pattern 3: Symptoms persisting over long period
        for symptom, dates in symptom_counts.items():
            if len(dates) >= 3:  # Same symptom on 3+ visits
                concerning_patterns += 1
                break
        
        return concerning_patterns >= 2