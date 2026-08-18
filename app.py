import streamlit as st
import datetime
import db
import logic
import verifier

st.set_page_config(
    page_title="DSA Lock",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db.init_db()

# Sync on app load
today = logic.get_today_date_str()
logic.init_today_stats(today)

# Theme CSS settings (Dark theme and clean spacing)
st.markdown("""
<style>
    .reportview-container {
        background-color: #0e1117;
        color: #ffffff;
    }
    .main-title {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        font-size: 32px;
        color: #ff4b4b;
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #1e222b;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2d3139;
    }
    .metric-value {
        font-size: 40px;
        font-weight: bold;
        color: #ff4b4b;
    }
    .metric-label {
        font-size: 14px;
        color: #8a92a6;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to get stats
def get_stats():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT target_points, completed_points, debt, streak, longest_streak 
    FROM daily_stats 
    WHERE date = ?
    """, (today,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "target": row[0],
            "completed": row[1],
            "debt": row[2],
            "streak": row[3],
            "longest_streak": row[4]
        }
    return {"target": 2.0, "completed": 0.0, "debt": 0.0, "streak": 0, "longest_streak": 0}

stats = get_stats()
locked = logic.is_locked()

# Sidebar Navigation
st.sidebar.markdown("<h2 style='text-align: center;'>🔒 DSA Lock</h2>", unsafe_allow_html=True)

# Show locking state in sidebar
if locked:
    st.sidebar.error("🔴 LOCK MODE ACTIVE")
else:
    st.sidebar.success("🟢 UNLOCKED")

menu = st.sidebar.radio("Go to", ["Dashboard", "DSA Planner", "Settings", "Emergency Unlock"])

# 1. Dashboard View
if menu == "Dashboard":
    st.markdown("<div class='main-title'>DSA Lock Dashboard</div>", unsafe_allow_html=True)
    
    # Grid metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-label'>Today's Target</div>
            <div class='metric-value'>{stats['target']:.1f} pts</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-label'>Completed Today</div>
            <div class='metric-value'>{stats['completed']:.1f} pts</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-label'>Current Debt</div>
            <div class='metric-value'>{stats['debt']:.1f} pts</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-container'>
            <div class='metric-label'>🔥 Current Streak</div>
            <div class='metric-value'>{stats['streak']} days</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Lock Warning
    if locked:
        st.markdown(f"""
        <div style="background-color: #3d0c0c; border: 1px solid #ff4b4b; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h3 style="color: #ff4b4b; margin: 0 0 10px 0; font-family: sans-serif;">⚠️ Laptop Access Restricted</h3>
            <p style="color: #ffcccc; margin: 0 0 15px 0; font-size: 15px;">You carry a DSA debt of <b>{stats['debt']:.1f} points</b>. Recreational apps and sites are locked.</p>
            <a href="https://leetcode.com/problemset/all/" target="_blank" style="background-color: #ff4b4b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Open LeetCode →</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #0c3d1e; border: 1px solid #28a745; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h3 style="color: #28a745; margin: 0 0 5px 0; font-family: sans-serif;">🎉 System Unlocked & Safe</h3>
            <p style="color: #ccffdd; margin: 0; font-size: 15px;">Keep up the streak! You have no outstanding debt today.</p>
        </div>
        """, unsafe_allow_html=True)
    
    col_entry, col_list = st.columns([1, 1])
    
    with col_entry:
        st.subheader("Add Completed Problem")
        with st.form("problem_form", clear_on_submit=True):
            prob_name = st.text_input("Problem Name", placeholder="e.g. Two Sum")
            prob_url = st.text_input("LeetCode URL", placeholder="https://leetcode.com/problems/two-sum/")
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            date_solved = st.date_input("Date Solved", datetime.date.today())
            
            submit = st.form_submit_button("Submit & Verify")
            if submit:
                if prob_name and prob_url:
                    logic.add_problem(
                        name=prob_name,
                        url=prob_url,
                        difficulty=difficulty,
                        date_solved=date_solved.strftime("%Y-%m-%d"),
                        verified=0 # Manual verified
                    )
                    st.success(f"Successfully added '{prob_name}'!")
                    st.rerun()
                else:
                    st.error("Please fill in both Name and URL.")

        # Quick verification trigger
        leetcode_user = db.get_setting("leetcode_username", "")
        if leetcode_user:
            if st.button("🔄 Sync with LeetCode Profile"):
                with st.spinner("Checking your recent submissions..."):
                    verifier.sync_leetcode_submissions()
                st.success("Submissions checked!")
                st.rerun()

    with col_list:
        st.subheader("Today's Solved Problems")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, difficulty, points, verified FROM problems WHERE date_solved = ?", (today,))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            for r_name, r_diff, r_pts, r_ver in rows:
                ver_badge = "✅ Auto" if r_ver == 1 else "📝 Manual"
                st.markdown(f"**✓ {r_name}** — {r_diff} — `+{r_pts:.1f} pts` ({ver_badge})")
        else:
            st.info("No problems completed today yet.")

# 2. DSA Planner View
elif menu == "DSA Planner":
    st.markdown("<div class='main-title'>DSA Queue & Recommendations</div>", unsafe_allow_html=True)
    
    # Show recommendations
    recs = logic.get_recommendations()
    if recs:
        st.subheader("💡 Suggested Next Steps to Clear Debt/Target")
        for rec in recs:
            st.info(f"👉 Solve **[{rec['name']}]({rec['url']})** ({rec['difficulty']}) for **+{rec['points']:.1f} pts**")
            
    st.markdown("---")
    
    col_add_plan, col_queue = st.columns([1, 1])
    
    with col_add_plan:
        st.subheader("Queue Up a New Problem")
        with st.form("planner_form", clear_on_submit=True):
            plan_name = st.text_input("Problem Name", placeholder="e.g. Valid Parentheses")
            plan_url = st.text_input("LeetCode URL")
            plan_diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            
            plan_submit = st.form_submit_button("Add to Queue")
            if plan_submit:
                if plan_name and plan_url:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO planner (name, url, difficulty, added_date, status)
                    VALUES (?, ?, ?, ?, 'pending')
                    """, (plan_name, plan_url, plan_diff, today))
                    conn.commit()
                    conn.close()
                    st.success(f"Added '{plan_name}' to planner queue!")
                    st.rerun()
                else:
                    st.error("Please provide both name and URL.")

    with col_queue:
        st.subheader("Your Pending DSA Queue")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, url, difficulty FROM planner WHERE status = 'pending'")
        items = cursor.fetchall()
        conn.close()
        
        if items:
            for item_id, name, url, diff in items:
                col_i, col_d = st.columns([4, 1])
                col_i.markdown(f"🔗 [{name}]({url}) ({diff})")
                if col_d.button("Remove", key=f"del_{item_id}"):
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM planner WHERE id = ?", (item_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
        else:
            st.info("Your queue is currently empty.")

# 3. Settings View
elif menu == "Settings":
    st.markdown("<div class='main-title'>Configuration & Settings</div>", unsafe_allow_html=True)
    
    with st.form("settings_form"):
        target_pts = st.number_input("Daily Target Points", min_value=0.5, max_value=10.0, value=float(db.get_setting("daily_target", 2.0)))
        max_debt_pts = st.number_input("Maximum Accrued Debt Points", min_value=2.0, max_value=20.0, value=float(db.get_setting("max_debt", 8.0)))
        
        easy_pts = st.number_input("Points per Easy", min_value=0.0, value=float(db.get_setting("easy_points", 1.0)))
        med_pts = st.number_input("Points per Medium", min_value=0.0, value=float(db.get_setting("medium_points", 2.0)))
        hard_pts = st.number_input("Points per Hard", min_value=0.0, value=float(db.get_setting("hard_points", 4.0)))
        
        leetcode_user = st.text_input("LeetCode Username (For Auto Verification)", value=db.get_setting("leetcode_username", ""))
        
        pin_val = st.text_input("Emergency Unlock PIN (Numbers only)", type="password", value=db.get_setting("emergency_pin", "1234"))
        autostart_val = st.checkbox("Start Automatically with Windows", value=(db.get_setting("start_with_windows", "False") == "True"))
        
        save_settings = st.form_submit_button("Save Core Settings")
        if save_settings:
            db.set_setting("daily_target", target_pts)
            db.set_setting("max_debt", max_debt_pts)
            db.set_setting("easy_points", easy_pts)
            db.set_setting("medium_points", med_pts)
            db.set_setting("hard_points", hard_pts)
            db.set_setting("leetcode_username", leetcode_user)
            db.set_setting("emergency_pin", pin_val)
            db.set_setting("start_with_windows", str(autostart_val))
            st.success("Core settings updated successfully!")
            st.rerun()

    # Blocklist Apps UI Manager
    st.markdown("---")
    st.subheader("🚫 Blocked Applications (.exe)")
    col_add_app, col_list_app = st.columns([1, 1])
    
    # Read Apps blocklist from db
    app_list_raw = db.get_setting("blocklist_apps", "")
    current_apps = [a.strip().lower() for a in app_list_raw.split(",") if a.strip()]
    
    with col_add_app:
        st.markdown("**Add App to Blocklist**")
        new_app_input = st.text_input("Enter Process Name", placeholder="e.g. steam.exe")
        if st.button("Block App"):
            new_app_clean = new_app_input.strip().lower()
            if new_app_clean:
                if not new_app_clean.endswith(".exe"):
                    new_app_clean += ".exe"
                if new_app_clean not in current_apps:
                    current_apps.append(new_app_clean)
                    db.set_setting("blocklist_apps", ",".join(current_apps))
                    st.success(f"Added {new_app_clean} to blocklist!")
                    st.rerun()
                else:
                    st.warning("App is already blocked.")
            else:
                st.error("Please enter a valid process name.")
                
    with col_list_app:
        st.markdown("**Currently Blocked Apps**")
        if current_apps:
            for app in current_apps:
                col_txt, col_btn = st.columns([3, 1])
                col_txt.write(f"🎮 `{app}`")
                if col_btn.button("Unblock", key=f"unblock_app_{app}"):
                    current_apps.remove(app)
                    db.set_setting("blocklist_apps", ",".join(current_apps))
                    st.rerun()
        else:
            st.info("No applications are currently blocked.")

    # Blocklist Domains/Websites UI Manager
    st.markdown("---")
    st.subheader("🌐 Blocked Websites / URLs")
    col_add_dom, col_list_dom = st.columns([1, 1])
    
    # Read Domains blocklist from db
    dom_list_raw = db.get_setting("blocklist_domains", "")
    current_domains = [d.strip().lower() for d in dom_list_raw.split(",") if d.strip()]
    
    with col_add_dom:
        st.markdown("**Add Website/URL to Blocklist**")
        new_dom_input = st.text_input("Enter URL or Domain Name", placeholder="e.g. youtube.com or https://instagram.com/inbox")
        if st.button("Block Website"):
            item_cleaned = new_dom_input.strip().lower()
            if item_cleaned:
                # Clean URL components automatically
                if "://" in item_cleaned:
                    item_cleaned = item_cleaned.split("://")[-1]
                item_cleaned = item_cleaned.split("/")[0]
                item_cleaned = item_cleaned.split(":")[0]
                if item_cleaned.startswith("www."):
                    item_cleaned = item_cleaned[4:]
                    
                if item_cleaned:
                    if item_cleaned not in current_domains:
                        current_domains.append(item_cleaned)
                        db.set_setting("blocklist_domains", ",".join(current_domains))
                        st.success(f"Added {item_cleaned} to blocklist!")
                        st.rerun()
                    else:
                        st.warning("Website is already blocked.")
            else:
                st.error("Please enter a valid URL.")
                
    with col_list_dom:
        st.markdown("**Currently Blocked Websites**")
        if current_domains:
            for domain in current_domains:
                col_txt, col_btn = st.columns([3, 1])
                col_txt.write(f"🌐 `{domain}`")
                if col_btn.button("Unblock", key=f"unblock_dom_{domain}"):
                    current_domains.remove(domain)
                    db.set_setting("blocklist_domains", ",".join(current_domains))
                    st.rerun()
        else:
            st.info("No websites are currently blocked.")

    st.markdown("---")
    st.subheader("🧪 Testing & Trial Lock")
    trial_active = db.get_setting("trial_lock_active", "False") == "True"
    if trial_active:
        st.warning("⚠️ Trial Lock is currently ACTIVE. Blocker will enforce access restriction even if you have no debt.")
        if st.button("Disable Trial Lock"):
            db.set_setting("trial_lock_active", "False")
            st.rerun()
    else:
        st.info("Trial Lock is inactive. You can simulate locking your computer for testing by turning it on.")
        if st.button("Enable Trial Lock"):
            db.set_setting("trial_lock_active", "True")
            # Deactivate emergency bypass temporarily to force the lock
            db.set_setting("emergency_unlocked", "False")
            st.rerun()

    st.markdown("---")
    st.subheader("🚨 Master Kill Switch")
    kill_active = db.get_setting("master_kill_switch_active", "False") == "True"
    if kill_active:
        st.error("🔴 MASTER KILL SWITCH IS ACTIVE. ALL BLOCKING LAWS ARE SUSPENDED PERMANENTLY UNTIL TURNED OFF.")
        if st.button("Deactivate Kill Switch"):
            db.set_setting("master_kill_switch_active", "False")
            st.rerun()
    else:
        st.info("Activating this switch will completely disable the application blocker at once. Use this if the app starts misbehaving.")
        if st.button("Activate Master Kill Switch"):
            db.set_setting("master_kill_switch_active", "True")
            # Automatically wipe all blocked domains from the hosts file
            try:
                import hosts_blocker
                blocked_domains = [dom.strip().lower() for dom in db.get_setting("blocklist_domains", "").split(",") if dom.strip()]
                if blocked_domains:
                    hosts_blocker.unblock_domains_hosts(blocked_domains)
            except Exception as e:
                print(f"Kill switch hosts file clean error: {e}")
            st.rerun()

    st.markdown("---")
    st.subheader("⏸️ Temporary Suspension")
    is_suspended = db.get_setting("app_suspended", "False") == "True"
    if is_suspended:
        import time
        susp_time = float(db.get_setting("app_suspension_time", 0.0))
        elapsed = time.time() - susp_time
        remaining_mins = max(0.0, (7200 - elapsed) / 60.0)
        st.warning(f"⚠️ App blocking is currently SUSPENDED. Remaining time: {remaining_mins:.1f} minutes.")
        if st.button("Resume Blocker Now"):
            db.set_setting("app_suspended", "False")
            db.set_setting("app_suspension_time", "0")
            st.rerun()
    else:
        st.info("You can temporarily pause all application and browser blocking for 2 hours (e.g. for long focus sessions or system updates).")
        if st.button("Suspend Blocker for 2 Hours"):
            import time
            db.set_setting("app_suspended", "True")
            db.set_setting("app_suspension_time", str(time.time()))
            st.rerun()

    st.markdown("---")
    st.subheader("📆 Holidays (Skip Targets & Debt)")
    
    col_add_hol, col_list_hol = st.columns([1, 1])
    
    with col_add_hol:
        st.markdown("**Add Holiday Date**")
        hol_date = st.date_input("Select Date for Holiday", datetime.date.today())
        if st.button("Add Holiday"):
            date_str = hol_date.strftime("%Y-%m-%d")
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO holidays (date) VALUES (?)", (date_str,))
                conn.commit()
                st.success(f"Added {date_str} as holiday!")
                # Retroactively rebuild statistics to recalculate debt
                import history_rebuilder
                history_rebuilder.rebuild_all_history()
                st.rerun()
            except sqlite3.IntegrityError:
                st.warning("This date is already a holiday.")
            finally:
                conn.close()
                
    with col_list_hol:
        st.markdown("**Configured Holidays**")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT date FROM holidays ORDER BY date ASC")
        holidays_list = cursor.fetchall()
        conn.close()
        
        if holidays_list:
            for (h_date,) in holidays_list:
                col_h_txt, col_h_btn = st.columns([3, 1])
                col_h_txt.write(f"📅 {h_date}")
                if col_h_btn.button("Remove", key=f"del_hol_{h_date}"):
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM holidays WHERE date = ?", (h_date,))
                    conn.commit()
                    # Retroactively rebuild statistics to recalculate debt
                    import history_rebuilder
                    history_rebuilder.rebuild_all_history()
                    conn.close()
                    st.rerun()
        else:
            st.info("No holidays configured yet.")

# 4. Emergency Unlock View
elif menu == "Emergency Unlock":
    st.markdown("<div class='main-title'>Emergency Bypass</div>", unsafe_allow_html=True)
    st.warning("⚠️ Using the emergency bypass defeats the purpose of the app! Use only when absolutely necessary (e.g. system recovery).")
    
    unlock_active = db.get_setting("emergency_unlocked", "False") == "True"
    
    if unlock_active:
        st.success("Bypass is currently active. Access is restored.")
        if st.button("Re-enable Locks"):
            db.set_setting("emergency_unlocked", "False")
            st.rerun()
    else:
        pin_input = st.text_input("Enter 4-digit Emergency PIN", type="password")
        if st.button("Unlock (for 30 minutes)"):
            expected_pin = db.get_setting("emergency_pin", "1234")
            if pin_input == expected_pin:
                import time
                db.set_setting("emergency_unlocked", "True")
                db.set_setting("emergency_unlock_time", str(time.time()))
                st.success("Successfully Unlocked for 30 minutes!")
                st.rerun()
            else:
                st.error("Incorrect PIN.")
