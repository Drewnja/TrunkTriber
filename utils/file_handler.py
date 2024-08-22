import os
import re
from datetime import datetime
from threading import Event, Thread
from watchdog.events import FileSystemEventHandler
from utils import display
from utils.display import progress_indicator
from colorama import Fore, Style
from models.whisper_model import transcribe_audio
from pydub import AudioSegment
import webrtcvad
import numpy as np


# Create a global event to control the progress indicator
stop_progress_event = Event()

class AudioHandler(FileSystemEventHandler):
    def __init__(self, model):
        self.model = model

    def on_created(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.mp3'):
            self.process_audio_file(event.src_path)

    def process_audio_file(self, file_path):
        if self.is_short_audio(file_path):
            os.remove(file_path)
            print(f"\n[🗑️] Deleted short audio file: {Fore.RED + Style.BRIGHT}{os.path.basename(file_path)}{Style.RESET_ALL}")
            display.print_waiting_message()
            return

        if self.is_silent_audio(file_path):
            os.remove(file_path)
            print(f"\n[🗑️] Deleted silent audio file: {Fore.RED + Style.BRIGHT}{os.path.basename(file_path)}{Style.RESET_ALL}")
            display.print_waiting_message()
            return

        filename = os.path.basename(file_path)
        print(f"\n [💾] New audio: {Fore.GREEN + Style.BRIGHT}{filename}{Style.RESET_ALL}")

        # Extract date and time from filename
        date_str, time_str = self.extract_datetime_from_filename(filename)
        formatted_creation_datetime = f"{date_str} {time_str}"

        # Extract FROM and TO numbers using regex
        from_number, to_number = self.extract_from_to_numbers(filename)
        self.transcribe_and_print_result(file_path, formatted_creation_datetime, from_number, to_number)

    def extract_datetime_from_filename(self, filename):
        # Extract the date and time portions from the filename
        date_match = re.search(r'(\d{8})_(\d{6})', filename)
        if date_match:
            date_str = date_match.group(1)
            time_str = date_match.group(2)

            # Convert date_str and time_str to the desired format
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
            return formatted_date, formatted_time

        # Return empty strings if the pattern doesn't match
        return '', ''

    def extract_from_to_numbers(self, filename):
        to_match = re.search(r'TO_(\d+)', filename)
        from_match = re.search(r'FROM_(\d+)', filename)
        to_number = to_match.group(1) if to_match else ''
        from_number = from_match.group(1) if from_match else ''
        return from_number, to_number

    def transcribe_and_print_result(self, file_path, formatted_creation_datetime, from_number='', to_number=''):
        # Start the progress indicator
        stop_progress_event.clear()
        progress_thread = Thread(target=progress_indicator)
        progress_thread.start()

        # Transcribe the audio file
        result = transcribe_audio(file_path)

        # Stop the progress indicator
        stop_progress_event.set()
        progress_thread.join()

        # Format and print the output with hyphen
        output = f"{Fore.GREEN + Style.BRIGHT}{formatted_creation_datetime}{Style.RESET_ALL} "
        if from_number:
            output += f"{Fore.BLUE}FROM {from_number}{Style.RESET_ALL} "
        if to_number:
            output += f"{Fore.RED}TO {to_number}{Style.RESET_ALL} "
        if not from_number and not to_number:
            print(f"{Fore.YELLOW} [⚠️] SDRTrunk filename format not fully recognized{Style.RESET_ALL}")
        output += f"- {Fore.WHITE + Style.BRIGHT}{result}{Style.RESET_ALL}"
        print(output)

        display.print_waiting_message()

    def is_short_audio(self, file_path):
        audio = AudioSegment.from_file(file_path)
        duration_in_seconds = len(audio) / 1000.0

        # Check if the duration is shorter than 1.5 seconds
        return duration_in_seconds < 1.5

def is_silent_audio(self, file_path):
    # Initialize VAD (Voice Activity Detector)
    vad = webrtcvad.Vad()
    
    # Load the audio file
    audio = AudioSegment.from_file(file_path)
    sample_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples())

    # Convert samples to 16-bit PCM
    if audio.sample_width == 2:
        samples = samples.astype(np.int16)
    else:
        samples = (samples / 256).astype(np.int16)
    
    # Frame parameters for VAD
    frame_duration = 30  # milliseconds
    frame_size = int(sample_rate * frame_duration / 1000)
    
    # Check if audio is too short
    if len(samples) < frame_size:
        return True
    
    # Detect speech in frames
    for start in range(0, len(samples) - frame_size, frame_size):
        frame = samples[start:start + frame_size]
        if vad.is_speech(frame.tobytes(), sample_rate):
            return False  # Speech detected

    return True  # No speech detected

