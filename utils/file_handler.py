import os
import re
from datetime import datetime
from threading import Thread
from watchdog.events import FileSystemEventHandler
from utils import display
from utils.display import progress_indicator, stop_progress
from colorama import Fore, Style
from models.whisper_model import transcribe_audio
from threading import Event

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
        filename = os.path.basename(file_path)
        print(f"\n [💾] New audio: {Fore.GREEN + Style.BRIGHT}{filename}{Style.RESET_ALL}")

        # Get the creation date and time
        creation_time = os.path.getctime(file_path)
        creation_datetime = datetime.fromtimestamp(creation_time)
        formatted_creation_datetime = creation_datetime.strftime('%Y-%m-%d %H:%M:%S')

        # Extract FROM and TO numbers using regex
        from_number, to_number = self.extract_from_to_numbers(filename)
        if from_number and to_number:
            self.transcribe_and_print_result(file_path, formatted_creation_datetime, from_number, to_number)
        else:
            print(f"{Fore.YELLOW} [⚠️] SDRTrunk filename format not found{Style.RESET_ALL}")
            self.transcribe_and_print_result(file_path, formatted_creation_datetime)
            

    def extract_from_to_numbers(self, filename):
        match = re.search(r'TO_(\d+)_FROM_(\d+)', filename)
        if match:
            to_number = match.group(1)
            from_number = match.group(2)
            return from_number, to_number
        return None, None

    def transcribe_and_print_result(self, file_path, formatted_creation_datetime, from_number = '', to_number = ''):
        # Start the progress indicator
        global stop_progress
        stop_progress_event.clear()
        progress_thread = Thread(target=progress_indicator)
        progress_thread.start()

        # Transcribe the audio file
        result = transcribe_audio(file_path)

        # Stop the progress indicator
        stop_progress_event.set()
        progress_thread.join()
        

        # Format and print the output with hyphen
        print(f"{Fore.GREEN + Style.BRIGHT}{formatted_creation_datetime}{Style.RESET_ALL} "
              f"{Fore.BLUE}FROM {from_number}{Style.RESET_ALL} "
              f"{Fore.RED}TO {to_number}{Style.RESET_ALL} - "
              f"{Fore.WHITE + Style.BRIGHT}{result}{Style.RESET_ALL}")

        display.print_waiting_message()