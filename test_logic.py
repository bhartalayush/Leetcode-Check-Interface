import unittest
import sqlite3
import os
import datetime
import db
import logic

class TestDSALockLogic(unittest.TestCase):
    
    def setUp(self):
        # Override DB Path to a temporary test database
        self.original_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_dsa_lock.db")
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)
        db.init_db()
        
    def tearDown(self):
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)
        db.DB_PATH = self.original_db_path

    def get_stats(self, date_str):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT target_points, completed_points, debt, streak, longest_streak FROM daily_stats WHERE date = ?", (date_str,))
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
        return None

    def test_cases(self):
        day1 = "2026-08-18"
        day2 = "2026-08-19"
        day3 = "2026-08-20"
        
        # --- Case 1: 2 Easy completed -> debt 0 ---
        logic.init_today_stats(day1)
        logic.add_problem("Two Sum", "url1", "Easy", date_solved=day1)
        logic.add_problem("Binary Search", "url2", "Easy", date_solved=day1)
        stats = self.get_stats(day1)
        self.assertEqual(stats["completed"], 2.0)
        self.assertEqual(stats["debt"], 0.0)
        self.assertEqual(stats["streak"], 1)

        # Reset database for next isolated case tests
        self.setUp()

        # --- Case 2: 1 Medium completed -> debt 0 ---
        logic.init_today_stats(day1)
        logic.add_problem("Add Two Numbers", "url3", "Medium", date_solved=day1)
        stats = self.get_stats(day1)
        self.assertEqual(stats["completed"], 2.0)
        self.assertEqual(stats["debt"], 0.0)
        self.assertEqual(stats["streak"], 1)

        self.setUp()

        # --- Case 3: 1 Easy completed today -> next day debt becomes 3 (1 unpaid + 2 new) ---
        logic.init_today_stats(day1)
        logic.add_problem("Two Sum", "url1", "Easy", date_solved=day1)
        # Advance to next day
        logic.init_today_stats(day2)
        stats_day2 = self.get_stats(day2)
        # previous debt=0, unpaid yesterday=1. Total debt=1. Daily target today=2. 
        # (Debt + Target = 3).
        self.assertEqual(stats_day2["debt"], 1.0)
        self.assertEqual(stats_day2["streak"], 0) # streak breaks

        self.setUp()

        # --- Case 4: 0 completed -> next day debt becomes 4 (2 unpaid + 2 new) ---
        logic.init_today_stats(day1)
        # Advance to next day
        logic.init_today_stats(day2)
        stats_day2 = self.get_stats(day2)
        # yesterday unpaid = 2. today start debt = 2. 
        self.assertEqual(stats_day2["debt"], 2.0)

        self.setUp()

        # --- Case 5: 1 Hard completed -> today's requirement complete, tomorrow still requires 2 ---
        logic.init_today_stats(day1)
        logic.add_problem("Merge k Sorted Lists", "url4", "Hard", date_solved=day1)
        stats = self.get_stats(day1)
        self.assertEqual(stats["completed"], 4.0)
        self.assertEqual(stats["debt"], 0.0)
        
        logic.init_today_stats(day2)
        stats_day2 = self.get_stats(day2)
        # Tomorrow still requires 2.0, starting debt is 0.0
        self.assertEqual(stats_day2["target"], 2.0)
        self.assertEqual(stats_day2["debt"], 0.0)

        self.setUp()

        # --- Case 6: Maximum debt is enforced ---
        db.set_setting("max_debt", "5.0")
        logic.init_today_stats(day1) # Day 1: completed=0, unpaid=2. Start debt=0
        logic.init_today_stats(day2) # Day 2: completed=0, unpaid=2. Start debt=2
        logic.init_today_stats(day3) # Day 3: completed=0. yesterday debt=2, unpaid=2. Total debt should be 4.
        
        day4 = "2026-08-21"
        logic.init_today_stats(day4) # Day 4: yesterday debt=4, unpaid=2. Total debt = 6, but capped at max_debt=5.0
        stats_day4 = self.get_stats(day4)
        self.assertEqual(stats_day4["debt"], 5.0)

        self.setUp()

        # --- Case 10: Emergency unlock bypasses lock without corrupting db ---
        logic.init_today_stats(day1)
        # Carry a debt
        logic.init_today_stats(day2)
        self.assertTrue(logic.is_locked(day2))
        
        # Activate emergency unlock
        import time
        db.set_setting("emergency_unlocked", "True")
        db.set_setting("emergency_unlock_time", str(time.time()))
        self.assertFalse(logic.is_locked(day2)) # locked is bypassed
        
        # Verify database is intact
        stats = self.get_stats(day2)
        self.assertEqual(stats["debt"], 2.0)

if __name__ == "__main__":
    unittest.main()
