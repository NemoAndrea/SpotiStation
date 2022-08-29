#!/usr/bin/env python3
import argparse
from copyreg import constructor
import os
import time

from pprint import pprint  # TODO remove import

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import alsaaudio

from read_cache_into_environment import get_spotipy_auth
from setup_hardware import MusicPlayer, PlayerState
from bootmenu import query_boot_mode
from config_manager import update_playlists, get_playlists_in_config, get_device_config, write_device_config
from utils import print_song_info, has_internet_connection, has_bluetooth_connection
from quiet_mode import quiet_mode_active, enable_quiet_mode, enable_locked_mode, quiet_mode_enabled_since, set_display_quiet_mode
'''Raspberry pi music player'''
def start_player(force_local_playback=False, force_playlists=False):
    print("Starting SpotiStation...")

    ### Hardware setup - create a new MusicPlayer object  

    # this also sets up the display - ROOT is dropped here, be careful about removing/reordering for security.
    player = MusicPlayer()

    ### Software setup and checks

    config = get_device_config()
    playlist_index = int(config['playback']['current-playlist-index'])
    poll_period = float(config['settings']['playback-poll-period'])

    # wifi and internet checks
    if not has_internet_connection:        
        player.display.set_display_mode("no_wifi")
        print("[setup] No internet connection available!")
        time.sleep(30); raise Exception("No internet connection available!")

    # bluetooth checks
    if not has_bluetooth_connection(config['connectivity']['bluetooth-mac']):        
        player.display.set_display_mode("no_bluetooth_audio")
        print("[setup] No bluetooth audio connection available!")
        time.sleep(30); raise Exception("No bluetooth audio connection available!")

    # volume control
    audio = alsaaudio.Mixer()  # default settings should work
    volume = audio.getvolume()[0]  # intialise volume [0-100]

    # check if the spotifyd service is running
    if not os.system('systemctl --user is-active --quiet spotifyd.service')==0:
        player.display.set_display_mode("no_spotifyd")
        print("[setup] Spotifyd daemon is not running")
        time.sleep(30); raise Exception("Spotifyd daemon is not running")

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
    # if NO device is active, we switch to RPi too, as we need something to play on
    current_device = next(filter(lambda device: device["is_active"], devices), None)
    if force_local_playback or current_device == None:
        # we get the current device name. If no spotify app is opened elsewhere, current_device==None
        current_device_name = 'none' if current_device == None else current_device['name']
        if force_local_playback:
            print(f"[flag:force-local-playback] Switching from {current_device_name} to Raspberry " 
             "Pi for playback (--forcelocal is set to True )")
        else:
            print(f"Switching from {current_device_name} to Raspberry Pi for playback")
        # find the raspberry pi in devices
        current_device = next(filter(lambda device: device["name"]=="Music_Pi", devices))        
        # and switch to it
        sp.transfer_playback(current_device["id"])    

    # get the playlists that are in rotation, and check if there are any new playlist in account
    # TODO: handle the limit of 50 playlists (multiple api calls)
    api_playlists = sp.current_user_playlists()
    update_playlists(api_playlists['items'])
    playlists = get_playlists_in_config()['in rotation']

    # try to find out what we are playing/will be playing
    current_playback = sp.current_playback()  # we might already be playing something
    if current_playback == None:  
        # we select a song to queue up from the 'in rotation' playlists
        sp.start_playback(current_device["id"], playlists[playlist_index][1])
    elif force_playlists:  # we are already playing somethign (from e.g. phone) 
        # we check if the current song is in the playlists config, and otherwise switch to one
        # that is in the playlist config 'in rotation' section.
        if current_playback['context']['uri'] not in map(lambda x: x[1], playlists):
            print("[flag:force-playlist] switching from ignored/unknown playlist to an in-rotation playlist")
            sp.start_playback(current_device["id"], playlists[playlist_index][1])
    
    # fetch and display the intial playback state
    print("Currently playing:")
    print_song_info(current_playback)
    player.display.set_coverart(current_playback)  # show the coverart
    if not sp.current_playback()["is_playing"]: player.display.set_display_mode("paused")

    ### Main device loop

    last_poll_time = time.time()  # initialise
    while True:
        if player.state == PlayerState.ACTIVE:
            if player.playpause.got_pressed():
                if sp.current_playback()["is_playing"]:  # get current playback status (play/pause)
                    print("pausing playback")
                    sp.pause_playback()
                    player.display.set_display_mode("paused")
                else:
                    sp.start_playback()
                    print("starting/resuming playback")
                    player.display.set_display_mode("")

            # side button 1 -> next track
            elif player.sidebutton_1.got_pressed():
                print("> Skipping track")
                sp.next_track()  # go to next track
                # show the next track overlay - it will be cleared when the next track is loaded
                player.display.set_display_mode("next_track")  
                current_playback=sp.current_playback()    
                player.display.set_coverart(current_playback)    

            # side button 2 -> next playlist
            elif player.sidebutton_2.got_pressed():
                playlist_index = (playlist_index + 1) % len(playlists)
                playlist_name = playlists[playlist_index][0]
                print(f"> Switching playlist to '{playlist_name}'") 
                # switch to next playlist
                sp.start_playback(current_device["id"], playlists[playlist_index][1])
                # show the next playlist overlay - it will be cleared when the next track is loaded
                player.display.set_display_mode("next_playlist")  
                playlist_trim = playlist_name[:13] + ".." if len(playlist_name) > 14 else playlist_name
                player.display.add_text_to_overlay(playlist_trim, (32, 54),
                    fill=(255,255,255,200), clear=False)  
                player.display.add_overlay_to_display(dimming=0.9)
                config['playback']['current-playlist-index'] = str(playlist_index)
                write_device_config(config)  # update the file on disk
                time.sleep(1)  # ensure the overlay is visible

            # Handle device getting LOCKED by administrator or user
            elif config['settings']['lock-mode-enabled'] and player.backbutton_1.got_pressed():
                print(f"Leaving the ACTIVE state for LOCKED state.")
                enable_locked_mode(player, sp, config)
                continue

            # adjust volume

            slider_volume = int(player.volumeslider.position()*100)
            if volume != slider_volume:
                print(f'setting volume to {slider_volume} (0-100)')
                audio.setvolume(slider_volume)
                volume = slider_volume 

            # check current playback status for changes
            if time.time() - last_poll_time > poll_period: 
                latest_playback = sp.current_playback()  

                # this is only in case we pause spotify on another device (e.g. phone) - this avoids 
                # the display pause/play state getting out of sync
                if sp.current_playback()["is_playing"] and player.display.overlay_mode=="paused":
                    player.display.set_display_mode("")  # clear the erroneous pause overlay
                if (not sp.current_playback()["is_playing"]) and player.display.overlay_mode==None:
                    player.display.set_display_mode("paused")  # add pause overlay that is missing

                # check if the song has changed (by 'item' id)
                if current_playback["item"]["id"] != latest_playback["item"]['id']:
                    current_playback = latest_playback  # update current playback for next loop
                    print_song_info(current_playback)
                    player.display.set_coverart(current_playback) 

                    # set a temporary text overlay showing album name 
                    song_name = current_playback['item']['name']
                    # we will need to trim the song name for the 64x64 display
                    song_name_trim = song_name[:13] + ".." if len(song_name) > 15 else song_name                     
                    player.display.add_text_to_overlay(song_name_trim, (32, 5),
                        fill=(255,255,255,200), clear=True)  
                    player.display.add_overlay_to_display_falloff(dimming=0.85, offset=9, length=32)  
                    player.display.timer.start_timer(3)  # show name for 3 seconds                

                last_poll_time = time.time()  # reset poll time

                # check if we should enter QUIET mode. Don't need to do this often, so we 
                # put it within this check since it only happens every poll_period
                if quiet_mode_active(config):
                    print("Leaving the ACTIVE state for QUIET state.")
                    enable_quiet_mode(player, sp, config)  # start quiet mode
                    continue

            # check if overlay should be removed
            if player.display.timer.is_expired():
                print("Removing timed overlay")
                player.display.reset_overlay() 

            time.sleep(0.05)  # minimum time between ACTIVE loops

        # player in the QUIET state (enabled depending on localtime)
        elif player.state == PlayerState.QUIET:
            if not quiet_mode_active(config):
                print("Leaving the QUIET state and returning to ACTIVE state")
                # set the volume back to slider val
                player.unmute(audio) 
                player.state = PlayerState.ACTIVE
                player.display.timer.reset()

            # turn off the display if we have been in quiet mode for over 30 minutes.
            if quiet_mode_enabled_since(config, 30):
                # check for button presses, and temporarily light up display if press detected
                if player.any_button_got_pressed():                    
                    print("temporarily showing display in QUIET mode")
                    player.display.timer.start_timer(7)  # show display for 7 seconds 
                    set_display_quiet_mode(player, config)  

                # if the display timer is active we show the display again, otherwise we turn it off
                if player.display.timer.is_expired():  
                    player.display.scale_intensity(0) 
                elif not player.display.timer.is_enabled():  # default action, turn off display
                    player.display.scale_intensity(0)                     

            # set volume to 0 (as someone could still turn ON playback via the API, e.g. via phone)  
            player.mute(audio)         
            time.sleep(0.3)  # in QUIET mode we don't need to loop fast          
        
        # player is in the LOCKED state (manually enabled by user)
        elif player.state == PlayerState.LOCKED:
            # check for quiet mode set time (overrides locked mode)
            if quiet_mode_active(config):
                print("Leaving the LOCKED state for QUIET state.")
                enable_quiet_mode(player, sp, config)  # start quiet mode

            player.mute(audio) 
            time.sleep(0.3)  # in LOCKED mode we don't need to loop fast            
        else:
            raise Exception("Unknown player state")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Start the Raspberry Pi music player')
    parser.add_argument('--forcelocal', '-fl', help='Switch current spotify playback device to '
        'raspberry pi when launching.', action="store_true")
    parser.add_argument('--forceplaylists', '-fp', help='Switch playlist if current playlist is ' 
        'is not part of the "in rotation" section in the playlist config file.', action="store_true")
    args = parser.parse_args()

    

    start_player(args.forcelocal, args.forceplaylists)
