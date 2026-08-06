from pathlib import Path
import subprocess

# Paths
PIPER_EXE = Path("piper/piper.exe")
PIPER_MODEL = Path("models/en_US-amy-medium.onnx")

def is_hindi(text: str) -> bool:
    """Simple Hindi detection using Unicode range."""
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return True
    return False

def piper_tts(text: str, output_path: str = "audio/response.wav") -> str:
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

def text_to_speech(text: str, output_path: str = "audio/response.wav") -> str:
    # For now, both English and Hindi use the same Piper model.
    # Later we will replace the Hindi branch with IndicTTS.
    if is_hindi(text):
        return piper_tts(text, output_path)
    else:
        return piper_tts(text, output_path)

if __name__ == "__main__":
    path = text_to_speech("Hello Aman, welcome back.")
    print(path)