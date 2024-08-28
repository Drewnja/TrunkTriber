import os
import re
from datetime import datetime
from threading import Event, Thread, Lock
import time
from watchdog.events import FileSystemEventHandler
from utils import display
from colorama import Fore, Style
from models.whisper_model import transcribe_audio
from pydub import AudioSegment
import webrtcvad
import numpy as np
import itertools

# Create a global event to control the progress indicator
stop_progress_event = Event()
progress_lock = Lock()
spinner_cycle = itertools.cycle(['◜', '◝', '◞', '◟'])

class AudioHandler(FileSystemEventHandler):
    def __init__(self, model):
        self.model = model
        self.thread_data = {}

    def on_created(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.mp3'):
            self.process_audio_file(event.src_path)

    def process_audio_file(self, file_path, thread_index=None):
        if self.is_short_audio(file_path):
            print(f"\n[🗑️] Skipped short audio file: {Fore.RED + Style.BRIGHT}{os.path.basename(file_path)}{Style.RESET_ALL}")
            display.print_waiting_message()
            return

        if self.is_silent_audio(file_path):
            print(f"\n[🗑️] Skipped silent audio file: {Fore.RED + Style.BRIGHT}{os.path.basename(file_path)}{Style.RESET_ALL}")
            display.print_waiting_message()
            return

        filename = os.path.basename(file_path)
        print(f"\n [💾] Processing audio: {Fore.GREEN + Style.BRIGHT}{filename}{Style.RESET_ALL}")

        # Extract date and time from filename
        date_str, time_str = self.extract_datetime_from_filename(filename)
        formatted_creation_datetime = f"{date_str} {time_str}"

        # Extract FROM and TO numbers using regex
        from_number, to_number = self.extract_from_to_numbers(filename)

        # Start thread-specific progress indicator
        if thread_index is not None:
            self.start_progress_indicator(thread_index, filename)

        self.transcribe_and_print_result(file_path, formatted_creation_datetime, from_number, to_number, thread_index)

        # Stop thread-specific progress indicator
        if thread_index is not None:
            self.stop_progress_indicator(thread_index)

    def start_progress_indicator(self, thread_index, filename):
        stop_progress_event.clear()
        self.thread_data[thread_index] = {
            'filename': filename,
            'progress_thread': Thread(target=self.progress_indicator, args=(thread_index,))
        }
        self.thread_data[thread_index]['progress_thread'].start()

    def stop_progress_indicator(self, thread_index):
        stop_progress_event.set()
        self.thread_data[thread_index]['progress_thread'].join()
        del self.thread_data[thread_index]

    def progress_indicator(self, thread_index):
        while not stop_progress_event.is_set():
            with progress_lock:
                spinner = next(spinner_cycle)
                print(f"\r[ 🧵 ] Thread #{thread_index + 1}: {self.thread_data[thread_index]['filename']} | Processing {spinner}", end="")
            time.sleep(0.1)
        print("\r" + " " * 80, end="\r")  # Clear the line

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

    def transcribe_and_print_result(self, file_path, formatted_creation_datetime, from_number='', to_number='', thread_index=None):
        result = transcribe_audio(file_path)

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
        # Initialize VAD with aggressiveness mode 3
        vad = webrtcvad.Vad(3)

        # Load the audio file
        audio = AudioSegment.from_file(file_path)
        sample_rate = audio.frame_rate
        samples = np.array(audio.get_array_of_samples())

        # Convert samples to 16-bit PCM if needed
        if audio.sample_width != 2:
            samples = (samples / 256).astype(np.int16)

        # Define frame size for VAD (30 ms frames)
        frame_size = int(sample_rate * 0.03)  # 30 milliseconds

        # If audio is too short, consider it silent
        if len(samples) < frame_size:
            return True

        # Check for speech in frames
        for start in range(0, len(samples) - frame_size, frame_size):
            frame = samples[start:start + frame_size]
            if vad.is_speech(frame.tobytes(), sample_rate):
                return False  # Speech detected

        return True  # No speech detected
