# Applescript-main 
# Interface midi controllers with Photos app on macOS.
# Ian Webster
# Dec 2022

import applescript
import mido
import os
import pyautogui

# import atomac

def main():
    print(mido.get_output_names())
    print(mido.get_input_names())

    r_position = applescript.tell.app("System Events",f'''
                        set props to get position of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
                        return props
                        ''')
    r_size = applescript.tell.app("System Events",f'''
                        set props to get size of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
                        return props
                        ''')

    size = [int(val) for val in r_size.out.split(",")]
    coords = [int(val) for val in r_position.out.split(",")]

    print("size:", size)
    print("coords:", coords)
    pyautogui.moveTo(coords[0], coords[1] + 1, duration=0.01)

    count = 0

    buffer = []

    last_sampled_pitch = None

    with mido.open_input('SAMSON Graphite MF8') as port:
        for message in port:
            print(message)
            
            if hasattr(message, 'pitch'):
                # use FIFO buffer to skip commands if 2 commands are similar to the last, and there are no more events coming
                buffer.append(message.pitch)

            if len(buffer) > 3:
                # buffer = buffer[1:4]
                del buffer[0]
                print(buffer)
            
            if hasattr(message, 'control') and message.control == 60:
                    if message.value == 1:
                        # fine grain adjust
                        pyautogui.dragRel(1, 0, button='left')
                        # r_get = applescript.tell.app("System Events",'''
                        # get value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
                        # ''')
                        # # print(r_get.out)
                        # # print(r_get.err, 'erorrrrrr')
                        
                        # print(f"response: {r_get.out}")
                        # r_set = applescript.tell.app("System Events",f'''
                        # set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to {float(r_get.out) + 0.01} 
                        # return "Done"
                        # ''')

                    elif message.value == 65:
                        # fine grain adjust
                        pyautogui.dragRel(-1, 0, button='left')
                        # r_get = applescript.tell.app("System Events",'''
                        # get value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
                        # ''')
                        # # print(r_get.out)
                        # # print(r_get.err, 'erorrrrrr')
                        
                        # print(f"response: {r_get.out}")
                        # r_set = applescript.tell.app("System Events",f'''
                        # set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to {float(r_get.out) - 0.01} 
                        # return "Done"
                        # ''')

            elif len(buffer) == 3:

                # if (abs(buffer[1]) - abs(buffer[0]) == 128) and (abs(buffer[2]) - abs(buffer[1]) == 128):
                #     if hasattr(message, 'pitch'):
                # r_set = applescript.tell.app("System Events",f'''
                #         set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to {message.pitch / 8192} 
                #         return "Done"
                #         ''')
                
                if count == 0:
                    pyautogui.moveTo(coords[0] + (size[0] * message.pitch / 16383) + size[0] / 2, coords[1] + 1)

                elif count % 16 == 0 or buffer[2] == 8191 or buffer[2] == -8192:
                    # pyautogui.dragTo(coords[0] + (size[0] * buffer[2] / 16383) + size[0] / 2, coords[1] + 1, button='left')
                    last_sampled_pitch = buffer[2]
                    
                    # print(f"response: {r_get.out}")
                    r_set = applescript.tell.app("System Events",f'''
                    set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to {buffer[2] / 8192} 
                    return "Done"
                    ''')

                count += 1
                



            if hasattr(message, 'control'):
                if message.control == 16:
                    if message.value == 65:
                        r_get = applescript.tell.app("System Events",'''
                        get value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events"
                        ''')
                        # print(r_get.out)
                        # print(r_get.err, 'erorrrrrr')
                        
                        print(f"response: {r_get.out}")
                        r_set = applescript.tell.app("System Events",f'''
                        set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to {float(r_get.out) + 0.01} 
                        return "Done"
                        ''')
                        
                        # photos = atomac.getAppRefByBundleId('com.apple.Photos')
            

            if not hasattr(message, 'note'):
                continue


            print(message.note)
            if message.note == 8:
                print('running 8')

                cmd = """osascript -e '
                tell application "Photos" to activate 
                tell application "System Events" 
                set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to 0.15 
                end tell
                '
                """
                
                r = os.system(cmd)
                print(f"Applescript returned {r}")


            elif message.note == 0:
                print('running 0')
                r = applescript.run('set value of slider "Increase or decrease detail by darkening highlights" of group 1 of group "Light" of scroll area 1 of group 1 of group 1 of splitter group 1 of window 1 of application process "Photos" of application "System Events" to -0.15')
                if r.code == 0:
                    print("Applescript returned 0")

    return

if __name__ == "__main__":
    main()