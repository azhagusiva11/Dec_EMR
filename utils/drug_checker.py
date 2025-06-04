import json
import os
import re
from typing import Dict, List, Tuple

class DrugInteractionChecker:
    def __init__(self):
        """Initialize the drug interaction checker"""
        self.drug_database = self.load_drug_database()
    
    def load_drug_database(self) -> Dict:
        """Load the Indian drug database"""
        try:
            filepath = os.path.join("data", "indian_drugs.json")
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            else:
                # Return default database if file doesn't exist
                return self.get_default_database()
        except Exception as e:
            print(f"Error loading drug database: {e}")
            return self.get_default_database()
    
    def get_default_database(self) -> Dict:
        """Return default Indian drug database"""
        return {
            "drugs": {
                "paracetamol": {
                    "brand_names": ["Crocin", "Calpol", "Dolo", "Paracip"],
                    "category": "analgesic",
                    "interactions": {
                        "warfarin": {
                            "severity": "moderate",
                            "description": "May increase INR with regular use"
                        }
                    },
                    "contraindications": ["severe liver disease"],
                    "pregnancy_category": "B"
                },
                "aspirin": {
                    "brand_names": ["Ecosprin", "Disprin", "Aspro"],
                    "category": "antiplatelet",
                    "interactions": {
                        "warfarin": {
                            "severity": "major",
                            "description": "Increased risk of bleeding"
                        },
                        "ibuprofen": {
                            "severity": "moderate",
                            "description": "May reduce antiplatelet effect"
                        }
                    },
                    "contraindications": ["active bleeding", "peptic ulcer"],
                    "pregnancy_category": "D"
                },
                "metformin": {
                    "brand_names": ["Glycomet", "Glucophage", "Carbophage"],
                    "category": "antidiabetic",
                    "interactions": {
                        "alcohol": {
                            "severity": "major",
                            "description": "Risk of lactic acidosis"
                        }
                    },
                    "contraindications": ["renal impairment", "metabolic acidosis"],
                    "pregnancy_category": "B"
                },
                "amlodipine": {
                    "brand_names": ["Amlogard", "Amlip", "Norvasc"],
                    "category": "antihypertensive",
                    "interactions": {
                        "simvastatin": {
                            "severity": "moderate",
                            "description": "Increased statin levels, risk of myopathy"
                        }
                    },
                    "contraindications": ["severe hypotension"],
                    "pregnancy_category": "C"
                },
                "amoxicillin": {
                    "brand_names": ["Mox", "Novamox", "Amoxil"],
                    "category": "antibiotic",
                    "interactions": {
                        "warfarin": {
                            "severity": "moderate",
                            "description": "May increase INR"
                        }
                    },
                    "contraindications": ["penicillin allergy"],
                    "pregnancy_category": "B"
                },
                "omeprazole": {
                    "brand_names": ["Omez", "Prilosec", "Ocid"],
                    "category": "ppi",
                    "interactions": {
                        "clopidogrel": {
                            "severity": "major",
                            "description": "Reduces antiplatelet effect of clopidogrel"
                        }
                    },
                    "contraindications": [],
                    "pregnancy_category": "C"
                },
                "atorvastatin": {
                    "brand_names": ["Atorva", "Lipitor", "Storvas"],
                    "category": "statin",
                    "interactions": {
                        "clarithromycin": {
                            "severity": "major",
                            "description": "Increased risk of myopathy and rhabdomyolysis"
                        }
                    },
                    "contraindications": ["active liver disease", "pregnancy"],
                    "pregnancy_category": "X"
                },
                "warfarin": {
                    "brand_names": ["Warf", "Coumadin"],
                    "category": "anticoagulant",
                    "interactions": {
                        "aspirin": {
                            "severity": "major",
                            "description": "Increased risk of bleeding"
                        },
                        "paracetamol": {
                            "severity": "moderate",
                            "description": "May increase INR with regular use"
                        }
                    },
                    "contraindications": ["active bleeding", "pregnancy"],
                    "pregnancy_category": "X"
                },
                "tramadol": {
                    "brand_names": ["Ultracet", "Tramazac", "Contramal"],
                    "category": "opioid_analgesic",
                    "interactions": {
                        "ssri": {
                            "severity": "major",
                            "description": "Risk of serotonin syndrome"
                        }
                    },
                    "contraindications": ["seizure disorder", "MAO inhibitor use"],
                    "pregnancy_category": "C"
                },
                "alprazolam": {
                    "brand_names": ["Alprax", "Restyl", "Alzolam"],
                    "category": "benzodiazepine",
                    "interactions": {
                        "alcohol": {
                            "severity": "major",
                            "description": "Severe CNS depression, potentially fatal"
                        }
                    },
                    "contraindications": ["narrow angle glaucoma", "severe respiratory depression"],
                    "pregnancy_category": "D"
                }
            }
        }
    
    def extract_drugs_from_prescription(self, prescription: str) -> List[str]:
        """Extract drug names from prescription text"""
        prescription_lower = prescription.lower()
        found_drugs = []
        
        # Check for generic names
        for drug_name in self.drug_database.get("drugs", {}).keys():
            if drug_name in prescription_lower:
                found_drugs.append(drug_name)
        
        # Check for brand names
        for drug_name, drug_info in self.drug_database.get("drugs", {}).items():
            for brand in drug_info.get("brand_names", []):
                if brand.lower() in prescription_lower:
                    if drug_name not in found_drugs:
                        found_drugs.append(drug_name)
        
        return found_drugs
    
    def check_interactions(self, drugs: List[str]) -> List[Dict]:
        """Check for drug-drug interactions"""
        interactions = []
        
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                # Check if drug1 has interactions with drug2
                drug1_info = self.drug_database.get("drugs", {}).get(drug1, {})
                if drug2 in drug1_info.get("interactions", {}):
                    interaction = drug1_info["interactions"][drug2]
                    interactions.append({
                        "drug1": drug1,
                        "drug2": drug2,
                        "severity": interaction["severity"],
                        "description": f"{drug1.title()} + {drug2.title()}: {interaction['description']}"
                    })
                
                # Check reverse interaction
                drug2_info = self.drug_database.get("drugs", {}).get(drug2, {})
                if drug1 in drug2_info.get("interactions", {}):
                    # Avoid duplicate entries
                    already_added = any(
                        i["drug1"] == drug2 and i["drug2"] == drug1 
                        for i in interactions
                    )
                    if not already_added:
                        interaction = drug2_info["interactions"][drug1]
                        interactions.append({
                            "drug1": drug2,
                            "drug2": drug1,
                            "severity": interaction["severity"],
                            "description": f"{drug2.title()} + {drug1.title()}: {interaction['description']}"
                        })
        
        return interactions
    
    def check_pregnancy_safety(self, drugs: List[str]) -> List[str]:
        """Check pregnancy safety categories"""
        warnings = []
        
        for drug in drugs:
            drug_info = self.drug_database.get("drugs", {}).get(drug, {})
            category = drug_info.get("pregnancy_category", "Unknown")
            
            if category == "D":
                warnings.append(f"{drug.title()}: Category D - Positive evidence of risk in pregnancy")
            elif category == "X":
                warnings.append(f"{drug.title()}: Category X - CONTRAINDICATED in pregnancy")
        
        return warnings
    
    def check_contraindications(self, drugs: List[str]) -> List[str]:
        """Check for important contraindications"""
        warnings = []
        
        for drug in drugs:
            drug_info = self.drug_database.get("drugs", {}).get(drug, {})
            contraindications = drug_info.get("contraindications", [])
            
            if contraindications:
                warnings.append(f"{drug.title()}: Contraindicated in {', '.join(contraindications)}")
        
        return warnings
    
    def check_prescription(self, prescription: str) -> Dict:
        """Main method to check prescription for interactions and warnings"""
        # Extract drugs from prescription
        drugs = self.extract_drugs_from_prescription(prescription)
        
        # Check for interactions
        interactions = self.check_interactions(drugs)
        
        # Check pregnancy safety
        pregnancy_warnings = self.check_pregnancy_safety(drugs)
        
        # Check contraindications
        contraindication_warnings = self.check_contraindications(drugs)
        
        # Combine all warnings
        all_warnings = pregnancy_warnings + contraindication_warnings
        
        return {
            "drugs_found": drugs,
            "interactions": interactions,
            "has_interactions": len(interactions) > 0,
            "warnings": all_warnings,
            "has_warnings": len(all_warnings) > 0
        }