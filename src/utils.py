from urllib.request import urlopen
import subprocess
import time
import sys
import logging
import logging.handlers
import requests

def has_internet_connection():
    try:
        response = urlopen('https://www.google.com/', timeout=10)
        logging.getLogger().info(f"[wifi] confirmed functional wifi connection")
        return True
    except: 
        return False

def has_bluetooth_connection(bluetooth_MAC, retries=3):
    # connect to bluetooth (should already be connected)
    for _ in range(retries):
        bluetooth_status = subprocess.run(["bluetoothctl", "connect", bluetooth_MAC])
        if bluetooth_status.returncode == 0:
            logging.getLogger().info(f"[bluetooth] successfully connected to {bluetooth_MAC}")
            return True
        else:
            # try one more time, but give it 10 seconds before next try
            time.sleep(10)
    return False  # return false if we have not managed to connect within the number retries


def format_song_info(spotipy_item):
    return f">> Current song is '{spotipy_item['item']['name']}' by {spotipy_item['item']['artists'][0]['name']}"


def setup_logger(mode):
    '''Configures logging to use a TimedRotatingFileHandler that creates a new file at midnight'''
    # set TimedRotatingFileHandler for root
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # set up a file handler that creates a new log file at midnight, and keeps 14 backups (~2 weeks)
    handler = logging.handlers.TimedRotatingFileHandler('playerstate.log', when="midnight", backupCount=14)
    handler.setFormatter(formatter)
    logger = logging.getLogger() 
    logger.addHandler(handler)
    # set up another handler that will also print logged statements to console
    handler_stdout = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler_stdout)

    logger.setLevel(mode)  # explicitly set the logger level
    # intialise a message (so we can track e.g. program restarts)
    logger.info('[NEW LOG START]')

    return logger


def get_new_playback(spotipy, old_playback):
    '''Try to fetch the latest playback information from spotify API, but return old playback in case of timeout.'''
    try:
        return spotipy.current_playback()
    except requests.exceptions.ReadTimeout:
        logging.getLogger.warning("error fetching current playback from spotify API", exc_info=True)
        # return the old playback info. Hopefully next iteration when this is called 
        # we are able to fetch the information correctly.
        return old_playback  
