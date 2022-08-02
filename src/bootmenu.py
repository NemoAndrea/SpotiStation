from curses import flash
import socket
import time
import math
from config_manager import get_playlists_in_config_as_sorted_list, write_playlist_config
import configparser


''''Boot mode selection

To keep the ui simple, there are few buttons on the device. To avoid complex multi-button 
commands, the device will wait a few seconds when starting the player in this 'boot menu'
which allows for a few utility menus/selection panels. Of course the easiest is to ssh into the
device, but for quick on the go or for less tech savy users these menus can be useful.
'''

def query_boot_mode(player, duration=5):
    '''Main loop that allows for boot mode selection'''
    print(f">> Waiting for boot mode selection - limit={duration} sec")
    initial_time = time.time()  
    seconds_since_start = -1
    
    # wait for button press until 'duration' has passed. If loop expires, then None is returned
    while time.time()-initial_time < duration:
        if any([player.playpause.got_pressed(), player.sidebutton_1.got_pressed(),player.sidebutton_2.got_pressed()]):
            print("> Skipped boot menu, launching application as normal")
            break
        elif any((player.backbutton_1.got_pressed(), player.backbutton_2.got_pressed())):
            print("> Launching Configuration Menu")
            display_config_menu(player); break 
        # update the text on display once per second
        if seconds_since_start != math.floor(time.time()-initial_time):
            seconds_since_start = math.floor(time.time()-initial_time)
            player.display.add_text_to_overlay("Press button", (32, 52),
             fill=(255,255,255,200), clear=True)  
            player.display.add_text_to_overlay(f"for config {duration-seconds_since_start}", (32, 60),
             fill=(255,255,255,200), clear=False)  
            player.display.add_overlay_to_display(dimming=0.5)
        time.sleep(0.01)

    print("> Leaving Boot Menu, launching application as normal")
    player.display.add_text_to_overlay(f"starting...", (32, 60), fill=(255,255,255,200), clear=True)  
    player.display.add_overlay_to_display(dimming=0.7)
    time.sleep(0.5)
    return None  # if we wait the full duration


def display_config_menu(player, duration=30):
    '''Configuration/boot menu that allows setting a few player options without ssh
    
    The menu will automatically exit if no action is chosen within 30 seconds. This is in case
    someone accidentally opened the menu and is not sure what to do.'''
    initial_time = time.time()  
    current_item_index = 0  # current item in list that is selected
    options = ["-- exit --", "playlists", "ip adress"]  #TODO: bluetooth connection menu?
    
    # wait for button press until 'duration' has passed. If loop expires, then None is returned
    while time.time()-initial_time < duration:
        player.display.add_text_to_overlay("Config Menu", (32, 5), fill=(0,139,139,255), clear=True)        

        # display the options on screen
        for i, option in enumerate(options):
            if current_item_index == i:
                color = (248,221,116,255)  # make text yellow
                textfill = "> "  # add '> {optiontext}' to further clarify that this option is selected
            else:
                color = (255,255,255,180)
                textfill = ""  # no leading text
            player.display.add_text_to_overlay(f"{textfill}{option}", (10, 14+i*6),
             fill=color, clear=False, center=False) 

        # actually show the overlay
        player.display.add_overlay_to_display(dimming=0.9)  

        # the playpause button serves as the 'select' key, so when that is pressed we choose that option 
        if player.playpause.got_pressed(): 
            if current_item_index == 0: return  # exit menu, just return without doing anything
            elif current_item_index == 1: select_playlists_on_display(player); return
            elif current_item_index == 2: display_ip_info(player); return
            # add more options here
        
        if player.sidebutton_2.got_pressed():
            if current_item_index > 0:  # check we cannot exceed the list of options
                current_item_index -= 1
        elif player.sidebutton_1.got_pressed():
            if current_item_index < (len(options)-1):  # check we cannot exceed the list of options
                current_item_index += 1       


        time.sleep(0.02)
    return


def display_ip_info(player):
    '''Display the local IP adress on screen for SSH connection
    
    Show the local IP adress on screen. In case you need to connect to the device via SSH but do
    not use a fixed IP adress. Playpause button will exit the menu and start the player.'''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(f"IP Address of {socket.gethostname()}: {s.getsockname()[0]}")
    player.display.set_image_from_file("/home/musicpi/minimal-music-player/interface/ip_screen.png")  # TODO avoid abs path
    player.display.add_text_overlay(str(s.getsockname()[0]), (32, 50),
             dimming=0, fill=(255,255,255,200), clear=True)  

    # wait until ok button is pressed
    while not player.playpause.got_pressed():
        time.sleep(0.03)

    # user pressed ok button, let them know
    player.display.add_text_overlay(f"starting...", (32, 50),
             dimming=0.9, fill=(255,255,255,200), clear=True)  


