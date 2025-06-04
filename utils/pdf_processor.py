# utils/pdf_processor.py
"""
PDF Lab Report Processor with OCR support - Windows Compatible Version
Handles text PDFs, image PDFs, and patient name validation
"""

import re
import PyPDF2
import pytesseract
from PIL import Image
import io
from difflib import SequenceMatcher
import logging
from pdf2image import convert_from_bytes
import tempfile
import os

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
        self.common_lab_patterns = {
            'hemoglobin': r'(?:hemoglobin|hb|haemoglobin)[\s:]*(\d+\.?\d*)\s*(?:g/dl|gm/dl)?',
            'wbc': r'(?:wbc|white blood cells?|total wbc)[\s:]*(\d+\.?\d*)\s*(?:/cumm|x10)?',
            'platelets': r'(?:platelets?|platelet count)[\s:]*(\d+\.?\d*)\s*(?:lakhs?|/cumm)?',
            'glucose': r'(?:glucose|blood sugar|fbs|rbs|ppbs)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
            'creatinine': r'(?:creatinine|creat)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
            'urea': r'(?:urea|blood urea)[\s:]*(\d+\.?\d*)\s*(?:mg/dl)?',
            'sgpt': r'(?:sgpt|alt|alanine)[\s:]*(\d+\.?\d*)\s*(?:u/l|iu/l)?',
            'sgot': r'(?:sgot|ast|aspartate)[\s:]*(\d+\.?\d*)\s*(?:u/l|iu/l)?',
        }
        
        self.name_patterns = [
            r'patient\s*name\s*:?\s*([a-zA-Z\s\.]+)',
            r'name\s*:?\s*([a-zA-Z\s\.]+)',
            r'pt\.\s*name\s*:?\s*([a-zA-Z\s\.]+)',
            r'patient\s*:?\s*([a-zA-Z\s\.]+)'
        ]
        
        # Check if Tesseract is available on Windows
        self.ocr_available = False
        if os.name == 'nt':  # Windows
            tesseract_path = os.environ.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                self.ocr_available = True
                logger.info(f"Tesseract found at: {tesseract_path}")
            else:
                logger.warning("Tesseract not found. OCR will be disabled.")
                logger.warning("To enable OCR, install Tesseract-OCR and set TESSERACT_CMD in .env")
        else:
            # On Linux/Mac, assume tesseract is in PATH
            try:
                pytesseract.get_tesseract_version()
                self.ocr_available = True
            except:
                self.ocr_available = False
    
    def process_pdf(self, pdf_file, expected_patient_name=None):
        """Main entry point for PDF processing"""
        try:
            # Read PDF bytes
            pdf_file.seek(0)  # Reset file pointer
            pdf_bytes = pdf_file.read()
            
            # Try text extraction first
            text_content = self._extract_text_pypdf(pdf_bytes)
            
            # If no text found and OCR is available, try OCR
            if not text_content.strip() and self.ocr_available:
                logger.info("No text found, attempting OCR")
                text_content = self._ocr_pdf(pdf_bytes)
            elif not text_content.strip():
                logger.warning("No text found and OCR not available")
                text_content = ""
            
            # Parse lab values
            lab_results = self._parse_lab_values(text_content)
            
            # Extract and validate patient name
            extracted_name = self._extract_patient_name(text_content)
            name_match = True
            match_confidence = 1.0
            
            if expected_patient_name and extracted_name:
                name_match, match_confidence = self._validate_name(
                    extracted_name, expected_patient_name
                )
            
            return {
                'success': True,
                'text_content': text_content,
                'lab_results': lab_results,
                'extracted_name': extracted_name,
                'name_match': name_match,
                'match_confidence': match_confidence,
                'ocr_available': self.ocr_available
            }
            
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'lab_results': {},
                'text_content': '',
                'ocr_available': self.ocr_available
            }
    
    def _extract_text_pypdf(self, pdf_bytes):
        """Extract text using PyPDF2"""
        text_content = ""
        try:
            # Create BytesIO object from bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
                    
            logger.info(f"Extracted {len(text_content)} characters from PDF")
            
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            import traceback
            traceback.print_exc()
        
        return text_content
    
    def _ocr_pdf(self, pdf_bytes):
        """OCR PDF pages - only if OCR is available"""
        if not self.ocr_available:
            logger.warning("OCR not available")
            return ""
        
        ocr_text = ""
        try:
            # Check if pdf2image and poppler are available
            try:
                # Convert PDF to images
                images = convert_from_bytes(pdf_bytes, dpi=200)
                logger.info(f"Converted PDF to {len(images)} images")
                
                # OCR each page
                for i, image in enumerate(images[:5]):  # Limit to first 5 pages
                    try:
                        text = pytesseract.image_to_string(image)
                        if text.strip():
                            ocr_text += f"\n--- Page {i + 1} ---\n{text}\n"
                    except Exception as e:
                        logger.error(f"OCR error on page {i}: {e}")
                        
            except Exception as e:
                logger.error(f"PDF to image conversion error: {e}")
                logger.info("Note: You need to install poppler-utils for Windows")
                logger.info("Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
                
        except Exception as e:
            logger.error(f"OCR process error: {e}")
        
        return ocr_text
    
    def _parse_lab_values(self, text):
        """Extract lab values from text"""
        if not text:
            return {}
            
        text_lower = text.lower()
        results = {}
        
        for test_name, pattern in self.common_lab_patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    results[test_name] = {
                        'value': value,
                        'raw_match': match.group(0).strip()
                    }
                    
                    # Add interpretation
                    results[test_name]['status'] = self._interpret_value(
                        test_name, value
                    )
                except ValueError:
                    continue
        
        logger.info(f"Found {len(results)} lab values in PDF")
        return results
    
    def _interpret_value(self, test_name, value):
        """Basic interpretation of lab values"""
        normal_ranges = {
            'hemoglobin': {'male': (13, 17), 'female': (12, 15)},
            'wbc': {'all': (4000, 11000)},
            'platelets': {'all': (1.5, 4.5)},  # in lakhs
            'glucose': {'fasting': (70, 100), 'random': (70, 140)},
            'creatinine': {'male': (0.7, 1.3), 'female': (0.6, 1.1)},
            'urea': {'all': (15, 40)},
            'sgpt': {'all': (0, 40)},
            'sgot': {'all': (0, 40)}
        }
        
        if test_name in normal_ranges:
            ranges = normal_ranges[test_name]
            # Simple check (can be enhanced with age/sex specific ranges)
            range_key = 'all' if 'all' in ranges else list(ranges.keys())[0]
            low, high = ranges[range_key]
            
            if value < low:
                return 'low'
            elif value > high:
                return 'high'
            else:
                return 'normal'
        
        return 'unknown'
    
    def _extract_patient_name(self, text):
        """Extract patient name from text"""
        if not text:
            return None
            
        for pattern in self.name_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up name
                name = re.sub(r'\s+', ' ', name)
                name = name.title()
                
                # Basic validation - should have at least 2 characters
                if len(name) > 2 and not name.lower().startswith('test'):
                    return name
        
        return None
    
    def _validate_name(self, extracted_name, expected_name):
        """Validate if names match using fuzzy matching"""
        # Normalize names
        name1 = extracted_name.lower().strip()
        name2 = expected_name.lower().strip()
        
        # Direct match
        if name1 == name2:
            return True, 1.0
        
        # Fuzzy match
        similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # Check if one name contains the other (common with initials)
        if name1 in name2 or name2 in name1:
            return True, max(similarity, 0.8)
        
        # Threshold for acceptance
        if similarity > 0.85:
            return True, similarity
        
        return False, similarity
    
    def format_lab_report(self, lab_results):
        """Format lab results for display"""
        if not lab_results:
            return "No lab values detected"
        
        report = "**Detected Lab Values:**\n\n"
        
        for test, data in lab_results.items():
            status_emoji = {
                'normal': '✅',
                'low': '⬇️',
                'high': '⬆️',
                'unknown': '❓'
            }
            
            emoji = status_emoji.get(data['status'], '❓')
            test_name = test.replace('_', ' ').title()
            
            report += f"{emoji} **{test_name}**: {data['value']} "
            if data['status'] != 'normal' and data['status'] != 'unknown':
                report += f"({data['status'].upper()})"
            report += "\n"
        
        return report