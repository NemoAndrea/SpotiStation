# Software Setup 

### 🚧 IN NEED OF REVIEW: this setup guide is currently purely functional, it needs to be rewritten for new users.

We are assuming the code is run from a raspberry pi running `Raspberry Pi OS Lite` and that the raspberry pi has some way to connect to Wi-Fi. Bluetooth connectivity is required if speakers are to be driven wirelessly (as opposed to via 3.5mm jack of the Pi).

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

For reasons that are not entirely clear to me, the NeoSlider does not work well with the default i2c bus frequency. It will randomly lock up the bus, or read values beyond it's normal valid range (0,1023). To fix this, we need to [change the i2c bus frequency to 400kHz](https://gist.github.com/ribasco/c22ab6b791e681800df47dd0a46c7c3a) on the Pi. 

1. Open system config `sudo nano /boot/config.txt`. Be careful not to mess anything up there.
2. Find the line `dtparam=i2c_arm=on` 
3. Add `i2c_arm_baudrate=400000` to the **same** line (comma separated), so it now reads `dtparam=i2c_arm=on,i2c_arm_baudrate=400000`
4. Save and exit `nano` (ctrl s, ctrl x)
5. Reboot (maybe even power cycle)

We will also need to be able to control the system volume, for which we will need another python package

```
pip3 install pyalsaaudio
```

### TODO: setup RGB panel

Solder jumper between 4 and 18, picture quality is not good enough without. Analog audio (3.5mm jack or HDMI) will be disabled, but Bluetooth audio is fine.

Enable the CPU core reservation (pi 3 and 4) with `isolcpus=3`

### Setup - Spotify (background)

