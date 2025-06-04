"""
Vitals Validator Service
Simple validation for vital signs with clinical ranges
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class VitalsValidator:
    """Validates vital signs against physiological ranges"""
    
    def __init__(self):
        # Basic physiological ranges
        self.ranges = {
            'blood_pressure': {
                'systolic': {'min': 70, 'max': 200, 'normal_min': 90, 'normal_max': 140},
                'diastolic': {'min': 40, 'max': 130, 'normal_min': 60, 'normal_max': 90}
            },
            'heart_rate': {
                'adult': {'min': 40, 'max': 180, 'normal_min': 60, 'normal_max': 100},
                'child': {'min': 70, 'max': 190, 'normal_min': 80, 'normal_max': 130},
                'infant': {'min': 100, 'max': 200, 'normal_min': 110, 'normal_max': 160}
            },
            'temperature': {
                'celsius': {'min': 35.0, 'max': 42.0, 'normal_min': 36.1, 'normal_max': 37.8},
                'fahrenheit': {'min': 95.0, 'max': 107.6, 'normal_min': 97.0, 'normal_max': 100.0}
            },
            'respiratory_rate': {
                'adult': {'min': 8, 'max': 40, 'normal_min': 12, 'normal_max': 20},
                'child': {'min': 15, 'max': 50, 'normal_min': 20, 'normal_max': 30},
                'infant': {'min': 25, 'max': 70, 'normal_min': 30, 'normal_max': 50}
            },
            'spo2': {
                'all': {'min': 70, 'max': 100, 'normal_min': 95, 'normal_max': 100}
            }
        }
    
    def validate_vitals(self, vitals: Dict, age: int = 30, sex: str = 'unknown') -> Dict:
        """
        Validate vital signs and return status with alerts
        """
        validation_result = {
            'status': 'normal',
            'alerts': [],
            'suggestions': [],
            'details': {}
        }
        
        # Determine age category
        age_category = self._get_age_category(age)
        
        # Validate each vital sign
        if 'blood_pressure' in vitals and vitals['blood_pressure']:
            bp_result = self._validate_blood_pressure(vitals['blood_pressure'])
            if bp_result['status'] != 'normal':
                validation_result['status'] = 'abnormal'
                validation_result['alerts'].extend(bp_result['alerts'])
                validation_result['suggestions'].extend(bp_result['suggestions'])
            validation_result['details']['blood_pressure'] = bp_result
        
        if 'heart_rate' in vitals and vitals['heart_rate']:
            hr_result = self._validate_heart_rate(vitals['heart_rate'], age_category)
            if hr_result['status'] != 'normal':
                validation_result['status'] = 'abnormal'
                validation_result['alerts'].extend(hr_result['alerts'])
                validation_result['suggestions'].extend(hr_result['suggestions'])
            validation_result['details']['heart_rate'] = hr_result
        
        if 'temperature' in vitals and vitals['temperature']:
            temp_result = self._validate_temperature(vitals['temperature'])
            if temp_result['status'] != 'normal':
                validation_result['status'] = 'abnormal'
                validation_result['alerts'].extend(temp_result['alerts'])
                validation_result['suggestions'].extend(temp_result['suggestions'])
            validation_result['details']['temperature'] = temp_result
        
        if 'respiratory_rate' in vitals and vitals['respiratory_rate']:
            rr_result = self._validate_respiratory_rate(vitals['respiratory_rate'], age_category)
            if rr_result['status'] != 'normal':
                validation_result['status'] = 'abnormal'
                validation_result['alerts'].extend(rr_result['alerts'])
                validation_result['suggestions'].extend(rr_result['suggestions'])
            validation_result['details']['respiratory_rate'] = rr_result
        
        if 'spo2' in vitals and vitals['spo2']:
            spo2_result = self._validate_spo2(vitals['spo2'])
            if spo2_result['status'] != 'normal':
                validation_result['status'] = 'abnormal'
                validation_result['alerts'].extend(spo2_result['alerts'])
                validation_result['suggestions'].extend(spo2_result['suggestions'])
            validation_result['details']['spo2'] = spo2_result
        
        # Determine overall severity
        if validation_result['alerts']:
            critical_count = sum(1 for alert in validation_result['alerts'] if 'critical' in alert.lower())
            if critical_count > 0:
                validation_result['severity'] = 'critical'
            else:
                validation_result['severity'] = 'moderate'
        else:
            validation_result['severity'] = 'normal'
        
        return validation_result
    
    def _get_age_category(self, age: int) -> str:
        """Determine age category for vital sign ranges"""
        if age < 1:
            return 'infant'
        elif age < 12:
            return 'child'
        else:
            return 'adult'
    
    def _validate_blood_pressure(self, bp_string: str) -> Dict:
        """Validate blood pressure values"""
        try:
            # Parse BP string (e.g., "120/80")
            parts = bp_string.strip().split('/')
            if len(parts) != 2:
                return {
                    'status': 'error',
                    'alerts': ['Invalid blood pressure format'],
                    'suggestions': ['Please enter BP as systolic/diastolic (e.g., 120/80)']
                }
            
            systolic = int(parts[0])
            diastolic = int(parts[1])
            
            result = {
                'status': 'normal',
                'alerts': [],
                'suggestions': [],
                'values': {'systolic': systolic, 'diastolic': diastolic}
            }
            
            # Check ranges
            sys_range = self.ranges['blood_pressure']['systolic']
            dia_range = self.ranges['blood_pressure']['diastolic']
            
            # Critical values
            if systolic < sys_range['min'] or systolic > sys_range['max']:
                result['status'] = 'critical'
                result['alerts'].append(f'Critical: Systolic BP {systolic} mmHg')
                result['suggestions'].append('Immediate medical attention required')
            elif systolic < sys_range['normal_min']:
                result['status'] = 'abnormal'
                result['alerts'].append(f'Low systolic BP: {systolic} mmHg')
                result['suggestions'].append('Monitor for hypotension symptoms')
            elif systolic > sys_range['normal_max']:
                result['status'] = 'abnormal'
                result['alerts'].append(f'High systolic BP: {systolic} mmHg')
                result['suggestions'].append('Consider antihypertensive evaluation')
            
            if diastolic < dia_range['min'] or diastolic > dia_range['max']:
                result['status'] = 'critical'
                result['alerts'].append(f'Critical: Diastolic BP {diastolic} mmHg')
                result['suggestions'].append('Immediate medical attention required')
            elif diastolic < dia_range['normal_min']:
                result['status'] = 'abnormal'
                result['alerts'].append(f'Low diastolic BP: {diastolic} mmHg')
            elif diastolic > dia_range['normal_max']:
                result['status'] = 'abnormal'
                result['alerts'].append(f'High diastolic BP: {diastolic} mmHg')
            
            return result
            
        except ValueError:
            return {
                'status': 'error',
                'alerts': ['Invalid blood pressure values'],
                'suggestions': ['Please enter numeric values']
            }
    
    def _validate_heart_rate(self, hr: int, age_category: str) -> Dict:
        """Validate heart rate"""
        hr_range = self.ranges['heart_rate'][age_category]
        
        result = {
            'status': 'normal',
            'alerts': [],
            'suggestions': [],
            'value': hr
        }
        
        if hr < hr_range['min'] or hr > hr_range['max']:
            result['status'] = 'critical'
            result['alerts'].append(f'Critical: Heart rate {hr} bpm')
            result['suggestions'].append('Immediate cardiac evaluation needed')
        elif hr < hr_range['normal_min']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Bradycardia: {hr} bpm')
            result['suggestions'].append('Monitor for symptoms, consider ECG')
        elif hr > hr_range['normal_max']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Tachycardia: {hr} bpm')
            result['suggestions'].append('Evaluate for underlying causes')
        
        return result
    
    def _validate_temperature(self, temp: float) -> Dict:
        """Validate temperature"""
        # Determine if Celsius or Fahrenheit
        if temp > 50:  # Likely Fahrenheit
            temp_range = self.ranges['temperature']['fahrenheit']
            unit = '°F'
        else:
            temp_range = self.ranges['temperature']['celsius']
            unit = '°C'
        
        result = {
            'status': 'normal',
            'alerts': [],
            'suggestions': [],
            'value': temp,
            'unit': unit
        }
        
        if temp < temp_range['min'] or temp > temp_range['max']:
            result['status'] = 'critical'
            result['alerts'].append(f'Critical: Temperature {temp}{unit}')
            result['suggestions'].append('Immediate medical attention required')
        elif temp < temp_range['normal_min']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Hypothermia: {temp}{unit}')
            result['suggestions'].append('Warm patient, monitor closely')
        elif temp > temp_range['normal_max']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Fever: {temp}{unit}')
            result['suggestions'].append('Consider antipyretics, investigate cause')
        
        return result
    
    def _validate_respiratory_rate(self, rr: int, age_category: str) -> Dict:
        """Validate respiratory rate"""
        rr_range = self.ranges['respiratory_rate'][age_category]
        
        result = {
            'status': 'normal',
            'alerts': [],
            'suggestions': [],
            'value': rr
        }
        
        if rr < rr_range['min'] or rr > rr_range['max']:
            result['status'] = 'critical'
            result['alerts'].append(f'Critical: Respiratory rate {rr}/min')
            result['suggestions'].append('Assess airway and breathing immediately')
        elif rr < rr_range['normal_min']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Bradypnea: {rr}/min')
            result['suggestions'].append('Monitor for respiratory depression')
        elif rr > rr_range['normal_max']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Tachypnea: {rr}/min')
            result['suggestions'].append('Evaluate for respiratory distress')
        
        return result
    
    def _validate_spo2(self, spo2: int) -> Dict:
        """Validate oxygen saturation"""
        spo2_range = self.ranges['spo2']['all']
        
        result = {
            'status': 'normal',
            'alerts': [],
            'suggestions': [],
            'value': spo2
        }
        
        if spo2 < spo2_range['min']:
            result['status'] = 'critical'
            result['alerts'].append(f'Critical: SpO2 {spo2}%')
            result['suggestions'].append('Administer oxygen immediately')
        elif spo2 < spo2_range['normal_min']:
            result['status'] = 'abnormal'
            result['alerts'].append(f'Hypoxemia: SpO2 {spo2}%')
            result['suggestions'].append('Consider supplemental oxygen')
        
        return result