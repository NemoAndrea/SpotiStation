# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
NeoSlider NeoPixel Rainbow Demo
"""
import board
print(dir(board))
print(type(int(board.MOSI)))
# from rainbowio import colorwheel
# from adafruit_seesaw.seesaw import Seesaw
# from adafruit_seesaw.analoginput import AnalogInput
# from adafruit_seesaw import neopixel

# # NeoSlider Setup
# neoslider = Seesaw(board.I2C(), 0x30)
# potentiometer = AnalogInput(neoslider, 18)
# pixels = neopixel.NeoPixel(neoslider, 14, 4)


# def potentiometer_to_color(value):
#     """Scale the potentiometer values (0-1023) to the colorwheel values (0-255)."""
#     return value / 1023 * 255


# while True:
#     print(potentiometer.value)
#     # Fill the pixels a color based on the position of the potentiometer.
#     pixels.fill(colorwheel(potentiometer_to_color(potentiometer.value)))
