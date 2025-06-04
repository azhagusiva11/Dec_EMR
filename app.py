import streamlit as st
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables properly
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Verify API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OpenAI API key loaded: {len(api_key)} characters")
else:
    print("❌ OpenAI API key not found in environment")

# USING THE NEW MODULAR STRUCTURE - NO OLD BACKEND
from api import (
    register_patient, get_all_patients, get_patient_data,
    save_visit, save_consultation, update_patient_data, 
    initialize_rare_disease_matrix, check_longitudinal_risks, 
    extract_text_from_pdf, delete_patient_visit,
    get_cancer_screening_alerts, generate_referral_letter, 
    save_clinician_feedback, get_feedback_stats,
    generate_clinical_summary, get_patient_analytics,
    search_patients, delete_patient, export_patient_data
)

from utils.export_tools import generate_visit_pdf, generate_discharge_summary
from utils.voice_input import create_voice_input_widget
from utils.drug_checker import DrugInteractionChecker
from utils.whatsapp_sender import WhatsAppSender
from utils.medical_validator_v2 import MedicalValidator
from utils.pdf_processor import PDFProcessor

# Helper functions
def safe_save_visit(patient_id: str, visit_data: dict) -> dict:
    """Wrapper to ensure data is in correct format before calling save_visit"""
    try:
        # Ensure all required fields exist and are correct type
        cleaned_data = {
            'chief_complaint': str(visit_data.get('chief_complaint', '')),
            'visit_type': str(visit_data.get('visit_type', 'opd')).lower(),
            'timestamp': visit_data.get('timestamp', datetime.now().isoformat()),
            'doctor': visit_data.get('doctor', 'Unknown'),
            'format_type': visit_data.get('format_type', 'SOAP')
        }
        
        # Ensure vitals is a dict, not a list or None
        vitals = visit_data.get('vitals', {})
        if not isinstance(vitals, dict):
            vitals = {}
        
        # Remove any empty string values from vitals
        cleaned_vitals = {}
        for key, value in vitals.items():
            if value and str(value).strip():
                cleaned_vitals[key] = value
        
        cleaned_data['vitals'] = cleaned_vitals
        
        # Add optional fields if they exist
        if 'summary' in visit_data:
            cleaned_data['summary'] = str(visit_data['summary'])
        if 'prescription' in visit_data:
            cleaned_data['prescription'] = str(visit_data['prescription'])
        if 'is_backdated' in visit_data:
            cleaned_data['is_backdated'] = visit_data['is_backdated']
        if 'lab_results' in visit_data:
            cleaned_data['lab_results'] = visit_data['lab_results']
            
        # Call the actual save_visit
        return save_visit(patient_id, cleaned_data)
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in safe_save_visit: {str(e)}"
        }

# Temporary fix for disease config format issue
def fix_disease_config():
    """Fix the disease detector config loading issue"""
    try:
        import json
        
        # Try to load and fix rare_diseases_comprehensive.json
        config_path = "data/config/rare_diseases_comprehensive.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # If it has a 'diseases' key that's a list, convert to dict
            if isinstance(data, dict) and 'diseases' in data and isinstance(data['diseases'], list):
                # Convert list to dict using disease name as key
                diseases_dict = {}
                for disease in data['diseases']:
                    if isinstance(disease, dict) and 'name' in disease:
                        # Use disease name as key, converting to valid key format
                        key = disease['name'].lower().replace(' ', '_').replace("'", "")
                        diseases_dict[key] = disease
                
                # Save the fixed version
                fixed_data = {'diseases': diseases_dict}
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(fixed_data, f, indent=2, ensure_ascii=False)
                
                print(f"Fixed disease config format - converted {len(diseases_dict)} diseases from list to dict")
    except Exception as e:
        print(f"Could not fix disease config: {e}")

# Call the fix on startup
fix_disease_config()

