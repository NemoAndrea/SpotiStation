# 👷 Hardware assembly

### 📜 List of components

To build the SpotiStation, you will need to purchase the following items (or find alternatives).

| Vendor   | Item                                                         | Amount | vendor ID            | cost, total (euro) |
| -------- | ------------------------------------------------------------ | ------ | -------------------- | ------------------ |
| Digi-key | Raspberry Pi 3*                                              | 1      | 2648-RASPBERRYPI3-ND | 35                 |
| Adafruit | 64x64 RGB LED Matrix - 2.5mm Pitch                           | 1      | 3649                 | 53                 |
| Adafruit | Black LED Diffusion Acrylic Panel 12" x 12"                  | 1      | 4594                 | 9.6                |
| Adafruit | NeoKey Socket Breakout for Mechanical Key Switches with NeoPixel | 5      | 4978                 | 8.4                |
| Adafruit | Adafruit NeoSlider I2C QT Slide Potentiometer                | 1      | 5295                 | 9.6                |
| Adafruit | 5V 10A switching power supply                                | 1      | 658                  | 28.8               |
| Adafruit | Relegendable Plastic Keycaps for MX Compatible Switches 10 pack | 1      | 5039                 | 4.76               |
| Adafruit | Bluetooth 4.0 USB Module (v2.1 Back-Compatible)              | 1      | 1327                 | 12                 |
| Adafruit | Any MX-style keyswitch, ideally with heavy spring**          | 5      | 5124                 | 5                  |
| Adafruit | Black Nylon Machine Screw and Stand-off Set – M2.5 Thread*** | 1      | 3299                 | 17                 |
| Adafruit | STEMMA QT / Qwiic JST SH 4-pin Cable with Premium Female Sockets - 150mm   Long | 1      | 4397                 | 1                  |
| Adafruit | 2.54mm 0.1" Pitch 12-pin Jumper Cable - 20cm long            | 1      | 4942                 | 2                  |

Total: **186 Euro**

*The hardware has been tested with a Raspberry Pi 3, but any newer version should also work fine. I suspect a Raspberry Pi Zero 2W might also work.

**you can get any variety (clicky, tactile or linear), but in my opinion a linear is most appropriate, and especially for the main play/pause button it would be good to have a switch that has a heavy spring (force).

***If you already have a set at home, then of course there is no need to get a full box. You will need 12 `M2.5` screws (8x `6mm`, 4x `10mm`) and matching nuts.

In addition to the items above you will need:

1. 8x `M4` `16mm` bolts and nuts.
2. 8x `M3` `12mm` bolts.
3. The 3D printed parts. Printable `stl` files can be found in [the 3D printing directory](../3D-printing/stl), and sent to a commercial 3D printing company if you do not have a printer yourself. See the assembly section below.
4. A set of Bluetooth enabled speakers. This is totally up to you, but I would **strongly** suggest you chose a (set of) speakers that are **powered from mains** and not from a battery. An example would be the [Logitech Z207](https://www.logitech.com/de-de/products/speakers/z207-stereo-speakers-bluetooth.980-001295.html), which goes for about 45 euros.

### 🧰 Tools

To assemble your own SpotiStation, you will need

* Small screwdriver to tighten down `M2.5`  screws
* Medium/large screwdriver to tighten down `M4` and `M3` screws
* Soldering iron and solder, to solder some headers onto components

### 🖨️ 3D printing

There are 4 large parts that need to be printed, and 2 smaller ones. I suggest you pick two different colours to print with for visual interest, but can pick whatever colour you like of course.

All parts can be printed without supports on an FDM printer, and all parts fit* on the buildplate of small 3D printers such as a Prusa Mini+. Print them as oriented in the `.stl`

The `case-top.stl` file *can* be printed without supports, but it is probably best to add some supports as depicted below.

![](../media/prusaslicer_top_box_supports.JPG)

*for the largest print it is important that you disable perimeters and purge lines on a Prusa Mini+ as those end up outside the print volume.

### 👷 Assembly

## 🚧 Under construction

Where is your hardhat? This is not safe, please leave this markdown doc!