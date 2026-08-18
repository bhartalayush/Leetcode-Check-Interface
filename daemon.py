import time
import db
import logic
import blocker
import verifier
from winotify import Notification, audio

def main_loop():
    print("DSA Lock Daemon starting...")
    db.init_db()
    
    # Track when we last verified LeetCode (every 5 minutes / 300 seconds)
    last_leetcode_sync = 0
    # Track when we last rolled over / checked midnight
    last_day_check = 0
    
    # Store previous lock state to trigger notifications on lock/unlock transitions
    was_locked = logic.is_locked()
    
    while True:
        try:
            current_time = time.time()
            today = logic.get_today_date_str()
            
            # 1. Day Rollover check (every 30 seconds)
            if current_time - last_day_check > 30:
                logic.init_today_stats(today)
                last_day_check = current_time
                
            # 2. LeetCode Submissions Sync (every 5 minutes)
            if current_time - last_leetcode_sync > 300:
                print("Syncing LeetCode submissions...")
                verifier.sync_leetcode_submissions()
                last_leetcode_sync = current_time
                
            # 3. Process Block Enforcement (every 2 seconds for responsiveness)
            is_currently_locked = logic.is_locked()
            
            # Transition notifications
            if is_currently_locked and not was_locked:
                # Lock activated
                try:
                    toast = Notification(
                        app_id="DSA Lock",
                        title="DSA Lock Activated!",
                        msg="You have outstanding debt. Recreational apps are now locked.",
                        duration="long"
                    )
                    toast.set_audio(audio.Reminder, loop=False)
                    toast.show()
                except Exception as e:
                    print(f"Could not show notification: {e}")
            elif not is_currently_locked and was_locked:
                # Lock cleared
                try:
                    toast = Notification(
                        app_id="DSA Lock",
                        title="System Unlocked!",
                        msg="Congratulations! Today's DSA requirement/debt is cleared.",
                        duration="short"
                    )
                    toast.set_audio(audio.Default, loop=False)
                    toast.show()
                except Exception as e:
                    print(f"Could not show notification: {e}")
                    
            was_locked = is_currently_locked
            
            if is_currently_locked:
                blocker.enforce_blocks()
                
            # Sleep 2 seconds
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("DSA Lock Daemon stopping gracefully.")
            break
        except Exception as e:
            print(f"Error in Daemon loop: {e}")
            time.sleep(5) # Delay retry on error

if __name__ == "__main__":
    main_loop()
