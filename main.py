from sys import exit
import atexit
from contextlib import redirect_stdout
with redirect_stdout(None):
    from pynput.keyboard import Key, KeyCode, Listener
    import pygame

from files import load_config, load_key_history, save_key_history
from KeyButton import KeyButton

current_keys: set = set()
memory_keys: dict = {}
config: dict


def nice_key(key: Key | KeyCode | None) -> str | None:
    if key is None:
        return None
    return key.name.removeprefix("Key.").lower() if isinstance(key, Key) else str(key).strip("'").lower()


def on_press(key: Key | KeyCode | None) -> None:
    if key is None:
        return
    
    key_name = nice_key(key)
    if key_name in current_keys:
        return      
    current_keys.add(key_name)
    memory_keys[key_name] = memory_keys.get(key_name, 0) + 1
    #print("DEBUG: Pressed", key_name, memory_keys[key_name], "times")


def on_release(key: Key | KeyCode | None) -> None:
    key_name = nice_key(key)
    if key is None or key_name not in current_keys:
        #print("DEBUG: Ignored release of", key)
        return
    
    current_keys.remove(key_name)
    #print("DEBUG: Released", key_name)


def parse_key(key_setup: dict, window: pygame.Surface) -> KeyButton:
    font = config["font"] if "font" not in key_setup else key_setup["font"]
    if key_setup["key"] == "\\\\":
        key_setup["key"] = '\\'

    button_bottom = window.get_height() - key_setup["position"][1]
    trail_length = key_setup["trailLength"] if key_setup["showTrail"] else 0
    ## The division by 4 baffles me
    trail_speed = key_setup["trailLength"] / key_setup["trailTime"] * config["fps"] / 4

    return KeyButton(
        window, (key_setup["position"][0], button_bottom), (key_setup["width"], key_setup["height"]),
        key_setup["borderWidth"], key_setup["trailWidth"], trail_length, trail_speed, key_setup["trailOffset"],
        key_setup["backgroundColor"], key_setup["pressedBackgroundColor"], key_setup["borderColor"],
        key_setup["labelColor"], key_setup["counterColor"], key_setup["trailColor"], font,
        key_setup["key"], key_setup["labelFontSize"], key_setup["counterFontSize"], key_setup["labelRotation"],
        key_setup["showLabel"], key_setup["showCounter"]
    )


if __name__ == "__main__":
    config = load_config()
    
    # Load key press history file
    memory_keys = load_key_history()
    atexit.register(save_key_history, memory_keys)

    # Start keyboard listener thread
    keyboard_listener = Listener(on_press=on_press, on_release=on_release)
    keyboard_listener.start()

    pygame.font.init()

    # Find bounds of window
    left, right, top, bottom = None, None, None, None
    for entry in config["keys"]:
        ## Add default values for key if skipped
        default = config["defaultKeySetup"]
        for setting in default:
            if setting not in entry:
                entry[setting] = default[setting]

        entry_left = entry["position"][0]
        entry_right = entry_left + entry["width"]
        entry_top = entry["position"][1] + entry["height"] + entry["trailLength"] - entry["trailOffset"]
        entry_bottom = entry["position"][1]

        if left is None or entry_left < left:
            left = entry_left
        if right is None or entry_right > right:
            right = entry_right
        if top is None or entry_top > top:
            top = entry_top
        if bottom is None or entry_bottom < bottom:
            bottom = entry_bottom

    if left is None or right is None or top is None or bottom is None:
        print("No keys defined in config.json, exiting...")
        exit(1)

    # Normalize bounds to be (0, 0) at bottom-left, room added for window padding
    for entry in config["keys"]:
        entry["position"][0] -= left - config["windowPadding"]
        entry["position"][1] -= bottom - config["windowPadding"]
    right -= left
    top -= bottom
    left = 0
    bottom = 0

    window_length = right - left + config["windowPadding"] * 2
    window_height = top - bottom + config["windowPadding"] * 2
                    
    pygame.display.init()
    window = pygame.display.set_mode((window_length, window_height))
    pygame.display.set_caption("Key Trail Overlay")
    clock = pygame.time.Clock()

    buttons: list[KeyButton] = []
    for entry in config["keys"]:
        buttons.append(parse_key(entry, window)) 

    running = True
    while running:
        window.fill(config["windowBackgroundColor"])
        for button in buttons:
            button.draw(current_keys, memory_keys)

        pre_draw_events = pygame.event.get()
        pygame.display.update()
        pre_wait_events = pygame.event.get()
        clock.tick(config["fps"])
        
        for event in (*pygame.event.get(), *pre_wait_events, *pre_draw_events):
            if event.type == pygame.QUIT:
                running = False
                keyboard_listener.stop()
                pygame.display.quit()
                break

    pygame.quit()
    print("Stopping program and saving...")
