import socket
import time

''''Boot mode selection

To keep the ui simple, there are few buttons on the device. To avoid complex multi-button 
commands, the device will wait a few seconds when starting the player in this 'boot menu'
which allows for a few utility menus/selection panels. Of course the easiest is to ssh into the
device, but for quick on the go or for less tech savy users these menus can be useful.
'''

def query_boot_mode(skip_button, ip_button, playlist_button, duration=5):
    '''Main loop that allows for boot mode selection'''
    print(f">> Launching boot menu - limit={duration} sec")
    initial_time = time.time()  
    
    # wait for button press until 'duration' has passed. If loop expires, then None is returned
    while time.time()-initial_time < duration:
        if skip_button.got_pressed():
            print("> Skipped boot menu, launching application as normal")
            return None
        elif ip_button.got_pressed():
            print("> Boot menu: selected IP menu")
            return "ip"
        elif playlist_button.got_pressed():
            print("> Boot menu: selected playlist selection")
            return "playlist"
        time.sleep(0.01)

    print("> Boot menu expired, launching application as normal")
    return None  # if we wait the full duration

def display_ip_info(ok_button, display):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(f"IP Address of {socket.gethostname()}: {s.getsockname()[0]}")

def select_playlists_on_display(ok_button, display, up_button, down_button, toggle_button):
    return 