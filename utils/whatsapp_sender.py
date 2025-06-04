import os
from twilio.rest import Client
from datetime import datetime
import json
from typing import Dict, Optional

class WhatsAppSender:
    def __init__(self):
        # Load Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Twilio sandbox default
        
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                print(f"WhatsApp integration enabled. From: {self.whatsapp_number}")
            except Exception as e:
                self.enabled = False
                print(f"WhatsApp initialization error: {e}")
        else:
            self.enabled = False
            print("WhatsApp integration disabled - Missing Twilio credentials")
            print("Add to .env file:")
            print("TWILIO_ACCOUNT_SID=your_sid")
            print("TWILIO_AUTH_TOKEN=your_token")
    
    def format_prescription_message(self, patient_name: str, prescription: str, doctor_name: str = "Smart EMR") -> str:
        """Format prescription for WhatsApp"""
        # Clean prescription text
        prescription_clean = prescription.strip()
        if prescription_clean.startswith("PRESCRIPTION:"):
            prescription_clean = prescription_clean.replace("PRESCRIPTION:", "").strip()
        
        message = f"""
*Smart EMR - Prescription* 📋

*Patient:* {patient_name}
*Date:* {datetime.now().strftime('%d-%m-%Y')}
*Time:* {datetime.now().strftime('%I:%M %p')}

*Prescription:*
{prescription_clean}

*Instructions:*
• Take medicines as prescribed
• Complete the full course
• Follow up if symptoms persist

*Doctor:* {doctor_name}

_This is an automated message from Smart EMR_
        """
        return message.strip()
    
    def format_visit_summary(self, patient_data: Dict, visit_data: Dict) -> str:
        """Format visit summary for WhatsApp"""
        # Handle both old and new patient data formats
        if 'patient_profile' in patient_data:
            name = patient_data['patient_profile'].get('name', 'Patient')
        else:
            name = patient_data.get('name', 'Patient')
        
        symptoms = visit_data.get('symptoms', 'No symptoms recorded')
        
        # Extract key points from clinical summary
        clinical_summary = visit_data.get('ai_summary', visit_data.get('clinical_summary', 'No assessment available'))
        
        # Try to extract diagnosis from summary
        diagnosis = "See full summary"
        if "ASSESSMENT:" in clinical_summary:
            assessment_part = clinical_summary.split("ASSESSMENT:")[1].split("\n")[0:2]
            diagnosis = " ".join(assessment_part).strip()[:100] + "..."
        
        prescription = visit_data.get('prescription', 'No prescription')
        
        message = f"""
*Smart EMR - Visit Summary* 🏥

*Patient:* {name}
*Date:* {datetime.now().strftime('%d-%m-%Y')}

*Chief Complaints:*
{symptoms[:200]}...

*Diagnosis:*
{diagnosis}

*Prescription:*
{prescription}

*Next Steps:*
• Follow prescription carefully
• Return if symptoms worsen
• Schedule follow-up as advised

_Smart EMR - Better Healthcare_
        """
        return message.strip()
    
    def send_message(self, to_number: str, message: str) -> Dict:
        """Send WhatsApp message with better error handling"""
        if not self.enabled:
            return {
                "success": False,
                "error": "WhatsApp not configured. Add Twilio credentials to .env file:\nTWILIO_ACCOUNT_SID=xxx\nTWILIO_AUTH_TOKEN=xxx"
            }
        
        try:
            # Clean and format the number
            to_number = to_number.strip()
            
            # Ensure proper WhatsApp format
            if not to_number.startswith('whatsapp:'):
                # Ensure country code is present
                if not to_number.startswith('+'):
                    # Default to India if no country code
                    if to_number.startswith('91'):
                        to_number = f'+{to_number}'
                    else:
                        to_number = f'+91{to_number}'
                
                to_number = f'whatsapp:{to_number}'
            
            print(f"Sending WhatsApp to: {to_number}")
            print(f"From: {self.whatsapp_number}")
            
            # Send message
            message_instance = self.client.messages.create(
                body=message[:1600],  # WhatsApp has a 1600 char limit
                from_=self.whatsapp_number,
                to=to_number
            )
            
            return {
                "success": True,
                "message_sid": message_instance.sid,
                "status": message_instance.status,
                "to": to_number
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"WhatsApp send error: {error_msg}")
            
            # Provide helpful error messages
            if "21408" in error_msg:
                return {
                    "success": False,
                    "error": "Number has not joined Twilio Sandbox. Ask them to send 'join <your-sandbox-word>' to +14155238886"
                }
            elif "authenticate" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Invalid Twilio credentials. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env"
                }
            elif "21211" in error_msg:
                return {
                    "success": False,
                    "error": f"Invalid phone number format: {to_number}. Use format: +919876543210"
                }
            else:
                return {
                    "success": False,
                    "error": f"WhatsApp error: {error_msg}"
                }
    
    def send_prescription(self, patient_data: Dict, prescription: str, doctor_name: str = "Smart EMR") -> Dict:
        """Send prescription to patient via WhatsApp"""
        # Handle both old and new patient data formats
        if 'patient_profile' in patient_data:
            name = patient_data['patient_profile'].get('name', 'Patient')
            mobile = patient_data['patient_profile'].get('mobile', '')
        else:
            name = patient_data.get('name', 'Patient')
            mobile = patient_data.get('mobile', '')
        
        if not mobile:
            return {"success": False, "error": "No mobile number found for patient"}
        
        # Format message
        message = self.format_prescription_message(
            patient_name=name,
            prescription=prescription,
            doctor_name=doctor_name
        )
        
        # Send via WhatsApp
        result = self.send_message(mobile, message)
        
        if result['success']:
            print(f"Prescription sent to {name} at {mobile}")
        else:
            print(f"Failed to send prescription: {result['error']}")
            
        return result
    
    def send_visit_summary(self, patient_data: Dict, visit_data: Dict) -> Dict:
        """Send complete visit summary to patient"""
        # Handle both old and new patient data formats
        if 'patient_profile' in patient_data:
            mobile = patient_data['patient_profile'].get('mobile', '')
        else:
            mobile = patient_data.get('mobile', '')
        
        if not mobile:
            return {"success": False, "error": "No mobile number found for patient"}
        
        # Format message
        message = self.format_visit_summary(patient_data, visit_data)
        
        # Send via WhatsApp
        result = self.send_message(mobile, message)
        
        if result['success']:
            print(f"Visit summary sent to {mobile}")
        else:
            print(f"Failed to send visit summary: {result['error']}")
            
        return result
    
    def send_appointment_reminder(self, patient_name: str, mobile: str, 
                                appointment_date: str, appointment_time: str) -> Dict:
        """Send appointment reminder"""
        message = f"""
*Appointment Reminder* 📅

Dear {patient_name},

This is a reminder for your appointment:

*Date:* {appointment_date}
*Time:* {appointment_time}

Please arrive 10 minutes early.

Reply CONFIRM to confirm or CANCEL to cancel.

_Smart EMR Appointments_
        """
        
        return self.send_message(mobile, message)
    
    def test_connection(self, test_number: str) -> Dict:
        """Test WhatsApp connection with a simple message"""
        test_message = f"""
*Smart EMR Test Message* ✅

Hello! This is a test message from Smart EMR.

Time: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}

If you received this message, WhatsApp integration is working correctly.

_This is an automated test message_
        """
        return self.send_message(test_number, test_message)

