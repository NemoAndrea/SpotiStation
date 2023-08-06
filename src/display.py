import sys
import requests  # downloading image
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from datetime import datetime, timedelta
import math
import os  # needed to drop root privs
import logging

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
        # TODO: make this a relative link
        self.font = ImageFont.truetype('/home/musicpi/SpotiStation/media/slkscr.ttf',8)  
        self.timer = DisplayOverlayTimer()
        self.overlay_mode = None  # keep track of what kind of overlay we are using

        options = RGBMatrixOptions()
        options.rows = int(height)
        options.cols = int(width)
        options.gpio_slowdown = 3
        options.hardware_mapping = 'adafruit-hat-pwm'
        # https://github.com/hzeller/rpi-rgb-led-matrix#panel-arrangement
        options.pixel_mapper_config = 'Rotate:270'  
        options.brightness = 50  # in percent
        options.limit_refresh_rate_hz  = 60 
        # We disable the feature that automatically drops root privs (as it sets uid=1)
        # which means all your python imports get borked. We MANUALLY set it back to 1000
        # it is important that we ensure we drop root.
        options.drop_privileges = False  

        self.display = RGBMatrix(options = options)
        os.setuid(1000)  # set to default user (which we assume is at uid 1000, default for raspbberry pi os)
        
    def set_coverart(self, spotipy_item):        
        url = spotipy_item['item']['album']["images"][0]["url"]
        logging.getLogger().debug(f"[display] setting coverart url: {url}")
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image.thumbnail((self.width, self.height), Image.ANTIALIAS)
        self.coverart = image.convert('RGB')
        self.display.SetImage(self.coverart)
        self.overlay = Image.new('RGBA', (self.width, self.height))  # reset the overlay

    # TODO: maybe just use mode string to fetch file
    def set_display_mode(self, mode):
        '''Display an image on disk as overlay
        
        Load an image on disk as overlay. Meant for important overlays. Will reset any active 
        timers on the display.'''

        logging.getLogger().debug(f"[display] setting inferface image: {mode}")

        # reset timer (no situation where you set a timer, add a display overlay and STILL want to keep overlay)
        self.timer.reset_timer()  
        # load overlay image
        self.overlay_mode = mode
        if mode == "paused":
            self.set_image_overlay("./media/interface/paused.png")
        elif mode == "next_track":
            self.set_image_overlay("./media/interface/next_track.png")
        elif mode == "next_playlist":
            self.set_image_overlay("./media/interface/next_playlist.png")
        elif mode == "no_wifi":
            self.set_image_overlay("./media/interface/no_wifi.png")
        elif mode == "no_bluetooth_audio":
            self.set_image_overlay("./media/interface/no_bluetooth.png")
        elif mode == "no_spotifyd":
            self.set_image_overlay("./media/interface/no_spotifyd.png")
        elif mode == "quiet_mode":
            self.set_image_overlay("./media/interface/quiet_mode.png")
        elif mode == "lock_mode":
            self.set_image_overlay("./media/interface/lock_mode.png")
        else:
            self.display.SetImage(self.coverart)  # just use whatever the current song image is 
            self.overlay = Image.new('RGBA', (self.width, self.height))   # reset overlay
            self.overlay_mode = None

    def reset_overlay(self):
        '''Remove any overlay from display, and show only coverart'''
        logging.getLogger().debug(f"[display] reset overlay")
        self.overlay = Image.new('RGBA', (self.width, self.height))  # reset overlay
        self.add_overlay_to_display(dimming=0)  # without overlay this just draws self.coverart


    # TODO load these into memory
    def set_image_overlay(self, overlay_file, dimming=0.9):
        #print(f"setting overlay: {overlay_file}")
        self.overlay = Image.open(overlay_file)  # load the overlay
        composite = self.coverart.copy()  # make a copy of the coverart
        composite = Image.eval(composite, (lambda pix: pix*(1-dimming)))  # lower intensity
        composite.paste(self.overlay, (0,0), self.overlay)  # add overlay on top of coverart
        self.display.SetImage(composite)


    # simple display image from file function for e.g. splash screen	
    def set_image_from_file(self, path):
        logging.getLogger().debug(f"[display] setting image from path: {path}")
        self.coverart = Image.open(path) 
        self.display.SetImage(self.coverart.convert('RGB'))

    
    def add_text_to_overlay(self, text, location, fill=(255,255,255,255), clear=False, center=True):     
        logging.getLogger().debug(f"[display] add text '{text}' to overlay at location {location}") 
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
        '''Add overlay to coverart image. 
        
        For displaying custom overlay items (e.g. text). Has bulk dimming parameter.
        for darkening the background image.'''
        composite = self.coverart.copy()  # make a copy of the coverart
        composite = Image.eval(composite, (lambda pix: pix*(1-dimming)))  # lower intensity
        composite.paste(self.overlay, (0,0), self.overlay)  # add overlay on top of coverart
        self.display.SetImage(composite)

    def add_overlay_to_display_falloff(self, dimming, offset, length, top=True):
        '''Add overlay to coverart image. 
        
        For displaying custom overlay items (e.g. text). Has graduated (linear) falloff
        of intensity. Bigger `length` means a shallower gradient.'''
        gradient = Image.new('RGBA', (self.width, self.height))
        for i in range(self.height):
            # if top=False, we put the gradient from the bottom towards top.
            i_coord = i if top else self.height-i
            if i < offset:
                for j in range (self.width):
                    gradient.putpixel((j,i_coord), (0,0,0,int(255*dimming)))
            else:
                intensity = int(dimming*255*(1-(i-offset)/length))
                if intensity > 0:
                    for j in range (self.width):
                        gradient.putpixel((j,i_coord), (0,0,0,intensity))
                else: 
                    # opacity < 0, no more need to compute any further iterations
                    break        
        
        composite = self.coverart.copy()  # make a copy of the coverart
        # exponential falloff (from top of image) with decay exponent
        composite.paste(gradient, (0,0), gradient)  # add overlay on top of coverart
        composite.paste(self.overlay, (0,0), self.overlay)  # add overlay on top of coverart
        self.display.SetImage(composite)

    def scale_intensity(self, factor=0.1):
        '''Nondestructively drop the intensity of the image
        
        This decreases the intensity of the image on screen, without changing internal images,
        meaning that when a new image is drawn this will be reset'''
        self.display.SetImage(Image.eval(self.coverart, (lambda pix: pix*factor)))



