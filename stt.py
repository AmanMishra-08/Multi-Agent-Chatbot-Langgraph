import whisper
from pathlib import Path

# Load the Whisper model once when the file is imported
# tiny is fast; later you can use base or small for better accuracy.
model = whisper.load_model("base")

def speech_to_text(audio_path: str) -> str:
    """
    Convert speech audio into text using Whisper.

    Args:
        audio_path: Path to a WAV audio file.

    Returns:
        Transcribed text.
    """

    audio_file = Path(audio_path)

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Reading: {audio_file.resolve()}")

    result = model.transcribe(str(audio_file),language="en")

    print("Whisper result:", result)
    

    return result["text"].strip()

if __name__ == "__main__":
    text = speech_to_text("audio/input.wav")
    print("Transcribed Text:", text)