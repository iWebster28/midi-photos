Help on module main:

NAME
    main

DESCRIPTION
    main.py
    Interface midi controllers with Photos app on macOS.
    Ian Webster
    Dec 2022

FUNCTIONS
    button_handler(message: mido.messages.messages.Message) -> None
        Handle button messages from controller.
        
        Args:
            message (mido.Message): Message from controller.
        
        Raises:
            Exception: If applescript returns non-zero code.
    
    event_handler_loop() -> None
        Main event handler loop to handle midi events from controller.
    
    get_init_slider_positions() -> None
        Get the initial slider positions from the Photos app.
        
        Raises:
            Exception: If applescript returns non-zero code.
    
    init_io() -> None
        Initialize MIDI I/O.
    
    init_leds() -> None
        Initialize LEDs on controller.
    
    jog_handler(message: mido.messages.messages.Message) -> None
        Handle jog wheel messages from controller.
        
        Args:
            message (mido.Message): Message from controller.
    
    main()
        Main function to run program.
    
    pitch_handler(message: mido.messages.messages.Message) -> None
        Handle pitch messages from controller.
        
        Args:
            message (mido.Message): Message from controller.
    
    set_init_slider_positions() -> None
        Set the initial slider positions from the Photos app.
    
    set_slider_constants() -> None
        Set constants for slider UI automation.
    
    update_loading_led(load_state: int) -> None
        Update the loading LED to indicate the loading state.
        Ranges from midi note 54-58 (F1-F5 buttons) to indicate loading status.
        
        Args:
            load_state (int): The loading state to update the LED for. EX: 0 = F1 led, 1 = F2 led, 2 = F3 led, 3 = F4 led, 4 = F5 led, 5 = all off
    
    update_track_led(slider_channel: int) -> None
        Update the track LED to indicate which slider is active.
        
        Args:
            slider_channel (int): The slider channel to update the LED for.

DATA
    CONST_SCALE = None
    CONTROLLER_NAME = 'SAMSON Graphite MF8'
    DIAGNOSTIC_MODE = 0
    FINE_GRAIN_DELTA = 81.92
    HW_SLIDER_MAX = 8191
    HW_SLIDER_MIN = -8192
    HW_SLIDER_RANGE = 16383
    NUM_LOADING_LEDS = 5
    QUANTIZE_MOD = 2047.875
    SAMPLE_PERIOD = 16
    SLIDER_BUFFER_SIZE = 2
    SW_NUM_STEPS_SLIDER = 200
    X_OFFSET_SLIDER_MIDDLE = None
    Y_OFFSET_SLIDER = 2
    channel_names = ['Brilliance', 'Exposure', 'Highlights', 'Shadows', 'B...
    hw_slider_buffer = [[0], [0], [0], [0], [0], [0], [0]]
    last_channel = None
    midi_note_to_applescript = {0: 'key code 36', 1: 'keystroke "e" using ...
    outport = None
    slider_channel = 0
    slider_coords = [(None, None), (None, None), (None, None), (None, None...

FILE
    main.py


