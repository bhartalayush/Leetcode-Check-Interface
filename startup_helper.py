import os
import sys
import winshell
from win32com.client import Dispatch

def create_startup_shortcut():
    try:
        # Get startup folder path
        startup_dir = winshell.startup()
        shortcut_path = os.path.join(startup_dir, "DSALock.lnk")
        
        # Target is the bat file
        target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.bat")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.Description = "DSA Lock Launcher"
        shortcut.save()
        print("Successfully created startup shortcut.")
        return True
    except Exception as e:
        print(f"Error creating startup shortcut: {e}")
        return False

def remove_startup_shortcut():
    try:
        startup_dir = winshell.startup()
        shortcut_path = os.path.join(startup_dir, "DSALock.lnk")
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print("Successfully removed startup shortcut.")
        return True
    except Exception as e:
        print(f"Error removing startup shortcut: {e}")
        return False

if __name__ == "__main__":
    create_startup_shortcut()
