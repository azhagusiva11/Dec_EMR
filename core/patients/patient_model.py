"""
Patient Data Models
Using Pydantic for validation and type safety
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from datetime import datetime
import re


class Vitals(BaseModel):
    """Vital signs model with validation"""
    blood_pressure: Optional[str] = Field(None, pattern=r'^\d{2,3}/\d{2,3}$')
    heart_rate: Optional[int] = Field(None, ge=30, le=250)
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0)
    respiratory_rate: Optional[int] = Field(None, ge=8, le=40)
    spo2: Optional[int] = Field(None, ge=70, le=100)
    weight: Optional[float] = Field(None, ge=0.5, le=300)
    
    @validator('blood_pressure')
    def validate_bp(cls, v):
        if v:
            systolic, diastolic = map(int, v.split('/'))
            if not (60 <= systolic <= 250 and 40 <= diastolic <= 150):
                raise ValueError('Blood pressure out of physiological range')
        return v


class PatientCreate(BaseModel):
    """Model for creating new patient"""
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=150)
    sex: str = Field(..., pattern='^(male|female|other)$')
    mobile: str = Field(..., pattern=r'^\+?[1-9]\d{9,14}$')
    blood_group: Optional[str] = Field(None, pattern='^(A|B|AB|O)[+-]$')
    address: Optional[str] = None
    chronic_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    emergency_contact: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z\s\'-]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip().title()
    
    @validator('mobile')
    def validate_mobile(cls, v):
        # Remove any non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', v)
        if not cleaned.startswith('+91') and len(cleaned) == 10:
            cleaned = '+91' + cleaned
        return cleaned


class PatientUpdate(BaseModel):
    """Model for updating patient info"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    sex: Optional[str] = Field(None, pattern='^(male|female|other)$')
    mobile: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{9,14}$')
    blood_group: Optional[str] = Field(None, pattern='^(A|B|AB|O)[+-]$')
    address: Optional[str] = None
    chronic_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    emergency_contact: Optional[str] = None


class Patient(BaseModel):
    """Complete patient model"""
    id: str
    name: str
    age: int
    sex: str
    mobile: str
    blood_group: Optional[str] = None
    address: Optional[str] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    emergency_contact: Optional[str] = None
    registration_date: str
    visits: List[Dict] = []
    symptom_tracking: Dict[str, List[Dict]] = {}
    admissions: List[Dict] = []
    
    class Config:
        schema_extra = {
            "example": {
                "id": "P20241226123456",
                "name": "John Doe",
                "age": 35,
                "sex": "male",
                "mobile": "+919876543210",
                "blood_group": "O+",
                "registration_date": "2024-12-26T12:34:56",
                "visits": [],
                "symptom_tracking": {},
                "admissions": []
            }
        }