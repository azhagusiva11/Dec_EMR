"""
Medical Validator 2.0 - Physiological Validation Engine for Smart EMR
Age-aware, context-sensitive vital signs validation for Indian clinics
"""

import json
import re
from typing import Dict, List, Tuple, Optional, Union


class PhysiologyEngine:
    def __init__(self, ranges_file: str = 'data/physiological_ranges.json'):
        """Initialize with physiological ranges data"""
        self.ranges_file = ranges_file
        self._load_ranges()
    
    def _load_ranges(self):
        """Load physiological ranges from JSON file"""
        try:
            with open(self.ranges_file, 'r') as f:
                self.ranges = json.load(f)
        except FileNotFoundError:
            # Fallback to hardcoded ranges if file not found
            self.ranges = self._get_default_ranges()
    
    def _get_default_ranges(self) -> dict:
        """Hardcoded physiological ranges as fallback"""
        return {
            "heart_rate": {
                "newborn": {"range": [120, 160], "critical_low": 90, "critical_high": 180},
                "infant": {"range": [100, 150], "critical_low": 80, "critical_high": 170},
                "toddler": {"range": [90, 140], "critical_low": 70, "critical_high": 160},
                "preschool": {"range": [80, 120], "critical_low": 65, "critical_high": 140},
                "school_age": {"range": [75, 115], "critical_low": 60, "critical_high": 130},
                "adolescent": {"range": [60, 105], "critical_low": 50, "critical_high": 120},
                "adult": {"range": [60, 100], "critical_low": 40, "critical_high": 150},
                "elderly": {"range": [60, 100], "critical_low": 45, "critical_high": 140},
                "athlete": {"range": [40, 60], "critical_low": 35, "critical_high": 100}
            },
            "blood_pressure": {
                "newborn": {
                    "range": {"systolic": [60, 90], "diastolic": [30, 60]},
                    "critical_low": {"systolic": 50, "diastolic": 25},
                    "critical_high": {"systolic": 100, "diastolic": 70}
                },
                "infant": {
                    "range": {"systolic": [70, 100], "diastolic": [40, 65]},
                    "critical_low": {"systolic": 60, "diastolic": 30},
                    "critical_high": {"systolic": 110, "diastolic": 75}
                },
                "toddler": {
                    "range": {"systolic": [80, 110], "diastolic": [50, 70]},
                    "critical_low": {"systolic": 70, "diastolic": 40},
                    "critical_high": {"systolic": 120, "diastolic": 80}
                },
                "preschool": {
                    "range": {"systolic": [85, 115], "diastolic": [55, 75]},
                    "critical_low": {"systolic": 75, "diastolic": 45},
                    "critical_high": {"systolic": 125, "diastolic": 85}
                },
                "school_age": {
                    "range": {"systolic": [90, 120], "diastolic": [60, 80]},
                    "critical_low": {"systolic": 80, "diastolic": 50},
                    "critical_high": {"systolic": 130, "diastolic": 90}
                },
                "adolescent": {
                    "range": {"systolic": [95, 125], "diastolic": [60, 85]},
                    "critical_low": {"systolic": 85, "diastolic": 50},
                    "critical_high": {"systolic": 140, "diastolic": 95}
                },
                "adult": {
                    "range": {"systolic": [90, 130], "diastolic": [60, 90]},
                    "critical_low": {"systolic": 70, "diastolic": 40},
                    "critical_high": {"systolic": 180, "diastolic": 120}
                },
                "elderly": {
                    "range": {"systolic": [90, 140], "diastolic": [60, 90]},
                    "critical_low": {"systolic": 80, "diastolic": 45},
                    "critical_high": {"systolic": 180, "diastolic": 110}
                }
            },
            "temperature": {
                "default": {
                    "range_c": [36.1, 37.9],
                    "range_f": [97.0, 100.2],
                    "critical_high_c": 40.0,
                    "critical_low_c": 34.0,
                    "critical_high_f": 104.0,
                    "critical_low_f": 93.2
                }
            },
            "respiratory_rate": {
                "newborn": {"range": [30, 60], "critical_low": 20, "critical_high": 70},
                "infant": {"range": [25, 50], "critical_low": 20, "critical_high": 60},
                "toddler": {"range": [20, 40], "critical_low": 15, "critical_high": 45},
                "preschool": {"range": [20, 30], "critical_low": 15, "critical_high": 40},
                "school_age": {"range": [18, 25], "critical_low": 12, "critical_high": 35},
                "adolescent": {"range": [12, 20], "critical_low": 10, "critical_high": 30},
                "adult": {"range": [12, 20], "critical_low": 8, "critical_high": 30},
                "elderly": {"range": [12, 25], "critical_low": 10, "critical_high": 35}
            },
            "oxygen_saturation": {
                "default": {"range": [95, 100], "critical_low": 90},
                "high_altitude": {"range": [92, 100], "critical_low": 88}
            }
        }
    
    def _get_age_category(self, age_years: float) -> str:
        """Map age in years to age category"""
        if age_years < 0.08:  # < 1 month
            return "newborn"
        elif age_years < 1:
            return "infant"
        elif age_years < 3:
            return "toddler"
        elif age_years < 6:
            return "preschool"
        elif age_years < 12:
            return "school_age"
        elif age_years < 18:
            return "adolescent"
        elif age_years < 65:
            return "adult"
        else:
            return "elderly"
    
    def get_normal_ranges(self, age_years: float, sex: Optional[str] = None, 
                         context: Optional[List[str]] = None) -> Dict:
        """
        Returns age-specific normal and critical ranges for vital signs
        
        Args:
            age_years: Age in years (can be decimal for infants)
            sex: 'M' or 'F' (optional)
            context: List of contexts like ['athlete', 'pregnant', 'diabetic']
        
        Returns:
            Dictionary with ranges for each vital sign
        """
        age_category = self._get_age_category(age_years)
        context = context or []
        
        ranges_output = {}
        
        # Heart rate
        if 'athlete' in context and age_years >= 16:
            hr_ranges = self.ranges['heart_rate']['athlete']
        else:
            hr_ranges = self.ranges['heart_rate'].get(age_category, self.ranges['heart_rate']['adult'])
        ranges_output['heart_rate'] = hr_ranges
        
        # Blood pressure
        bp_ranges = self.ranges['blood_pressure'].get(age_category, self.ranges['blood_pressure']['adult'])
        ranges_output['blood_pressure'] = bp_ranges
        
        # Temperature (same for all ages)
        ranges_output['temperature'] = self.ranges['temperature']['default']
        
        # Respiratory rate
        rr_ranges = self.ranges['respiratory_rate'].get(age_category, self.ranges['respiratory_rate']['adult'])
        ranges_output['respiratory_rate'] = rr_ranges
        
        # Oxygen saturation
        if 'high_altitude' in context:
            ranges_output['oxygen_saturation'] = self.ranges['oxygen_saturation']['high_altitude']
        else:
            ranges_output['oxygen_saturation'] = self.ranges['oxygen_saturation']['default']
        
        return ranges_output
    
    def detect_units(self, value_string: str) -> Dict:
        """
        Detect and normalize units from various input formats
        
        Args:
            value_string: Input string like "120/80", "38.5C", "101.3F"
        
        Returns:
            Normalized values with detected units
        """
        value_string = str(value_string).strip()
        
        # Blood pressure pattern (e.g., "120/80", "120/80 mmHg", "16/10 kPa")
        bp_pattern = r'(\d+)\s*/\s*(\d+)\s*(mmHg|kPa)?'
        bp_match = re.match(bp_pattern, value_string, re.IGNORECASE)
        if bp_match:
            systolic, diastolic, unit = bp_match.groups()
            systolic, diastolic = float(systolic), float(diastolic)
            
            # Convert kPa to mmHg if needed
            if unit and unit.lower() == 'kpa':
                systolic = systolic * 7.50062  # 1 kPa = 7.50062 mmHg
                diastolic = diastolic * 7.50062
            
            return {
                'systolic': round(systolic),
                'diastolic': round(diastolic),
                'unit': 'mmHg',
                'original': value_string
            }
        
        # Temperature pattern (e.g., "38.5C", "101.3F", "38.5°C")
        temp_pattern = r'(\d+\.?\d*)\s*°?\s*(C|F|celsius|fahrenheit)?'
        temp_match = re.match(temp_pattern, value_string, re.IGNORECASE)
        if temp_match:
            temp_value, unit = temp_match.groups()
            temp_value = float(temp_value)
            
            # Determine unit if not specified
            if not unit:
                # Assume Fahrenheit if > 45 (no human survives 45°C)
                unit = 'F' if temp_value > 45 else 'C'
            
            # Convert to Celsius
            if unit.upper() == 'F' or unit.lower() == 'fahrenheit':
                temp_celsius = (temp_value - 32) * 5/9
            else:
                temp_celsius = temp_value
            
            return {
                'value': round(temp_celsius, 1),
                'unit': 'C',
                'original': value_string,
                'original_unit': unit
            }
        
        # Simple numeric pattern
        numeric_pattern = r'(\d+\.?\d*)'
        numeric_match = re.match(numeric_pattern, value_string)
        if numeric_match:
            return {
                'value': float(numeric_match.group(1)),
                'unit': 'unknown',
                'original': value_string
            }
        
        return {'error': 'Unable to parse value', 'original': value_string}
    
    def _calculate_percentile(self, value: float, range_min: float, range_max: float) -> int:
        """Calculate approximate percentile within normal range"""
        if value < range_min:
            return 0
        elif value > range_max:
            return 100
        else:
            # Linear interpolation within range
            position = (value - range_min) / (range_max - range_min)
            return int(position * 100)
    
    def _assess_severity(self, value: float, normal_range: List[float], 
                        critical_low: float, critical_high: float) -> str:
        """Determine severity assessment"""
        if value < critical_low or value > critical_high:
            return "Critical"
        elif value < normal_range[0] or value > normal_range[1]:
            return "Caution"
        else:
            return "Normal"
    
    def validate(self, vitals: Dict, age_years: float, sex: Optional[str] = None, 
                context: List[str] = None) -> Dict:
        """
        Validates input vitals based on age and context
        
        Args:
            vitals: Dictionary with vital signs (e.g., {'heart_rate': 72, 'blood_pressure': '120/80'})
            age_years: Age in years
            sex: 'M' or 'F' (optional)
            context: List of contexts like ['athlete', 'pregnant', 'diabetic']
        
        Returns:
            Structured validation output with confidence, assessment, and suggestions
        """
        context = context or []
        ranges = self.get_normal_ranges(age_years, sex, context)
        results = {}
        overall_valid = True
        overall_assessment = "Normal"
        messages = []
        suggestions = []
        
        # Validate heart rate
        if 'heart_rate' in vitals and vitals['heart_rate'] is not None:
            hr = float(vitals['heart_rate'])
            hr_range = ranges['heart_rate']
            assessment = self._assess_severity(hr, hr_range['range'], 
                                             hr_range['critical_low'], hr_range['critical_high'])
            
            results['heart_rate'] = {
                'value': hr,
                'assessment': assessment,
                'percentile': self._calculate_percentile(hr, hr_range['range'][0], hr_range['range'][1])
            }
            
            if assessment == "Critical":
                overall_assessment = "Critical"
                overall_valid = False
                if hr < hr_range['critical_low']:
                    messages.append(f"Heart rate dangerously low ({hr} bpm)")
                    suggestions.extend(["Check for bradycardia", "Immediate cardiac assessment"])
                else:
                    messages.append(f"Heart rate dangerously high ({hr} bpm)")
                    suggestions.extend(["Check for tachycardia", "Monitor for arrhythmia"])
            elif assessment == "Caution":
                if overall_assessment != "Critical":
                    overall_assessment = "Caution"
                if hr < hr_range['range'][0]:
                    messages.append(f"Heart rate below normal ({hr} bpm)")
                    suggestions.append("Monitor for symptoms of bradycardia")
                else:
                    messages.append(f"Heart rate above normal ({hr} bpm)")
                    suggestions.append("Check for fever, anxiety, or dehydration")
        
        # Validate blood pressure
        if 'blood_pressure' in vitals and vitals['blood_pressure'] is not None:
            bp_parsed = self.detect_units(str(vitals['blood_pressure']))
            if 'systolic' in bp_parsed:
                bp_range = ranges['blood_pressure']
                sys = bp_parsed['systolic']
                dia = bp_parsed['diastolic']
                
                sys_assessment = self._assess_severity(sys, bp_range['range']['systolic'],
                                                      bp_range['critical_low']['systolic'],
                                                      bp_range['critical_high']['systolic'])
                dia_assessment = self._assess_severity(dia, bp_range['range']['diastolic'],
                                                      bp_range['critical_low']['diastolic'],
                                                      bp_range['critical_high']['diastolic'])
                
                # Overall BP assessment is worst of the two
                bp_assessment = "Critical" if "Critical" in [sys_assessment, dia_assessment] else \
                               "Caution" if "Caution" in [sys_assessment, dia_assessment] else "Normal"
                
                results['blood_pressure'] = {
                    'systolic': sys,
                    'diastolic': dia,
                    'assessment': bp_assessment,
                    'normalized': f"{int(sys)}/{int(dia)} mmHg"
                }
                
                if bp_assessment == "Critical":
                    overall_assessment = "Critical"
                    overall_valid = False
                    if sys < bp_range['critical_low']['systolic']:
                        messages.append(f"Critically low BP ({int(sys)}/{int(dia)} mmHg)")
                        suggestions.extend(["Check for shock", "IV fluids may be needed"])
                    elif sys > bp_range['critical_high']['systolic']:
                        messages.append(f"Hypertensive crisis ({int(sys)}/{int(dia)} mmHg)")
                        suggestions.extend(["Immediate BP management", "Check for end-organ damage"])
                elif bp_assessment == "Caution":
                    if overall_assessment != "Critical":
                        overall_assessment = "Caution"
                    if sys < bp_range['range']['systolic'][0]:
                        messages.append(f"BP low for age ({int(sys)}/{int(dia)} mmHg)")
                        suggestions.append("Check hydration and medications")
                    elif sys > bp_range['range']['systolic'][1]:
                        messages.append(f"BP elevated ({int(sys)}/{int(dia)} mmHg)")
                        suggestions.append("Monitor BP trend")
        
        # Validate temperature
        if 'temperature' in vitals and vitals['temperature'] is not None:
            temp_parsed = self.detect_units(str(vitals['temperature']))
            if 'value' in temp_parsed:
                temp_c = temp_parsed['value']
                temp_range = ranges['temperature']
                
                if temp_c < temp_range['critical_low_c'] or temp_c > temp_range['critical_high_c']:
                    assessment = "Critical"
                elif temp_c < temp_range['range_c'][0] or temp_c > temp_range['range_c'][1]:
                    assessment = "Caution"
                else:
                    assessment = "Normal"
                
                results['temperature'] = {
                    'value': temp_c,
                    'assessment': assessment,
                    'normalized': f"{temp_c}°C"
                }
                
                if assessment == "Critical":
                    overall_assessment = "Critical"
                    overall_valid = False
                    if temp_c < temp_range['critical_low_c']:
                        messages.append(f"Severe hypothermia ({temp_c}°C)")
                        suggestions.extend(["Urgent rewarming needed", "Check for causes"])
                    else:
                        messages.append(f"Severe hyperthermia ({temp_c}°C)")
                        suggestions.extend(["Urgent cooling needed", "Check for heat stroke"])
                elif assessment == "Caution":
                    if overall_assessment != "Critical":
                        overall_assessment = "Caution"
                    if temp_c > temp_range['range_c'][1]:
                        messages.append(f"Fever detected ({temp_c}°C)")
                        suggestions.append("Investigate infection source")
        
        # Validate respiratory rate
        if 'respiratory_rate' in vitals and vitals['respiratory_rate'] is not None:
            rr = float(vitals['respiratory_rate'])
            rr_range = ranges['respiratory_rate']
            assessment = self._assess_severity(rr, rr_range['range'],
                                             rr_range['critical_low'], rr_range['critical_high'])
            
            results['respiratory_rate'] = {
                'value': rr,
                'assessment': assessment
            }
            
            if assessment == "Critical":
                overall_assessment = "Critical"
                overall_valid = False
                if rr < rr_range['critical_low']:
                    messages.append(f"Dangerously low respiratory rate ({rr}/min)")
                    suggestions.append("Check for respiratory depression")
                else:
                    messages.append(f"Dangerously high respiratory rate ({rr}/min)")
                    suggestions.append("Check for respiratory distress")
        
        # Validate oxygen saturation
        if 'oxygen_saturation' in vitals and vitals['oxygen_saturation'] is not None:
            spo2 = float(vitals['oxygen_saturation'])
            spo2_range = ranges['oxygen_saturation']
            
            if spo2 < spo2_range['critical_low']:
                assessment = "Critical"
            elif spo2 < spo2_range['range'][0]:
                assessment = "Caution"
            else:
                assessment = "Normal"
            
            results['oxygen_saturation'] = {
                'value': spo2,
                'assessment': assessment
            }
            
            if assessment == "Critical":
                overall_assessment = "Critical"
                overall_valid = False
                messages.append(f"Critical hypoxemia (SpO2 {spo2}%)")
                suggestions.extend(["Immediate oxygen therapy", "Check for respiratory failure"])
            elif assessment == "Caution":
                if overall_assessment != "Critical":
                    overall_assessment = "Caution"
                messages.append(f"Low oxygen saturation (SpO2 {spo2}%)")
                suggestions.append("Monitor closely, consider supplemental O2")
        
        # Calculate confidence based on number of vitals provided
        vitals_checked = len(results)
        total_possible = 5  # HR, BP, Temp, RR, SpO2
        confidence = vitals_checked / total_possible
        
        # Compile final output
        return {
            "valid": overall_valid,
            "confidence": round(confidence, 2),
            "assessment": overall_assessment,
            "message": " ".join(messages) if messages else "All vitals within normal range",
            "suggestions": suggestions,
            "details": results,
            "age_category": self._get_age_category(age_years)
        }
