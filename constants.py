# constants.py
# Constants for Samson Graphite MF8 midi controller
# Ian Webster
# Dec 2022

DIAGNOSTIC_MODE = 0

CONTROLLER_NAME = 'SAMSON Graphite MF8'

# Define Samson Graphite MF8 Slider Ranges - TODO FUTURE: implement calibration/midi learn feature
HW_SLIDER_MAX = 8191
HW_SLIDER_MIN = -8192
HW_SLIDER_RANGE = HW_SLIDER_MAX - HW_SLIDER_MIN

SAMPLE_PERIOD = 16 # sample every 16th event for all midi events
QUANTIZE_MOD = HW_SLIDER_RANGE / SAMPLE_PERIOD * 2 
SW_NUM_STEPS_SLIDER = (100 * 2) # TODO FUTURE: get steps programmatically using applescript to extract range of slider
FINE_GRAIN_DELTA = (HW_SLIDER_RANGE + 1) / SW_NUM_STEPS_SLIDER

# SW
Y_OFFSET_SLIDER = 2

# Loading LEDs
NUM_LOADING_LEDS = 5

# Store last 2 values for slider buffer
SLIDER_BUFFER_SIZE = 2 

# Button mapping to applescript commands (run under System Events)
midi_note_to_applescript = {
    1: 'keystroke "e" using {command down}', # rec button on slider 2 -> Apply preset edits
    2: 'keystroke "e" using {command down}', # rec button on slider 3 -> Apply preset edits (but no set_init_slider_positions after)
    0: 'key code 36', # Rec button on slider 1 -> Open/close editor pane (key code 36 == enter)
    46: 'key code 123', # Left button -> prev photo (key code 123 == left arrow)
    91: 'key code 123', # RW button
    47: 'key code 124', # Right button -> prev photo (key code 124 == right arrow)
    92: 'key code 124', # FF button
    # 93: 'keystroke "-" using {command down}', # Zoom in button
    # 94: 'keystroke "=" using {command down}', # Zoom out button
}
