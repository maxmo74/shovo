# Quick Manual Test - Update Banner Flow

## Critical Bugs Fixed

1. **Service worker wasn't registering at all** - Missing `Service-Worker-Allowed` header
2. **SW install was failing** - Trying to cache non-existent `/manifest.json`

These bugs prevented ANY service worker functionality. Now fixed in v1.6.41.

---

## Quick Test Steps

### 1. Clear Everything First

**In Browser DevTools (F12):**
- Application tab → Service Workers → Click "Unregister" for any workers
- Application tab → Storage → Clear site data
- Hard refresh: **Ctrl+Shift+R** (or Cmd+Shift+R on Mac)

### 2. Load Fresh Page

```bash
# Make sure server is running
cd webapp
source .venv/bin/activate
python app.py
```

**In Browser:**
- Go to: `http://localhost:5000/r/test`
- **Open DevTools Console (F12)**

**Expected Console Output:**
```
[SW] Registered: http://localhost:5000/
[SW] Installing service worker v1.6.41
[SW] Activating service worker v1.6.41
[SW] Clients claimed, activation complete
```

**Check Application Tab → Service Workers:**
- Should show: **activated and is running**
- Source: `/static/sw.js?v=1.6.41`

✅ If you see this, service worker is now working!

---

### 3. Simulate Version Update

**In Terminal:**
```bash
# Change version to 1.6.42
sed -i 's/APP_VERSION = "1.6.41"/APP_VERSION = "1.6.42"/' webapp/routes.py

# Restart server (Ctrl+C, then):
python app.py
```

**In Browser (keep page open, don't refresh):**
- In Application → Service Workers, click **Update** button

**Expected Console Output:**
```
[Update] New service worker installing...
[Update] New worker state: installing
[Update] New worker state: installed
[Update] New version available!
[Update] Notification shown
```

**Expected Result:**
- 🟡 **Gold banner appears** at top: "New version available! Update now"

**Check Service Workers Panel:**
- Should see **TWO** workers:
  - activated (v1.6.41)
  - waiting to activate (v1.6.42)

---

### 4. Click "Update now"

**Action:** Click the "Update now" button

**Expected Console Output:**
```
[Update] User clicked update button
[Update] Telling waiting worker to skip waiting
[SW] Message received: {type: 'SKIP_WAITING'}
[SW] SKIP_WAITING received - activating immediately
[Update] Controller changed, reloading...
```

**Expected:**
- Page reloads automatically (within 1 second)

---

### 5. CRITICAL CHECK - After Reload

**After page reloads:**

**The banner should be GONE** ✅

**Console should show:**
```
[SW] Registered: http://localhost:5000/
[SW] Activating service worker v1.6.42
[SW] Clients claimed, activation complete
```

**Service Workers panel should show:**
- Only **ONE** worker: activated v1.6.42
- NO "waiting to activate" workers

**Version in UI:**
- Should show: **v1.6.42**

---

## Expected Behavior Summary

✅ Initial load → SW installs v1.6.41
✅ Update detected → Banner appears
✅ Click "Update now" → Page reloads
✅ **After reload → Banner GONE**
✅ Version updated to v1.6.42
✅ Only one active SW (no waiting workers)

---

## If Banner Still Appears After Reload

**That means the bug is NOT fixed. Report:**

1. Copy/paste ALL console logs
2. Screenshot of Service Workers panel after reload
3. Check Application → Service Workers - how many workers?
4. Run this in console after reload:
   ```javascript
   navigator.serviceWorker.getRegistration().then(reg => {
     console.log('Active:', reg.active?.scriptURL);
     console.log('Waiting:', reg.waiting?.scriptURL || 'none');
   });
   ```

---

## Reset to Try Again

**Console:**
```javascript
navigator.serviceWorker.getRegistrations().then(regs => {
  regs.forEach(reg => reg.unregister());
});
```

**Then:** Ctrl+Shift+R (hard refresh)

**Or:** Application → Clear site data → Reload

---

## Why It Should Work Now

**Before (v1.6.40 and earlier):**
- Service worker NEVER registered (Security error)
- Even if it did, install failed (manifest.json 404)
- Update banner code never ran

**Now (v1.6.41+):**
- Service-Worker-Allowed header lets SW control root scope
- Removed broken manifest.json reference
- SW installs successfully
- Update detection works
- Banner appears and disappears correctly

---

## Quick Sanity Check

If you want to verify SW is working AT ALL:

**Console:**
```javascript
navigator.serviceWorker.getRegistration().then(reg => {
  if (!reg) {
    console.log('❌ NO SERVICE WORKER REGISTERED');
  } else {
    console.log('✅ Service Worker:', reg.active?.scriptURL);
  }
});
```

**Should print:**
```
✅ Service Worker: http://localhost:5000/static/sw.js?v=1.6.41
```

If you see "NO SERVICE WORKER REGISTERED", the basic fixes didn't work.
