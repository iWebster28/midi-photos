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

## Issues:
- For python-rtmidi: https://github.com/SpotlightKid/python-rtmidi/issues/149
- Fix as of 6/22/23: ```pip install --upgrade --no-cache-dir --no-binary python-rtmidi python-rtmidi```