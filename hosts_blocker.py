import os

# Host file path on Windows
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"

def block_domains_hosts(domains):
    try:
        with open(HOSTS_PATH, "r") as file:
            content = file.read()
            
        lines_to_add = []
        for domain in domains:
            # We want to block both domain.com and www.domain.com
            for host in [domain, f"www.{domain}"]:
                entry = f"{REDIRECT_IP} {host}"
                if entry not in content:
                    lines_to_add.append(entry)
                    
        if lines_to_add:
            # Write access needs admin privileges. We'll attempt it or log it
            import subprocess
            with open(HOSTS_PATH, "a") as file:
                file.write("\n" + "\n".join(lines_to_add) + "\n")
            # Flush local DNS cache
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            print("Successfully added domains to hosts file and flushed DNS cache.")
            return True
    except PermissionError:
        print("Permission Denied: Run script as administrator to block domains via hosts.")
    except Exception as e:
        print(f"Error updating hosts file: {e}")
    return False

def unblock_domains_hosts(domains):
    try:
        with open(HOSTS_PATH, "r") as file:
            lines = file.readlines()
            
        new_lines = []
        modified = False
        for line in lines:
            should_remove = False
            for domain in domains:
                if domain in line.lower():
                    should_remove = True
                    modified = True
                    break
            if not should_remove:
                new_lines.append(line)
                
            import subprocess
            with open(HOSTS_PATH, "w") as file:
                file.writelines(new_lines)
            # Flush local DNS cache
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            print("Successfully removed domains from hosts file and flushed DNS cache.")
            return True
    except PermissionError:
        print("Permission Denied: Run script as administrator to unblock domains via hosts.")
    except Exception as e:
        print(f"Error restoring hosts file: {e}")
    return False
