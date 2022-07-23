import socket
import time
import math

''''Boot mode selection

To keep the ui simple, there are few buttons on the device. To avoid complex multi-button 
commands, the device will wait a few seconds when starting the player in this 'boot menu'
which allows for a few utility menus/selection panels. Of course the easiest is to ssh into the
device, but for quick on the go or for less tech savy users these menus can be useful.
'''

def query_boot_mode(skip_button, ip_button, playlist_button,display, duration=5):
    '''Main loop that allows for boot mode selection'''
    print(f">> Launching boot menu - limit={duration} sec")
    initial_time = time.time()  
    seconds_since_start = -1
    
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
        # update the text on display once per second
        if seconds_since_start != math.floor(time.time()-initial_time):
            seconds_since_start = math.floor(time.time()-initial_time)
            display.add_text_overlay(f"booting in {duration-seconds_since_start}", (32, 60),
             dimming=0, fill=(255,255,255,200), clear=True)  
        time.sleep(0.01)

    print("> Boot menu expired, launching application as normal")
    display.add_text_overlay(f"starting...", (32, 60),
             dimming=0.7, fill=(255,255,255,200), clear=True)  
    return None  # if we wait the full duration

def display_ip_info(ok_button, display):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(f"IP Address of {socket.gethostname()}: {s.getsockname()[0]}")
    display.set_image_from_file("/home/musicpi/minimal-music-player/interface/ip_screen.png")  # TODO avoid abs path
    display.add_text_overlay(str(s.getsockname()[0]), (32, 50),
             dimming=0, fill=(255,255,255,200), clear=True)  

    # wait until ok button is pressed
    while not ok_button.got_pressed():
        time.sleep(0.03)

    # user pressed ok button, let them know
    display.add_text_overlay(f"starting...", (32, 50),
             dimming=0.9, fill=(255,255,255,200), clear=True)  


def select_playlists_on_display(ok_button, display, up_button, down_button, toggle_button):
    return 