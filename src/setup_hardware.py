import board 
from digitalio import DigitalInOut, Pull

def initialise_buttons():
    # play pause button - wired to SPI0_MOSI
    playpause_button = DigitalInOut(board.MOSI)
    playpause_button.pull = Pull.UP

    return playpause_button


from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel

def intialise_slider():
    neoslider = Seesaw(board.I2C(), 0x30)
    potentiometer = AnalogInput(neoslider, 18)
    ledpixel = neopixel.NeoPixel(neoslider, 14, 4)

    return VolumeSlider(potentiometer, ledpixel)


class VolumeSlider:
    def __init__(self, potentiometer, neopixel):
        self.slider = potentiometer
        self.led = neopixel

    '''
    Return value of neoslider between 0-1 or None.
    
    Careful: calling `slider.value` in too quick succession seems to result
    in serious errors that require a RPi restart.

    On the RPi the slider returns values outside the spec range [0, 1023]
    this is probably something wrong in the hardware or rpi i2c but we will 
    just have to deal with it by returning None and then handling it. 

    setting RPi i2c bus frequency to 400kHz seems to be a solution, but better be 
    safe than sorry and make sure we can handle an edge case
    '''
    def position(self):
        value = self.slider.value

        if value > 1023:  
            return None
        else:
            return value / 1023  # we will return float between [0, 1]
            