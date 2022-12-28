# Interface midi controllers with Photos app on macOS.
# Ian Webster
# Dec 2022

# Known issues:
# - Moving 2 sliders at a time causes a ping-pong effect
# - Button 8 messes things up
# - Clicking an already-selected track (green) toggles it to orange, but it should stay green
# - applescript algos are slow.

import applescript
import mido
import pyautogui

# Basic light sliders:

# Brilliance: slider "Adjust the properties of Light locally across this image" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Exposure: set value of slider "Adjust the overall lightness of the image" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Highlights: get position of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Shadows: set value of slider "Increase or decrease detail by lightening shadows" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Brightness: slider "Lighten or darken the mid tones" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" 
# Contrast: slider "Adjust the difference between light and dark tones" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Black Point: slider "Adjust the darkest tonal area of the image " of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"

# Define Samson Graphite MF8 Slider Ranges - TODO FUTURE: implement calibration/midi learn feature
HW_SLIDER_MAX = 8191
HW_SLIDER_MIN = -8192
HW_SLIDER_RANGE = HW_SLIDER_MAX - HW_SLIDER_MIN

SAMPLE_PERIOD = 16 # sample every 16th event for all midi events
QUANTIZE_MOD = HW_SLIDER_RANGE / SAMPLE_PERIOD * 2 
SW_NUM_STEPS_SLIDER = (100 * 2) # TODO: get steps programmatically using applescript to extract range of slider
FINE_GRAIN_DELTA = (HW_SLIDER_RANGE + 1) / SW_NUM_STEPS_SLIDER

# SW
Y_OFFSET_SLIDER = 2

# Globals
CONST_SCALE = None
X_OFFSET_SLIDER_MIDDLE = None

outport = None
last_channel = None

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
SLIDER_BUFFER_SIZE = 2 # Store last 2 values for slider buffer

# Button mapping to applescript commands (run under System Events)
midi_note_to_applescript = {
    1: 'keystroke "e" using {command down}', # rec button on slider 2 -> Apply preset edits
    0: 'key code 36', # Rec button on slider 1 -> Open/close editor pane (key code 36 == enter)
    46: 'key code 123', # Left button -> prev photo (key code 123 == left arrow)
    91: 'key code 123', # RW button
    47: 'key code 124', # Right button -> prev photo (key code 124 == right arrow)
    92: 'key code 124', # FF button
}

# UI coordinates of sliders in photos.
slider_coords = [(None, None) for i in range(0, len(channel_names))]

