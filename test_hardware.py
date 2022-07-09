import board  # NOTE: this means we use GPIO.BCM mode
from digitalio import DigitalInOut, Pull
import time
import RPi.GPIO
from test_utils import print_progress
from utils import slidervalue

# slider imports
from rainbowio import colorwheel
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel

# play pause button - wired to SPI0_MOSI
playpause_button = DigitalInOut(board.MOSI)
playpause_button.pull = Pull.UP

# NeoSlider Setup
neoslider = Seesaw(board.I2C(), 0x30)
potentiometer = AnalogInput(neoslider, 18)
pixels = neopixel.NeoPixel(neoslider, 14, 4)

device_status = [
    {"id" :"Play/Pause Button", "help": "Hold for 1s and release", "progress":"-", "ok":False},
    {"id" :"volume_slider", "help": "slide across entire range", "progress":"-", "ok":False}]


def test_button(device_id, pressed_iterations):      
    if playpause_button.value == False:  # button is pressed down
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
    pixels.fill(colorwheel((1-value) / 2 * 255))
    return range_progress

try:
    print(">>> Starting hardware checks...")
    print_progress(device_status)

    button_held = 0  # number of loop cycles the button has been (continously) pressed down
    slider = slidervalue(potentiometer)
    if slider == None:
        # TODO this should probably be handled with a few tries 
        raise Exception("BAD i2c START - Exiting...")
    else:
        slider_progress = [slider,slider]  # range covered by slider so far

    while any(not device["ok"] for device in device_status):    
        """
        Play/Pause button check
        """    

        button_held = test_button(0, button_held)    

        """
        NeoSlider check
        """

        slider = slidervalue(potentiometer)
        if slider is not None:
            slider_progress = check_slider(1, slider, slider_progress)  

        print_progress(device_status, clear=True)
        time.sleep(0.1)

    print(">>> All hardware checks passed!")
    RPi.GPIO.cleanup()
        
except KeyboardInterrupt:
    pixels.fill(0)
    RPi.GPIO.cleanup()
    print("\nKeyboardInterrupt - cleaned up GPIO resources.")
except Exception as e:
    pixels.fill(0)
    RPi.GPIO.cleanup()
    print(e) 
    print("\nCleaned up GPIO resources.")

   

