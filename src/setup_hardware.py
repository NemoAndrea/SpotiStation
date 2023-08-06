import board 
from digitalio import DigitalInOut, Pull
from enum import Enum, auto


from display import MusicDisplay

class MusicPlayer:
    def __init__(self):
        buttons = initialise_buttons()
        self.playpause = buttons[0]
        self.sidebutton_1 = buttons[1]
        self.sidebutton_2 = buttons[2]
        self.backbutton_1 = buttons[3]
        self.backbutton_2 = buttons[4]

        # Set up display - ROOT is dropped here, be careful about removing/reordering for security.
        self.display = MusicDisplay(64, 64)  # needs root privileges, but those are dropped after this function 
        # set the boot screen image 
        self.display.set_image_from_file("./media/interface/splash_screen.png")  

        # current playback device (normally the spotistation itself, but could be another device
        # connected to spotify API)
        self.playback_device = None  
        self.last_playback= None  # we keep track of this in case the API times out
        self.state = PlayerState.ACTIVE

    def any_button_got_pressed(self):
        '''checks if any of the buttons have been pressed.
        
        Functionality is the same as got_pressed for PlayerButton, and hence must be called in a loop
        for it to work properly.'''
        return any([
             self.playpause.got_pressed(),
             self.sidebutton_1.got_pressed(),
             self.sidebutton_2.got_pressed(),
             self.backbutton_2.got_pressed(),
             self.backbutton_1.got_pressed()
        ])
        

class PlayerState(Enum):
    ACTIVE = auto()
    QUIET = auto()
    LOCKED = auto()



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
