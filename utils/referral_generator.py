"""
Professional Referral Letter Generator for Smart EMR
Generates PDF referral letters for rare disease cases
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os

def generate_referral_letter_pdf(patient_data, disease_info, doctor_info, referring_to="Specialist", urgency="Soon"):
    """
    Generate a professional referral letter PDF for rare disease cases
    
    Args:
        patient_data: Dict with patient demographics
        disease_info: Dict with disease detection details
        doctor_info: Dict with referring doctor's details
        referring_to: Specialist type or hospital name
        urgency: Routine/Soon/Urgent
    
    Returns:
        str: Path to generated PDF file
    """
    
    # Create filename
    safe_disease_name = disease_info['disease'].replace(' ', '_').replace("'", "")
    filename = f"exports/referral_{patient_data['id']}_{safe_disease_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Ensure exports directory exists
    os.makedirs("exports", exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    subheader_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    # Add clinic letterhead if available
    if doctor_info.get('clinic_name'):
        letterhead = Paragraph(f"<b>{doctor_info['clinic_name']}</b>", 
                             ParagraphStyle('Letterhead', 
                                          parent=styles['Normal'],
                                          fontSize=16,
                                          alignment=TA_CENTER,
                                          textColor=colors.HexColor('#1f4788')))
        elements.append(letterhead)
        elements.append(Spacer(1, 0.2*inch))
    
    # Title
    elements.append(Paragraph("MEDICAL REFERRAL LETTER", title_style))
    
    # Urgency indicator
    urgency_colors = {
        "Routine": colors.green,
        "Soon": colors.orange,
        "Urgent": colors.red
    }
    urgency_table = Table([[f"URGENCY: {urgency.upper()}"]], 
                         colWidths=[2*inch])
    urgency_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), urgency_colors.get(urgency, colors.orange)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(urgency_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Date and reference
    date_ref_data = [
        ['Date:', datetime.now().strftime('%d %B %Y')],
        ['Ref No:', f"REF/{patient_data['id']}/{datetime.now().strftime('%Y%m%d')}"],
        ['From:', f"{doctor_info.get('name', 'Doctor')} ({doctor_info.get('registration_no', 'Reg. No.')})"]
    ]
    
    date_ref_table = Table(date_ref_data, colWidths=[1.5*inch, 4.5*inch])
    date_ref_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(date_ref_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # To section
    elements.append(Paragraph(f"<b>To:</b> {referring_to}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Patient details section
    elements.append(Paragraph("PATIENT DETAILS", header_style))
    
    # Create patient info table
    patient_info_data = [
        ['Name:', patient_data['name'], 'Age/Sex:', f"{patient_data['age']} years / {patient_data['sex']}"],
        ['Mobile:', patient_data['mobile'], 'Patient ID:', patient_data['id']],
        ['Height/Weight:', f"{patient_data.get('height', 'N/A')} cm / {patient_data.get('initial_vitals', {}).get('weight', 'N/A')} kg", 
         'Ethnicity:', patient_data.get('ethnicity', 'Not specified')]
    ]
    
    if patient_data.get('address'):
        patient_info_data.append(['Address:', patient_data['address'], '', ''])
    
    patient_table = Table(patient_info_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Clinical Alert Section
    elements.append(Paragraph("CLINICAL ALERT - RARE DISEASE SUSPECTED", header_style))
    
    # Alert details table
    alert_data = [
        ['Suspected Condition:', disease_info['disease']],
        ['ICD-10 Code:', disease_info.get('icd10', 'Pending classification')],
        ['Confidence Level:', f"{disease_info.get('confidence_score', 0.8)*100:.0f}%"],
        ['Detection Date:', datetime.now().strftime('%d-%m-%Y')],
        ['Pattern Detected:', f"{disease_info['total_matches']} symptoms over {disease_info['days_span']} days"]
    ]
    
    alert_table = Table(alert_data, colWidths=[2*inch, 4.5*inch])
    alert_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#856404')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#856404')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(alert_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Symptom Timeline
    elements.append(Paragraph("Symptom Timeline & Clinical Presentation", subheader_style))
    
    # Create timeline table
    timeline_data = [['Date', 'Symptom', 'Category', 'Visit ID']]
    for symptom in disease_info['matched_symptoms']:
        timeline_data.append([
            symptom['date'],
            symptom['symptom'].replace('_', ' ').title(),
            symptom.get('category', 'General').title(),
            symptom['visit_id']
        ])
    
    timeline_table = Table(timeline_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch, 1.3*inch])
    timeline_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(timeline_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Recommended Tests
    elements.append(Paragraph("Recommended Diagnostic Tests", subheader_style))
    
    tests_text = ""
    for idx, test in enumerate(disease_info.get('diagnostic_tests', [])[:8], 1):
        tests_text += f"{idx}. {test}<br/>"
    
    elements.append(Paragraph(tests_text, normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Clinical significance
    elements.append(Paragraph("Clinical Significance", subheader_style))
    significance = disease_info.get('clinical_significance', 
                                  f"Early detection and treatment of {disease_info['disease']} is crucial for optimal patient outcomes.")
    elements.append(Paragraph(significance, normal_style))
    elements.append(Spacer(1, 0.4*inch))
    
    # Reason for referral
    elements.append(Paragraph("Reason for Referral", subheader_style))
    
    referral_text = f"""
    This patient presents with a constellation of clinical features that our AI-assisted longitudinal tracking system 
    has identified as highly suggestive of {disease_info['disease']}. The pattern recognition algorithm detected 
    {disease_info['total_matches']} characteristic symptoms occurring over a {disease_info['days_span']}-day period, 
    which meets the diagnostic criteria for suspected {disease_info['disease']}.
    <br/><br/>
    Given the complexity and rarity of this condition, specialist evaluation is warranted for:
    <br/>
    • Confirmatory diagnostic testing as outlined above<br/>
    • Genetic counseling if applicable<br/>
    • Development of a specialized treatment plan<br/>
    • Long-term management and monitoring strategy<br/>
    • Family screening recommendations if hereditary component suspected
    """
    
    elements.append(Paragraph(referral_text, normal_style))
    elements.append(Spacer(1, 0.4*inch))
    
    # Additional notes
    if patient_data.get('allergies'):
        elements.append(Paragraph("Known Allergies", subheader_style))
        elements.append(Paragraph(patient_data['allergies'], normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    if patient_data.get('medical_history'):
        elements.append(Paragraph("Relevant Medical History", subheader_style))
        elements.append(Paragraph(patient_data['medical_history'], normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Closing
    elements.append(Spacer(1, 0.5*inch))
    closing_text = """
    I would be grateful if you could see this patient at your earliest convenience. 
    Please feel free to contact me if you require any additional clinical information or clarification.
    <br/><br/>
    Thank you for your assistance in managing this complex case.
    """
    elements.append(Paragraph(closing_text, normal_style))
    
    # Signature section
    elements.append(Spacer(1, 0.8*inch))
    
    signature_data = [
        ['Yours sincerely,'],
        [''],
        [''],
        [f"{doctor_info.get('name', 'Doctor')}"],
        [f"Registration No: {doctor_info.get('registration_no', 'N/A')}"],
        [f"{doctor_info.get('clinic_name', 'Smart EMR Clinic')}"],
        [f"Date: {datetime.now().strftime('%d/%m/%Y')}"]
    ]
    
    signature_table = Table(signature_data, colWidths=[4*inch])
    signature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(signature_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    footer_text = """
    <i>This referral letter was generated using Smart EMR - AI-assisted clinical decision support system.<br/>
    The rare disease detection is based on longitudinal symptom tracking and pattern recognition algorithms.<br/>
    For queries about this system, contact: support@smartemr.in</i>
    """
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(elements)
    
    return filename


def generate_simple_referral(patient_name: str, disease: str, doctor_name: str, 
                           symptoms: list, tests: list) -> str:
    """
    Generate a simple text referral letter
    
    Args:
        patient_name: Patient's name
        disease: Suspected disease
        doctor_name: Referring doctor's name
        symptoms: List of symptoms
        tests: List of recommended tests
    
    Returns:
        str: Formatted referral letter text
    """
    
    letter = f"""
{datetime.now().strftime('%d %B %Y')}

MEDICAL REFERRAL LETTER

Dear Colleague,

Re: {patient_name}

I am referring the above patient for specialist evaluation regarding suspected {disease}.

CLINICAL PRESENTATION:
The patient has presented with the following symptoms:
"""
    
    for symptom in symptoms:
        letter += f"\n• {symptom}"
    
    letter += f"""

RECOMMENDED INVESTIGATIONS:
"""
    
    for idx, test in enumerate(tests, 1):
        letter += f"\n{idx}. {test}"
    
    letter += f"""

I would be grateful if you could see this patient at your earliest convenience.

Yours sincerely,

{doctor_name}
{datetime.now().strftime('%d/%m/%Y')}

Generated by Smart EMR - AI-assisted clinical decision support
"""
    
    return letter