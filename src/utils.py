from urllib.request import urlopen
import subprocess

def has_internet_connection():
    try:
        response = urlopen('https://www.google.com/', timeout=10)
        return True
    except: 
        return False

def has_bluetooth_connection(bluetooth_MAC):
    # connect to bluetooth (should already be connected)
    bluetooth_status = subprocess.run(["bluetoothctl", "connect", bluetooth_MAC])
    if bluetooth_status.returncode == 0:
        return True
    else:
        return False



def print_song_info(spotipy_item):
    print(f">> Current song is '{spotipy_item['item']['name']}' by {spotipy_item['item']['artists'][0]['name']}")