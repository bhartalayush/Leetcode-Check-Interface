import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    if not is_admin():
        # Re-run current script with admin privileges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

if __name__ == "__main__":
    if is_admin():
        print("Running with administrator privileges.")
    else:
        print("Requesting administrator privileges...")
        run_as_admin()
