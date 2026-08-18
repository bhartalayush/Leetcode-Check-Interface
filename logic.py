import datetime
import db

def get_difficulty_points():
    return {
        "Easy": float(db.get_setting("easy_points", 1.0)),
        "Medium": float(db.get_setting("medium_points", 2.0)),
        "Hard": float(db.get_setting("hard_points", 4.0))
    }

def get_today_date_str():
    return datetime.date.today().strftime("%Y-%m-%d")

def is_holiday(date_str, conn=None):
    if not conn:
        conn = db.get_connection()
        close_conn = True
    else:
        close_conn = False
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM holidays WHERE date = ?", (date_str,))
    row = cursor.fetchone()
    if close_conn:
        conn.close()
    return row is not None

def init_today_stats(date_str, conn=None):
    if not conn:
        conn = db.get_connection()
        close_conn = True
    else:
        close_conn = False
        
    cursor = conn.cursor()
    
    # 1. Fetch previous day's stats if any to carry over debt and streak
    cursor.execute("SELECT date, debt, streak, longest_streak FROM daily_stats ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    
    # If today is a holiday, daily target is 0 points.
    is_today_holiday = is_holiday(date_str, conn)
    target_points = 0.0 if is_today_holiday else float(db.get_setting("daily_target", 2.0))
    max_debt = float(db.get_setting("max_debt", 8.0))
    
    if row:
        prev_date, prev_debt, prev_streak, prev_longest = row
        if prev_date == date_str:
            # Already initialized for today. If holiday status changed, we update target_points
            cursor.execute("UPDATE daily_stats SET target_points = ? WHERE date = ?", (target_points, date_str))
            conn.commit()
            if close_conn:
                conn.close()
            return
            
        # Day rollover! Calculate unpaid points from previous days
        d1 = datetime.datetime.strptime(prev_date, "%Y-%m-%d").date()
        d2 = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        days_gap = (d2 - d1).days
        
        # Calculate streak break
        cursor.execute("SELECT completed_points, target_points, debt FROM daily_stats WHERE date = ?", (prev_date,))
        prev_day_stats = cursor.fetchone()
        
        streak = prev_streak
        if days_gap > 1:
            # If there was a gap, we must check if the skipped days were all holidays.
            # If any skipped day was not a holiday and had completed < target, streak resets.
            temp_date = d1
            for _ in range(days_gap - 1):
                temp_date += datetime.timedelta(days=1)
                temp_date_str = temp_date.strftime("%Y-%m-%d")
                if not is_holiday(temp_date_str, conn):
                    streak = 0
                    break
        elif days_gap == 1 and prev_day_stats:
            comp, target, dbt = prev_day_stats
            # Only reset streak if it was not a holiday (target > 0) and progress < target
            if target > 0.0 and comp < target:
                streak = 0
                
        # Rebuild daily stats step by step for missing days if any
        current_debt = prev_debt
        temp_date = d1
        for _ in range(days_gap - 1):
            temp_date += datetime.timedelta(days=1)
            temp_date_str = temp_date.strftime("%Y-%m-%d")
            
            # If the skipped day was a holiday, target_points = 0. No new debt is added.
            day_is_hol = is_holiday(temp_date_str, conn)
            day_target = 0.0 if day_is_hol else float(db.get_setting("daily_target", 2.0))
            
            # New debt accumulates target of missed non-holiday day
            current_debt = min(current_debt + day_target, max_debt)
            
            cursor.execute("""
            INSERT OR IGNORE INTO daily_stats (date, target_points, completed_points, debt, streak, longest_streak)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (temp_date_str, day_target, 0.0, current_debt, 0, prev_longest))
            
        # Finally, today's start:
        cursor.execute("SELECT completed_points, target_points FROM daily_stats WHERE date = ?", (prev_date,))
        y_comp, y_target = cursor.fetchone()
        unpaid = max(0.0, y_target - y_comp)
        
        today_start_debt = min(prev_debt + unpaid, max_debt)
        
        cursor.execute("""
        INSERT OR IGNORE INTO daily_stats (date, target_points, completed_points, debt, streak, longest_streak)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (date_str, target_points, 0.0, today_start_debt, streak, prev_longest))
    else:
        # First time ever running the app
        cursor.execute("""
        INSERT OR IGNORE INTO daily_stats (date, target_points, completed_points, debt, streak, longest_streak)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (date_str, target_points, 0.0, 0.0, 0, 0))
        
    conn.commit()
    if close_conn:
        conn.close()

def add_problem(name, url, difficulty, date_solved=None, verified=0):
    if not date_solved:
        date_solved = get_today_date_str()
        
    init_today_stats(date_solved)
    
    diff_pts = get_difficulty_points()
    points = diff_pts.get(difficulty, 0.0)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Insert the problem
    cursor.execute("""
    INSERT INTO problems (name, url, difficulty, date_solved, points, verified)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (name, url, difficulty, date_solved, points, verified))
    
    # If this problem was in the planner, mark it as solved
    # Extract slug/title for loose matching
    slug = url.split("/problems/")[-1].strip("/").split("/")[0] if "/problems/" in url else name.lower().replace(" ", "-")
    cursor.execute("""
    UPDATE planner 
    SET status = 'solved' 
    WHERE url LIKE ? OR LOWER(name) = ?
    """, (f"%{slug}%", name.lower()))
    
    # 2. Update today's completed points
    cursor.execute("""
    UPDATE daily_stats
    SET completed_points = completed_points + ?
    WHERE date = ?
    """, (points, date_solved))
    
    # 3. Recalculate debt and streak
    # Get current completed, target, and debt
    cursor.execute("SELECT completed_points, target_points, debt, streak, longest_streak FROM daily_stats WHERE date = ?", (date_solved,))
    comp, target, debt, streak, longest = cursor.fetchone()
    
    # Debt reduction rule:
    # If we complete points, it first covers today's target. Any excess covers the debt.
    # Today's excess points = max(0, completed_points - target_points)
    # New debt = max(0, start_of_day_debt - excess)
    # But wait, let's track the start of day debt. How?
    # At the start of the day, before any problem is solved,completed_points = 0.
    # The debt value in the db is the start of day debt until we solve problems.
    # Wait, if we keep modifying the debt column, we lose the start_of_day_debt reference.
    # A cleaner way:
    # Today's net debt = max(0, (previous_day_debt + unpaid_yesterday) - max(0, completed_points - target_points))
    # Let's query previous day's stats to compute this dynamically and keep the DB state correct!
    cursor.execute("SELECT date, debt, target_points, completed_points FROM daily_stats WHERE date < ? ORDER BY date DESC LIMIT 1", (date_solved,))
    prev_row = cursor.fetchone()
    
    start_debt = 0.0
    if prev_row:
        _, p_debt, p_target, p_comp = prev_row
        unpaid = max(0.0, p_target - p_comp)
        max_debt = float(db.get_setting("max_debt", 8.0))
        start_debt = min(p_debt + unpaid, max_debt)
        
    excess = max(0.0, comp - target)
    new_debt = max(0.0, start_debt - excess)
    
    # Update streak:
    # Today's target is met if completed_points >= target_points
    if comp >= target and streak == 0:
        # Check if yesterday was also completed to continue streak, or if we are starting a new streak
        if prev_row and prev_row[3] >= prev_row[2]: # yesterday completed >= yesterday target
            # Get yesterday's streak
            cursor.execute("SELECT streak FROM daily_stats WHERE date < ? ORDER BY date DESC LIMIT 1", (date_solved,))
            ystreak = cursor.fetchone()[0]
            streak = ystreak + 1
        else:
            streak = 1
    elif comp >= target and streak > 0:
        pass # Already incremented or continuing
    else:
        # Target not met yet
        streak = 0
        
    new_longest = max(longest, streak)
    
    cursor.execute("""
    UPDATE daily_stats
    SET debt = ?, streak = ?, longest_streak = ?
    WHERE date = ?
    """, (new_debt, streak, new_longest, date_solved))
    
    conn.commit()
    conn.close()

def is_locked(date_str=None):
    # Check Master Kill Switch override first
    if db.get_setting("master_kill_switch_active", "False") == "True":
        return False

    # Check if app is temporarily suspended (e.g. for 2 hours)
    if db.get_setting("app_suspended", "False") == "True":
        import time
        susp_time = float(db.get_setting("app_suspension_time", 0.0))
        if time.time() - susp_time < 7200: # 2 hours = 7200 seconds
            return False
        else:
            db.set_setting("app_suspended", "False")
            db.set_setting("app_suspension_time", "0")

    # Trial Lock feature overrides unlock state
    if db.get_setting("trial_lock_active", "False") == "True":
        return True

    # Check emergency unlock duration (30 mins = 1800 seconds)
    if db.get_setting("emergency_unlocked", "False") == "True":
        import time
        unlock_time = float(db.get_setting("emergency_unlock_time", 0.0))
        if time.time() - unlock_time < 1800:
            return False
        else:
            # Expired! Reset bypass values
            db.set_setting("emergency_unlocked", "False")
            db.set_setting("emergency_unlock_time", "0")
        
    if not date_str:
        date_str = get_today_date_str()
    init_today_stats(date_str)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT target_points, completed_points, debt FROM daily_stats WHERE date = ?", (date_str,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        target, comp, debt = row
        return debt > 0.0
        
    return False

def get_recommendations():
    # Recommend problems from planner matching the outstanding target/debt points
    today = get_today_date_str()
    init_today_stats(today)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT target_points, completed_points, debt FROM daily_stats WHERE date = ?", (today,))
    row = cursor.fetchone()
    
    needed = 0.0
    if row:
        target, comp, debt = row
        needed = max(0.0, debt) # If in debt, we need that many points. 
        # If no debt, we still might want to show recommendations to complete today's target
        if needed == 0.0:
            needed = max(0.0, target - comp)
            
    cursor.execute("SELECT name, url, difficulty FROM planner WHERE status = 'pending'")
    planner_probs = cursor.fetchall()
    conn.close()
    
    if needed <= 0.0:
        return []
        
    # Map difficulties to points
    pts_map = get_difficulty_points()
    
    # Basic greedy match or filter
    recommendations = []
    for name, url, diff in planner_probs:
        pts = pts_map.get(diff, 1.0)
        recommendations.append({
            "name": name,
            "url": url,
            "difficulty": diff,
            "points": pts
        })
        
    # Sort recommendations: prioritize files that can help clear the target/debt nicely
    # (e.g. if we need exactly 2 points, a Medium or 2 Easies are good).
    recommendations.sort(key=lambda x: abs(x["points"] - needed))
    return recommendations[:3]
