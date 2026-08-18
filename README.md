# DSA Lock

A local-only Windows desktop productivity application designed to enforce a daily DSA (Data Structures and Algorithms) solving habit. If daily targets are not met, a debt is accrued, and the system restricts access to a list of blacklisted applications and entertainment websites. Access is restored once the debt is paid off (verified automatically via LeetCode's public GraphQL API or manual override).

## System Architecture

1. SQLite Database: Local persistence of statistics, problem logs, and settings.
2. Streamlit Dashboard: Accessible at http://localhost:8501 for tracking progress, adding solved problems, planning queues, and managing settings.
3. Background Daemon: A silent service running in an infinite loop that evaluates midnight rollovers, checks LeetCode submissions, and terminates unauthorized processes/browser tabs when locked.

## Core Features

1. Daily DSA Tracking: Logs date, required points, completed points, debt, problems solved, and streak counts.
2. Problem Entry: Direct manual entry or auto-verification using LeetCode profile sync.
3. Lock Mode: Restricts recreational application usage and closes YouTube and Instagram browser tabs when unpaid debt exists.
4. Emergency Unlock: Bypasses locks for 30 minutes via a configurable PIN.
5. Temporary Suspension: Pauses blocking rules for 2 hours for uninterrupted focus sessions.
6. DSA Planner: Queue planned questions and receive recommendations matching outstanding target points.
7. Holiday Mode: Schedule holiday dates to bypass daily targets and debt accumulation.
8. Master Kill Switch: Disables the blocker permanently and cleans system records when activated.

## Installation and Startup

1. Run the database initialization:
   python db.py

2. Launch the application:
   Right-click run.bat and select "Run as administrator"

The launcher script will automatically request administrator privileges. Running as administrator is required to write autostart registry configuration, execute background processes, clean hosts-level domain rules, and open the Streamlit web dashboard in your default browser.
