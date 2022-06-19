# minimal-music-player
Minimalist music player built around open hardware design intended to be extremely simple in operation. Intended to be usable by people with disabilities.



### Setup

We are assuming the code is run from a raspberry pi running `Raspberry Pi OS Lite` and that the raspberry pi has some way to connect to WiFi. Bluetooth connectivity is required if speakers are to be driven wirelessly (as opposed to via 3.5mm jack of the Pi).

Raspbian OS Lite comes with A Python 3 installation, and a GPIO library, so that will be pre-installed. But we will still need to get `pip` installed. 

```
sudo apt-get install python3-pip -y
```

To drive the **Adafruit NeoSlider** we will need to get the appropriate package

```
pip3 install adafruit-circuitpython-seesaw
```

In addition, we will need to activate the `I2C` (hardware) interface on the Pi (disabled by default). We can do this in the configuration of the raspberry pi. 

```
sudo raspi-config
```

In the configuration menu, go to `Display Options`, enable `I2C` and close out of the menu. 