def main():
    global CONST_SCALE
    global X_OFFSET_SLIDER_MIDDLE

    global outport
    global last_channel

    # List MIDI Inputs and Outputs (we just need inputs)
    print("MIDI Outputs: ")
    print(mido.get_output_names())
    print("MIDI Inputs: ")
    print(mido.get_input_names())

    # Init output (for sending LED messages)
    outport = mido.open_output('SAMSON Graphite MF8')

    # Initialize LEDs
    for i in range(0, 32):
        outport.send(mido.Message("note_on", note=i, velocity=0))
        outport.send(mido.Message("note_on", note=i, velocity=127))

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

        # print(r_position.out)

        print(f"Found slider {channel_names[i]} at position (x, y): {r_position.out}")
        slider_coords[i] = [int(val) for val in r_position.out.split(", ")] # Leftmost x-coord remains unchanged for all sliders as they are left-aligned in the Photos UI
        
        i += 1

    print(f"Found all sliders: {slider_coords}")
    
    # Set slider constants for UI automation
    r_size = get_applescript_slider_attribute_by_description(attribute="size", description=channel_names[0])
    SLIDER_WIDTH, SLIDER_HEIGHT = [int(val) for val in r_size.out.split(", ")]
    X_OFFSET_SLIDER_MIDDLE = SLIDER_WIDTH / 2
    CONST_SCALE = SLIDER_WIDTH / HW_SLIDER_RANGE # Each slider on the Graphite MF8 has a range -8192 to 8191

    slider_channel = 0
    last_channel = None
    set_init_slider_positions()

    # Start receiving MIDI events and translate to pyautogui actions
    with mido.open_input('SAMSON Graphite MF8') as port:
        for message in port:
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
                # Deal with negative slider values
                neg = False
                pitch = message.pitch
                if pitch < 0:
                    pitch *= -1
                    neg = True

                # MAYBE: just check lowest log_2(step_size) bits to see if == 0 first. Won't help in the case that the majority of slider vals are non divisible by step_size though.
                rem = (pitch % (QUANTIZE_MOD)) # Quantize to 2048-size steps
                # print("rem:", rem)

                if message.pitch == HW_SLIDER_MAX: # max
                    hw_slider_buffer[slider_channel].append(HW_SLIDER_MAX) # Since 8191 remainder for mod `any multiple of 8` is nonzero.
                else: # Quantize
                    # hw_slider_buffer[slider_channel].append(message.pitch - rem if rem < 0 else message.pitch - rem)
                    hw_slider_buffer[slider_channel].append(pitch - rem if neg == False else 0 - (pitch - rem))

                # Maintain buffer of size SLIDER_BUFFER_SIZE
                if len(hw_slider_buffer[slider_channel]) > SLIDER_BUFFER_SIZE:
                    del hw_slider_buffer[slider_channel][0] # hw_slider_buffer[slider_channel] = hw_slider_buffer[slider_channel][1:4]

                # hw_slider_buffer[slider_channel][-1] = message.pitch # No quantizing. (very slow due to pyautogui calls.)

                # print(hw_slider_buffer[slider_channel][-1]) # Diagnostic

                if slider_channel != last_channel: # First event, or touched another slider: move instead of dragging (move and clicking) the mouse.
                    pyautogui.leftClick(slider_coords[slider_channel][0] + (CONST_SCALE * hw_slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + Y_OFFSET_SLIDER) # was moveTo
                
                elif (hw_slider_buffer[slider_channel][-1] != hw_slider_buffer[slider_channel][-2]) or \
                    hw_slider_buffer[slider_channel][-1] == HW_SLIDER_MAX or \
                    hw_slider_buffer[slider_channel][-1] == HW_SLIDER_MIN: # If at sample freq, or at min/max of given slider
                    pyautogui.dragTo(slider_coords[slider_channel][0] + (CONST_SCALE * hw_slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + Y_OFFSET_SLIDER, button='left')

                update_track_led(slider_channel)
            
            # Jog wheel
            if hasattr(message, 'control') and message.control == 60: 

                # Jog CW
                if message.value == 1:
                    # fine grain adjust
                    pitch_delta = FINE_GRAIN_DELTA if not hw_slider_buffer[slider_channel][-1] >= HW_SLIDER_MAX else 0
                    if pitch_delta != 0:
                        pyautogui.dragRel(1, 0, button='left')
                    hw_slider_buffer[slider_channel][-1] += pitch_delta
                    # print(f'fine grain CW {hw_slider_buffer[slider_channel][-1]}')
                # Jog CCW
                elif message.value == 65:
                    # print("ch:", slider_channel)
                    # fine grain adjust
                    pitch_delta = -FINE_GRAIN_DELTA if not hw_slider_buffer[slider_channel][-1] <= HW_SLIDER_MIN else 0
                    if pitch_delta != 0:
                        pyautogui.dragRel(-1, 0, button='left')
                    hw_slider_buffer[slider_channel][-1] += pitch_delta
                    # print(f'fine grain CCW {hw_slider_buffer[slider_channel][-1]}')

            if not hasattr(message, 'note'):
                continue
            
            # Buttons
            if message.type == "note_on" and message.velocity == 127:
                if message.note in midi_note_to_applescript:
                    r = applescript.tell.app('System Events', midi_note_to_applescript[message.note]) # prev photo (key code 124 == right arrow)
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")
                    
                    if message.note == 1: # Rec button on slider 2
                        set_init_slider_positions() # Apply the auto effects
                
                elif message.note - 8 <= 15 and message.note - 8 >= 0: # Solo track selects (to select a slider to edit again. Should point mouse to last value)
                    slider_channel = message.note - 8
                    if slider_channel == 7: # Unused slider_channel
                        continue
                    pyautogui.moveTo(slider_coords[slider_channel][0] + (CONST_SCALE * hw_slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + Y_OFFSET_SLIDER)
                    
                    # print(f"BUTTONS: last_channel: {last_channel}, channel: {slider_channel}")
                    update_track_led(slider_channel)

    return

def set_init_slider_positions():
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
        i += 1

    # Arbitrarily move to starting position of first slider
    pyautogui.moveTo(slider_coords[0][0] + (CONST_SCALE * hw_slider_buffer[0][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[0][1] + Y_OFFSET_SLIDER)
    update_track_led(0)

def update_track_led(slider_channel):
    global last_channel
    global outport
    # Turn the LED at `slider_channel` channel to GREEN.
    if last_channel != slider_channel:
        outport.send(mido.Message("note_on", note=slider_channel + 8, velocity=0)) # Turn off red (green state)
        if last_channel != None: 
            outport.send(mido.Message("note_on", note=last_channel + 8, velocity=127)) # Add red back (orange state)
    last_channel = slider_channel
    

def get_applescript_slider_attribute_by_description(attribute, description):
    # NOTE: O(n) where `n` is size of all contents/items in photos app window
    result = applescript.run(f'''
    tell application "Photos" to activate
        tell application "System Events"
            tell process "Photos"
                set i to 0
                set itemVals to {{}}
                set listItems to (entire contents of window 1 as list)
                repeat with thisItem in listItems
                    set i to i + 1
                    if (class of item i of listItems is slider) then
                        if description of item i of listItems is "{description}" then
                            copy {attribute} of thisItem to end of itemVals
                            exit repeat
                        end if
                    end if
                end repeat
                return itemVals
            end tell
        end tell
    ''')

    err = result.err
    if err != '':
        print(f"Error: attribute={attribute}, description={description}: {err}")
        
    return result

def click_applescript_item_by_attribute_and_by_description(attribute, description):
    # NOTE: O(n) where `n` is size of all contents/items in photos app window
    result = applescript.run(f'''
    tell application "Photos" to activate
        tell application "System Events"
            tell process "Photos"
                set i to 0
                set itemVals to {{}}
                set listItems to (entire contents of window 1 as list)
                repeat with thisItem in listItems
                    set i to i + 1
                    if (class of item i of listItems is {attribute}) then
                        if description of item i of listItems is "{description}" then
                            click item i of listItems
                            exit repeat
                        end if
                    end if
                end repeat
                return itemVals
            end tell
        end tell
    ''')

    err = result.err
    if err != '':
        print(f"Error: attribute={attribute}, description={description}: {err}")
        
    return result

if __name__ == "__main__":
    main()