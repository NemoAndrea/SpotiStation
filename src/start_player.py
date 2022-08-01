#!/usr/bin/env python3
import argparse
from dis import dis
from linecache import cache
import os
import time

from pprint import pprint  # TODO remove import

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import alsaaudio

from read_cache_into_environment import get_spotipy_auth
from setup_hardware import MusicPlayer
from bootmenu import query_boot_mode
from config_manager import configure_playlists
from utils import print_song_info

''''Raspberry pi music player'''
def start_player(force_local_playback=False):
    print("Starting music player...")

    # TODO move to config
    poll_freq = 2  # how many seconds between playback status checks (to see if song changed etc)  

    ### Hardware setup - create a new MusicPlayer object  

    # this also sets up the display - ROOT is dropped here, be careful about removing/reordering for security.
    player = MusicPlayer()

    ### Software setup and checks

    # volume control
    audio = alsaaudio.Mixer()  # default settings should work
    volume = audio.getvolume()[0]  # intialise volume [0-100]

    # check if the spotifyd service is running
    assert os.system('systemctl --user is-active --quiet spotifyd.service')==0,  "Spotifyd daemon \
        is not running"

    # quick and dirty get the id, secret and redirect URL into environment variable
    # this assumes the cache_spotipy_credentials.py has been run and .cache was generated before
    # TODO: make this more automatic (no longer manually need to save .creds)
    print("loading client id and secret into environment variables for spotipy")
    get_spotipy_auth()

    # check the Spotipy API 
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(cache_path=".cache"))
    except Exception as e:
        print(e) 
        print("Problem setting up Spotipy (python spotify api control).")

    ### Boot Menu

    query_boot_mode(player)

    # Check that we can find the raspberry pi in playback devices (if spotifyd is working correctly)
    devices = sp.devices()["devices"]
    assert any("Music_Pi" in device["name"] for device in devices), "Unable to find 'Music_Pi' in  \
        spotify playback devices. There is probably something wrong with spotifyd"

    # set the volume for the raspberry pi in spotify to 100%, we will do volume control on
    # device and want to guarantee that it cannot be turned up more than the base setting
    sp.volume(100, next(filter(lambda device: device["name"]=="Music_Pi", devices))["id"])

    # when lanching the player, you may not want to switch to the local device for playback 
    # as you may want to listen on your phone or other set of speakers not controlled by raspberry
    current_device = next(filter(lambda device: device["is_active"], devices))
    if force_local_playback:
        print(f"Switching from {current_device['name']} to Raspberry Pi for playback \
             (--forcelocal is set to True)")
        # find the raspberry pi in devices
        current_device = next(filter(lambda device: device["name"]=="Music_Pi", devices))        
        # and switch to it
        sp.transfer_playback(current_device["id"])     

    print("Currently playing:")
    
    current_playback = sp.current_playback()
    print_song_info(current_playback)
    player.display.set_coverart(current_playback)   

    # get the playlists that are in rotation, and check if there are any new playlist in account
    # TODO: exceed the limit of 50 playlists (multiple api calls)

    all_playlists = sp.current_user_playlists()
    playlists = configure_playlists(all_playlists['items'])
    # TODO: automatically select playlist and add flag to accept current playlist even if not in rotation?

    last_poll_time = time.time()  # initialise
    while True:
        if player.playpause.got_pressed():
            if sp.current_playback()["is_playing"]:  # get current playback status (play/pause)
                print("pausing playback")
                sp.pause_playback()
                player.display.set_display_mode("paused")
            else:
                sp.start_playback()
                print("starting/resuming playback")
                player.display.set_display_mode("")

        elif player.sidebutton_1.got_pressed():
            print("> Skipping track")
            sp.next_track()  # go to next track
            # show the next track overlay - it will be cleared when the next track is loaded
            player.display.set_display_mode("next_track")  
            current_playback=sp.current_playback()    
            player.display.set_coverart(current_playback)            

        elif player.backbutton_1.got_pressed():
            player.display.set_image_overlay('bla')  # testing

        # # check if overlay should be removed
        
        # if disp_timer.overlay_expired() and display.overlay != None:
        #     display.set_display_mode("")  # reset the overlay

        # adjust volume

        slider_volume = int(player.volumeslider.position()*100)
        if volume != slider_volume:
            print(f'setting volume to {slider_volume} (0-100)')
            audio.setvolume(slider_volume)
            volume = slider_volume 

        # check for song changes

        if time.time() - last_poll_time > 1:  # check current playback status for changes
            latest_playback = sp.current_playback()             

            # check if the song has changed (by 'item' id)
            if current_playback["item"]["id"] != latest_playback["item"]['id']:
                current_playback = latest_playback  # update current playback for next loop
                print_song_info(current_playback)
                player.display.set_coverart(current_playback)              

            last_poll_time = time.time()

        time.sleep(0.05)  # minimum time between loops


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Start the Raspberry Pi music player')
    parser.add_argument('--forcelocal', '-fl', help='Switch current spotify playback device to \
        raspberry pi when launching.', action="store_true")
    args = parser.parse_args()

    

    start_player(args.forcelocal)
