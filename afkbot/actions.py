import time

import pydirectinput

from afkbot.models import Action


KEY_ALIASES = {
    "alt": "altleft",
}


def execute_actions(actions: list[Action]) -> None:
    for action in actions:
        execute_action(action)


def execute_action(action: Action) -> None:
    action_type = action["type"]
    if action_type == "press":
        pydirectinput.press(normalize_key(action["key"]))
    elif action_type == "click":
        button = str(action.get("button", "left"))
        pydirectinput.click(button=button)
    elif action_type == "keyDown":
        pydirectinput.keyDown(normalize_key(action["key"]))
    elif action_type == "keyUp":
        pydirectinput.keyUp(normalize_key(action["key"]))
    elif action_type in {"sleep", "delay"}:
        time.sleep(int(action["ms"]) / 1000)
    elif action_type == "repeat":
        times = int(action["times"])
        delay_ms = int(action.get("delay_ms", 0))
        nested_actions = list(action.get("actions", []))
        for index in range(times):
            execute_actions(nested_actions)
            if delay_ms > 0 and index < times - 1:
                time.sleep(delay_ms / 1000)
    else:
        raise ValueError(f"不支援的 action type: {action_type}")


def normalize_key(key_name: str) -> str:
    return KEY_ALIASES.get(key_name.lower(), key_name)