class DisplayOverlayTimer:
    '''Simple class that can handle the time an overlay should be displayed

    Some overlay images (e.g. next track) should only be shown for a short time, and then go back to
    coverart.

    The reason why this exsists (and not just a time.sleep(x)) is that I don't want to hold uo
    the other interface buttons. Maybe subprocess could work for that too but this should do the trick'''
    def __init__(self):
        self.anchortime = datetime.now()
        # if timelimit is None the timer will always return false, so that effectively disables it
        self.timelimit = None  

    def start_timer(self, duration):
        self.anchortime = datetime.now()
        self.timelimit = timedelta(seconds=duration)

    def reset_timer(self):
        self.timelimit = None

    def is_enabled(self):
        '''Is timer enabled or is it reset'''
        if self.timelimit:
            return True
        else:
            return False

    def is_expired(self):        
        '''Check if a started timer has completed
        
        Function will return False if (1) the timer is not set up or (2) if it is still active.
        If the timer is expired and this function is called, the timer will return True once, and then
        reset it self. So you can use it to do a display action exactly once after the timer expires
        
        e.g. 
        ```python        
        display.set_to_red_color()
        while True:
            if cool_button.is_pressed():
                display.set_to_green_color()  # do something with display that you want active for 5 sec
                display.timer.start_timer(5)
            
            if display.timer.is_expired():
                display.set_to_red_color()  # do something with display (e.g. reset to original state), will only be called once
        ```
        '''
        if self.timelimit:  # to disable the timer you can set timelimit to be None
            if datetime.now() - self.anchortime > self.timelimit:
                self.reset_timer()  # reset the timer, next time it is called it will return False until a new timer is started
                return True
        return False
