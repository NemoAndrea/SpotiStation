import json
import os

def get_spotipy_auth():
    f = open('/home/musicpi/minimal-music-player/.creds')  #TODO generalise
    credentials = json.load(f)
    for k,v in credentials.items():
        print(f"setting {v} to ${k}")
        os.environ[k] = str(v)
