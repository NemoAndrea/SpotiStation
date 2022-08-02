from urllib.request import urlopen
import subprocess
import time

def has_internet_connection():
    try:
        response = urlopen('https://www.google.com/', timeout=10)
        return True
    except: 
        return False

def has_bluetooth_connection(bluetooth_MAC, retries=3):
    # connect to bluetooth (should already be connected)
    for _ in range(retries):
        bluetooth_status = subprocess.run(["bluetoothctl", "connect", bluetooth_MAC])
        if bluetooth_status.returncode == 0:
            return True
        else:
            # try one more time, but give it 10 seconds before next try
            time.sleep(10)
    return False  # return false if we have not managed to connect within the number retries




def print_song_info(spotipy_item):
    print(f">> Current song is '{spotipy_item['item']['name']}' by {spotipy_item['item']['artists'][0]['name']}")