To stream Spotify, we will use [spotifyd](https://github.com/Spotifyd). We need to install the latest release (for ARMv6), as per the instructions laid out on [their raspberry pi guide page](https://spotifyd.github.io/spotifyd/installation/Raspberry-Pi.html). For completeness I will cover the contents of their page here. If in doubt, follow the instructions on `spotifyd`'s page.  Make sure you get the latest release. At the time of writing, the latest version is `0.3.3`, so we install that with:

```
wget https://github.com/Spotifyd/spotifyd/releases/download/v0.3.3/spotifyd-linux-armv6-slim.tar.gz
```

> This setup assumes you are downloading this into your home directory on the raspberry pi. (type `cd` to go there if you are not sure)

The command above will give you a `tar.gz` archive, which you can unpack with

```
tar -xf <name of downloaded file>.tar.gz
```

Now we need to create a config file where we set up`spotifyd` to our liking.

```
mkdir ~/.config/spotifyd/
```

> It may be the case that you do not have a `.config` folder on your Pi. If so, just create an empty one by `mkdir ~/.config`

and again we must create and edit this file in `nano` (use `nano ~/.config/spotifyd/spotifyd.conf`) and paste the following information into it:

```toml
[global]
username = "USER"
password = "PASS"
backend = "alsa"
#device = alsa_audio_device # Given by `aplay -L`
mixer = "PCM"
volume-controller = "alsa" # or alsa_linear, or softvol
#onevent = command_run_on_playback_event
device_name = "name_in_spotify_connect"
bitrate = 96|160|320
cache_path = "cache_directory"
volume-normalisation = true
normalisation-pregain = -10
```

Where of course the following items have to be changed to your own credentials/requirements:

* username
* password
* bitrate (choose 320)

* device name (I suggest `Music_Pi`. *do not use spaces in the name*)
* (optional) device - uncomment this line (remove `#`) and set a device if you want to select a specific output for audio (e.g. HDMI/Bluetooth)

> If you use Facebook login for Spotify, you will need to go to Spotify's website and look at your account settings. You should be able to find a numerical username. This is the username you will want to use for `spotifyd`. As for the password, you will probably have to request a 'device password' somewhere in the account settings in Spotify. This takes less than 3 minutes.

If you have filled in your credentials, it would be good to check if its all working before making the daemon start up automatically. Give it a whirl by typing `~/spotifyd --no-daemon`. **You should get some information about the information it is using and if it managed to make a connection. If you go to Spotify on your phone or pc, the device should now be listed in playback devices (as 'Music_Pi')!**

If everything worked up to this point, it is time to set `spotifyd` to start when the raspberry pi is booted. That way we always have it running and ready to play! Let's make a service file for `systemctl` to run.

```bash
mkdir -p ~/.config/systemd/user/
nano ~/.config/systemd/user/spotifyd.service
```

This will open the text editor `nano`. You  need to copy the contents of [github.com/Spotifyd/spotifyd/blob/master/contrib/spotifyd.service](https://github.com/Spotifyd/spotifyd/blob/master/contrib/spotifyd.service) into it. As before, use the most up-to-date version that is found at that URL. For completeness, this is the version I used:

```toml
[Unit]
Description=A spotify playing daemon
Documentation=https://github.com/Spotifyd/spotifyd
Wants=sound.target
After=sound.target
Wants=network-online.target
After=network-online.target

[Service]
ExecStart=<path to where you unzipped spotifyd - e.g. /home/<username>/spotifyd> --no-daemon
Restart=always
RestartSec=12

[Install]
WantedBy=default.target
```

And then we can run `systemctl --user daemon-reload`. And then give the background process a test run with `systemctl --user start spotifyd.service`. Check in Spotify if the raspberry pi showed up in playback devices after running that command.

If it's working, all we need to do is ensure this runs on startup. This is simple with the two following commands:

```bash
sudo loginctl enable-linger <username>
systemctl --user enable spotifyd.service
```

Let's do one final check if its all set up right: shut down your raspberry pi (`sudo shutdown -h now`) and the raspberry pi should disappear from Spotify devices after a short while. Now start up the raspberry pi and see if it shows up in Spotify devices automatically!

### Setup - Spotify (API control)

While `spotifyd` actually handles the audio streaming, it does not control playback. Playback control and playlist selection etc is done via the Spotify API. Luckily, there is a python package for this [called spotipy](https://pypi.org/project/spotipy/). Let's install it

```
pip3 install spotipy
```

We need to get credentials for the api, which we can realise by making an 'app' in the [spotify developer bashboard](https://developer.spotify.com/dashboard/applications). Go to the dashboard, add  a new app, and from that new app get the `client id` and the `client secret` and `redirect url`.

> Redirect url is best set to something local; I suggest `https://localhost:8888/spotipycode`. It doesn't matter. You will need to set this in the Spotify dashboard in your app under the app-specific settings.

We will put these credentials in environment variables as one would not want to have this included in the repository.

```
export SPOTIPY_CLIENT_ID='your-spotify-client-id'
export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
export SPOTIPY_REDIRECT_URI='your-app-redirect-url'
```

then run `test_spotipy.py` it will generate a .cache file in the current directory.

Now you can use 

``` python
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth())
```

and use it as you would expect

## Setup - Bluetooth speaker

Apparently you cannot use Bluetooth and Wi-Fi at the same time on a RPi with the built-in system so a dongle is needed. Let's use  a dongle for Bluetooth and disable the internal one in `/boot/config.txt,`.

```
dtoverlay=pi3-disable-bt-overlay
```

Apparently, `raspbian OS lite` does not come with all the bits and pieces needed to connect to Bluetooth speakers. Luckily, [others have treaded before](https://www.okdo.com/project/set-up-a-bluetooth-speaker-with-a-raspberry-pi/).  For whatever reason, `pulseaudio` is  required for this.  Let's install it by

```
sudo apt install pulseaudio-module-bluetooth
```

We also need to change some permissions of our main user account (find it by typing `who` in terminal). You will have chosen this name when you generated a Raspbian OS installation image.

```
sudo usermod -a -G bluetooth <useraccount>
```

And reboot the Raspberry Pi (`sudo reboot`)

Now we start connecting to the speaker. First we must use the `bluetoothctl` command to be brought into a separate CLI. Turn on your Bluetooth device, and **make sure it is in pairing mode (if connecting for the first time)**. In this new CLI, type

```
scan on
```

wait for your speaker to show up (your speaker should be listed by name - give it a minute to scan for devices). Once you see your speaker name, we can stop the scanning  by `scan off`. Now we must make a note of the *Bluetooth MAC address* (e.g. 00:11:22:33:FF:EE). Then, with the Bluetooth speaker in pairing mode, enter

```
pair <MAC adress>
trust <MAC adress>
```

Now we are paired (**but not connected**) with the device - this is the one-time setup part.  To actually connect, type

```
connect <MAC adress
```

## Setup - run music player as service

We need to ensure the music player runs as a service upon startup. We use the same approach as before, but specify that we want to run this as root, but still as a user.

> I must admit here that I am not entirely too sure how this whole root thing works, as a normal systemctl process (in /lib/) would make more sense, but that has no access to the  python environment so I am just going with what is below - which seems to work fine.

```
nano ~/.config/systemd/user/rpi-spotiplayer.service
```

We make the contents of the file the following:

```
[Unit]
Description=A python spotify music player service
Requisite=spotifyd.service
After=spotifyd.service

[Service]
Type=simple
WorkingDirectory=/home/musicpi/minimal-music-player
ExecStart=/usr/bin/sudo -E /usr/bin/python /home/musicpi/minimal-music-player/src/start_player.py
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
```

> We set it such that it will restart automatically when the python script exits (which will only happen in case of an error)

We make it active via: 

```
 sudo chmod 644 ~/.config/systemd/user/rpi-spotiplayer.service
```

And then we update our `systemctl` process by running `sudo systemctl --user daemon-reload`. As before, it is good to see if it works before making it run on start-up by running `systemctl --user start rpi-spotiplayer.service`. That should start the player as normal after few seconds. 

If that all seems to work well, stop the process and set it up for running at boot:

```
systemctl --user enable rpi-spotiplayer.service
```

### .bashrc setup

Nice to have, but not needed

```bash
alias startplayer='systemctl --user start rpi-spotiplayer.service'
alias stopplayer='systemctl --user stop rpi-spotiplayer.service'
alias restartplayer='systemctl --user restart rpi-spotiplayer.service'
# in case you want to manually start the player and observe the log in terminal via SSH
# make sure the service is stopped and that you are in the repository directory
alias startplayer_manual='sudo -E python ~/minimal-music-player/src/start_player.py'
```

