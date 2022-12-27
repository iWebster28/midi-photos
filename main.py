# Interface midi controllers with Photos app on macOS.
# Ian Webster
# Dec 2022

import applescript
import mido
import pyautogui

# Brilliance: slider "Adjust the properties of Light locally across this image" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Exposure: set value of slider "Adjust the overall lightness of the image" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Highlights: get position of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Shadows: set value of slider "Increase or decrease detail by lightening shadows" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Brightness: slider "Lighten or darken the mid tones" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" 
# Contrast: slider "Adjust the difference between light and dark tones" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
# Black Point: slider "Adjust the darkest tonal area of the image " of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"

# Names of sliders referenced with AppleScript
slider_ids = [
    "Adjust the properties of Light locally across this image",
    "Adjust the overall lightness of the image",
    "Increase or decrease detail by darkening highlights",
    "Increase or decrease detail by lightening shadows",
    "Lighten or darken the mid tones",
    "Adjust the difference between light and dark tones",
    "Adjust the darkest tonal area of the image ",
]

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

#                                                                                                                    v this can also be 2!
# slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 2 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"

# UI coordinates of slides in photos.
slider_coords = [(None, None) for i in range(0, len(channel_names))]

def main():
    # Used to deal with UI group num changes in photos (sometimes group is 1; sometimes it is 2) - TODO: understand why
    group_num = 2
    group_num_2 = 2 # weird
    slider_group = None
    def update_slider_group():
        return f'of group 1 of group "Light" of scroll area 1 of group {group_num_2} of group {group_num} of splitter group 1 of window 1 of application process "Photos" of application "System Events"'
    slider_group = update_slider_group()

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
    while i < len(slider_ids):
        slider_id = slider_ids[0]
        # r_position = applescript.tell.app("System Events",f'''
        #                     set props to get position of slider "{slider_id}" {slider_group}
        #                     return props
        #                     ''')

        r_position = applescript.run(f'''
        tell application "Photos" to activate
            tell application "System Events"
                tell process "Photos"
                    set i to 0
                    set itemVals to {{}}
                    set listItems to (entire contents of window 1 as list)
                    repeat with thisItem in listItems
                        set i to i + 1
                        if (class of item i of listItems is slider) then
                            if description of item i of listItems is "{channel_names[i]}" then
                                copy position of thisItem to end of itemVals
                                exit repeat
                            end if
                        end if
                    end repeat
                    return itemVals
                end tell
            end tell
        ''')

        # group_num didn't work:
        if r_position.out == '':
            print("Could not hook into Photos window. Trying new group_num")
            # group_num = 2 if group_num == 1 else 1 # Try 1 or 2
            # slider_group = update_slider_group()
            # r_position = applescript.tell.app("System Events",f'''
            #                     set props to get position of slider "{slider_id}" {slider_group}
            #                     return props
            #                     ''')
            r_edit = applescript.run(f'''
            tell application "Photos" to activate
                tell application "System Events"
                    tell process "Photos"
                    set i to 0
                    set itemVals to {{}}
                    set listItems to (entire contents of window 1 as list)
                    repeat with thisItem in listItems
                        set i to i + 1
                        if (class of item i of listItems is button) then
                            if description of item i of listItems is "Edit" then
                                click item i of listItems
                                exit repeat
                            end if
                        end if
                    end repeat
                    return itemVals
                end tell
            end tell
            ''')
            continue

        # print(r_position.out)
        err = r_position.err
        if err != '':
            print(err)
        print(r_position.out)

        slider_coords[i] = [int(val) for val in r_position.out.split(", ")] # Leftmost x-coord remains unchanged for all sliders as they are left-aligned in the Photos UI
        i += 1
    print(slider_coords)
    
    # Get slider size (width, height) (which is the same across all sliders)
    # Arbitrarily use the first slider since they are all the same size.
    # r_size = applescript.tell.app("System Events",f'''
    #                     set props to get size of slider "{slider_ids[0]}" {slider_group}
    #                     return props
    #                     ''')
    r_size = applescript.run(f'''
        tell application "Photos" to activate
            tell application "System Events"
                tell process "Photos"
                    set i to 0
                    set itemVals to {{}}
                    set listItems to (entire contents of window 1 as list)
                    repeat with thisItem in listItems
                        set i to i + 1
                        if (class of item i of listItems is slider) then
                            if description of item i of listItems is "{channel_names[0]}" then
                                copy size of thisItem to end of itemVals
                                exit repeat
                            end if
                        end if
                    end repeat
                    return itemVals
                end tell
            end tell
    ''')
    SLIDER_WIDTH, SLIDER_HEIGHT = [int(val) for val in r_size.out.split(", ")]
    X_OFFSET_SLIDER_MIDDLE = SLIDER_WIDTH / 2
    CONST_SCALE = SLIDER_WIDTH / 16383 # Each slider on the Graphite MF8 has a range -8192 to 8191

    # Arbitrarily move to starting position of first slider
    channel = 0
    pyautogui.moveTo(slider_coords[channel][0], slider_coords[channel][1] + 1)
    
    count = 0
    slider_buffer = None
    last_channel = None

    # Start receiving MIDI events and translate to pyautogui actions
    with mido.open_input('SAMSON Graphite MF8') as port:
        for message in port:
            print(message)

            if hasattr(message, 'channel'):
                channel = message.channel
            
            if hasattr(message, 'pitch'):
                slider_buffer = message.pitch
            
            if hasattr(message, 'control') and message.control == 60: # Jog wheel
                # Jog CW
                if message.value == 1:
                    # fine grain adjust
                    pitch_delta = 128 if not slider_buffer >= 8191 else 0
                    if pitch_delta != 0:
                        pyautogui.dragRel(1, 0, button='left')
                    slider_buffer += pitch_delta
                    # print(f'fine grain CW {slider_buffer}')
                # Jog CCW
                elif message.value == 65:
                    # fine grain adjust
                    pitch_delta = -128 if not slider_buffer <= -8192 else 0
                    if pitch_delta != 0:
                        pyautogui.dragRel(-1, 0, button='left')
                    slider_buffer += pitch_delta
                    # print(f'fine grain CCW {slider_buffer}')

            elif hasattr(message, 'pitch'): # Slider  
                if channel != last_channel: # First event, or touched another slier: move instead of dragging (move and clicking) the mouse.
                    pyautogui.moveTo(slider_coords[channel][0] + (CONST_SCALE * slider_buffer) + X_OFFSET_SLIDER_MIDDLE, slider_coords[channel][1] + 1)

                elif count == 0 or slider_buffer == 8191 or slider_buffer == -8192: # If at sample freq, or at min/max of given slider
                    pyautogui.dragTo(slider_coords[channel][0] + (CONST_SCALE * slider_buffer) + X_OFFSET_SLIDER_MIDDLE, slider_coords[channel][1] + 1, button='left')
                
                count += 1
                if count == 16:
                    count = 0
                
                last_channel = channel

            if not hasattr(message, 'note'):
                continue
            
            # Buttons
            if message.type == "note_on" and message.velocity == 127:
                if message.note == 8: # Solo button on slider 1
                    r = applescript.tell.app('System Events', 'keystroke "e" using {command down}') # Apply preset edits
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")
                elif message.note == 0: # Rec button on slider 1
                    r = applescript.tell.app('System Events', 'key code 36') # Open/close editor pane (key code 36 == enter)
                    if r.code != 0:
                        raise Exception(f"Applescript returned {r.code}")


    return

if __name__ == "__main__":
    main()