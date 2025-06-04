"""
Symptom Analyzer Service
Extracts and normalizes symptoms from clinical text
"""

import re
from typing import List, Set, Dict
import logging

logger = logging.getLogger(__name__)


class SymptomAnalyzer:
    """Analyzes clinical text to extract symptoms"""
    
    def __init__(self):
        # Common symptom keywords
        self.symptom_keywords = {
            # General
            'fever', 'chills', 'fatigue', 'weakness', 'malaise', 'weight loss', 
            'weight gain', 'loss of appetite', 'night sweats',
            
            # Pain
            'pain', 'headache', 'chest pain', 'abdominal pain', 'back pain', 
            'joint pain', 'muscle pain', 'neck pain', 'pelvic pain',
            
            # Respiratory
            'cough', 'shortness of breath', 'wheezing', 'sputum', 'hemoptysis',
            'dyspnea', 'congestion', 'runny nose', 'sneezing', 'sore throat',
            
            # Gastrointestinal
            'nausea', 'vomiting', 'diarrhea', 'constipation', 'bloating',
            'heartburn', 'dysphagia', 'melena', 'hematochezia', 'jaundice',
            
            # Neurological
            'dizziness', 'vertigo', 'syncope', 'seizure', 'tremor', 'paralysis',
            'numbness', 'tingling', 'confusion', 'memory loss', 'difficulty speaking',
            
            # Cardiovascular
            'palpitations', 'irregular heartbeat', 'edema', 'swelling',
            'claudication', 'cyanosis',
            
            # Dermatological
            'rash', 'itching', 'lesions', 'bruising', 'discoloration',
            'hives', 'eczema', 'psoriasis',
            
            # Genitourinary
            'dysuria', 'hematuria', 'frequency', 'urgency', 'incontinence',
            'discharge', 'erectile dysfunction',
            
            # Psychiatric
            'anxiety', 'depression', 'insomnia', 'hallucinations', 'delusions',
            'mood swings', 'irritability',
            
            # Special senses
            'blurred vision', 'vision loss', 'hearing loss', 'tinnitus',
            'ear pain', 'eye pain', 'photophobia'
        }
        
        # Symptom patterns for extraction
        self.extraction_patterns = [
            r'complains? of (.+?)(?:\.|,|and|with)',
            r'presents? with (.+?)(?:\.|,|and)',
            r'reports? (.+?)(?:\.|,|and)',
            r'experiencing (.+?)(?:\.|,|and|for)',
            r'has (?:been having|had) (.+?)(?:\.|,|and|for)',
            r'suffering from (.+?)(?:\.|,|and)',
            r'symptoms? (?:include|are|:) (.+?)(?:\.|,|and)',
            r'chief complaint[s]?(?:\s+is|\s+are|:) (.+?)(?:\.|,|and)',
            r'c/o (.+?)(?:\.|,|and)',  # Common medical abbreviation
        ]
    
    def extract_symptoms(self, text: str) -> List[str]:
        """
        Extract symptoms from clinical text
        """
        if not text:
            return []
        
        text_lower = text.lower()
        symptoms = set()
        
        # Method 1: Pattern-based extraction
        for pattern in self.extraction_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Split by commas and 'and'
                parts = re.split(r',|and', match)
                for part in parts:
                    symptom = self._clean_symptom(part)
                    if self._is_valid_symptom(symptom):
                        symptoms.add(symptom)
        
        # Method 2: Keyword matching
        for keyword in self.symptom_keywords:
            # Look for the keyword with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                symptoms.add(keyword)
        
        # Method 3: Multi-word symptom phrases
        multi_word_symptoms = [
            'shortness of breath', 'chest pain', 'abdominal pain',
            'difficulty speaking', 'difficulty swallowing', 'loss of appetite',
            'weight loss', 'weight gain', 'night sweats', 'memory loss',
            'irregular heartbeat', 'blurred vision', 'vision loss',
            'hearing loss', 'joint pain', 'muscle pain', 'back pain'
        ]
        
        for symptom in multi_word_symptoms:
            if symptom in text_lower:
                symptoms.add(symptom)
                # Remove individual words if multi-word symptom found
                for word in symptom.split():
                    symptoms.discard(word)
        
        # Convert to list and remove duplicates
        symptom_list = list(symptoms)
        
        # Remove redundant symptoms
        symptom_list = self._remove_redundant_symptoms(symptom_list)
        
        logger.debug(f"Extracted {len(symptom_list)} symptoms from text")
        return symptom_list
    
    def _clean_symptom(self, symptom: str) -> str:
        """Clean and normalize a symptom string"""
        # Remove extra whitespace
        symptom = ' '.join(symptom.split())
        
        # Remove common medical words
        remove_words = [
            'symptoms', 'symptom', 'complains', 'complaint',
            'presents', 'reports', 'states', 'denies',
            'bilateral', 'left', 'right', 'mild', 'moderate', 'severe',
            'acute', 'chronic', 'intermittent', 'persistent'
        ]
        
        words = symptom.split()
        words = [w for w in words if w not in remove_words]
        
        return ' '.join(words).strip()
    
    def _is_valid_symptom(self, symptom: str) -> bool:
        """Check if extracted text is a valid symptom"""
        if not symptom or len(symptom) < 3:
            return False
        
        # Exclude if contains numbers (likely measurements)
        if any(char.isdigit() for char in symptom):
            return False
        
        # Exclude if too long (likely a sentence)
        if len(symptom.split()) > 5:
            return False
        
        # Exclude common non-symptoms
        exclude_terms = [
            'patient', 'history', 'examination', 'treatment',
            'medication', 'allergy', 'surgery', 'procedure'
        ]
        
        if any(term in symptom for term in exclude_terms):
            return False
        
        return True
    
    def _remove_redundant_symptoms(self, symptoms: List[str]) -> List[str]:
        """Remove redundant symptoms (e.g., 'pain' when 'chest pain' exists)"""
        filtered = []
        
        for symptom in symptoms:
            is_redundant = False
            
            # Check if this symptom is part of another symptom
            for other in symptoms:
                if symptom != other and symptom in other:
                    is_redundant = True
                    break
            
            if not is_redundant:
                filtered.append(symptom)
        
        return filtered
    
    def categorize_symptoms(self, symptoms: List[str]) -> Dict[str, List[str]]:
        """Categorize symptoms by body system"""
        categories = {
            'general': [],
            'cardiovascular': [],
            'respiratory': [],
            'gastrointestinal': [],
            'neurological': [],
            'musculoskeletal': [],
            'genitourinary': [],
            'dermatological': [],
            'psychiatric': [],
            'sensory': []
        }
        
        # Mapping of symptoms to categories
        category_map = {
            'general': ['fever', 'fatigue', 'weakness', 'weight loss', 'weight gain'],
            'cardiovascular': ['chest pain', 'palpitations', 'edema', 'swelling'],
            'respiratory': ['cough', 'shortness of breath', 'wheezing', 'hemoptysis'],
            'gastrointestinal': ['nausea', 'vomiting', 'diarrhea', 'abdominal pain'],
            'neurological': ['headache', 'dizziness', 'seizure', 'tremor', 'numbness'],
            'musculoskeletal': ['joint pain', 'muscle pain', 'back pain', 'stiffness'],
            'genitourinary': ['dysuria', 'hematuria', 'frequency', 'discharge'],
            'dermatological': ['rash', 'itching', 'lesions', 'bruising'],
            'psychiatric': ['anxiety', 'depression', 'insomnia', 'hallucinations'],
            'sensory': ['blurred vision', 'hearing loss', 'tinnitus', 'eye pain']
        }
        
        # Categorize each symptom
        for symptom in symptoms:
            categorized = False
            
            for category, keywords in category_map.items():
                if any(keyword in symptom for keyword in keywords):
                    categories[category].append(symptom)
                    categorized = True
                    break
            
            if not categorized:
                categories['general'].append(symptom)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}