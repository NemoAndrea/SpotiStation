from spotipy.oauth2 import SpotifyOAuth

scope = 'user-read-currently-playing'  # TODO find minimal set needed for player

auth = SpotifyOAuth(scope=scope, open_browser=False)
token = auth.get_access_token()