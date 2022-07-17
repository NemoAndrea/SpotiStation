import sys
import requests  # downloading image
from PIL import Image
from io import BytesIO

sys.path.append('/home/musicpi/rpi-rgb-led-matrix/bindings/python/rgbmatrix')
from rgbmatrix import RGBMatrix, RGBMatrixOptions


# see https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python 
# for more information about options and driving the display

class MusicDisplay:
    def __init__(self, width, height):
        self.width = width
        self.height= height

        options = RGBMatrixOptions()
        options.rows = int(height)
        options.cols = int(width)
        options.gpio_slowdown = 3
        options.hardware_mapping = 'adafruit-hat-pwm'
        # https://github.com/hzeller/rpi-rgb-led-matrix#panel-arrangement
        options.pixel_mapper_config = 'Rotate:270'  
        options.brightness = 35  # in percent
        options.limit_refresh_rate_hz  = 60 

        self.display = RGBMatrix(options = options)


    def set_background_image(self, spotipy_item):
        url = spotipy_item['item']['album']["images"][0]["url"]
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image.thumbnail((self.width, self.height), Image.ANTIALIAS)
        self.display.SetImage(image.convert('RGB'))


    def fade_background():
        print("TODO")