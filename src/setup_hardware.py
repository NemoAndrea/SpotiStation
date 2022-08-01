import board 
from digitalio import DigitalInOut, Pull

from display import MusicDisplay

class MusicPlayer:
    def __init__(self):
        buttons = initialise_buttons()
        self.playpause = buttons[0]
        self.sidebutton_1 = buttons[1]
        self.sidebutton_2 = buttons[2]
        self.backbutton_1 = buttons[3]
        self.backbutton_2 = buttons[4]
        self.volumeslider = intialise_slider()

        # Set up display - ROOT is dropped here, be careful about removing/reordering for security.
        self.display = MusicDisplay(64, 64)  # needs root privileges, but those are dropped after this function 
        # set the boot screen image TODO avoid abs path 
        self.display.set_image_from_file("/home/musicpi/minimal-music-player/interface/splash_screen.png")  


def initialise_buttons():
    # play pause button - wired to SPI0_MOSI
    playpause_button = DigitalInOut(board.MOSI)
    playpause_button.pull = Pull.UP

    # back button 1 and 2
    back_button_1 = DigitalInOut(board.MISO)
    back_button_1.pull = Pull.UP
    back_button_2 = DigitalInOut(board.SCLK)
    back_button_2.pull = Pull.UP

    # side button 1 and 2
    side_button_1 = DigitalInOut(board.CE0)
    side_button_1.pull = Pull.UP
    side_button_2 = DigitalInOut(board.CE1)
    side_button_2.pull = Pull.UP

    return [
        PlayerButton(playpause_button),
        PlayerButton(side_button_1), 
        PlayerButton(side_button_2),
        PlayerButton(back_button_1),
        PlayerButton(back_button_2),
    ]

class PlayerButton:
    def __init__(self, button):
        self.button = button
        self.last_value = button.value
    
    '''
    Determine if button just got pressed

    This is a convenience function that only returns true when the button is pressed
    but was not yet pressed (held down) before. If the button is not pressed it will always
    return false. To access the raw button value just use obj.button.value instead of obj.got_pressed()
    '''
    def got_pressed(self):
        # button is physically pressed AND it was not pressed before
        if self.button.value == False and self.last_value != False:  
            self.last_value = self.button.value
            return True
        else:
            self.last_value = self.button.value
            return False



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
            