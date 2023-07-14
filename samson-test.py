# samson-test.py
# Testing suite for Samson Graphite MF8 midi controller LEDs.
# Ian Webster
# Dec 2022

# Summary of Samson Graphite MF8 midi controller MIDI I/O:

# Green light indicates active track (slider, button, of jog last pressed, or track 1 as default - whenever init fn called)
# Everything else is red

# MIDI note numbers and channels for toggling lights:
# 127 is red for channels 0-15
# 127 is green for channels 16-31
# 0 is off

import mido
import time

DELAY = 0.03 # seconds between light toggles

class Test():
    def __init__(self, echo=False):
        """Initialize Test class.

        Args:
            echo (bool, optional): Whether to echo messages to console. Defaults to False.
        """
        # Echo messages
        self._echo = echo
        # Initialize controller ports
        self.inport = mido.open_input('SAMSON Graphite MF8')
        self.outport = mido.open_output('SAMSON Graphite MF8')
    
    def echo_messages(self) -> None:
        """Echo messages from controller to console.
        """
        if not self._echo:
            return
        in_msg = self.inport.receive()
        self.outport.send(in_msg)
        print(in_msg)
    
    def all_ports(self) -> None:
        """Test all ports on controller.
        """
        # Scan over all available controller lights
        while True:       
            self.echo_messages()

            for msg_type in ['note_on']:
                # for channel in range(0, 8):
                for velocity in [127, 0]:
                    # SOLO TRACKS 1-8, REC TRACKS 1-8
                    # RED
                    for note in [x for x in range(0, 16)]:
                        msg = mido.Message(msg_type, note=note, velocity=velocity)
                        self.outport.send(msg)
                        time.sleep(DELAY)
                    # GREEN
                    for note in [x for x in range(16, 32)]:
                        msg = mido.Message(msg_type, note=note, velocity=velocity)
                        self.outport.send(msg)
                        time.sleep(DELAY)

                    # RW, FF, STOP, PLAY, REC
                    for note in [x for x in range(91, 96)]:
                        msg = mido.Message(msg_type, note=note, velocity=velocity)
                        self.outport.send(msg)
                        time.sleep(DELAY)

                    # F1-F5
                    for note in [x for x in range(54, 59)]:
                        msg = mido.Message(msg_type, note=note, velocity=velocity)
                        self.outport.send(msg)
                        time.sleep(DELAY)

                    # SHIFT, PRESET
                    for note in [x for x in range(46, 48)]:
                        msg = mido.Message(msg_type, note=note, velocity=velocity)
                        self.outport.send(msg)
                        time.sleep(DELAY)

                    time.sleep(0.5)

def main():
    test = Test(echo=True)
    test.all_ports()

if __name__ == "__main__":
    main()