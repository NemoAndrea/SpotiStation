#!/usr/bin/env python3
import argparse
from copyreg import constructor
import os
import time
import logging
import subprocess

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from read_cache_into_environment import get_spotipy_auth
from setup_hardware import MusicPlayer, PlayerState
from bootmenu import query_boot_mode
from config_manager import update_playlists, get_playlists_in_config, get_device_config, write_device_config
from utils import format_song_info, has_internet_connection, has_bluetooth_connection, setup_logger, get_new_playback, trim_song_name
from quiet_mode import quiet_mode_active, enable_quiet_mode, enable_locked_mode, quiet_mode_enabled_since, set_display_quiet_mode

import alsaaudio  # for mute functionality

'''Raspberry pi music player'''
def start_player(force_local_playback=False, force_playlists=False, log_mode=logging.INFO):
    logger = setup_logger(log_mode)
    logger.info("Starting SpotiStation...")

    ### Hardware setup - create a new MusicPlayer object  

    # this also sets up the display - ROOT is dropped here, be careful about removing/reordering for security.
    player = MusicPlayer()

    ### Software setup and checks

    config = get_device_config()
    playlist_index = int(config['playback']['current-playlist-index'])
    poll_period = float(config['settings']['playback-poll-period'])

    # wifi and internet checks
    if not has_internet_connection():        
        player.display.set_display_mode("no_wifi")
        time.sleep(30)
        logger.exception("[setup] No internet connection available!", stack_info=True)
        raise Exception("No internet connection available!")

    # bluetooth checks
    if not has_bluetooth_connection(config['connectivity']['bluetooth-mac']):        
        player.display.set_display_mode("no_bluetooth_audio")
        time.sleep(30)
        logger.exception("[setup] No bluetooth audio connection available!", stack_info=True)
        raise Exception("No bluetooth audio connection available!")

    # check if the spotifyd service is running
    if not os.system('systemctl --user is-active --quiet spotifyd.service')==0:
        player.display.set_display_mode("no_spotifyd")
        time.sleep(30)
        logger.exception("[setup] Spotifyd daemon is not running")
        raise Exception("Spotifyd daemon is not running")

    # quick and dirty get the id, secret and redirect URL into environment variable
    # this assumes the cache_spotipy_credentials.py has been run and .cache was generated before
    # TODO: make this more automatic (no longer manually need to save .creds)
    logger.info("loading client id and secret into environment variables for spotipy")
    get_spotipy_auth()

    # check the Spotipy API 
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(cache_path=".cache"))
    except Exception as e:
        logger.exception("Problem setting up Spotipy (python spotify api control).")

    # we need to get a handle on alsa for the mute functionality
    # note that volume adjustment via the slider is handled by a separate python service
    audio = alsaaudio.Mixer()  
    audio.setmute(0)
    if player.state == PlayerState.ACTIVE:
        audio.setmute(0)  # this is insurance in case the player crashes in quiet/lock mode and
                          # comes out in active mode. The system could remain muted without this.

    # this is a bit hacky, but due to some startup sequence issues the volume service will
    # start correctly but not actually control volume. Restarting (sometime after boot) fixes it.
    subprocess.run(["systemctl", "--user", "restart",  "rpi-spotiplayer-volume.service"])

    ### Boot Menu

    query_boot_mode(player)

    # wrap everything in try except in order to log issues as they occur
    try:
        # Check that we can find the raspberry pi in playback devices (if spotifyd is working correctly)
        devices = sp.devices()["devices"]
        if not any("SpotiStation" in device["name"] for device in devices):
            # this is a rare case were the spotifyd service is running (which we check above),
            # but not actually working correctly. This can occur e.g. if internet connection is lost
            # and not regained for a while). We manually restart the service and
            # hope it will work after restart. 

            # restart the systemd spotifyd process
            subprocess.run(["systemctl", "--user", "restart",  "spotifyd.service"])

            # throw error (trigger auto-restart)
            errormsg = "Unable to find 'SpotiStation' in spotify playback devices. " \
            "Restarting spotifyd.service in attempt to fix."
            logger.exception(errormsg); raise Exception(errormsg)

        # set the volume for the raspberry pi in _spotify_ to 100%, we will do volume control on
        # device and want to guarantee that it cannot be turned up more than the base setting
        sp.volume(100, next(filter(lambda device: device["name"]=="SpotiStation", devices))["id"])

        # when lanching the player, you may not want to switch to the local device for playback 
        # as you may want to listen on your phone or other set of speakers not controlled by raspberry
        # if NO device is active, we switch to RPi too, as we need something to play on
        player.playback_device = next(filter(lambda device: device["is_active"], devices), None)
        if force_local_playback or player.playback_device == None:
            # we get the current device name. If no spotify app is opened elsewhere, player.playback_device==None
            current_device_name = 'none' if player.playback_device == None else player.playback_device['name']
            if force_local_playback:
                logger.info(f"[flag:force-local-playback] Switching from {current_device_name} to Raspberry " 
                "Pi for playback (--forcelocal is set to True )")
            else:
                logger.info(f"Switching from {current_device_name} to Raspberry Pi for playback")
            # find the raspberry pi in devices
            player.playback_device = next(filter(lambda device: device["name"]=="SpotiStation", devices))        
            # and switch to it
            sp.transfer_playback(player.playback_device["id"])    

        # get the playlists that are in rotation, and check if there are any new playlist in account
        # TODO: handle the limit of 50 playlists (multiple api calls)
        api_playlists = sp.current_user_playlists()
        update_playlists(api_playlists['items'])
        playlists = get_playlists_in_config()['in rotation']

        # Ensure the shuffle mode (on/off) is set correctly from value listed in config
        sp.shuffle(config.getboolean('settings', 'shuffle-songs'))

        # try to find out what we are playing/will be playing
        get_new_playback(sp, player) 

        if force_playlists:  # we are already playing somethign (from e.g. phone) 
            # we check if the current song is in the playlists config, and otherwise switch to one
            # that is in the playlist config 'in rotation' section.
            if player.last_playback['context']['uri'] not in map(lambda x: x[1], playlists):
                logger.info("[flag:force-playlist] switching from ignored/unknown playlist to an in-rotation playlist")
                sp.start_playback(player.playback_device["id"], playlists[playlist_index][1])
        
        # fetch and display the intial playback state
        logger.info(format_song_info(player.last_playback))
        player.display.set_coverart(player.last_playback)  # show the coverart
        if not sp.current_playback()["is_playing"]: player.display.set_display_mode("paused")

        ####################
        ### Main device loop
        ####################

        last_poll_time = time.time()  # initialise
        while True:
            if player.state == PlayerState.ACTIVE:
                if player.playpause.got_pressed():
                    if player.last_playback["is_playing"]:  # get current playback status (play/pause)
                        logger.info("pausing playback")
                        sp.pause_playback()
                        player.display.set_display_mode("paused")
                        # also show the song name at the top of display when track is paused
                        player.display.add_text_to_overlay(trim_song_name(player.last_playback), (32, 5),
                            fill=(255,255,255,200), clear=False)  
                        player.display.add_overlay_to_display(dimming=0.9)
                    else:
                        sp.start_playback()
                        logger.info("starting/resuming playback")
                        player.display.set_display_mode("")

                # side button 1 -> next track
                elif player.sidebutton_1.got_pressed():
                    logger.info("> Skipping track")
                    sp.next_track()  # go to next track
                    # show the next track overlay - it will be cleared when the next track is loaded
                    player.display.set_display_mode("next_track")   

                # side button 2 -> next playlist
                elif player.sidebutton_2.got_pressed():
                    playlist_index = (playlist_index + 1) % len(playlists)
                    playlist_name = playlists[playlist_index][0]
                    logger.info(f">>> Switching playlist to '{playlist_name}'") 
                    # switch to next playlist
                    sp.start_playback(player.playback_device["id"], playlists[playlist_index][1])
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
                elif config.getboolean('settings', 'lock-mode-enabled') and player.backbutton_1.got_pressed():                                       
                    logger.info(f"Leaving the ACTIVE state for LOCKED state.") 
                    enable_locked_mode(player, sp, config)
                    continue 

                # check current playback status for changes
                if time.time() - last_poll_time > poll_period:
                    old_playback = player.last_playback
                    get_new_playback(sp, player)  # update playback from API

                    # this is only in case we pause spotify on another device (e.g. phone) - this avoids 
                    # the display pause/play state getting out of sync
                    if player.last_playback["is_playing"] and player.display.overlay_mode=="paused":
                        player.display.set_display_mode("")  # clear the erroneous pause overlay
                    if (not player.last_playback["is_playing"]) and player.display.overlay_mode==None:
                        player.display.set_display_mode("paused")  # add pause overlay that is missing

                    # check if the song has changed (by 'item' id) - in this case the 'current_playback'
                    # could be older than the 'latest_playback'
                    if player.last_playback["item"]["id"] != old_playback["item"]['id']:
                        # update current playback for next loop
                        logger.info(format_song_info(player.last_playback))
                        player.display.set_coverart(player.last_playback) 

                        # set a temporary text overlay showing album name                                             
                        player.display.add_text_to_overlay(trim_song_name(player.last_playback), (32, 5),
                            fill=(255,255,255,200), clear=True)  
                        player.display.add_overlay_to_display_falloff(dimming=0.85, offset=9, length=32) 
                        if config.getboolean('settings', 'fade-song-name'): 
                            player.display.timer.start_timer(3)  # show name for 3 seconds only              

                    last_poll_time = time.time()  # reset poll time

                    # check if we should enter QUIET mode. Don't need to do this often, so we 
                    # put it within this check since it only happens every poll_period
                    if quiet_mode_active(config):
                        logger.info("Leaving the ACTIVE state for QUIET state.")
                        enable_quiet_mode(player, sp, config)  # start quiet mode
                        continue

                # check if overlay should be removed
                if player.display.timer.is_expired():
                    logger.debug("Removing timed display overlay")
                    player.display.reset_overlay() 

                time.sleep(0.05)  # minimum time between ACTIVE loops

            # player in the QUIET state (enabled depending on localtime)
            elif player.state == PlayerState.QUIET:
                if not quiet_mode_active(config):
                    logger.info("Leaving the QUIET state and returning to ACTIVE state")
                    # set the volume back to slider val
                    audio.setmute(0)
                    player.state = PlayerState.ACTIVE
                    player.display.timer.reset()

                # turn off the display if we have been in quiet mode for over 30 minutes.
                if quiet_mode_enabled_since(config, 30):
                    # check for button presses, and temporarily light up display if press detected
                    if player.any_button_got_pressed():                    
                        logger.info("temporarily showing display in QUIET mode")
                        set_display_quiet_mode(player, config)  
                        player.display.timer.start_timer(7)  # show display for 7 seconds                     

                    # if the display timer is active we show the display again, otherwise we turn it off
                    if player.display.timer.is_expired():  
                        player.display.scale_intensity(0) 
                    elif not player.display.timer.is_enabled():  # default action, turn off display
                        player.display.scale_intensity(0)                     

                # set volume to 0 (as someone could still turn ON playback via the API, e.g. via phone)  
                audio.setmute(1)        
                time.sleep(0.3)  # in QUIET mode we don't need to loop fast          
            
            # player is in the LOCKED state (manually enabled by user)
            elif player.state == PlayerState.LOCKED:
                # check for quiet mode set time (overrides locked mode)
                if quiet_mode_active(config):
                    logger.info("Leaving the LOCKED state for QUIET state.")
                    enable_quiet_mode(player, sp, config)  # start quiet mode

                audio.setmute(1)
                time.sleep(0.3)  # in LOCKED mode we don't need to loop fast          
    except KeyboardInterrupt as e:
        logger.warning("SpotiStation interrupted via KeyboardInterrupt")
    except:
        logger.exception("Unhandled exception in SpotiStation playback", stack_info=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Start the Raspberry Pi music player')
    parser.add_argument('--forcelocal', '-fl', help='Switch current spotify playback device to '
        'raspberry pi when launching.', action="store_true")
    parser.add_argument('--forceplaylists', '-fp', help='Switch playlist if current playlist is ' 
        'is not part of the "in rotation" section in the playlist config file.', action="store_true")
    parser.add_argument('--debug', help='Switch playlist if current playlist is ' 
        'is not part of the "in rotation" section in the playlist config file.', action="store_true")
    args = parser.parse_args()
    
    logmode = logging.DEBUG if args.debug else logging.INFO
    start_player(args.forcelocal, args.forceplaylists, logmode)
