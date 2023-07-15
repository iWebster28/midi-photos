"""
main.py
Interface midi controllers with Photos app on macOS.
Ian Webster
Dec 2022
"""

# Note: this is not an object-oriented approach, but rather a functional approach. 
# It is assumed that only ONE controller is connected to the computer at a time, to ONE instance of Photos.

import applescript
import mido
import pyautogui

from constants import *
from utils import *

# Globals
CONST_SCALE = None
X_OFFSET_SLIDER_MIDDLE = None

outport = None
slider_channel = 0
last_channel = None

# Enumeration where RIGHT = 1, LEFT = -1
class JogDirection:
    RIGHT = 1
    LEFT = -1

# Summary of Basic light sliders in Photos app according to AppleScript descriptions:

# Brilliance: slider "Adjust the properties of Light locally across this image" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Exposure: set value of slider "Adjust the overall lightness of the image" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Highlights: get position of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Shadows: set value of slider "Increase or decrease detail by lightening shadows" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Brightness: slider "Lighten or darken the mid tones" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" 
# Contrast: slider "Adjust the difference between light and dark tones" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Black Point: slider "Adjust the darkest tonal area of the image " of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"

# Accessibility descriptions of sliders referenced with AppleScript
# slider_ids = [
#     "Adjust the properties of Light locally across this image",
#     "Adjust the overall lightness of the image",
#     "Increase or decrease detail by darkening highlights",
#     "Increase or decrease detail by lightening shadows",
#     "Lighten or darken the mid tones",
#     "Adjust the difference between light and dark tones",
#     "Adjust the darkest tonal area of the image ",
# ]

# Map slider name in photos to midi channel name.
channel_names = [
    "Brilliance",
    "Exposure",
    "Highlights",
    "Shadows",
    "Brightness",
    "Contrast",
    "Black Point"
]

# Slider buffers 
hw_slider_buffer = [[0] for i in range(len(channel_names))] # Buffer 

# UI coordinates of sliders in photos.
slider_coords = [(None, None) for i in range(0, len(channel_names))]

def main():
    """Main function to run program.
    """
    global slider_channel
    global last_channel

    # Intialize Controller with Photos app data
    init_io()
    init_leds()
    get_init_slider_positions()
    set_slider_constants()

    slider_channel = 0
    last_channel = None
    set_init_slider_positions()

    # Start receiving MIDI events and translate to pyautogui actions
    event_handler_loop()
    return


### Main Event Handler Loop

def event_handler_loop() -> None:
    """Main event handler loop to handle midi events from controller.
    """
    global outport
    global slider_channel

    with mido.open_input(CONTROLLER_NAME) as port:
        for message in port:
            if DIAGNOSTIC_MODE:
                print(message)

            # Unused channel
            if hasattr(message, 'note'):
                if message.note == 7 or message.note == 15:
                    continue
            
            # Store channel for sliders; ignore jog wheel and buttons.
            if hasattr(message, 'channel'):
                # Unused channel
                if message.channel == 7 or slider_channel == 7:
                    continue

                if message.type != "control_change" and message.type != "note_on" and message.type != "note_off":
                    slider_channel = message.channel

            if hasattr(message, 'velocity'):
                if message.velocity != 0: # Prevent turning off lights
                    outport.send(message) # Light

            # Slider
            if hasattr(message, 'pitch'):
                pitch_handler(message)
            
            # Jog wheel
            if hasattr(message, 'control') and message.control == 60: 
                jog_handler(message)

            if not hasattr(message, 'note'):
                continue
            
            # Buttons
            if message.type == "note_on" and message.velocity == 127:
                button_handler(message)


### Message Handlers

