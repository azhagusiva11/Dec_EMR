"""
Test if the modular setup is working completely
"""

try:
    # Test all imports
    from api import (
        register_patient, get_all_patients, get_patient_data,
        save_consultation, update_patient_data, initialize_rare_disease_matrix,
        check_longitudinal_risks, extract_text_from_pdf, delete_patient_visit,
        get_cancer_screening_alerts, generate_referral_letter, save_clinician_feedback,
        get_feedback_stats, get_patient_analytics  # ADD THIS
    )
    
    print("✓ All imports successful!")
    
    # Test basic workflow
    # 1. Register patient (use different mobile to avoid duplicate)
    import random
    test_patient = {
        "name": "Test Patient",
        "age": 30,
        "sex": "male",
        "mobile": f"98765{random.randint(10000, 99999)}"  # Random mobile
    }
    
    result = register_patient(test_patient)
    print(f"✓ Patient registration: {result}")
    
    # 2. Initialize disease matrix
    matrix_result = initialize_rare_disease_matrix()
    print(f"✓ Disease matrix: {matrix_result}")
    
    # 3. Get analytics
    analytics = get_patient_analytics()
    print(f"✓ Analytics: Total patients = {analytics['total_patients']}")
    
    print("\n✅ All systems operational! Ready to update app.py")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()