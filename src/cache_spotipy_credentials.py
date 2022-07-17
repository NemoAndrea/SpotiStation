from spotipy.oauth2 import SpotifyOAuth
import sys
import spotipy.util as util


# see https://developer.spotify.com/documentation/general/guides/authorization/scopes/
# for more information about these permissions/scopes
api_scopes = [
    'user-read-currently-playing',
    'user-modify-playback-state',
    'user-read-playback-state',
    'playlist-read-private', 
    'playlist-read-collaborative',
    'playlist-read-private'
]

scope = ','.join(api_scopes) 

auth = SpotifyOAuth(scope=scope, open_browser=False)
token = auth.get_access_token()  # this should generate a .cache file in current dir