# Start wrapper for silent background daemon launch via windows startup
import subprocess
import os

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    daemon_file = os.path.join(current_dir, "daemon.py")
    # Launch daemon process silently without window overlay
    subprocess.Popen(["pythonw", daemon_file], cwd=current_dir, creationflags=subprocess.CREATE_NO_WINDOW)
