import pyttsx3
import os

# Initialize TTS engine once at startup (uses system voices; no downloads needed)
engine = pyttsx3.init()

# Optional: Customize voice properties (uncomment and adjust as needed)
# engine.setProperty('rate', 180)  # Speed (words per minute)
# engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
# voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[0].id)  # Select first voice; change index for others

def synthesize_speech(text: str, filename: str):
    # Ensure output dir exists
    output_dir = os.path.dirname(filename) or "."
    os.makedirs(output_dir, exist_ok=True)

    # Synthesize to WAV
    engine.save_to_file(text, filename)
    engine.runAndWait()  # Process the speech (blocking call)
    return os.path.abspath(filename)
