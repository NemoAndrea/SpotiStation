import configparser
import re

def get_device_config():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("config/player.ini")
    return config

def update_playlists(playlists):
    '''Updates and returns the user playlists that are 'in rotation' per the playlist.ini configuration file
    
    Takes the current user playlists as fetched from the spotify API to update the lists of
    playlists - as the user may have added new playlists to their account'''
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("config/playlists.ini")

    # something to print to console
    status = {'active':0, 'ignored':0, 'newly_added': 0}

    ### check for new playlists

    # first we draw up a list of playlist that are already in our config file
    config_playlists = []
    for key in config["in rotation"]:
        config_playlists.append(key)
        status['active'] += 1
    for key in config["ignored"]:
        config_playlists.append(key)
        status['ignored'] += 1

    for playlistentry in playlists:
        # get the name of playlist, but remove any funny characters and trailing and leading whitespace
        # we assume that whatever is left is unique enough to identify the playlist later from
        # future API calls
        name = re.sub('[^a-zA-Z0-9 \n\.]', '', playlistentry["name"]).strip().lower()
        if name != '':  # sometimes there is some unnamed playlist. TODO: figure out if this is important to include
            if not any(name == playlistname for playlistname in config_playlists):
                config["ignored"][name] = playlistentry["uri"]
                status['newly_added'] += 1

    write_playlist_config(config)

    print(f"Playlist Configuration: There are {status['active']} active playlists with "
          f"{status['ignored']} playlists being ignored. There were {status['newly_added']} new "
          f"playlist found and added to the 'ignored' section")

def get_playlists_in_config():
    '''Simple function that reads the current playlist config to list of tuples nested in dict'''
    
    config = configparser.ConfigParser()  # this will ignore comments
    config.read("config/playlists.ini")

    return {s:config.items(s) for s in config.sections()}

def get_playlists_in_config_as_sorted_list():
    playlists =  get_playlists_in_config()
    playlists_unsorted = []
    for playlist_name in playlists["in rotation"].keys():
        playlists_unsorted.append([playlist_name, True])
    for playlist_name in playlists["ignored"].keys():
        playlists_unsorted.append([playlist_name, False])

    return sorted(playlists_unsorted, key=lambda item: item[0])



def write_playlist_config(config):
    # add some comments to make it clearer what the structure of the config is
    config.set('in rotation', '# playlists in this section will be played and switched between in the player')
    config.set('ignored', '# playlists in this section will be ignored by the music player')
    config.set('ignored', '# new playlists in spotify will automatically be added here when player boots')
    with open('config/playlists.ini', 'w') as fp:
        config.write(fp)

def write_device_config(config):
    # add some comments to make it clearer what the structure of the config is
    config.set('connectivity', '# use a separate device (e.g. phone) to get this adress for your bluetooth device')
    with open('config/player.ini', 'w') as fp:
        config.write(fp)