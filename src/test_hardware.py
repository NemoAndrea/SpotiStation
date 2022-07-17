import board  # NOTE: this means we use GPIO.BCM mode
import time
import RPi.GPIO
from test_utils import print_progress

# slider imports
from rainbowio import colorwheel

from setup_hardware import initialise_buttons, intialise_slider

# Set up the buttons
playpause, back_but_1, back_but_2, side_but_1, side_but_2 = initialise_buttons()

# Set up slider
volumeslider = intialise_slider() 

device_status = [
    {"id" :"Play/Pause Button", "help": "Hold for 1s and release", "progress":"-", "ok":False},
    {"id" :"Back Button 1", "help": "Hold for 1s and release", "progress":"-", "ok":False},
    {"id" :"Back Button 2", "help": "Hold for 1s and release", "progress":"-", "ok":False},
    {"id" :"Side Button 1", "help": "Hold for 1s and release", "progress":"-", "ok":False},
    {"id" :"Side Button 2", "help": "Hold for 1s and release", "progress":"-", "ok":False},
    {"id" :"volume_slider", "help": "slide across entire range", "progress":"-", "ok":False}]


def test_button(device_id, button, pressed_iterations):      
    if button.value == False:  # button is pressed down
        device_status[device_id]["progress"] = "holding button..."
        pressed_iterations += 1
    else: 
        if pressed_iterations > 20:
            device_status[device_id]["ok"] = True
            device_status[device_id]["progress"] = "complete"
        elif pressed_iterations > 0:
            device_status[device_id]["progress"] = "released too fast! Try again."
        pressed_iterations = 0
    return pressed_iterations

def check_slider(device_id, value, range_progress):
    if  value > range_progress[1]:
        range_progress[1] = value
    elif value < range_progress[0]:
        range_progress[0] = value

    if (range_progress[1]-range_progress[0]) >= 1:
        device_status[device_id]["ok"] = True

    device_status[device_id]["progress"] = (f"Range: {range_progress[0]:.2f} to "
    f"{range_progress[1]:.2f} ({(range_progress[1]-range_progress[0])*100:.0f})%")
    # Fill the pixels a color based on the position of the potentiometer.
    volumeslider.led.fill(colorwheel((1-value) / 2 * 255))
    return range_progress

try:
    print(">>> Starting hardware checks...")
    print_progress(device_status)

    # number of loop cycles the button has been (continously) pressed down
    buttons_held_pp = 0 
    buttons_held_t1 = 0 
    buttons_held_t2 = 0 
    buttons_held_s1 = 0 
    buttons_held_s2 = 0 

    slider = volumeslider.position()
    if slider == None:
        # TODO this should probably be handled with a few tries 
        raise Exception("BAD i2c START - Exiting...")
    else:
        slider_progress = [slider,slider]  # range covered by slider so far

    while any(not device["ok"] for device in device_status):    
        
        ### Button checks           

        buttons_held_pp = test_button(0, playpause.button, buttons_held_pp)
        buttons_held_t1 = test_button(1, back_but_1.button, buttons_held_t1)   
        buttons_held_t2 = test_button(2, back_but_2.button, buttons_held_t2)   
        buttons_held_s1 = test_button(3, side_but_1.button, buttons_held_s1)   
        buttons_held_s2 = test_button(4, side_but_2.button, buttons_held_s2)       

        ### NeoSlider check

        slider = volumeslider.position()
        if slider is not None:
            slider_progress = check_slider(5, slider, slider_progress)  

        print_progress(device_status, clear=True)
        time.sleep(0.1)

    print(">>> All hardware checks passed!")
    
    volumeslider.led.fill(0)  # turn off slider neopixek
    RPi.GPIO.cleanup()
        
except KeyboardInterrupt:
    volumeslider.led.fill(0)  # turn off slider neopixek  
    RPi.GPIO.cleanup()    
    print("\nKeyboardInterrupt - cleaned up GPIO resources.")
except Exception as e:
    volumeslider.led.fill(0)  # turn off slider neopixek
    RPi.GPIO.cleanup()
    print(e) 
    print("\nCleaned up GPIO resources.")

   

