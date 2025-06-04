"""
Bulk Disease Importer for Smart EMR
Import diseases from various medical databases and formats
"""

import json
import csv
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
from typing import Dict, List, Optional
import re
from datetime import datetime

class DiseaseBulkImporter:
    """
    Import diseases from multiple sources:
    - CSV files (from medical databases)
    - ORPHANET XML
    - ICD-10 databases
    - Custom Excel sheets
    - Online APIs
    """
    
    def __init__(self, output_path: str = "data/rare_diseases_comprehensive.json"):
        self.output_path = Path(output_path)
        self.existing_diseases = self._load_existing_diseases()
        self.import_stats = {
            "total_imported": 0,
            "duplicates_skipped": 0,
            "errors": 0
        }
    
    def _load_existing_diseases(self) -> Dict:
        """Load existing diseases to avoid duplicates"""
        if self.output_path.exists():
            with open(self.output_path, 'r') as f:
                data = json.load(f)
                return {d['name']: d for d in data.get('diseases', [])}
        return {}
    
    def import_from_csv(self, csv_path: str, mapping: Dict[str, str] = None) -> int:
        """
        Import diseases from CSV file with flexible column mapping
        
        Example CSV format:
        Disease Name, ICD10, Symptoms, Min Age, Max Age, Tests, Specialist
        
        Args:
            csv_path: Path to CSV file
            mapping: Column name mapping, e.g., {"Disease Name": "name", "ICD10": "icd10"}
        """
        print(f"📥 Importing from CSV: {csv_path}")
        
        default_mapping = {
            "Disease Name": "name",
            "Disease": "name",
            "Name": "name",
            "ICD10": "icd10",
            "ICD-10": "icd10",
            "ICD10 Code": "icd10",
            "Symptoms": "symptoms",
            "Clinical Features": "symptoms",
            "Signs and Symptoms": "symptoms",
            "Tests": "diagnostic_tests",
            "Diagnostic Tests": "diagnostic_tests",
            "Laboratory Tests": "diagnostic_tests",
            "Specialist": "specialist",
            "Specialty": "specialist",
            "Prevalence": "prevalence",
            "Frequency": "prevalence",
            "Age of Onset": "age_onset",
            "OMIM": "omim",
            "OMIM Number": "omim",
            "Inheritance": "inheritance",
            "Gene": "gene",
            "Category": "category"
        }
        
        if mapping:
            default_mapping.update(mapping)
        
        imported_count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for row in reader:
                    disease = self._parse_csv_row(row, default_mapping)
                    if disease and disease['name'] not in self.existing_diseases:
                        self.existing_diseases[disease['name']] = disease
                        imported_count += 1
                        
                        if imported_count % 10 == 0:
                            print(f"  ✓ Imported {imported_count} diseases...")
                    elif disease:
                        self.import_stats["duplicates_skipped"] += 1
        
        except Exception as e:
            print(f"❌ Error importing CSV: {e}")
            self.import_stats["errors"] += 1
        
        self.import_stats["total_imported"] += imported_count
        print(f"✅ Imported {imported_count} new diseases from CSV")
        return imported_count
    
    def _parse_csv_row(self, row: Dict, mapping: Dict) -> Optional[Dict]:
        """Parse a CSV row into disease format"""
        try:
            disease = {
                "name": "",
                "icd10": "",
                "prevalence": "Unknown",
                "symptoms": {},
                "time_window_days": 180,
                "min_symptoms": 3,
                "diagnostic_tests": [],
                "specialist": "Specialist"
            }
            
            # Map basic fields
            for csv_col, json_field in mapping.items():
                if csv_col in row and row[csv_col]:
                    if json_field == "name":
                        disease["name"] = row[csv_col].strip()
                    elif json_field == "icd10":
                        disease["icd10"] = row[csv_col].strip()
                    elif json_field == "prevalence":
                        disease["prevalence"] = self._normalize_prevalence(row[csv_col])
                    elif json_field == "specialist":
                        disease["specialist"] = row[csv_col].strip()
            
            # Skip if no name
            if not disease["name"]:
                return None
            
            # Parse symptoms (handle various formats)
            symptom_cols = [col for col in row if any(s in col.lower() for s in ["symptom", "clinical", "signs"])]
            all_symptoms = []
            
            for col in symptom_cols:
                if row[col]:
                    # Handle different delimiters
                    symptoms = re.split(r'[;,|\n]', row[col])
                    all_symptoms.extend([s.strip().lower() for s in symptoms if s.strip()])
            
            # Categorize symptoms
            disease["symptoms"] = self._categorize_symptoms(all_symptoms)
            
            # Parse diagnostic tests
            test_cols = [col for col in row if any(t in col.lower() for t in ["test", "diagnostic", "laboratory"])]
            for col in test_cols:
                if row[col]:
                    tests = re.split(r'[;,|\n]', row[col])
                    disease["diagnostic_tests"].extend([t.strip() for t in tests if t.strip()])
            
            # Set age-specific parameters
            if "age" in row.get("Age of Onset", "").lower() or "pediatric" in str(row.values()).lower():
                disease["age_focus"] = "pediatric"
                disease["min_symptoms"] = 2  # Lower threshold for children
            
            # Calculate urgency based on keywords
            disease["urgency_score"] = self._calculate_urgency(disease)
            
            return disease
            
        except Exception as e:
            print(f"  ⚠️ Error parsing row: {e}")
            return None
    
    def import_from_orphanet_xml(self, xml_path: str) -> int:
        """
        Import from ORPHANET XML format
        ORPHANET is the reference portal for rare diseases
        """
        print(f"📥 Importing from ORPHANET XML: {xml_path}")
        imported_count = 0
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Navigate ORPHANET structure
            for disorder in root.findall('.//Disorder'):
                disease = self._parse_orphanet_disorder(disorder)
                if disease and disease['name'] not in self.existing_diseases:
                    self.existing_diseases[disease['name']] = disease
                    imported_count += 1
                    
                    if imported_count % 10 == 0:
                        print(f"  ✓ Imported {imported_count} diseases...")
        
        except Exception as e:
            print(f"❌ Error importing ORPHANET XML: {e}")
            self.import_stats["errors"] += 1
        
        self.import_stats["total_imported"] += imported_count
        print(f"✅ Imported {imported_count} new diseases from ORPHANET")
        return imported_count
    
    def _parse_orphanet_disorder(self, disorder_elem) -> Optional[Dict]:
        """Parse ORPHANET disorder element"""
        try:
            disease = {
                "name": disorder_elem.findtext('.//Name', '').strip(),
                "orpha_code": disorder_elem.findtext('.//OrphaCode', ''),
                "icd10": "",
                "prevalence": "Unknown",
                "symptoms": {},
                "time_window_days": 180,
                "min_symptoms": 3,
                "diagnostic_tests": [],
                "specialist": "Rare Disease Specialist"
            }
            
            # Get ICD codes
            for ext_ref in disorder_elem.findall('.//ExternalReference'):
                if ext_ref.findtext('Source') == 'ICD-10':
                    disease["icd10"] = ext_ref.findtext('Reference', '')
                    break
            
            # Get prevalence
            prevalence_elem = disorder_elem.find('.//AveragePrevalence')
            if prevalence_elem is not None:
                disease["prevalence"] = prevalence_elem.findtext('Name', 'Unknown')
            
            # Get clinical signs
            symptoms = []
            for sign in disorder_elem.findall('.//ClinicalSign'):
                symptom = sign.findtext('Name', '').lower()
                if symptom:
                    symptoms.append(symptom)
            
            disease["symptoms"] = self._categorize_symptoms(symptoms)
            
            # Get age of onset
            onset = disorder_elem.findtext('.//AverageAgeOfOnset/Name', '')
            if any(term in onset.lower() for term in ['infant', 'neonatal', 'childhood']):
                disease["age_focus"] = "pediatric"
                disease["min_symptoms"] = 2
            
            return disease if disease["name"] else None
            
        except Exception as e:
            print(f"  ⚠️ Error parsing disorder: {e}")
            return None
    
    def import_from_icd10_api(self, chapter: str = None, limit: int = 100) -> int:
        """
        Import from WHO ICD-10 API
        Note: Requires API token from https://icd.who.int/icdapi
        """
        print(f"📥 Importing from WHO ICD-10 API...")
        
        # This is a mock implementation - actual API requires authentication
        # Example of how it would work:
        
        api_token = "your_api_token_here"  # Get from WHO
        base_url = "https://id.who.int/icd/release/10/"
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
            "API-Version": "v2"
        }
        
        # Note: This is pseudocode - actual implementation would need proper API setup
        print("ℹ️ ICD-10 API import requires WHO API credentials")
        print("  Visit: https://icd.who.int/icdapi to get access")
        
        return 0
    
    def import_from_custom_excel(self, excel_path: str, sheet_name: str = None) -> int:
        """
        Import from Excel files (common in hospitals)
        Requires: pip install openpyxl or xlrd
        """
        print(f"📥 Importing from Excel: {excel_path}")
        
        try:
            import pandas as pd
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(excel_path)
            
            # Convert to CSV-like format and use CSV importer
            temp_csv = "temp_import.csv"
            df.to_csv(temp_csv, index=False)
            
            count = self.import_from_csv(temp_csv)
            
            # Clean up
            Path(temp_csv).unlink()
            
            return count
            
        except ImportError:
            print("❌ Please install pandas and openpyxl: pip install pandas openpyxl")
            return 0
        except Exception as e:
            print(f"❌ Error importing Excel: {e}")
            return 0
    
    def import_from_medical_database(self, db_name: str, connection_string: str = None) -> int:
        """
        Import from medical databases like:
        - OMIM (Online Mendelian Inheritance in Man)
        - ClinVar
        - PubMed
        - Hospital databases
        """
        print(f"📥 Importing from {db_name}...")
        
        if db_name.lower() == "omim":
            return self._import_from_omim()
        elif db_name.lower() == "clinvar":
            return self._import_from_clinvar()
        else:
            print(f"ℹ️ Database {db_name} not yet implemented")
            return 0
    
    def _import_from_omim(self) -> int:
        """Import from OMIM (requires API key)"""
        print("ℹ️ OMIM import requires API key from https://omim.org/api")
        
        # Example structure:
        """
        api_key = "your_omim_api_key"
        base_url = "https://api.omim.org/api"
        
        # Get genetic diseases
        response = requests.get(
            f"{base_url}/entry/search",
            params={
                "search": "rare disease",
                "include": "clinicalSynopsis",
                "format": "json",
                "apiKey": api_key
            }
        )
        """
        
        return 0
    
    def _categorize_symptoms(self, symptoms: List[str]) -> Dict[str, List[str]]:
        """Intelligently categorize symptoms"""
        categories = {
            "neurological": [],
            "gastrointestinal": [],
            "cardiovascular": [],
            "respiratory": [],
            "musculoskeletal": [],
            "dermatological": [],
            "ophthalmologic": [],
            "psychiatric": [],
            "endocrine": [],
            "hematologic": [],
            "renal": [],
            "immunologic": [],
            "other": []
        }
        
        # Keywords for categorization
        category_keywords = {
            "neurological": ["tremor", "seizure", "headache", "numbness", "paralysis", "ataxia", "dystonia"],
            "gastrointestinal": ["vomiting", "nausea", "diarrhea", "constipation", "abdominal", "hepat"],
            "cardiovascular": ["chest pain", "palpitation", "hypertension", "hypotension", "heart"],
            "respiratory": ["cough", "dyspnea", "wheeze", "breathing", "respiratory"],
            "musculoskeletal": ["joint", "muscle", "bone", "arthralgia", "myalgia", "weakness"],
            "dermatological": ["rash", "skin", "lesion", "pruritus", "eczema", "erythema"],
            "ophthalmologic": ["vision", "eye", "blindness", "diplopia", "ptosis"],
            "psychiatric": ["depression", "anxiety", "psychosis", "mood", "behavior"],
            "endocrine": ["diabetes", "thyroid", "hormone", "growth"],
            "hematologic": ["anemia", "bleeding", "bruising", "thrombocytopenia"],
            "renal": ["kidney", "renal", "proteinuria", "hematuria"],
            "immunologic": ["immunodeficiency", "autoimmune", "allergy"]
        }
        
        for symptom in symptoms:
            categorized = False
            for category, keywords in category_keywords.items():
                if any(keyword in symptom.lower() for keyword in keywords):
                    categories[category].append(symptom)
                    categorized = True
                    break
            
            if not categorized:
                categories["other"].append(symptom)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _normalize_prevalence(self, prevalence_str: str) -> str:
        """Normalize prevalence formats"""
        if not prevalence_str:
            return "Unknown"
        
        # Common patterns
        patterns = {
            r"(\d+)\s*[/:]?\s*(\d+[,\d]*)\s*000": r"1 in \2,000",
            r"<?\s*1\s*[/:]?\s*(\d+)": r"1 in \1",
            r"(\d+\.?\d*)\s*%": lambda m: f"1 in {int(100/float(m.group(1)))}",
        }
        
        for pattern, replacement in patterns.items():
            if callable(replacement):
                match = re.search(pattern, prevalence_str)
                if match:
                    return replacement(match)
            else:
                prevalence_str = re.sub(pattern, replacement, prevalence_str)
        
        return prevalence_str
    
    def _calculate_urgency(self, disease: Dict) -> int:
        """Calculate urgency score (1-5) based on disease characteristics"""
        score = 3  # Default moderate
        
        # Keywords that increase urgency
        urgent_keywords = ["acute", "fatal", "emergency", "crisis", "failure", "severe", "malignant"]
        moderate_keywords = ["progressive", "chronic", "degenerative"]
        
        # Check disease name and symptoms
        all_text = disease["name"].lower() + " ".join(str(disease["symptoms"].values())).lower()
        
        if any(keyword in all_text for keyword in urgent_keywords):
            score = 5
        elif any(keyword in all_text for keyword in moderate_keywords):
            score = 4
        
        # Pediatric diseases get +1 urgency
        if disease.get("age_focus") == "pediatric":
            score = min(score + 1, 5)
        
        return score
    
    def save_to_file(self, merge: bool = True) -> None:
        """Save imported diseases to file"""
        print(f"\n💾 Saving to {self.output_path}")
        
        if merge and self.output_path.exists():
            # Load existing data
            with open(self.output_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {"diseases": []}
        
        # Convert to list and sort by name
        all_diseases = list(self.existing_diseases.values())
        all_diseases.sort(key=lambda x: x["name"])
        
        existing_data["diseases"] = all_diseases
        existing_data["metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "total_diseases": len(all_diseases),
            "import_stats": self.import_stats
        }
        
        # Save with pretty formatting
        with open(self.output_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"✅ Saved {len(all_diseases)} total diseases")
        print(f"📊 Import Statistics:")
        print(f"  - New diseases imported: {self.import_stats['total_imported']}")
        print(f"  - Duplicates skipped: {self.import_stats['duplicates_skipped']}")
        print(f"  - Errors: {self.import_stats['errors']}")
    
    def bulk_import_sources(self, sources: List[Dict]) -> None:
        """
        Import from multiple sources at once
        
        Example:
        sources = [
            {"type": "csv", "path": "diseases1.csv"},
            {"type": "csv", "path": "diseases2.csv", "mapping": {"Disease": "name"}},
            {"type": "orphanet", "path": "orphanet.xml"},
            {"type": "excel", "path": "hospital_diseases.xlsx"}
        ]
        """
        print(f"\n🚀 Starting bulk import from {len(sources)} sources\n")
        
        for source in sources:
            source_type = source.get("type", "").lower()
            path = source.get("path")
            
            if source_type == "csv":
                self.import_from_csv(path, source.get("mapping"))
            elif source_type == "orphanet":
                self.import_from_orphanet_xml(path)
            elif source_type == "excel":
                self.import_from_custom_excel(path, source.get("sheet"))
            elif source_type == "icd10":
                self.import_from_icd10_api(source.get("chapter"))
            else:
                print(f"⚠️ Unknown source type: {source_type}")
            
            print()  # Blank line between sources
        
        # Save all imported data
        self.save_to_file()


# Example usage
if __name__ == "__main__":
    importer = DiseaseBulkImporter()
    
    # Example 1: Import from CSV
    # importer.import_from_csv("rare_diseases_database.csv")
    
    # Example 2: Import from multiple sources
    sources = [
        {"type": "csv", "path": "pediatric_diseases.csv"},
        {"type": "csv", "path": "neurological_diseases.csv"},
        {"type": "excel", "path": "hospital_rare_diseases.xlsx"}
    ]
    # importer.bulk_import_sources(sources)
    
    # Save the results
    # importer.save_to_file()
    
    print("\n📌 Import tool ready. Use the methods above to import your disease databases!")