# Add this to medical_validator_v2.py at the very end:
class MedicalValidator:
    """Compatibility wrapper for old validation methods"""
    def __init__(self):
        self.engine = PhysiologyEngine()
    
    def validate_patient_name(self, name):
        if not name or len(name) < 2:
            return False, "Name must be at least 2 characters"
        if not all(c.isalpha() or c.isspace() for c in name):
            return False, "Name should only contain letters"
        return True, "Valid"
    
    def validate_age(self, age):
        if age <= 0 or age > 120:
            return False, "Age must be between 1 and 120"
        return True, "Valid"
    
    def validate_mobile_number(self, mobile, country_code="+91"):
        if not mobile.isdigit():
            return False, "Mobile number must contain only digits"
        if len(mobile) != 10:
            return False, "Mobile number must be 10 digits"
        return True, "Valid"
    
    def validate_blood_pressure(self, bp):
        result = self.engine.detect_units(bp)
        if 'systolic' in result:
            return True, "Valid"
        return False, "Invalid BP format (use format like 120/80)"
    
    def validate_heart_rate(self, hr):
        if hr <= 0 or hr > 300:
            return False, "Heart rate must be between 1 and 300"
        return True, "Valid"
    
    def validate_weight(self, weight, age):
        if weight <= 0:
            return False, "Weight must be greater than 0"
        if age < 1 and weight > 10:
            return False, "Weight too high for infant"
        if weight > 500:
            return False, "Weight seems too high"
        return True, "Valid"
    
    def validate_height(self, height, age):
        if height <= 0:
            return False, "Height must be greater than 0"
        if height > 300:
            return False, "Height seems too high"
        return True, "Valid"
    
    def validate_consultation_data(self, symptoms, patient_name):
        # Basic check
        return True, "Valid"