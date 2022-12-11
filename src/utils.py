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


def trim_song_name(current_playback):
    '''Trim the song name to a length that can be displayed on the 64x64 panel'''
    song_name = current_playback['item']['name']
    return song_name[:13] + ".." if len(song_name) > 15 else song_name 


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


def get_new_playback(spotipy, player):
    '''Try to fetch the latest playback information from spotify API, but return old playback in case of timeout.'''
    try:
        current_playback = spotipy.current_playback()

        # all is well, we were able to refresh the current playback info
        if current_playback is not None:  
            player.last_playback = current_playback
            return 
        else:
            # API call returns None; we probably timed out our playback (if player is paused for a while).
            # We will manually restart playback of the last known playback 
            logging.getLogger().warning("[Spotify API] current_playback status timed out, needs kickstart", stack_info=True)

            # we manually restart (kickstart) the playback from the last known track
            # this should then start playback again
            spotipy.start_playback(player.playback_device, player.last_playback)
            time.sleep(0.1)  # wait a bit and then manually pause playback
            spotipy.pause_playback()  # and pause playback
            return  # in the next loop spotipy.current_playback() should no longer be None
    except requests.exceptions.ReadTimeout:
        logging.getLogger().warning("error fetching current playback from spotify API", exc_info=True)
        # return the without updating the last_playback status (still pointing to old playback)
        # we assume that some future API call will be able to recover
        return   
