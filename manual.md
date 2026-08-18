# DSA Lock - User Manual & Troubleshooting Guide

This manual covers the core usage details and troubleshoot guidelines for the **DSA Lock** application on your Windows laptop.

---

## 🚀 Quick Start Guide

1. Double-click the launcher script:
   [`e:\studyforce\run.bat`](file:///e:/studyforce/run.bat)
2. This runs the silent background blocker service and automatically launches the user dashboard interface in your web browser at:
   **[http://localhost:8501](http://localhost:8501)**

---

## 🛠️ Browser DNS / Hosts Troubleshooting

Because the first versions of the application modified the system hosts file (`C:\Windows\System32\drivers\etc\hosts`) to block websites, web browsers like **Brave** or **Chrome** might aggressively cache the blocked redirection IP (`127.0.0.1`) in their memory.

If you unlock your computer (via Emergency Unlock, solving targets, or Suspend mode) but YouTube or Instagram still say "No Internet/Connection", follow these quick steps:

### For Brave Browser:
1. Open a new tab, paste **`brave://net-internals/#dns`** in the address bar, and press Enter.
2. Click the **"Clear host cache"** button.
3. Next, paste **`brave://net-internals/#sockets`** in the address bar, and press Enter.
4. Click **"Close idle sockets"** followed by **"Flush socket pools"**.
5. Reload YouTube/Instagram.

### For Google Chrome:
1. Open a new tab, paste **`chrome://net-internals/#dns`** in the address bar, and press Enter.
2. Click **"Clear host cache"**.
3. Next, paste **`chrome://net-internals/#sockets`** in the address bar, and press Enter.
4. Click **"Close idle sockets"** and **"Flush socket pools"**.
5. Reload YouTube/Instagram.

---

## 🚨 Emergency System Override

If the application is locked and you need to restore normal system usage immediately:

1. **Dashboard Emergency Unlock**: Go to the **Emergency Unlock** tab, type your PIN (default is **`1234`**), and unlock. This suspends blocking rules for exactly **30 minutes**.
2. **Suspension Mode**: Go to the **Settings** tab and click **"Suspend Blocker for 2 Hours"** to pause blocking rules for a 2-hour window.
3. **Master Kill Switch**: Go to the **Settings** tab and click **"Activate Master Kill Switch"**. This permanently deactivates all blocking rules, clears old hosts records, and flushes your DNS cache. Turn it off when you want to resume study rules.

---

## 📅 Retroactive Holidays (Forgetting to log a break)

If you forget to log a holiday in advance (e.g. you went on a trip and came back to find a lot of unpaid DSA backlog debt restricting your computer):

1. Go to the **Settings** tab.
2. Under the **Holidays** section, select the dates you missed and click **Add Holiday**.
3. The system will automatically recalculate your historic debt day-by-day.
4. Any backlog debt accumulated during those holiday dates will be wiped out immediately, restoring your system access.
