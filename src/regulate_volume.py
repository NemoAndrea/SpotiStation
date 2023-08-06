import time

import alsaaudio

import board 
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel


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
        

## set up the hardware

neoslider = Seesaw(board.I2C(), 0x30)
potentiometer = AnalogInput(neoslider, 18)
ledpixel = neopixel.NeoPixel(neoslider, 14, 4)

slider = VolumeSlider(potentiometer, ledpixel)

print("i2c slider setup succesful")

## get ready to talk to system volume settings

audio = alsaaudio.Mixer()  # default settings should work
volume = audio.getvolume()[0]  # intialise volume [0-100]

print("alsa-audio connection ok")

print(f"Playback mute state: {audio.getmute()}")
print(f"Mixer ID : {audio.mixerid()}")


## main loop checking for updates in slider state

while True:
    time.sleep(0.1)  # don't need to check more than 10 times per second
    slider_volume = int(slider.position()*100)
    if volume != slider_volume:
        print(f'setting volume to {slider_volume} (0-100)')
        audio.setvolume(slider_volume)
        print(f'system volume is at: {audio.getvolume()[0]}')
        volume = slider_volume