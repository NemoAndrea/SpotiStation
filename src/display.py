import sys
import requests  # downloading image
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import time
import math
import os  # needed to drop root privs

sys.path.append('/home/musicpi/rpi-rgb-led-matrix/bindings/python/rgbmatrix')
from rgbmatrix import RGBMatrix, RGBMatrixOptions


# see https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python 
# for more information about options and driving the display

class MusicDisplay:
    '''RGB panel object with overlay support'''
    def __init__(self, width, height):
        self.width = width
        self.height= height
        self.coverart = Image.new('RGB', (width, height)) 
        self.overlay= Image.new('RGBA', (width, height)) 
        # we use the silkscreen font by Jason Kottke, which is meant to be used at 
        # 8pt (or multiples of that)
        self.font = ImageFont.truetype('/home/musicpi/minimal-music-player/media/slkscr.ttf',8)  

        options = RGBMatrixOptions()
        options.rows = int(height)
        options.cols = int(width)
        options.gpio_slowdown = 3
        options.hardware_mapping = 'adafruit-hat-pwm'
        # https://github.com/hzeller/rpi-rgb-led-matrix#panel-arrangement
        options.pixel_mapper_config = 'Rotate:270'  
        options.brightness = 35  # in percent
        options.limit_refresh_rate_hz  = 60 
        # We disable the feature that automatically drops root privs (as it sets uid=1)
        # which means all your python imports get borked. We MANUALLY set it back to 1000
        # it is important that we ensure we drop root.
        options.drop_privileges = False  

        self.display = RGBMatrix(options = options)
        os.setuid(1000)  # set to default user (which we assume is at uid 1000, default for raspbberry pi os)
        


    def set_coverart(self, spotipy_item):
        url = spotipy_item['item']['album']["images"][0]["url"]
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image.thumbnail((self.width, self.height), Image.ANTIALIAS)
        self.coverart = image.convert('RGB')
        self.display.SetImage(self.coverart)
        self.overlay = None  # reset the overlay

    def set_display_mode(self, mode):
        if mode == "paused":
            self.set_image_overlay("/home/musicpi/minimal-music-player/interface/paused.png")
        elif mode == "next_track":
            self.set_image_overlay("/home/musicpi/minimal-music-player/interface/next_track.png")
        else:
            self.display.SetImage(self.coverart)  # just use whatever the current song image is 
            self.overlay = None  # reset overlay

    # TODO load these into memory
    def set_image_overlay(self, overlay_file, dimming=0.9):
        print(f"setting overlay: {overlay_file}")

        self.overlay = Image.open(overlay_file)  # load the overlay
        composite = self.coverart.copy()  # make a copy of the coverart
        composite = Image.eval(composite, (lambda pix: pix*(1-dimming)))  # lower intensity
        composite.paste(self.overlay, (0,0), self.overlay)  # add overlay on top of coverart
        self.display.SetImage(composite)


    # simple display image from file function for e.g. splash screen	
    def set_image_from_file(self, path):
        self.coverart = Image.open(path) 
        self.display.SetImage(self.coverart.convert('RGB'))

    
    def add_text_to_overlay(self, text, location, fill=(255,255,255,255), clear=False, center=True):        
        draw = ImageDraw.Draw(self.overlay)
        if clear: 
            draw.rectangle((0,0,self.width, self.height), fill=(0,0,0,0))

        # determine initial location of first letter (center alignment)
        if center:
            offset = -math.floor(sum([self.font.getsize(letter)[0]-1 for letter in text])/2) 
        else:
            offset = 0
        for i, letter in enumerate(text):
            basewidth, _ = self.font.getsize(letter)
            letter_loc = (location[0]+offset, location[1])
            draw.text(letter_loc, letter, anchor="lm", font=self.font, fill=fill)  
            offset += basewidth-1  # update location for next letter, we reduce the native kerning by 1px     
            

    def add_overlay_to_display(self, dimming):
        composite = self.coverart.copy()  # make a copy of the coverart
        composite = Image.eval(composite, (lambda pix: pix*(1-dimming)))  # lower intensity
        composite.paste(self.overlay, (0,0), self.overlay)  # add overlay on top of coverart
        self.display.SetImage(composite)

    

    def fade_background(self, factor=0.1):
        '''Nondestructively drop the intensity of the image
        
        This decreases the intensity of the image on screen, without changing internal images,
        meaning that when a new image is drawn this will be reset'''
        print("fading background")
        self.display.SetImage(Image.eval(self.coverart, (lambda pix: pix*factor)))



class DisplayOverlayTimer:
    '''Simple class that can handle the time an overlay should be displayed

    Some overlay images (e.g. next track) should only be shown for a short time, and then go back to
    coverart.

    The reason why this exsists (and not just a time.sleep(x)) is that I don't want to hold uo
    the other interface buttons. Maybe subprocess could work for that too but this should do the trick'''
    def __init__(self):
        self.anchortime = time.time()
        # if activetime is None the timer will always return false, so that effectively disables it
        self.activetime = None  

    def start_timer(self, activetime):
        self.anchortime = time.time()
        self.activetime = activetime

    def overlay_expired(self):
        if self.activetime:  # to disable the timer you can set anchortime to be None
            if time.time() - self.anchortime > self.activetime:
                return True
        return False