def select_playlists_on_display(player):
    '''Display the user's spotify playlists, their status and change the status
    
    Shows all the playlists associated with the spotify account. Green playlists are 'in rotation',
    while 'gray' playlists are ignored. Use side buttons for up-down navigation and playpause button
    to toggle the state of the playlist. Use the 'save' option (top of the list) to save config and
    start the player.'''
    display_limit = 8  # how many items for on one screen
    playlists = get_playlists_in_config_as_sorted_list()
    playlists.insert(0, ["-- save --", False])
    caroussel_offset = 0  # keep track of which playlists fit on the screen
    cursor_position = 0
    while True:        
        # show page header
        player.display.add_text_to_overlay("playlist state", (32, 5), fill=(0,139,139,255), clear=True)

        # show playlists
        for i, (playlist, in_rotation) in enumerate(playlists):
            if caroussel_offset <= i < caroussel_offset+display_limit:  
                # do nothing if i=0 and caroussel>0, as then i=0 location is occupied by 'more'                  
                if not (caroussel_offset > 0 and i-caroussel_offset==0):                    
                    color = (0, 255, 0, 255) if in_rotation else (255,255, 255, 80)
                    if i==cursor_position:
                        filltext = "> "
                        text_x = 0
                    else:
                        filltext = ""
                        text_x = 5
                    player.display.add_text_to_overlay(f"{filltext}{playlist}", (text_x, 12 +
                     (i-caroussel_offset)*6), fill=color, clear=False, center=False)

        # display '...MORE' if more content can be revelead by scroll (moving cursor)
        if display_limit+caroussel_offset-1 < len(playlist):
            player.display.add_text_to_overlay("...more", (5, 60), fill=(248,221,116,255),
             clear=False, center=False)
        if caroussel_offset > 0:
            player.display.add_text_to_overlay("...more", (5, 12), fill=(248,221,116,255),
             clear=False, center=False)     
        
        # actually show the overlay
        player.display.add_overlay_to_display(dimming=0.9)     

        if player.sidebutton_2.got_pressed():
            if cursor_position > 0:  # check we cannot exceed the list of options
                cursor_position -= 1
            if cursor_position-1 < caroussel_offset:
                if caroussel_offset != 0: caroussel_offset -=1
        elif player.sidebutton_1.got_pressed():
            if cursor_position < (len(playlists)-1):  # check we cannot exceed the list of options
                cursor_position += 1  
            if cursor_position+1 > caroussel_offset+display_limit:
                caroussel_offset +=1

                
        if player.playpause.got_pressed():
            if cursor_position == 0:  # save and exit option
                # get the old config
                config = configparser.ConfigParser(allow_no_value=True)
                config.read("config/playlists.ini")
                # get the new user selection
                in_rotation = list(filter(lambda x: x[1], playlists[1:]))
                ignored = list(filter(lambda x: not x[1], playlists[1:]))

                for new_playlist, _ in in_rotation:
                    if new_playlist not in [key for key in config["in rotation"]]:
                        # swap to in_rotation
                        print(f"[config change] (new in-rotation): {new_playlist}")
                        # we get the uri from the old section (which is the 'ignored' section)
                        uri = config.get("ignored", new_playlist)
                        config.remove_option("ignored", new_playlist)
                        config.set("in rotation", new_playlist, uri)
                for new_playlist, _ in ignored:
                    if new_playlist not in [key for key in config["ignored"]]:
                        # swap to ignored
                        print(f"[config change] (new ignored): {new_playlist}")
                        # we get the uri from the old section (which is the 'in rotation' section)
                        uri = config.get("in rotation", new_playlist)
                        config.remove_option("in rotation", new_playlist)
                        config.set("ignored", new_playlist, uri)
                
                write_playlist_config(config)
                return
            else:  
                # we are toggling the state of the playlist 'ignored'<->'in rotation'
                playlists[cursor_position][1] = not playlists[cursor_position][1]
        
        time.sleep(0.02)
