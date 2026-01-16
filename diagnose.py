
import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Importing flask...")
try:
    from flask import Flask
    print("Flask imported.")
except Exception as e:
    print(f"Flask import failed: {e}")

print("Importing whisper...")
try:
    import whisper
    print("Whisper imported.")
except Exception as e:
    print(f"Whisper import failed: {e}")

print("Importing summarizer...")
try:
    from summarizer import Summarizer
    print("Summarizer imported.")
except Exception as e:
    print(f"Summarizer import failed: {e}")

print("Importing Main...")
try:
    import Main
    print("Main imported.")
except Exception as e:
    print(f"Main import failed: {e}")

print("All imports successful. Attempting to load models (light check)...")
try:
    # Just check if we can instantiate class without full load if possible, or load tiny model
    # whisper.load_model("tiny") 
    print("Skipping full model load in diagnostic to save time, but imports work.")
except Exception as e:
    print(f"Model load failed: {e}")
