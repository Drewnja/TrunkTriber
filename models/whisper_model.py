# whisper_model.py

from colorama import Fore, Style
import whisper
from time import time
import logging
import os

# Load the Whisper model at the start of the program
WHISPER_MODEL = None

def load_whisper_model():
    global WHISPER_MODEL
    print(f"{Fore.MAGENTA + Style.BRIGHT}Loading Whisper-v3 model...{Style.RESET_ALL}")
    start_time = time()

    try:
        WHISPER_MODEL = whisper.load_model("large-v3")
    except Exception as e:
        logging.error(f"Error loading Whisper model: {e}")
        print(f"Error loading Whisper model: {e}")
        WHISPER_MODEL = None

    print(f"Model loaded in {Fore.BLUE + Style.BRIGHT}{time() - start_time:.2f} seconds{Style.RESET_ALL}")
    return WHISPER_MODEL

def transcribe_audio(audio_file):
    if WHISPER_MODEL is None:
        return None

    try:
        result = WHISPER_MODEL.transcribe(audio_file, language="ru", verbose=True)
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None
    

    return result['text']