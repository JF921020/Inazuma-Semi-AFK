from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass


user32 = ctypes.windll.user32


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str

    @property
    def label(self) -> str:
        return f"{self.title} [{self.hwnd}]"


EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def list_visible_windows() -> list[WindowInfo]:
    windows: list[WindowInfo] = []

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if title:
            windows.append(WindowInfo(hwnd=int(hwnd), title=title))
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return sorted(windows, key=lambda window: window.title.lower())


def is_window(hwnd: int) -> bool:
    return bool(user32.IsWindow(wintypes.HWND(hwnd)))
