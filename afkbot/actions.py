import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

import pydirectinput

from afkbot.models import Action


KEY_ALIASES = {
    "alt": "altleft",
}

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MAPVK_VK_TO_VSC = 0

VK_KEYS = {
    "enter": 0x0D,
    "return": 0x0D,
    "down": 0x28,
    "up": 0x26,
    "left": 0x25,
    "right": 0x27,
    "space": 0x20,
    "esc": 0x1B,
    "escape": 0x1B,
    "alt": 0x12,
    "altleft": 0x12,
}

user32 = ctypes.windll.user32


@dataclass
class InputContext:
    mode: str = "foreground"
    target_hwnd: int | None = None
    log: object | None = None

    @property
    def use_background(self) -> bool:
        return self.mode == "background" and self.target_hwnd is not None

    def write_log(self, message: str) -> None:
        if callable(self.log):
            self.log(message)


def execute_actions(
    actions: list[Action],
    input_context: InputContext | None = None,
) -> None:
    for action in actions:
        execute_action(action, input_context)


def execute_action(action: Action, input_context: InputContext | None = None) -> None:
    action_type = action["type"]
    if action_type == "press":
        key = normalize_key(action["key"])
        if should_use_background(input_context):
            post_key_press(input_context.target_hwnd, key)
        else:
            pydirectinput.press(key)
    elif action_type == "click":
        button = str(action.get("button", "left"))
        if should_use_background(input_context):
            post_mouse_click(input_context.target_hwnd, button, action)
        else:
            pydirectinput.click(button=button)
    elif action_type == "keyDown":
        key = normalize_key(action["key"])
        if should_use_background(input_context):
            post_key(input_context.target_hwnd, key, is_down=True)
        else:
            pydirectinput.keyDown(key)
    elif action_type == "keyUp":
        key = normalize_key(action["key"])
        if should_use_background(input_context):
            post_key(input_context.target_hwnd, key, is_down=False)
        else:
            pydirectinput.keyUp(key)
    elif action_type in {"sleep", "delay"}:
        time.sleep(int(action["ms"]) / 1000)
    elif action_type == "repeat":
        times = int(action["times"])
        delay_ms = int(action.get("delay_ms", 0))
        nested_actions = list(action.get("actions", []))
        for index in range(times):
            execute_actions(nested_actions, input_context)
            if delay_ms > 0 and index < times - 1:
                time.sleep(delay_ms / 1000)
    else:
        raise ValueError(f"Unsupported action type: {action_type}")


def normalize_key(key_name: str) -> str:
    return KEY_ALIASES.get(key_name.lower(), key_name)


def should_use_background(input_context: InputContext | None) -> bool:
    return input_context is not None and input_context.use_background


def post_key_press(hwnd: int, key_name: str) -> None:
    post_key(hwnd, key_name, is_down=True)
    time.sleep(0.04)
    post_key(hwnd, key_name, is_down=False)


def post_key(hwnd: int, key_name: str, is_down: bool) -> None:
    vk_code = resolve_vk_code(key_name)
    is_alt = vk_code == VK_KEYS["alt"]
    if is_alt:
        message = WM_SYSKEYDOWN if is_down else WM_SYSKEYUP
    else:
        message = WM_KEYDOWN if is_down else WM_KEYUP

    scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
    lparam = 1 | (scan_code << 16)
    if not is_down:
        lparam |= 0xC0000000
    user32.PostMessageW(wintypes.HWND(hwnd), message, vk_code, lparam)


def post_mouse_click(hwnd: int, button: str, action: Action) -> None:
    x, y = get_click_point(hwnd, action)
    lparam = make_lparam(x, y)
    if button.lower() == "right":
        down_message = WM_RBUTTONDOWN
        up_message = WM_RBUTTONUP
        wparam = MK_RBUTTON
    else:
        down_message = WM_LBUTTONDOWN
        up_message = WM_LBUTTONUP
        wparam = MK_LBUTTON

    user32.PostMessageW(wintypes.HWND(hwnd), down_message, wparam, lparam)
    time.sleep(0.04)
    user32.PostMessageW(wintypes.HWND(hwnd), up_message, 0, lparam)


def get_click_point(hwnd: int, action: Action) -> tuple[int, int]:
    if "x" in action and "y" in action:
        return int(action["x"]), int(action["y"])

    point = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    user32.ScreenToClient(wintypes.HWND(hwnd), ctypes.byref(point))
    return int(point.x), int(point.y)


def make_lparam(x: int, y: int) -> int:
    return (y & 0xFFFF) << 16 | (x & 0xFFFF)


def resolve_vk_code(key_name: str) -> int:
    normalized = key_name.lower()
    if normalized in VK_KEYS:
        return VK_KEYS[normalized]
    if len(normalized) == 1:
        return ord(normalized.upper())
    raise ValueError(f"Background input does not support key: {key_name}")
