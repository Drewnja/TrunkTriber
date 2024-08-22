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

        # Get the creation date and time
        creation_time = os.path.getctime(file_path)
        creation_datetime = datetime.fromtimestamp(creation_time)
        formatted_creation_datetime = creation_datetime.strftime('%Y-%m-%d %H:%M:%S')

        # Extract FROM and TO numbers using regex
        from_number, to_number = self.extract_from_to_numbers(filename)
        self.transcribe_and_print_result(file_path, formatted_creation_datetime, from_number, to_number)

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
        audio = AudioSegment.from_file(file_path)

        # Analyze the audio file for speech presence
        samples = audio.get_array_of_samples()
        return max(samples) - min(samples) < 500  # Simple threshold for detecting speech
