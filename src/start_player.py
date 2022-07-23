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
from setup_hardware import initialise_buttons, intialise_slider
from bootmenu import query_boot_mode, display_ip_info, select_playlists_on_display
from display import MusicDisplay, DisplayOverlayTimer
from utils import print_song_info

''''Raspberry pi music player'''
def start_player(force_local_playback=False):
    print("Starting music player...")

    poll_freq = 2  # how many seconds between playback status checks (to see if song changed etc)  

    ### Hardware setup  
    
    # Set up the buttons
    playpause, back_but_1, back_but_2, side_but_1, side_but_2 = initialise_buttons()   

    # Set up slider & volume control
    volumeslider = intialise_slider()

    # Set up display - ROOT is dropped here, be careful about removing/reordering for security.
    display = MusicDisplay(64, 64)  # needs root privileges, but those are dropped after this function 
    display.set_image_from_file("/home/musicpi/minimal-music-player/interface/splash_screen.png")  # TODO avoid abs path
    #disp_timer = DisplayOverlayTimer()

    ### Boot Menu

    bootmode = query_boot_mode(playpause, back_but_2, side_but_1, display)
    if bootmode:  # if user waited out the timeout or skipped the boot menu then bootmode=None
        if bootmode=="ip":
            display_ip_info(playpause, display)
        elif bootmode=="playlist":
            select_playlists_on_display(back_but_2, display, side_but_1, side_but_2, playpause)

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
    # pprint(current_playback)  # debugging
    print_song_info(current_playback)
    display.set_coverart(current_playback)   

    last_poll_time = time.time()  # initialise
    while True:
        if playpause.got_pressed():
            if sp.current_playback()["is_playing"]:  # get current playback status (play/pause)
                print("pausing playback")
                sp.pause_playback()
                display.set_display_mode("paused")
            else:
                sp.start_playback()
                print("starting/resuming playback")
                display.set_display_mode("")

        elif side_but_1.got_pressed():
            print("> Skipping track")
            sp.next_track()  # go to next track
            # show the next track overlay - it will be cleared when the next track is loaded
            display.set_display_mode("next_track")  
            current_playback=sp.current_playback()    
            display.set_coverart(current_playback)            

        elif back_but_1.got_pressed():
            display.set_image_overlay('bla')  # testing

        # # check if overlay should be removed
        
        # if disp_timer.overlay_expired() and display.overlay != None:
        #     display.set_display_mode("")  # reset the overlay

        # adjust volume

        slider_volume = int(volumeslider.position()*100)
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
                display.set_coverart(current_playback)              

            last_poll_time = time.time()

        time.sleep(0.05)  # minimum time between loops


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Start the Raspberry Pi music player')
    parser.add_argument('--forcelocal', '-fl', help='Switch current spotify playback device to \
        raspberry pi when launching.', action="store_true")
    args = parser.parse_args()

    

    start_player(args.forcelocal)