# Utility function for easy integration
def setup_whatsapp_integration():
    """Setup WhatsApp integration in Streamlit"""
    import streamlit as st
    
    with st.expander("WhatsApp Settings"):
        st.info("To enable WhatsApp, add these to your .env file:")
        st.code("""
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
        """)
        
        # Check current status
        sender = WhatsAppSender()
        if sender.enabled:
            st.success("✅ WhatsApp integration is active!")
            st.info(f"Using WhatsApp number: {sender.whatsapp_number}")
        else:
            st.error("❌ WhatsApp not configured. Add Twilio credentials.")
        
        # For testing with Twilio Sandbox
        st.markdown("""
        **For Testing (Twilio Sandbox):**
        1. Send `join <your-sandbox-keyword>` to **+1 415 523 8886** on WhatsApp
        2. You'll receive a confirmation
        3. Then you can receive messages from Smart EMR
        
        **Important:** Each new number must join the sandbox before receiving messages!
        """)

# Template messages in multiple languages
class MultilingualWhatsApp:
    def __init__(self):
        self.templates = {
            "English": {
                "greeting": "Hello",
                "prescription_header": "Prescription",
                "take_medicine": "Take medicines as prescribed",
                "follow_up": "Follow up if needed"
            },
            "Tamil": {
                "greeting": "வணக்கம்",
                "prescription_header": "மருந்து சீட்டு",
                "take_medicine": "மருந்துகளை பரிந்துரைத்தபடி எடுத்துக்கொள்ளவும்",
                "follow_up": "தேவைப்பட்டால் மீண்டும் வரவும்"
            },
            "Kannada": {
                "greeting": "ನಮಸ್ಕಾರ",
                "prescription_header": "ಔಷಧಿ ಪಟ್ಟಿ",
                "take_medicine": "ಸೂಚಿಸಿದಂತೆ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ",
                "follow_up": "ಅಗತ್ಯವಿದ್ದರೆ ಮತ್ತೆ ಬನ್ನಿ"
            },
            "Hindi": {
                "greeting": "नमस्ते",
                "prescription_header": "दवा पर्ची",
                "take_medicine": "दवाइयां निर्देशानुसार लें",
                "follow_up": "जरूरत पड़ने पर फॉलो अप करें"
            }
        }
    
    def get_template(self, language: str, key: str) -> str:
        """Get template text in specified language"""
        return self.templates.get(language, self.templates["English"]).get(key, "")