from datetime import datetime
from setup_hardware import PlayerState

def quiet_mode_active(config):
    if config['settings']['night-mode-enabled']:
        current_time = datetime.now()
        # parse the config times. This will give objects with year = 1900
        starttime_raw = datetime.strptime(config['settings']['night-mode-time-start'], "%H:%M")
        endtime_raw = datetime.strptime(config['settings']['night-mode-time-end'], "%H:%M")
        # this is very clunky but it works and is not called frequently so it doesn't really matter
        starttime = datetime.now().replace(hour = starttime_raw.hour, minute = starttime_raw.minute)
        endtime = datetime.now().replace(hour = endtime_raw.hour, minute = endtime_raw.minute)
        #print(f"endtime {endtime} and starttime {starttime} and current {current_time}")
        if  current_time < endtime or current_time > starttime:       
            return True   # return True to inform that we should in QUIET mode
    else: 
        return False  # return False to inform that we can stay in current mode (ACTIVE or LOCKED)

def enable_quiet_mode(player, spotipy, config):
    print("Entering QUIET mode; pausing music and turning volume to 0")
    spotipy.pause_playback()  # pause the music via API (but could be turned back on via phone)
    player.display.set_display_mode("quiet_mode") 
    player.display.add_text_to_overlay(f"Wake at {config['settings']['night-mode-time-end']}",
     (32, 60), fill=(255,255,255,200))  
    player.display.add_overlay_to_display(dimming=0.95)
    player.state = PlayerState.QUIET

def enable_locked_mode(player, spotipy, config):
    print("Entering LOCKED mode; pausing music and turning volume to 0 until the next QUIET mode")
    spotipy.pause_playback()  # pause the music via API (but could be turned back on via phone)
    player.display.set_display_mode("lock_mode") 
    player.display.add_text_to_overlay(f"until {config['settings']['night-mode-time-start']}",
     (32, 58), fill=(255,255,255,200))  
    player.display.add_overlay_to_display(dimming=0.95)
    player.state = PlayerState.LOCKED
