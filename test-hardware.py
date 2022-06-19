import board  # NOTE: this means we use GPIO.BCM mode
from digitalio import DigitalInOut, Pull
import time
import RPi.GPIO

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

try:
    print(">>> Starting hardware checks...")

    checks = {"button_main": False, "slider_main": False}

    """
    Play/Pause button check
    """

    print("1. Press and hold down the play/pause button for at least 1 second and RELEASE")
    button_held = 0  # number of loop cycles the button has been (continously) pressed down
    while not checks["button_main"]:    
        if playpause_button.value == False:  # button is pressed down
            if button_held == 0:
                print("\n play/pause pressed")
                still_pressed = True
            else:
                print("... holding ...")
            button_held += 1
        else: 
            if button_held > 20:
                print("> Button check OK! - Play Pause Button")
                checks["button_main"] = True
            elif button_held > 0:
                print("Button released, but too fast! Be sure to hold it down for (at least) 1 second and then release.")
            button_held = 0
        time.sleep(0.05)


    """
    NeoSlider check
    """
    def potentiometer_to_color(value):
        """Scale the potentiometer values (0-1023) to the colorwheel values (0-255)."""
        return min(value, 1023) / 1023 * 255


    while True:
        print(potentiometer.value)
        # Fill the pixels a color based on the position of the potentiometer.
        pixels.fill(colorwheel(potentiometer_to_color(potentiometer.value)))
        time.sleep(0.05)
        
except KeyboardInterrupt:
    pixels.fill(0)
    RPi.GPIO.cleanup()
    print("\nCleaned up GPIO resources.")
   

