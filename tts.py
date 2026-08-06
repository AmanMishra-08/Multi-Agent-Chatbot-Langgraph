from pathlib import Path
import subprocess
import os

# Local Piper paths (only used locally)
PIPER_EXE = Path("piper/piper.exe")
PIPER_MODEL = Path("models/en_US-amy-medium.onnx")

def is_hindi(text: str) -> bool:
    """Simple Hindi detection using Unicode range."""
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return True
    return False

def is_streamlit_cloud() -> bool:
    """Check if running on Streamlit Cloud"""
    return "STREAMLIT_CLOUD" in os.environ

def piper_tts(text: str, output_path: str = "audio/response.wav") -> str:
    """Local Piper TTS - ENGLISH ONLY (Windows/Linux)"""
    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)

    subprocess.run(
        [
            str(PIPER_EXE),
            "--model",
            str(PIPER_MODEL),
            "--output_file",
            str(output_file),
        ],
        input=text.encode("utf-8"),
        check=True,
    )

    return str(output_file)

def gtts_fallback(text: str, output_path: str = "audio/response.wav") -> str:
    """gTTS for Hindi or Cloud"""
    from gtts import gTTS
    
    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    
    lang = 'hi' if is_hindi(text) else 'en'
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(str(output_file))
    
    return str(output_file)

def text_to_speech(text: str, output_path: str = "audio/response.wav") -> str:
    """
    Main TTS function:
    - Cloud: Always use gTTS (English + Hindi)
    - Locally:
      - English: Use Piper (fast, offline)
      - Hindi: Use gTTS (no IndicTTS yet)
    """
    
    # ON STREAMLIT CLOUD: Always use gTTS for everything
    if is_streamlit_cloud():
        print("🌐 Using gTTS (Cloud)")
        return gtts_fallback(text, output_path)
    
    # LOCALLY:
    if is_hindi(text):
        # Hindi: Use gTTS (for now)
        print("🇮🇳 Hindi detected - Using gTTS")
        return gtts_fallback(text, output_path)
    else:
        # English: Try Piper, fallback to gTTS if it fails
        try:
            print("🇬🇧 English detected - Using Piper")
            return piper_tts(text, output_path)
        except Exception as e:
            print(f"⚠️ Piper failed: {e}. Falling back to gTTS...")
            return gtts_fallback(text, output_path)

if __name__ == "__main__":
    path = text_to_speech("Hello Aman, welcome back.")
    print(path)