import json
import os

def get_spotipy_auth():
    f = open('.creds')
    credentials = json.load(f)
    for k,v in credentials.items():
        os.environ[k] = str(v)
