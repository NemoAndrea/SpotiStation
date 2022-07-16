#!/usr/bin/env python3
import argparse
import os
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from read_cache_into_environment import get_spotipy_auth
from setup_hardware import initialise_buttons, intialise_slider


''''Raspberry pi music player'''
def start_player():
    print("Starting music player...")

    # check if the spotifyd service is running (assuming service runs as user - as per setup instructions)
    assert os.system('systemctl --user is-active --quiet spotifyd.service')==0,  "Spotifyd daemon is not running"

    # quick and dirty get the id, secret and redirect URL into environment variable
    # this assumes the cache_spotipy_credentials.py has been run and .cache was generated before
    # TODO: make this more automatic (no longer manually need to save .creds)
    print("loading client id and secret into environment variables for spotipy")
    get_spotipy_auth()

    # check the Spotipy API 
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth())
    except Exception as e:
        print(e) 
        print("Problem setting up Spotipy (python spotify api control).")

    # Set up the buttons
    playpause = initialise_buttons()

    # Set up slider
    volumeslider = intialise_slider()    

    while True:
        print("loop...")
        print(f"Button value is {playpause.value}")
        print(f"Slider value is {volumeslider.position()}")
        time.sleep(0.2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Start the Raspberry Pi music player')

    start_player()
