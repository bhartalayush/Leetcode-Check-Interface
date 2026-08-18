import psutil
import pygetwindow as gw
import db
import logic

import win32gui
import win32process
import win32con
import hosts_blocker

# Browsers commonly used on Windows
BROWSER_PROCESSES = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"]

def get_blocklist_apps():
    apps_str = db.get_setting("blocklist_apps", "")
    if not apps_str:
        return []
    return [app.strip().lower() for app in apps_str.split(",") if app.strip()]

def get_blocklist_domains():
    domains_str = db.get_setting("blocklist_domains", "")
    if not domains_str:
        return []
    return [dom.strip().lower() for dom in domains_str.split(",") if dom.strip()]

def enforce_blocks():
    locked = logic.is_locked()
    if not locked:
        return
        
    blocked_domains = get_blocklist_domains()
    blocked_apps = get_blocklist_apps()
    
    # 1. Block standalone applications (by process name)
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name_lower = proc.info['name'].lower()
            if name_lower in blocked_apps:
                proc.terminate()
                print(f"Blocked process terminated: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # 2. Block entertainment sites on browsers using ctypes User32 API
    # We close the browser window/tab immediately if a blocked domain is open.
    # To force the browser to release socket memory, we close the window.
    try:
        import ctypes
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        
        def enum_opt_callback(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value.lower()
                    
                    for domain in blocked_domains:
                        keyword = domain.split(".")[0]
                        if keyword in title:
                            # Send close message to that window/tab
                            user32.PostMessageW(hwnd, 0x0010, 0, 0) # WM_CLOSE
                            print(f"Closed window matching domain '{domain}' (Title: {buffer.value})")
                            break
            return True
            
        callback_func = WNDENUMPROC(enum_opt_callback)
        user32.EnumWindows(callback_func, 0)
    except Exception as e:
        print(f"Error checking window titles: {e}")

if __name__ == "__main__":
    print("Testing block enforcement. Active lock state:", logic.is_locked())
    enforce_blocks()
