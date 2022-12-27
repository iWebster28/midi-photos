# Interface midi controllers with Photos app on macOS.
# Ian Webster
# Dec 2022

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

SAMPLE_PERIOD = 16 # sample every 16th event for all midi events
QUANTIZE_MOD = 16383 / SAMPLE_PERIOD * 2 
NUM_STEPS_SLIDER = (100 * 2) # TODO: get steps programmatically
FINE_GRAIN_DELTA = 16384 / NUM_STEPS_SLIDER

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

# UI coordinates of sliders in photos.
slider_coords = [(None, None) for i in range(0, len(channel_names))]

def main():
    # List MIDI Inputs and Outputs (we just need inputs)
    print("MIDI Outputs: ")
    print(mido.get_output_names())
    print("MIDI Inputs: ")
    print(mido.get_input_names())

    # Focus on the Photos editing pane
    result = applescript.tell.app("Photos", "activate") 
    if result.code != 0:
        raise Exception("Could not find Photos app window.")
        exit(1)

    # For every slider, get the initial slider position (x, y)
    i = 0
    while i < len(channel_names):
        r_position = get_applescript_item_attribute_by_description(attribute="position", description=channel_names[i])

        # Could not find a slider element: is the edit pane open?
        if r_position.out == '':
            print("Could not hook into Photos window. Assuming Edit pane is closed. Trying to open Edit pane.")
            r_edit = click_applescript_item_by_attribute_and_by_description(attribute="button", description="Edit")
            continue

        # print(r_position.out)
        err = r_position.err
        if err != '':
            print(err)
        print(f"Found slider {channel_names[i]} at position (x, y): {r_position.out}")
        slider_coords[i] = [int(val) for val in r_position.out.split(", ")] # Leftmost x-coord remains unchanged for all sliders as they are left-aligned in the Photos UI
        i += 1

    print(f"Found all sliders: {slider_coords}")
    
    # Set slider constants for UI automation
    r_size = get_applescript_item_attribute_by_description(attribute="size", description=channel_names[0])
    SLIDER_WIDTH, SLIDER_HEIGHT = [int(val) for val in r_size.out.split(", ")]
    X_OFFSET_SLIDER_MIDDLE = SLIDER_WIDTH / 2
    CONST_SCALE = SLIDER_WIDTH / 16383 # Each slider on the Graphite MF8 has a range -8192 to 8191

    # Arbitrarily move to starting position of first slider
    slider_channel = 0
    pyautogui.moveTo(slider_coords[slider_channel][0], slider_coords[slider_channel][1] + 1)
    
    # Slider buffers 
    slider_buffer = [[0] for i in range(len(channel_names))] # Buffer 
    SLIDER_BUFFER_SIZE = 2 # Store last 2 values for slider buffer
    last_channel = None

    # Start receiving MIDI events and translate to pyautogui actions
    with mido.open_input('SAMSON Graphite MF8') as port:
        for message in port:
            print(message)
            
            # Store channel for sliders; ignore jog wheel and buttons.
            if hasattr(message, 'channel') and message.type != "control_change" and message.type != "note_on" and message.type != "note_off":
                slider_channel = message.channel
            
            # Unused channel
            if message.channel == 7 or slider_channel == 7:
                continue

            # Slider
            if hasattr(message, 'pitch'):
                neg = False
                pitch = message.pitch
                if pitch < 0:
                    pitch *= -1
                    neg = True
                rem = (pitch % (QUANTIZE_MOD)) # Quantize to 2048-size steps
                # print("rem:", rem)
                if message.pitch == 8191: # max
                    slider_buffer[slider_channel].append(8191)
                else:
                    # slider_buffer[slider_channel].append(message.pitch - rem if rem < 0 else message.pitch - rem)
                    slider_buffer[slider_channel].append(pitch - rem if neg == False else 0 - (pitch - rem))

                if len(slider_buffer[slider_channel]) > SLIDER_BUFFER_SIZE:
                    del slider_buffer[slider_channel][0] # slider_buffer[slider_channel] = slider_buffer[slider_channel][1:4]

                # slider_buffer[slider_channel][-1] = message.pitch # No quantizing.

                # print(slider_buffer[slider_channel][-1]) # Diagnostic

                if slider_channel != last_channel: # First event, or touched another slier: move instead of dragging (move and clicking) the mouse.
                    pyautogui.leftClick(slider_coords[slider_channel][0] + (CONST_SCALE * slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + 2) # was moveTo
                elif (slider_buffer[slider_channel][-1] != slider_buffer[slider_channel][-2]) or slider_buffer[slider_channel][-1] == 8191 or slider_buffer[slider_channel][-1] == -8192: # If at sample freq, or at min/max of given slider
                    pyautogui.dragTo(slider_coords[slider_channel][0] + (CONST_SCALE * slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + 2, button='left')

                last_channel = slider_channel
            
            # Jog wheel
            if hasattr(message, 'control') and message.control == 60: 
                # Jog CW
                if message.value == 1:
                    # fine grain adjust
                    pitch_delta = FINE_GRAIN_DELTA if not slider_buffer[slider_channel][-1] >= 8191 else 0
                    if pitch_delta != 0:
                        pyautogui.dragRel(1, 0, button='left')
                    slider_buffer[slider_channel][-1] += pitch_delta
                    # print(f'fine grain CW {slider_buffer[slider_channel][-1]}')
                # Jog CCW
                elif message.value == 65:
                    # print("ch:", slider_channel)
                    # fine grain adjust
                    pitch_delta = -FINE_GRAIN_DELTA if not slider_buffer[slider_channel][-1] <= -8192 else 0
                    if pitch_delta != 0:
                        pyautogui.dragRel(-1, 0, button='left')
                    slider_buffer[slider_channel][-1] += pitch_delta
                    # print(f'fine grain CCW {slider_buffer[slider_channel][-1]}')

            if not hasattr(message, 'note'):
                continue
            
            # Buttons
            if message.type == "note_on" and message.velocity == 127:
                if message.note == 1: # rec button on slider 2
                    r = applescript.tell.app('System Events', 'keystroke "e" using {command down}') # Apply preset edits
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")
                elif message.note == 0: # Rec button on slider 1
                    r = applescript.tell.app('System Events', 'key code 36') # Open/close editor pane (key code 36 == enter)
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")
                elif message.note == 46 or message.note == 91: # Left button 
                    r = applescript.tell.app('System Events', 'key code 123') # prev photo (key code 123 == left arrow)
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")
                elif message.note == 47 or message.note == 92: # Right button 
                    r = applescript.tell.app('System Events', 'key code 124') # prev photo (key code 124 == right arrow)
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")
                
                elif message.note - 8 <= 15 and message.note - 8 >= 0: # Solo track selects (to select a slider to edit again. Should point mouse to last value)
                    slider_channel = message.note - 8
                    if slider_channel == 7: # Unused slider_channel
                        continue
                    pyautogui.moveTo(slider_coords[slider_channel][0] + (CONST_SCALE * slider_buffer[slider_channel][-1]) + X_OFFSET_SLIDER_MIDDLE, slider_coords[slider_channel][1] + 2)

    return

def get_applescript_item_attribute_by_description(attribute, description):
    # NOTE: O(n) where `n` is size of all contents/items in photos app window
    return applescript.run(f'''
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

def click_applescript_item_by_attribute_and_by_description(attribute, description):
    # NOTE: O(n) where `n` is size of all contents/items in photos app window
    return applescript.run(f'''
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

if __name__ == "__main__":
    main()