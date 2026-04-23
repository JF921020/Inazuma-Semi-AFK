import ctypes


VK_CODE_MAP = {
    "0": 0x30,
    "1": 0x31,
    "ALT": 0x12,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F12": 0x7B,
}


def is_key_pressed(key_name: str) -> bool:
    vk_code = VK_CODE_MAP.get(key_name.upper())
    if vk_code is None:
        supported = ", ".join(sorted(VK_CODE_MAP))
        raise ValueError(f"目前只支援這些熱鍵: {supported}")
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)


def is_hotkey_pressed(*key_names: str) -> bool:
    return all(is_key_pressed(key_name) for key_name in key_names)


class HotkeyLatch:
    def __init__(self, *keys: str) -> None:
        self.keys = keys
        self._latched = False

    def consume_press(self) -> bool:
        pressed = is_hotkey_pressed(*self.keys)
        if pressed and not self._latched:
            self._latched = True
            return True
        if not pressed:
            self._latched = False
        return False
