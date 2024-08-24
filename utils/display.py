# display.py

import time
from colorama import init, Fore, Style
from utils import file_handler

# Initialize colorama
init(autoreset=True)

stop_dots = False
stop_progress = False

def display_dots():
    global stop_dots
    spinner = ['▁','▃','▄','▅','▆','▇','█','▇','▆','▅','▄','▃']
    idx = 0
    while not stop_dots:
        print(f'\r{spinner[idx]}', end='', flush=True)
        idx = (idx + 1) % len(spinner)
        time.sleep(0.1)
    print('')

def progress_indicator():
    spinner = ["◜ ", " ◝", " ◞", "◟ "]
    # spinner = ["🔈", "🔉", "🔊"]
    idx = 0
    while not file_handler.stop_progress_event.is_set():
        print(f'\r [🔊] Transcribing... {spinner[idx]}', end='', flush=True)
        idx = (idx + 1) % len(spinner)
        time.sleep(0.1)
    print('\r [✅] Transcribing... Done!')
    

def print_waiting_message():
    # Print the initial waiting message
    print(f"{Fore.MAGENTA + Style.BRIGHT}Waiting for audio...{Style.RESET_ALL}", end='', flush=True)