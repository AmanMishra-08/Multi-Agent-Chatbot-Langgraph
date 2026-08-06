from pathlib import Path
import subprocess
import os

# Local Piper paths (only used if files exist)
PIPER_EXE = Path("piper/piper.exe")
PIPER_MODEL = Path("models/en_US-amy-medium.onnx")

def is_hindi(text: str) -> bool:
    """Simple Hindi detection using Unicode range."""
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return True
    return False

def piper_tts(text: str, output_path: str = "audio/response.wav") -> str:
    """Local Piper TTS (Windows/Linux)"""
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
    """Fallback for Streamlit Cloud using gTTS"""
    from gtts import gTTS
    
    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    
    # Use Hindi for Hindi text, English for everything else
    lang = 'hi' if is_hindi(text) else 'en'
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(str(output_file))
    
    return str(output_file)

def text_to_speech(text: str, output_path: str = "audio/response.wav") -> str:
    """Main TTS: Uses Piper locally, falls back to gTTS on Cloud"""
    
    # Check if Piper executable exists (only true locally)
    if PIPER_EXE.exists() and PIPER_MODEL.exists():
        try:
            return piper_tts(text, output_path)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"⚠️ Piper failed: {e}. Using gTTS fallback...")
            return gtts_fallback(text, output_path)
    else:
        # Streamlit Cloud (no Piper binary) → use gTTS
        return gtts_fallback(text, output_path)

if __name__ == "__main__":
    path = text_to_speech("Hello Aman, welcome back.")
    print(path)