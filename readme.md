# midi-photos

## What is it?
Midi Photos makes it easier for people to edit mass amounts of photos at once. It was motivated by my personal experience as a photographer, photo editor, and programmer, and has helped reduce physical strain in my editing workflow.  

The Midi Photos software-hardware interface is built in Python and makes photo editing faster on the macOS Photos app. Instead of manually using the mouse to change photo parameters like brightness and contrast, Midi Photos allows you to use a physical MIDI controller (usually used for music production) to control the same parameters in a faster, more tactile manner. As a musician, I saw the opportunity to create a new use for my MIDI controller. To build Midi Photos, I used libraries such as mido for MIDI event handling, and applescript paired with pyautogui as a pseudo-“macOS Photos API”.

## See wiki:
[Wiki](https://github.com/iWebster28/midi-photos/wiki)

## To install:
- Create a virtual environment  
```python3 -v venv env```
- Activate virtual environment (macOS)  
```source env/bin/activate```
- Install requirements  
```pip3 install -r requirements.txt```

## To run:
- Connect Samson Graphite MF8 to your computer (note: untested with multiple midi devices connected)
- Run
```python3 main.py```

## Known Issues:
- For python-rtmidi: https://github.com/SpotlightKid/python-rtmidi/issues/149
  - Fix as of 6/22/23: ```pip install --upgrade --no-cache-dir --no-binary python-rtmidi python-rtmidi```
- Applescript algos are slow.
- Upon using the back/forward buttons to change images, the track select will forget positions. 
  - If applescript is faster, could implement get_slider_position for this.
- Moving 2 sliders at a time causes a ping-pong effect
- Clicking an already-selected track (green) toggles it to orange, but it should stay green


## Generating docs:
- ```python3 -m pydoc main > main.md```