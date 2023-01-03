import mido
import time

DELAY = 0.03

# Idea:

# Green light on active track (slider, button, of jog last pressed, or track 1 as default - whenever init fn called)
# Everything else is red

# Functionality:
# 127 is red for channels 0-15
# 127 is green for channels 16-31
# 0 is off

inport = mido.open_input('SAMSON Graphite MF8')
outport = mido.open_output('SAMSON Graphite MF8')

while True:
    # in_msg = inport.receive()
    # outport.send(in_msg)
    # print(in_msg)

    for msg_type in ['note_on']:
        # for channel in range(0, 8):
        for velocity in [127, 0]:
            # SOLO TRACKS 1-8, REC TRACKS 1-8
            # RED
            for note in [x for x in range(0, 16)]:
                msg = mido.Message(msg_type, note=note, velocity=velocity)
                outport.send(msg)
                time.sleep(DELAY)
            # GREEN
            for note in [x for x in range(16, 32)]:
                msg = mido.Message(msg_type, note=note, velocity=velocity)
                outport.send(msg)
                time.sleep(DELAY)

            # RW, FF, STOP, PLAY, REC
            for note in [x for x in range(91, 96)]:
                msg = mido.Message(msg_type, note=note, velocity=velocity)
                outport.send(msg)
                time.sleep(DELAY)

            # F1-F5
            for note in [x for x in range(54, 59)]:
                msg = mido.Message(msg_type, note=note, velocity=velocity)
                outport.send(msg)
                time.sleep(DELAY)

            # SHIFT, PRESET
            for note in [x for x in range(46, 48)]:
                msg = mido.Message(msg_type, note=note, velocity=velocity)
                outport.send(msg)
                time.sleep(DELAY)

            time.sleep(0.5)

