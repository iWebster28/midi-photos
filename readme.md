# midi-photos

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