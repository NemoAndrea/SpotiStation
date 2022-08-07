from datetime import datetime

def quiet_mode_active(config):
    if config['settings']['night-mode-enabled']:
        current_time = datetime.now()
        # parse the config times. This will give objects with year = 1900
        starttime_raw = datetime.strptime(config['settings']['night-mode-time-start'], "%H:%M")
        endtime_raw = datetime.strptime(config['settings']['night-mode-time-end'], "%H:%M")
        # this is very clunky but it works and is not called frequently so it doesn't really matter
        starttime = datetime.now().replace(hour = starttime_raw.hour, minute = starttime_raw.minute)
        endtime = datetime.now().replace(hour = endtime_raw.hour, minute = endtime_raw.minute)
        if  current_time < endtime or current_time > starttime:       
            return True   # return True to inform that we should in QUIET mode
    else: 
        return False  # return False to inform that we can stay in current mode (ACTIVE or LOCKED)