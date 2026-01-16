
import whisper
from summarizer import Summarizer
import sys

print("Loading Whisper model 'base'...")
try:
    model = whisper.load_model("base")
    print("Whisper loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper: {e}")
    sys.exit(1)

print("Loading Summarizer...")
try:
    summ = Summarizer()
    print("Summarizer loaded successfully.")
except Exception as e:
    print(f"Error loading Summarizer: {e}")
    sys.exit(1)

print("Done.")
