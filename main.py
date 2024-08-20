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

if __name__ == "__main__":
    main()