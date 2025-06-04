import streamlit as st
import speech_recognition as sr
import tempfile
import os
import time

def create_voice_input_widget(key="voice_input", language="English"):
    """Simplified voice input using streamlit's audio_input"""
    
    languages = {
        "English": "en-IN",
        "Tamil": "ta-IN",
        "Kannada": "kn-IN",
        "Hindi": "hi-IN"
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_lang = st.selectbox(
            "Language",
            list(languages.keys()),
            key=f"{key}_lang"
        )
    
    with col2:
        st.write("🎤 Record your message")
    
    # Audio input
    audio_bytes = st.audio_input("Click to start recording", key=f"{key}_audio")
    
    if audio_bytes is not None:
        st.info("Processing audio... Please wait")
        
        try:
            # Save audio directly as WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes.getvalue())
                tmp_path = tmp_file.name
            
            # Initialize recognizer with adjusted settings
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300  # Lower threshold for better detection
            recognizer.pause_threshold = 0.8   # Faster response
            
            # Load and process audio
            with sr.AudioFile(tmp_path) as source:
                # Record with timeout
                audio_data = recognizer.record(source, duration=30)  # Max 30 seconds
            
            # Transcribe with timeout
            try:
                start_time = time.time()
                text = recognizer.recognize_google(
                    audio_data, 
                    language=languages[selected_lang],
                    show_all=False
                )
                
                # Success
                st.success("✅ Transcription complete!")
                st.write(f"**You said:** {text}")
                
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                
                return text
                
            except sr.UnknownValueError:
                st.error("❌ Could not understand the audio. Please try again with clearer speech.")
            except sr.RequestError as e:
                st.error(f"❌ Google Speech API error: {str(e)}")
                st.info("Tip: Check your internet connection")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Tip: Try recording a shorter message (under 30 seconds)")
        
        finally:
            # Always clean up
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    return None

# Alternative simple transcription function
def transcribe_audio_simple(audio_bytes, language="en-IN"):
    """Direct transcription without pydub conversion"""
    try:
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes.getvalue())
            audio_path = f.name
        
        # Transcribe
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        
        text = r.recognize_google(audio, language=language)
        
        # Cleanup
        os.unlink(audio_path)
        
        return text
    except Exception as e:
        return f"Error: {str(e)}"

# Dummy class to prevent import error
class MedicalSpeechRecognizer:
    pass