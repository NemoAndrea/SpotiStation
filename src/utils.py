def print_song_info(spotipy_item):
    print(f">> Current song is '{spotipy_item['item']['name']}' by {spotipy_item['item']['artists'][0]['name']}")