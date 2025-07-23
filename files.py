from sys import stderr, exit
from json import loads, dumps

CONFIG_FILE = "config.json"
KEY_BIN = "keys.bin"


def load_config() -> dict:
    try:
        with open(CONFIG_FILE) as CONFIG:
            return loads(CONFIG.read().strip())
    except FileNotFoundError:
        print(CONFIG_FILE, "not found", file=stderr)
        exit(1)


def load_key_history() -> dict[str, int]:
    try:
        with open(KEY_BIN) as SAVE:
            save_data = SAVE.read().strip()
            if not save_data:
                raise FileNotFoundError
            return eval(loads(save_data))
    except FileNotFoundError:
        # Will just load with empty history
        return {}


def save_key_history(memory_keys: dict[str, int]):
    try:
        with open(KEY_BIN, "w") as SAVE:
            SAVE.write(dumps(str(memory_keys)))
    except PermissionError:
        # Can't write? Too bad.
        return
