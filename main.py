# main.py
from pick import pick
import time
from threading import Thread
from watchdog.observers import Observer
from utils.file_handler import AudioHandler
from utils.logging_config import setup_logging
from models.whisper_model import load_whisper_model
from utils import display
from config import WATCHED_FOLDER
from utils.ascii_art import ascii_art
from colorama import init, Fore, Style
import os

# Initialize colorama
init(autoreset=True)

def main():
    # Print ASCII Art
    print(f'{Fore.BLUE + Style.BRIGHT}{ascii_art}{Style.RESET_ALL}') 

    # Set up logging
    setup_logging()

    # Load the Whisper model
    model = load_whisper_model()
    if not model:
        return
    
    def start_live_transcribing():
        # Set up the watchdog observer
        print(f"{Fore.GREEN + Style.BRIGHT}Attaching watchdog to folder >>>{WATCHED_FOLDER}{Style.RESET_ALL}")
        start_time = time.time()
        event_handler = AudioHandler(model)
        observer = Observer()
        observer.schedule(event_handler, path=WATCHED_FOLDER, recursive=False)
    
        # Start the observer
        observer.start()
        print(f"Watchdog setup in {Fore.BLUE + Style.BRIGHT}{time.time() - start_time:.2f} seconds{Style.RESET_ALL}")
        
        display.print_waiting_message()
    
        try:
            while True:
                time.sleep(1)  # Keep the script running
        except KeyboardInterrupt:
            observer.stop()  # Stop the observer on interrupt
        observer.join()
    
    def start_mass_transcribe():
        print(f"{Fore.GREEN + Style.BRIGHT}Starting mass transcribe for folder >>>{WATCHED_FOLDER}{Style.RESET_ALL}")
        event_handler = AudioHandler(model)
        
        # Get all .mp3 files in the folder
        mp3_files = [f for f in os.listdir(WATCHED_FOLDER) if f.endswith('.mp3')]
        
        # Sort files by creation time (oldest first)
        mp3_files.sort(key=lambda x: os.path.getctime(os.path.join(WATCHED_FOLDER, x)))
        
        total_files = len(mp3_files)
        for index, filename in enumerate(mp3_files, start=1):
            file_path = os.path.join(WATCHED_FOLDER, filename)
            print(f"\n{Fore.CYAN}Processing file {index}/{total_files}: {filename}{Style.RESET_ALL}")
            event_handler.process_audio_file(file_path)
        
        print(f"{Fore.GREEN + Style.BRIGHT}Mass transcribe complete. Processed {total_files} files.{Style.RESET_ALL}")
    
    title = f'Choose working mode:'
    options = ['Mass Transcribe (scan folder)', 'Live Transcribe', 'Start Server']
    
    option, picker_index = pick(options, title, indicator='>', default_index=1)
    
    if picker_index == 0:
        start_mass_transcribe()
        
    elif picker_index == 1:
        print("Live transcribe")
        start_live_transcribing()
        
    elif picker_index == 2:
        print("Server mode is in development")

if __name__ == "__main__":
    main()