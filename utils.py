# applescript-utils.py
# General AppleScript-based functions to hook into Photos app.
# Ian Webster
# Dec 2022

import applescript

def get_applescript_slider_attribute_by_description(attribute: str, description: str) -> applescript._result.Result:
    # NOTE: O(n) where `n` is size of all contents/items in photos app window
    result = applescript.run(f'''
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

    err = result.err
    if err != '':
        print(f"Error: attribute={attribute}, description={description}: {err}")
        
    return result

def click_applescript_item_by_attribute_and_by_description(attribute: str, description: str) -> applescript._result.Result:
    # NOTE: O(n) where `n` is size of all contents/items in photos app window
    result = applescript.run(f'''
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

    # Error logging
    err = result.err
    if err != '':
        print(f"Error: attribute={attribute}, description={description}: {err}")
        
    return result
