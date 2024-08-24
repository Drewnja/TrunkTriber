# logging_config.py

import logging
import warnings

def setup_logging():
   
    warnings.filterwarnings("ignore")

    logging.getLogger().setLevel(logging.ERROR)
    # pass