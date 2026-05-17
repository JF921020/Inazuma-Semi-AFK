import win32gui
import win32con
import pygetwindow as gw

def is_real_window(hwnd):
    """檢查該視窗控制代碼 (hwnd) 是否為使用者可見的前景應用程式"""
    # 1. 必須要有視窗標題
    title = win32gui.GetWindowText(hwnd)
    if not title.strip():
        return False
    
    # 2. 視窗必須是可見的 (Visible)
    if not win32gui.IsWindowVisible(hwnd):
        return False
        
    # 3. 排除沒有實體大小的背景視窗 (例如某些常駐服務的隱形視窗)
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    if (right - left) <= 0 or (bottom - top) <= 0:
        return False
        
    # 4. 排除視窗樣式中帶有工具箱 (ToolWindow) 屬性的特殊背景視窗
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return False
        
    return True

def get_foreground_windows():
    """取得所有真正由使用者執行的視窗清單"""
    visible_windows = []
    
    # 列舉桌面所有視窗
    def enum_windows_callback(hwnd, extra):
        if is_real_window(hwnd):
            title = win32gui.GetWindowText(hwnd)
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            visible_windows.append({
                "hwnd": hwnd,
                "title": title,
                "pos": (left, top),
                "size": (right - left, bottom - top)
            })
            
    win32gui.EnumWindows(enum_windows_callback, None)
    return visible_windows

# 執行並列印結果
if __name__ == "__main__":
    all_titles = gw.getAllTitles()
    for title in all_titles:
        if title.strip():  # 過濾掉空白的視窗名稱
            print(title)
