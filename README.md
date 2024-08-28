# TrunkTriber

TrunkTriber is a Python tool for transcribing audio files from trunked radio systems using Whisper AI. It supports both live and batch processing of recordings. Was originally designed to work with SDRtrunk, can parse SDRtrunk filename format, but can be used with any audiofiles.

## Features

- Live audio transcription
- Batch processing of audio files

## Requirements

- Python 3.8 or 3.9

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Drewnja/TrunkTriber.git
   cd TrunkTriber

2. Install dependencies:
    ```bash
    pip install -r requirements.txt

3. Run the script:
   Note: On first launch script will download Whisper large-v3 model, which can take a while (Model is ~1.5GB).

    ```bash

    python3 main.py
    ```

License
MIT License. See LICENSE for details.