def pitch_handler(message: mido.Message) -> None:
    """Handle pitch messages from controller.

    Args:
        message (mido.Message): Message from controller.
    """
    global slider_channel
    global last_channel
    global CONST_SCALE
    global X_OFFSET_SLIDER_MIDDLE

    # Deal with negative slider values
    neg = False
    pitch = message.pitch
    if pitch < 0:
        pitch *= -1
        neg = True

    # TODO MAYBE: just check lowest log_2(step_size) bits to see if == 0 first. Won't help in the case that the majority of slider vals are non divisible by step_size though.
    rem = (pitch % (QUANTIZE_MOD)) # Quantize to 2048-size steps
    if DIAGNOSTIC_MODE:
        print("rem:", rem)

    if message.pitch == HW_SLIDER_MAX: # max
        hw_slider_buffer[slider_channel].append(HW_SLIDER_MAX) # Since 8191 remainder for mod `any multiple of 8` is nonzero.
    else: # Quantize
        # hw_slider_buffer[slider_channel].append(message.pitch - rem if rem < 0 else message.pitch - rem)
        hw_slider_buffer[slider_channel].append(pitch - rem if neg == False else 0 - (pitch - rem))

    # Maintain buffer of size SLIDER_BUFFER_SIZE
    if len(hw_slider_buffer[slider_channel]) > SLIDER_BUFFER_SIZE:
        del hw_slider_buffer[slider_channel][0] # hw_slider_buffer[slider_channel] = hw_slider_buffer[slider_channel][1:4]

    # hw_slider_buffer[slider_channel][-1] = message.pitch # No quantizing. (very slow due to pyautogui calls.)

    if DIAGNOSTIC_MODE:
        print(hw_slider_buffer[slider_channel][-1]) # Diagnostic

    if slider_channel != last_channel: # First event, or touched another slider: move instead of dragging (move and clicking) the mouse.
        pyautogui.leftClick(slider_coords[slider_channel][0] + (CONST_SCALE * hw_slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + Y_OFFSET_SLIDER) # was moveTo
    
    elif (hw_slider_buffer[slider_channel][-1] != hw_slider_buffer[slider_channel][-2]) or \
        hw_slider_buffer[slider_channel][-1] == HW_SLIDER_MAX or \
        hw_slider_buffer[slider_channel][-1] == HW_SLIDER_MIN: # If at sample freq, or at min/max of given slider
        pyautogui.dragTo(slider_coords[slider_channel][0] + (CONST_SCALE * hw_slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + Y_OFFSET_SLIDER, button='left')

    update_track_led(slider_channel)

def jog_handler(message: mido.Message) -> None:
    """Handle jog wheel messages from controller.

    Args:
        message (mido.Message): Message from controller.
    """
    global slider_channel
    # Jog CW
    if message.value == 1:
        jog_handler_helper(JogDirection.RIGHT)
    # Jog CCW
    elif message.value == 65:
        jog_handler_helper(JogDirection.LEFT)

def jog_handler_helper(direction: JogDirection) -> None:
    """Helper to handle jog wheel changes.

    Args:
        direction (JogDirection): Indicates direction of jog wheel change. 

    Raises:
        Exception: If invalid JogDirection.
    """
    global slider_channel

    pitch_delta = 0

    if DIAGNOSTIC_MODE:
        print("ch:", slider_channel)
    # fine grain adjust
    if direction == JogDirection.RIGHT:
        pitch_delta = FINE_GRAIN_DELTA if not hw_slider_buffer[slider_channel][-1] >= HW_SLIDER_MAX else 0
    elif direction == JogDirection.LEFT:
        pitch_delta = -FINE_GRAIN_DELTA if not hw_slider_buffer[slider_channel][-1] <= HW_SLIDER_MIN else 0
    else:
        raise Exception("Incorrect direction call to jog_handler_helper().")
    
    if pitch_delta != 0:
        pyautogui.dragRel(direction, 0, button='left')
    hw_slider_buffer[slider_channel][-1] += pitch_delta
    if DIAGNOSTIC_MODE:
        print(f'fine grain CW {hw_slider_buffer[slider_channel][-1]}')


def button_handler(message: mido.Message) -> None:
    """Handle button messages from controller.

    Args:
        message (mido.Message): Message from controller.

    Raises:
        Exception: If applescript returns non-zero code.
    """
    if message.note in midi_note_to_applescript:
        r = applescript.tell.app('System Events', midi_note_to_applescript[message.note]) # prev photo (key code 124 == right arrow)
        if r.code != 0:
            raise Exception(f"Applescript returned {r.code}")
        
        if message.note == 1: # Rec button on slider 2
            set_init_slider_positions() # Apply the auto effects
    
    elif message.note - 8 <= 15 and message.note - 8 >= 0: # Solo track selects (to select a slider to edit again. Should point mouse to last value)
        slider_channel = message.note - 8
        if slider_channel == 7: # Unused slider_channel
            return
        pyautogui.moveTo(slider_coords[slider_channel][0] + (CONST_SCALE * hw_slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + Y_OFFSET_SLIDER)
        if DIAGNOSTIC_MODE:
            print(f"BUTTONS: last_channel: {last_channel}, channel: {slider_channel}")
        update_track_led(slider_channel)


### Initialization Functions

def init_io() -> None:
    """Initialize MIDI I/O.
    """
    global outport

    # List MIDI Inputs and Outputs (we just need inputs)
    print("MIDI Outputs: ")
    print(mido.get_output_names())
    print("MIDI Inputs: ")
    print(mido.get_input_names())

    # Init output (for sending LED messages)
    outport = mido.open_output('SAMSON Graphite MF8')

def init_leds() -> None:
    """Initialize LEDs on controller.
    """
    global outport
    
    # Initialize LEDs
    for i in range(0, 32):
        outport.send(mido.Message("note_on", note=i, velocity=0))
        outport.send(mido.Message("note_on", note=i, velocity=127))
    
    for i in [0, 1, 91, 92]:
        outport.send(mido.Message("note_on", note=i, velocity=0))
        outport.send(mido.Message("note_on", note=i, velocity=127))

def get_init_slider_positions() -> None:
    """Get the initial slider positions from the Photos app.

    Raises:
        Exception: If applescript returns non-zero code.
    """
    # Focus on the Photos editing pane
    result = applescript.tell.app("Photos", "activate") 
    if result.code != 0:
        raise Exception("Could not find Photos app window.")
        exit(1)

    # For every slider, get the initial slider position (x, y)
    i = 0
    while i < len(channel_names):
        r_position = get_applescript_slider_attribute_by_description(attribute="position", description=channel_names[i])

        # Could not find a slider element: is the edit pane open?
        if r_position.out == '':
            print("Could not hook into Photos window. Assuming Edit pane is closed. Trying to open Edit pane.")
            r_edit = click_applescript_item_by_attribute_and_by_description(attribute="button", description="Edit")
            continue
        
        if DIAGNOSTIC_MODE:
            print(r_position.out)

        print(f"Found slider {channel_names[i]} at position (x, y): {r_position.out}")
        slider_coords[i] = [int(val) for val in r_position.out.split(", ")] # Leftmost x-coord remains unchanged for all sliders as they are left-aligned in the Photos UI
        
        i += 1

    print(f"Found all sliders: {slider_coords}")

def set_slider_constants() -> None:
    """Set constants for slider UI automation.
    """
    global CONST_SCALE
    global X_OFFSET_SLIDER_MIDDLE

    r_size = get_applescript_slider_attribute_by_description(attribute="size", description=channel_names[0])
    SLIDER_WIDTH, SLIDER_HEIGHT = [int(val) for val in r_size.out.split(", ")]
    X_OFFSET_SLIDER_MIDDLE = SLIDER_WIDTH / 2
    CONST_SCALE = SLIDER_WIDTH / HW_SLIDER_RANGE # Each slider on the Graphite MF8 has a range -8192 to 8191


### Helper Functions 

def set_init_slider_positions() -> None:
    """Set the initial slider positions from the Photos app.
    """
    global CONST_SCALE
    global X_OFFSET_SLIDER_MIDDLE

    # Set init values of sliders
    # NOTE: Assume edit pane still open
    i = 0
    while i < len(channel_names):
        r_value = get_applescript_slider_attribute_by_description(attribute="value", description=channel_names[i])
        # Could not find a slider element: is the edit pane open?
        if r_value.out == '':
            print("Could not hook into Photos window. Assuming Edit pane is closed. Trying to open Edit pane.")
            r_edit = click_applescript_item_by_attribute_and_by_description(attribute="button", description="Edit")
            continue
        hw_slider_conv = (float(r_value.out) * (HW_SLIDER_RANGE + 1) / 2) # + slider_coords[i][0]
        hw_slider_buffer[i].append(hw_slider_conv)
        print(f"Found SW slider value for channel {channel_names[i]} with value: {r_value.out}")
        print(f"- Convert to HW slider value: {hw_slider_conv}")
        
        # Optional: show loading status on F1-F5 leds
        update_loading_led(int(((i / (len(channel_names) - 1)) * NUM_LOADING_LEDS)))
        
        i += 1

    # Arbitrarily move to starting position of first slider
    pyautogui.moveTo(slider_coords[0][0] + (CONST_SCALE * hw_slider_buffer[0][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[0][1] + Y_OFFSET_SLIDER)
    update_track_led(0)

def update_track_led(slider_channel: int) -> None:
    """Update the track LED to indicate which slider is active.

    Args:
        slider_channel (int): The slider channel to update the LED for.
    """
    global last_channel
    global outport
    # Turn the LED at `slider_channel` channel to GREEN.
    if last_channel != slider_channel:
        outport.send(mido.Message("note_on", note=slider_channel + 8, velocity=0)) # Turn off red (green state)
        if last_channel != None: 
            outport.send(mido.Message("note_on", note=last_channel + 8, velocity=127)) # Add red back (orange state)
    last_channel = slider_channel

def update_loading_led(load_state: int) -> None:
    """Update the loading LED to indicate the loading state.
    Ranges from midi note 54-58 (F1-F5 buttons) to indicate loading status.

    Args:
        load_state (int): The loading state to update the LED for. EX: 0 = F1 led, 1 = F2 led, 2 = F3 led, 3 = F4 led, 4 = F5 led, 5 = all off
    """
    global outport
    assert (load_state >= 0 and load_state <= NUM_LOADING_LEDS), \
        f"load_state {load_state} is not in range(0, NUM_LOADING_LEDS = {NUM_LOADING_LEDS})"
    if load_state == NUM_LOADING_LEDS:
        # Turn off all LEDs
        for i in range(0, NUM_LOADING_LEDS):
            outport.send(mido.Message("note_on", note=54+i, velocity=0)) # Turn off LED
        return
    
    outport.send(mido.Message("note_on", note=54+load_state, velocity=127)) # Turn on loading LED

if __name__ == "__main__":
    main()
