import db
import logic
import datetime

def rebuild_all_history():
    """
    Deletes all daily stats and regenerates them step-by-step from the very first recorded day
    to today. Re-evaluates holiday rules, solved problems, debts, and streaks sequentially.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch first date from problems or statistics
    cursor.execute("SELECT MIN(date_solved) FROM problems")
    p_min = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(date) FROM daily_stats")
    s_min = cursor.fetchone()[0]
    
    start_date_str = p_min or s_min or logic.get_today_date_str()
    
    # 2. Delete existing daily stats history
    cursor.execute("DELETE FROM daily_stats")
    conn.commit()
    
    # 3. Rebuild day-by-day sequentially up to today
    d1 = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    d2 = datetime.date.today()
    
    days_to_rebuild = (d2 - d1).days + 1
    
    temp_date = d1
    for i in range(days_to_rebuild):
        date_str = temp_date.strftime("%Y-%m-%d")
        
        # Initialize stats for this date (handles yesterday rollover debt/streaks)
        db.get_connection().close() # close local conn to allow logic module to run cleanly
        logic.init_today_stats(date_str)
        
        # Re-apply completed points for problems solved on this date
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, url, difficulty, points, verified FROM problems WHERE date_solved = ?", (date_str,))
        probs_today = cursor.fetchall()
        
        if probs_today:
            # Let's update stats based on today's solved problems
            # Sum up points
            total_pts = sum(float(p[3]) for p in probs_today)
            cursor.execute("UPDATE daily_stats SET completed_points = ? WHERE date = ?", (total_pts, date_str))
            
            # Recalculate debt & streaks
            # Get yesterday stats
            cursor.execute("SELECT date, debt, target_points, completed_points FROM daily_stats WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
            prev_row = cursor.fetchone()
            
            start_debt = 0.0
            if prev_row:
                _, p_debt, p_target, p_comp = prev_row
                unpaid = max(0.0, p_target - p_comp)
                max_debt = float(db.get_setting("max_debt", 8.0))
                start_debt = min(p_debt + unpaid, max_debt)
                
            cursor.execute("SELECT target_points, streak, longest_streak FROM daily_stats WHERE date = ?", (date_str,))
            target, streak, longest = cursor.fetchone()
            
            excess = max(0.0, total_pts - target)
            new_debt = max(0.0, start_debt - excess)
            
            # Streak logic
            if total_pts >= target:
                if prev_row and prev_row[3] >= prev_row[2]:
                    cursor.execute("SELECT streak FROM daily_stats WHERE date < ? ORDER BY date DESC LIMIT 1", (date_str,))
                    ystreak = cursor.fetchone()[0]
                    streak = ystreak + 1
                else:
                    streak = 1
            else:
                streak = 0
                
            new_longest = max(longest, streak)
            cursor.execute("""
            UPDATE daily_stats
            SET debt = ?, streak = ?, longest_streak = ?
            WHERE date = ?
            """, (new_debt, streak, new_longest, date_str))
            conn.commit()
            
        temp_date += datetime.timedelta(days=1)
        
    if conn:
        conn.close()
    print("History rebuild complete.")