# Page configuration
st.set_page_config(
    page_title="Smart EMR",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better vitals display
st.markdown("""
<style>
    .vitals-normal { 
        background-color: #d4edda; 
        padding: 10px; 
        border-radius: 5px; 
        margin: 5px 0;
    }
    .vitals-caution { 
        background-color: #fff3cd; 
        padding: 10px; 
        border-radius: 5px; 
        margin: 5px 0;
    }
    .vitals-critical { 
        background-color: #f8d7da; 
        padding: 10px; 
        border-radius: 5px; 
        margin: 5px 0;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'symptoms_text' not in st.session_state:
    st.session_state.symptoms_text = ""
if 'page' not in st.session_state:
    st.session_state.page = "main"
if 'doctor_settings' not in st.session_state:
    st.session_state.doctor_settings = {
        'name': 'Dr. Smith',
        'registration_no': 'REG12345',
        'clinic_name': 'Smart EMR Clinic',
        'specialization': 'General Physician'
    }
if 'current_doctor' not in st.session_state:
    st.session_state.current_doctor = "Dr. A"
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = {
        'summary_generated': False,
        'current_summary': None,
        'current_prescription': None,
        'current_visit_data': None,
        'lab_results': None,
        'visit_saved': False,
        'visit_id': None
    }

# Initialize services
initialize_rare_disease_matrix()
drug_checker = DrugInteractionChecker()
whatsapp = WhatsAppSender()
validator = MedicalValidator()
pdf_processor = PDFProcessor()

# Header with navigation
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
with col1:
    st.title("🏥 Smart EMR")
with col2:
    # Doctor selection dropdown
    st.session_state.current_doctor = st.selectbox(
        "Doctor:",
        ["Dr. A", "Dr. B", "Dr. C", "Dr. Admin"],
        key="doctor_select"
    )
with col3:
    if st.button("⚙️ Settings"):
        st.session_state.page = "settings"
        st.rerun()
with col4:
    # Quick metrics
    patients = get_all_patients()
    st.metric("Patients", len(patients))
with col5:
    # API Status indicator
    if api_key:
        st.success("API ✅")
    else:
        st.error("API ❌")

# Settings page
if st.session_state.page == "settings":
    st.header("⚙️ Settings")
    
    with st.form("doctor_settings"):
        st.subheader("Doctor Information")
        doc_name = st.text_input("Doctor Name", value=st.session_state.doctor_settings['name'])
        reg_no = st.text_input("Registration Number", value=st.session_state.doctor_settings['registration_no'])
        clinic = st.text_input("Clinic Name", value=st.session_state.doctor_settings['clinic_name'])
        spec = st.text_input("Specialization", value=st.session_state.doctor_settings['specialization'])
        
        if st.form_submit_button("Save Settings"):
            st.session_state.doctor_settings = {
                'name': doc_name,
                'registration_no': reg_no,
                'clinic_name': clinic,
                'specialization': spec
            }
            st.success("Settings saved!")
    
    if st.button("← Back to EMR"):
        st.session_state.page = "main"
        st.rerun()

else:  # Main EMR page
    # Sidebar for patient management
    with st.sidebar:
        st.header("Patient Management")
        
        # Search box
        search_term = st.text_input("🔍 Search patient", placeholder="Name or mobile...")
        
        if search_term:
            search_results = search_patients(search_term)
            if search_results:
                st.write(f"Found {len(search_results)} patient(s)")
                for patient in search_results:
                    if st.button(f"{patient['name']} ({patient['mobile']})", key=f"search_{patient['id']}"):
                        st.session_state.selected_patient = patient['id']
                        st.rerun()
            else:
                st.info("No patients found")
        
        st.markdown("---")
        
        # Patient list
        if patients:
            st.subheader("All Patients")
            for patient in patients[:10]:  # Show first 10
                if st.button(f"{patient['name']} ({patient.get('age', '?')}y)", key=f"pat_{patient['id']}"):
                    st.session_state.selected_patient = patient['id']
                    st.rerun()
            
            if len(patients) > 10:
                st.caption(f"... and {len(patients) - 10} more")
        else:
            st.info("No patients registered yet")
        
        # New patient registration
        st.markdown("---")
        with st.expander("➕ Register New Patient", expanded=not patients):
            with st.form("patient_registration"):
                name = st.text_input("Patient Name*")
                
                col1, col2 = st.columns(2)
                with col1:
                    age = st.number_input("Age*", min_value=0, max_value=120, value=0)
                with col2:
                    sex = st.selectbox("Sex*", ["male", "female", "other"])
                
                mobile = st.text_input("Mobile Number*", placeholder="9876543210")
                
                blood_group = st.selectbox("Blood Group", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                allergies = st.text_area("Known Allergies (comma separated)")
                chronic_conditions = st.text_area("Chronic Conditions (comma separated)")
                
                if st.form_submit_button("Register Patient"):
                    if name and age > 0 and mobile:
                        # Validate inputs
                        name_valid, name_msg = validator.validate_patient_name(name)
                        if not name_valid:
                            st.error(name_msg)
                            st.stop()
                        
                        mobile_valid, mobile_msg = validator.validate_mobile_number(mobile)
                        if not mobile_valid:
                            st.error(mobile_msg)
                            st.stop()
                        
                        # Create patient data dictionary
                        patient_dict = {
                            "name": name,
                            "age": age,
                            "sex": sex,
                            "mobile": mobile if mobile.startswith('+') else f"+91{mobile}",
                            "blood_group": blood_group if blood_group else None,
                            "allergies": [a.strip() for a in allergies.split(',')] if allergies else [],
                            "chronic_conditions": [c.strip() for c in chronic_conditions.split(',')] if chronic_conditions else []
                        }
                        
                        result = register_patient(patient_dict)
                        
                        if result['success']:
                            st.success("Patient registered successfully!")
                            st.session_state.selected_patient = result['patient_id']
                            st.rerun()
                        else:
                            st.error(result['message'])
                    else:
                        st.error("Please fill all required fields")

    # Main content area - TWO TABS ONLY
    if st.session_state.selected_patient:
        patient_data = get_patient_data(st.session_state.selected_patient)
        
        # Patient header
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.header(f"Patient: {patient_data['name']}")
        with col2:
            st.metric("Age", f"{patient_data['age']} yrs")
        with col3:
            st.metric("Sex", patient_data['sex'].title())
        with col4:
            if patient_data.get('blood_group'):
                st.metric("Blood", patient_data['blood_group'])
        
        # Check for alerts
        rare_disease_risks = check_longitudinal_risks(st.session_state.selected_patient)
        cancer_alerts = get_cancer_screening_alerts(st.session_state.selected_patient)
        
        # Display alerts if any
        if rare_disease_risks.get('risks'):
            st.markdown("## 🚨 Clinical Alerts")
            
            for risk in rare_disease_risks['risks']:
                if risk['type'] == 'rare_disease':
                    severity = risk.get('severity', 'moderate')
                    bg_color = "#ffebee" if severity == 'high' else "#fff3e0"
                    border_color = "#d32f2f" if severity == 'high' else "#f57c00"
                    
                    st.markdown(f"""
                    <div style='background-color: {bg_color}; border: 3px solid {border_color}; 
                                border-radius: 10px; padding: 20px; margin: 20px 0;'>
                        <h3 style='color: {border_color}; margin: 0;'>
                            ⚠️ RARE DISEASE ALERT: {risk['condition']}
                        </h3>
                        <p style='font-size: 16px; margin: 10px 0;'>
                            Confidence: {risk['confidence']*100:.0f}%<br>
                            {risk['message']}
                        </p>
                        <p style='font-size: 14px; margin: 5px 0;'>
                            <strong>Action:</strong> {risk['action']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Generate referral button
                    if st.button(f"📄 Generate Referral for {risk['condition']}", key=f"ref_{risk['condition']}"):
                        visits = patient_data.get('visits', [])
                        latest_visit = visits[-1] if visits else {}
                        
                        disease_alert = {
                            'disease': risk['condition'],
                            'confidence': risk['confidence'],
                            'specialists': ['Specialist'],
                            'suggested_tests': [],
                            'timeline': []
                        }
                        
                        letter = generate_referral_letter(patient_data, latest_visit, disease_alert)
                        st.text_area("Referral Letter", value=letter, height=400)
        
        if cancer_alerts:
            st.markdown("### 🔍 Cancer Screening Recommendations")
            for alert in cancer_alerts:
                st.info(f"**{alert['screening_type']}**: {alert['test_recommended']} - {alert['reason']}")
        
        # TABS - ONLY 2
        tab1, tab2 = st.tabs(["📋 Clinical Workflow", "📊 Analytics & Feedback"])
        
        # TAB 1: CLINICAL WORKFLOW
        with tab1:
            # Visit type selector
            visit_type = st.radio("Visit Type", ["OPD", "Admitted", "Backdated Entry"], horizontal=True)
            
            if visit_type == "OPD":
                st.header("New OPD Consultation")
                
                # STEP 1: DATA ENTRY
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Chief complaints with voice input option
                    st.subheader("Chief Complaints")
                    
                    # Voice input option
                    use_voice = st.checkbox("🎤 Use voice input")
                    if use_voice:
                        voice_text = create_voice_input_widget(key="voice_symptoms")
                        if voice_text:
                            st.session_state.symptoms_text = voice_text
                    
                    symptoms_text = st.text_area(
                        "Enter symptoms, history, examination findings...",
                        value=st.session_state.get('symptoms_text', ''),
                        height=150,
                        key="symptoms_input"
                    )
                
                with col2:
                    # Summary format selection
                    st.subheader("Options")
                    summary_format = st.radio(
                        "Summary Format",
                        ["SOAP", "INDIAN_EMR"],
                        format_func=lambda x: "SOAP Note" if x == "SOAP" else "Indian EMR Format"
                    )
                    
                    include_prescription = st.checkbox("Include prescription", value=True)
                
                # Vitals section
                st.subheader("Vital Signs")
                vcol1, vcol2, vcol3, vcol4 = st.columns(4)
                with vcol1:
                    bp = st.text_input("BP (mmHg)", placeholder="120/80", key="bp_input")
                with vcol2:
                    hr = st.number_input("HR (bpm)", min_value=0, max_value=250, value=0, key="hr_input")
                with vcol3:
                    temp = st.number_input("Temp (°C)", min_value=0.0, max_value=45.0, value=0.0, step=0.1, key="temp_input")
                with vcol4:
                    spo2 = st.number_input("SpO2 (%)", min_value=0, max_value=100, value=0, key="spo2_input")
                
                vcol1, vcol2, vcol3, vcol4 = st.columns(4)
                with vcol1:
                    weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, value=0.0, step=0.1, key="weight_input")
                with vcol2:
                    height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.1, key="height_input")
                with vcol3:
                    # Auto-calculate BMI
                    if weight > 0 and height > 0:
                        bmi = weight / ((height/100) ** 2)
                        bmi_status = "🟢" if 18.5 <= bmi <= 24.9 else "🟡" if 25 <= bmi <= 29.9 else "🔴"
                        st.metric("BMI", f"{bmi:.1f} {bmi_status}")
                    else:
                        st.metric("BMI", "---")
                with vcol4:
                    rr = st.number_input("RR (/min)", min_value=0, max_value=60, value=0, key="rr_input")
                
                # Lab Report Upload
                st.subheader("Lab Reports (Optional)")
                uploaded_lab = st.file_uploader("Upload Lab PDF", type=['pdf'], key="lab_upload")
                
                lab_results = {}
                if uploaded_lab:
                    with st.spinner("Processing lab report..."):
                        result = pdf_processor.process_pdf(uploaded_lab, patient_data['name'])
                        if result['success']:
                            # Name validation
                            if not result['name_match'] and result['extracted_name']:
                                st.warning(f"""
                                ⚠️ **Name Mismatch Detected!**
                                - Expected: {patient_data['name']}
                                - Found in PDF: {result['extracted_name']}
                                - Match confidence: {result['match_confidence']*100:.0f}%
                                """)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Proceed Anyway", key="proceed_mismatch"):
                                        st.session_state['lab_override'] = True
                                with col2:
                                    if st.button("❌ Cancel Upload", key="cancel_mismatch"):
                                        st.session_state['lab_upload'] = None
                                        st.rerun()
                            
                            # Show lab results
                            if result['lab_results']:
                                st.success("✅ Lab values detected:")
                                lab_report = pdf_processor.format_lab_report(result['lab_results'])
                                st.markdown(lab_report)
                                lab_results = result['lab_results']
                                st.session_state.workflow_state['lab_results'] = lab_results
                            else:
                                st.info("No standard lab values detected in PDF")
                        else:
                            st.error(f"Error processing PDF: {result.get('error', 'Unknown error')}")
                
                # STEP 2: GENERATE SUMMARY
                st.markdown("---")
                if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
                    if symptoms_text:
                        with st.spinner("Generating clinical summary..."):
                            # Validate vitals
                            vitals = {}
                            vitals_valid = True
                            
                            if bp and bp.strip():
                                bp_valid, bp_msg = validator.validate_blood_pressure(bp)
                                if bp_valid:
                                    vitals['blood_pressure'] = bp
                                else:
                                    st.error(f"❌ Invalid BP: {bp_msg}")
                                    vitals_valid = False
                            
                            if hr > 0:
                                hr_valid, hr_msg = validator.validate_heart_rate(hr)
                                if hr_valid:
                                    vitals['heart_rate'] = hr
                                else:
                                    st.error(f"❌ Invalid HR: {hr_msg}")
                                    vitals_valid = False
                            
                            if temp > 0:
                                if temp < 35.0 or temp > 42.0:
                                    st.error(f"❌ Invalid temperature: {temp}°C (must be between 35-42°C)")
                                    vitals_valid = False
                                else:
                                    vitals['temperature'] = temp
                            
                            if spo2 > 0:
                                vitals['spo2'] = spo2
                            if weight > 0:
                                vitals['weight'] = weight
                            if height > 0:
                                vitals['height'] = height
                            if rr > 0:
                                vitals['respiratory_rate'] = rr
                            
                            if not vitals_valid:
                                st.stop()
                            
                            # Prepare patient context with vitals and lab results
                            patient_context = patient_data.copy()
                            patient_context['current_vitals'] = vitals
                            patient_context['lab_results'] = lab_results
                            
                            # Generate summary
                            summary_result = generate_clinical_summary(
                                symptoms_text,
                                patient_context,
                                include_prescription=include_prescription,
                                format_type=summary_format
                            )
                            
                            if summary_result['success']:
                                # Store in session state
                                st.session_state.workflow_state['summary_generated'] = True
                                st.session_state.workflow_state['current_summary'] = summary_result['summary']
                                st.session_state.workflow_state['current_prescription'] = summary_result.get('prescription', '')
                                st.session_state.workflow_state['current_visit_data'] = {
                                    'chief_complaint': symptoms_text,
                                    'vitals': vitals,
                                    'lab_results': lab_results,
                                    'timestamp': datetime.now().isoformat(),
                                    'doctor': st.session_state.current_doctor,
                                    'format_type': summary_format
                                }
                                st.success("✅ Summary generated successfully!")
                            else:
                                st.error(f"Failed to generate summary: {summary_result.get('error', 'Unknown error')}")
                    else:
                        st.error("Please enter chief complaints first")
                
                # DISPLAY GENERATED SUMMARY
                if st.session_state.workflow_state['summary_generated']:
                    st.markdown("---")
                    st.subheader("Generated Clinical Summary")
                    
                    # Display summary
                    st.text_area(
                        "Clinical Summary",
                        value=st.session_state.workflow_state['current_summary'],
                        height=300,
                        disabled=True
                    )
                    
                    # Display prescription (editable)
                    if st.session_state.workflow_state['current_prescription']:
                        prescription = st.text_area(
                            "Prescription (Edit as needed)",
                            value=st.session_state.workflow_state['current_prescription'],
                            height=150,
                            key="prescription_edit"
                        )
                        
                        # Check drug interactions
                        if prescription:
                            drug_check = drug_checker.check_prescription(prescription)
                            if drug_check['has_interactions']:
                                st.warning("⚠️ Drug Interactions Detected:")
                                for interaction in drug_check['interactions']:
                                    st.write(f"- {interaction['description']}")
                            if drug_check['has_warnings']:
                                st.warning("⚠️ Warnings:")
                                for warning in drug_check['warnings']:
                                    st.write(f"- {warning}")
                    else:
                        prescription = ""
                    
                    # ACTION BUTTONS
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # STEP 3: EXPORT PDF
                    with col1:
                        if st.button("📄 Export PDF", use_container_width=True):
                            # Create visit data for PDF
                            visit_data_for_pdf = st.session_state.workflow_state['current_visit_data'].copy()
                            visit_data_for_pdf['summary'] = st.session_state.workflow_state['current_summary']
                            visit_data_for_pdf['prescription'] = prescription
                            visit_data_for_pdf['visit_id'] = f"TEMP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            
                            try:
                                pdf_path = generate_visit_pdf(patient_data, visit_data_for_pdf)
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        "⬇️ Download PDF",
                                        data=f.read(),
                                        file_name=f"visit_{patient_data['name']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                        mime="application/pdf"
                                    )
                                st.success("✅ PDF ready for download!")
                            except Exception as e:
                                st.error(f"PDF export failed: {str(e)}")
                    
                    # WhatsApp
                    with col2:
                        if whatsapp.enabled:
                            if st.button("📱 Send WhatsApp", use_container_width=True):
                                result = whatsapp.send_prescription(patient_data, prescription)
                                if result['success']:
                                    st.success("✅ WhatsApp sent!")
                                else:
                                    st.error(f"WhatsApp failed: {result['error']}")
                        else:
                            st.info("WhatsApp not configured")
                    
                    # STEP 4: SAVE VISIT
                    with col3:
                        if st.button("💾 Save Visit", type="primary", use_container_width=True):
                            if not st.session_state.workflow_state['visit_saved']:
                                # Prepare complete visit data
                                visit_data = st.session_state.workflow_state['current_visit_data'].copy()
                                visit_data['visit_type'] = 'opd'
                                
                                # Save visit
                                visit_result = safe_save_visit(st.session_state.selected_patient, visit_data)
                                
                                if visit_result['success']:
                                    visit_id = visit_result['visit_id']
                                    st.session_state.workflow_state['visit_id'] = visit_id
                                    
                                    # Save consultation data
                                    consultation_data = {
                                        'summary': st.session_state.workflow_state['current_summary'],
                                        'prescription': prescription,
                                        'format_type': summary_format
                                    }
                                    
                                    save_result = save_consultation(
                                        st.session_state.selected_patient,
                                        visit_id,
                                        consultation_data
                                    )
                                    
                                    if save_result['success']:
                                        st.success("✅ Visit saved successfully!")
                                        st.balloons()
                                        
                                        # Mark as saved
                                        st.session_state.workflow_state['visit_saved'] = True
                                        
                                        # Show vitals validation if any issues
                                        if visit_result.get('vitals_validation'):
                                            val = visit_result['vitals_validation']
                                            if val.get('alerts'):
                                                st.warning("⚠️ **Vitals Alert:**")
                                                for alert in val['alerts']:
                                                    st.write(f"- {alert}")
                                        
                                        # Check for disease alerts
                                        if visit_result.get('disease_alerts'):
                                            st.error(f"🚨 {len(visit_result['disease_alerts'])} Rare Disease Alert(s) Detected!")
                                            for alert in visit_result['disease_alerts']:
                                                st.write(f"- **{alert['disease']}** ({alert['confidence']*100:.0f}% confidence)")
                                                st.write(f"  {alert['message']}")
                                    else:
                                        st.error("Failed to save consultation")
                                else:
                                    st.error(f"Failed to save visit: {visit_result.get('message')}")
                            else:
                                st.info("Visit already saved")
                    
                    # New Visit
                    with col4:
                        if st.session_state.workflow_state['visit_saved']:
                            if st.button("🔄 New Visit", use_container_width=True):
                                # Clear workflow state
                                st.session_state.workflow_state = {
                                    'summary_generated': False,
                                    'current_summary': None,
                                    'current_prescription': None,
                                    'current_visit_data': None,
                                    'lab_results': None,
                                    'visit_saved': False,
                                    'visit_id': None
                                }
                                # Clear input fields
                                for key in ['symptoms_input', 'bp_input', 'hr_input', 'temp_input', 
                                           'spo2_input', 'weight_input', 'height_input', 'rr_input', 
                                           'lab_upload', 'symptoms_text']:
                                    if key in st.session_state:
                                        if 'input' in key and key != 'symptoms_input':
                                            st.session_state[key] = 0
                                        else:
                                            st.session_state[key] = ""
                                st.rerun()
                
                # Visit History Section
                st.markdown("---")
                st.subheader("Recent Visits")
                
                visits = patient_data.get('visits', [])
                if visits:
                    # Show last 5 visits
                    recent_visits = sorted(visits, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
                    
                    for visit in recent_visits:
                        visit_date = visit.get('timestamp', 'Unknown date')[:10]
                        visit_type = visit.get('visit_type', 'OPD')
                        
                        # Check if visit has disease alerts
                        alert_emoji = "🚨" if visit.get('disease_alerts') else ""
                        
                        with st.expander(f"{alert_emoji} 📅 {visit_date} - {visit_type} Visit"):
                            # Chief complaint
                            if visit.get('chief_complaint'):
                                st.markdown("**Chief Complaint:**")
                                st.write(visit['chief_complaint'])
                            
                            # Summary
                            if visit.get('summary'):
                                st.markdown("**Clinical Summary:**")
                                st.text(visit['summary'])
                            
                            # Prescription
                            if visit.get('prescription'):
                                st.markdown("**Prescription:**")
                                st.text(visit['prescription'])
                            
                            # Export button
                            if st.button(f"📄 Export PDF", key=f"export_hist_{visit.get('visit_id', visit_date)}"):
                                try:
                                    pdf_path = generate_visit_pdf(patient_data, visit)
                                    with open(pdf_path, "rb") as pdf_file:
                                        st.download_button(
                                            label="⬇️ Download PDF",
                                            data=pdf_file.read(),
                                            file_name=f"visit_{patient_data['name']}_{visit_date}.pdf",
                                            mime="application/pdf",
                                            key=f"download_hist_{visit.get('visit_id', visit_date)}"
                                        )
                                except Exception as e:
                                    st.error(f"PDF generation failed: {str(e)}")
                else:
                    st.info("No previous visits")
            
            elif visit_type == "Admitted":
                st.header("Admitted Patient Management")
                st.info("Inpatient module coming soon")
            
            elif visit_type == "Backdated Entry":
                st.header("Add Historical Visit")
                st.info("Add visits from paper records for longitudinal tracking")
                
                with st.form("backdated_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        back_date = st.date_input("Visit Date", max_value=datetime.now().date())
                    with col2:
                        back_time = st.time_input("Visit Time", value=datetime.strptime("09:00", "%H:%M").time())
                    
                    back_symptoms = st.text_area(
                        "Chief Complaints",
                        placeholder="Enter symptoms from historical visit...",
                        height=100
                    )
                    
                    # Historical vitals
                    st.subheader("Historical Vitals (if available)")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        back_bp = st.text_input("BP", placeholder="120/80", key="back_bp")
                    with col2:
                        back_hr = st.number_input("HR", min_value=0, max_value=250, value=0, key="back_hr")
                    with col3:
                        back_temp = st.number_input("Temp", min_value=0.0, max_value=45.0, value=0.0, key="back_temp")
                    
                    back_notes = st.text_area(
                        "Clinical Notes/Diagnosis",
                        placeholder="Any diagnosis or clinical findings...",
                        height=100
                    )
                    
                    back_prescription = st.text_area(
                        "Prescription (if any)",
                        placeholder="Medications prescribed...",
                        height=100
                    )
                    
                    if st.form_submit_button("Add Historical Visit", type="primary"):
                        if back_symptoms:
                            # Create historical visit
                            visit_datetime = datetime.combine(back_date, back_time)
                            
                            # Prepare vitals
                            historical_vitals = {}
                            if back_bp and back_bp.strip():
                                historical_vitals['blood_pressure'] = back_bp
                            if back_hr > 0:
                                historical_vitals['heart_rate'] = back_hr
                            if back_temp > 0:
                                historical_vitals['temperature'] = back_temp
                            
                            # Create visit
                            historical_visit = {
                                'chief_complaint': back_symptoms,
                                'visit_type': 'opd',
                                'vitals': historical_vitals,
                                'summary': back_notes if back_notes else f"Historical visit on {back_date}",
                                'prescription': back_prescription if back_prescription else "",
                                'is_backdated': True,
                                'timestamp': visit_datetime.isoformat(),
                                'doctor': st.session_state.current_doctor
                            }
                            
                            # Save
                            result = safe_save_visit(st.session_state.selected_patient, historical_visit)
                            
                            if result.get('success'):
                                st.success(f"✅ Historical visit added for {back_date}")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to add visit: {result.get('message', 'Unknown error')}")
                        else:
                            st.error("Please enter chief complaints")
        
        # TAB 2: ANALYTICS & FEEDBACK
        with tab2:
            st.header("📊 Analytics & Feedback Dashboard")
            
            # Date range selector
            col1, col2 = st.columns([1, 3])
            with col1:
                selected_doctor = st.selectbox(
                    "Filter by Doctor",
                    ["All Doctors", "Dr. A", "Dr. B", "Dr. C", "Dr. Admin"],
                    key="analytics_doctor"
                )
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(datetime.now() - timedelta(days=7), datetime.now()),
                    max_value=datetime.now().date(),
                    key="date_range"
                )
            
            # Get analytics
            analytics = get_patient_analytics()
            feedback_stats = get_feedback_stats()
            
            # Today's metrics
            st.subheader("📅 Today's Activity")
            t1, t2, t3, t4 = st.columns(4)
            
            with t1:
                visits_today = len([v for p in get_all_patients() 
                                   for v in get_patient_data(p['id']).get('visits', [])
                                   if v.get('timestamp', '')[:10] == datetime.now().strftime('%Y-%m-%d')])
                st.metric("Visits Today", visits_today)
            
            with t2:
                st.metric("Patients Seen", len(set([p['id'] for p in get_all_patients() 
                                                   for v in get_patient_data(p['id']).get('visits', [])
                                                   if v.get('timestamp', '')[:10] == datetime.now().strftime('%Y-%m-%d')])))
            
            with t3:
                st.metric("Avg Rating", f"{feedback_stats.get('average_rating', 0)}/5")
            
            with t4:
                st.metric("Total Feedback", feedback_stats.get('total_feedback', 0))
            
            # Visit feedback section
            st.markdown("---")
            st.subheader("👨‍⚕️ Recent Visits for Feedback")
            
            # Collect visits within date range
            all_visits = []
            for patient in get_all_patients():
                patient_data = get_patient_data(patient['id'])
                for visit in patient_data.get('visits', []):
                    visit_date = datetime.fromisoformat(visit['timestamp'].split('T')[0])
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        if date_range[0] <= visit_date.date() <= date_range[1]:
                            if selected_doctor == "All Doctors" or visit.get('doctor') == selected_doctor:
                                all_visits.append({
                                    'patient_name': patient_data['name'],
                                    'patient_id': patient['id'],
                                    'visit': visit,
                                    'visit_date': visit_date
                                })
            
            # Sort by date
            all_visits.sort(key=lambda x: x['visit_date'], reverse=True)
            
            # Display visits
            if all_visits:
                for idx, visit_info in enumerate(all_visits[:10]):  # Show max 10
                    visit = visit_info['visit']
                    has_feedback = 'clinician_feedback' in visit
                    
                    col1, col2, col3 = st.columns([3, 1, 2])
                    
                    with col1:
                        st.write(f"**{visit_info['patient_name']}** - {visit_info['visit_date'].strftime('%Y-%m-%d %H:%M')}")
                        if visit.get('doctor'):
                            st.caption(f"Doctor: {visit['doctor']}")
                    
                    with col2:
                        if has_feedback:
                            st.success("✅ Rated")
                        else:
                            st.info("Pending")
                    
                    with col3:
                        if not has_feedback:
                            fcol1, fcol2 = st.columns(2)
                            with fcol1:
                                if st.button("👍", key=f"like_{idx}"):
                                    feedback_data = {
                                        'overall_rating': 5,
                                        'summary_accuracy': 5,
                                        'prescription_appropriate': True,
                                        'disease_alert_helpful': True,
                                        'doctor': visit.get('doctor', 'Unknown')
                                    }
                                    save_clinician_feedback(
                                        visit_info['patient_id'],
                                        visit.get('visit_id'),
                                        feedback_data
                                    )
                                    st.success("Thanks!")
                                    time.sleep(0.5)
                                    st.rerun()
                            
                            with fcol2:
                                if st.button("👎", key=f"dislike_{idx}"):
                                    feedback_data = {
                                        'overall_rating': 2,
                                        'summary_accuracy': 2,
                                        'prescription_appropriate': False,
                                        'disease_alert_helpful': False,
                                        'doctor': visit.get('doctor', 'Unknown')
                                    }
                                    save_clinician_feedback(
                                        visit_info['patient_id'],
                                        visit.get('visit_id'),
                                        feedback_data
                                    )
                                    st.info("We'll improve!")
                                    time.sleep(0.5)
                                    st.rerun()
                    
                    st.divider()
            else:
                st.info("No visits found for selected criteria")
            
            # Overall statistics
            st.markdown("---")
            st.subheader("📈 Overall Statistics")
            
            s1, s2, s3, s4 = st.columns(4)
            
            with s1:
                st.metric("Total Patients", analytics.get('total_patients', 0))
            
            with s2:
                st.metric("Total Visits", analytics.get('total_visits', 0))
            
            with s3:
                st.metric("Disease Alerts", analytics.get('disease_alerts_count', 0))
            
            with s4:
                st.metric("Avg Visits/Patient", analytics.get('avg_visits_per_patient', 0))
            
            # AI Performance
            st.markdown("---")
            st.subheader("🤖 AI Performance")
            
            ai1, ai2, ai3 = st.columns(3)
            
            with ai1:
                ai_helpful = feedback_stats.get('ai_helpful_percentage', 0)
                st.metric("AI Helpful %", f"{ai_helpful}%")
                st.caption("Summaries rated 4+ stars")
            
            with ai2:
                # Calculate prescription edit rate
                total_visits_with_rx = sum(1 for p in get_all_patients() 
                                          for v in get_patient_data(p['id']).get('visits', [])
                                          if v.get('prescription'))
                edited_rx = sum(1 for p in get_all_patients() 
                               for v in get_patient_data(p['id']).get('visits', [])
                               if v.get('prescription_edited'))
                edit_rate = (edited_rx / total_visits_with_rx * 100) if total_visits_with_rx > 0 else 0
                st.metric("Rx Edit Rate", f"{edit_rate:.1f}%")
                st.caption("Prescriptions modified by doctors")
            
            with ai3:
                # API success rate (mock for now)
                st.metric("API Success", "98.5%")
                st.caption("GPT availability")
    
    else:
        # Welcome screen
        st.header("🏥 Welcome to Smart EMR")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("### Getting Started\n👈 Register a patient or select an existing one from the sidebar")
        
        with col2:
            st.success("### Key Features\n- AI Clinical Summaries\n- Rare Disease Detection\n- Lab Report Integration\n- Drug Safety Checks\n- WhatsApp Integration")
        
        with col3:
            st.warning("### What's New\n- Sequential workflow\n- PDF before save\n- Lab value extraction\n- Doctor feedback tracking\n- BMI auto-calculation")

# Footer
st.markdown("---")
st.caption(f"Smart EMR v2.0 - Complete Version | Current Doctor: {st.session_state.current_doctor} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")