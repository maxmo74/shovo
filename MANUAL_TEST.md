# Manual Testing Steps - Update Notification

## Setup

1. **Start the server:**
   ```bash
   cd /home/massimo/repos/shovo/webapp
   source .venv/bin/activate
   python app.py
   ```

2. **Open in browser:**
   - Chrome/Firefox recommended for DevTools
   - Navigate to: `http://localhost:5000/r/test`

3. **Open DevTools:**
   - Press F12
   - Go to **Console** tab - keep this visible
   - Go to **Application** tab > **Service Workers** - check status

## Test Procedure

### Step 1: Verify Initial State

In Console, you should see:
```
[SW] Registered: /
[SW] Installing service worker v1.6.39
[SW] Activating service worker v1.6.39
```

In Application > Service Workers:
- Should see: `activated and is running`
- Source: `/static/sw.js?v=1.6.39`

**✓ Checkpoint:** No update banner visible (we're on latest version)

---

### Step 2: Simulate Version Update

**In Terminal:**
```bash
# Edit routes.py
sed -i 's/APP_VERSION = "1.6.39"/APP_VERSION = "1.6.40"/' /home/massimo/repos/shovo/webapp/routes.py

# Restart server (Ctrl+C then restart)
python app.py
```

**In Browser:**
- Keep the page open (don't refresh yet!)
- In Application > Service Workers, click **Update** button

**Expected Console Output:**
```
[SW] Periodic update check
[Update] New service worker installing...
[Update] New worker state: installing
[Update] New worker state: installed
[Update] New version available!
[Update] Notification shown
```

**✓ Checkpoint:** Gold banner should appear at top: "New version available!"

---

### Step 3: Verify Banner Appearance

**Visual Check:**
- Banner at top of page
- Gold gradient background
- Text: "New version available!"
- Button: "Update now"
- Dismiss button: "×"

**In Application > Service Workers:**
- Should see TWO workers:
  - One `activated and is running` (v1.6.39)
  - One `waiting to activate` (v1.6.40)

**✓ Checkpoint:** Banner visible, two service workers listed

---

### Step 4: Click "Update now"

**Actions:**
1. Click the "Update now" button on the banner

**Expected Console Output:**
```
[Update] User clicked update button
[Update] Telling waiting worker to skip waiting
[SW] Message received: {type: 'SKIP_WAITING'}
[SW] SKIP_WAITING received - activating immediately
[Update] Controller changed, reloading...
```

**Expected Behavior:**
- Page reloads automatically (within 1 second)

**✓ Checkpoint:** Page reloads

---

### Step 5: Verify After Reload

**After page reloads, check:**

**Console:**
```
[SW] Registered: /
[SW] Activating service worker v1.6.40
[SW] Old caches deleted
[SW] Clients claimed, activation complete
```

**Visual:**
- **Banner should be GONE** ✓
- Version tag in header: "v1.6.40"

**Application > Service Workers:**
- Only ONE worker: `activated and is running`
- Source: `/static/sw.js?v=1.6.40`
- No "waiting to activate" workers

**Application > Cache Storage:**
- `shovo-v1.6.40`
- `shovo-static-v1.6.40`
- `shovo-api-v1.6.40`
- Old caches (v1.6.39) should be DELETED

**✓ Checkpoint:** Banner GONE, version updated, only new caches present

---

## Expected vs Current Behavior

### EXPECTED (after fix):
```
1. Update detected → Banner shows
2. Click "Update now"
3. Page reloads
4. Banner GONE ✓
5. Version updated ✓
```

### IF STILL BROKEN:
```
1. Update detected → Banner shows
2. Click "Update now"
3. Page reloads
4. Banner STILL THERE ✗
5. Need to manually refresh
```

---

## Debugging - If Banner Persists

### Check 1: Console Logs
Look for:
- `[Update] Controller changed, reloading...`
  - **If missing:** controllerchange event not firing
- `[SW] SKIP_WAITING received`
  - **If missing:** Message not reaching service worker

### Check 2: Service Workers Panel
After clicking "Update now":
- Should go from 2 workers → 1 worker
- **If still 2 workers:** skipWaiting() didn't work

### Check 3: Network Tab
- After reload, check `/static/sw.js` request
- Should have `?v=1.6.40` in URL
- **If shows v1.6.39:** Server didn't restart or browser cache issue

### Check 4: Registration State
In Console, run:
```javascript
navigator.serviceWorker.getRegistration().then(reg => {
  console.log('Active:', reg.active ? 'yes' : 'no');
  console.log('Waiting:', reg.waiting ? 'yes' : 'no');
  console.log('Installing:', reg.installing ? 'yes' : 'no');
});
```

**After update should show:**
```
Active: yes
Waiting: no   ← Key: should be NO
Installing: no
```

**If Waiting: yes** → That's the problem! The waiting worker didn't activate.

---

## Quick Reset

If you need to start fresh:

**In Console:**
```javascript
navigator.serviceWorker.getRegistrations().then(regs => {
  regs.forEach(reg => reg.unregister());
});
location.reload();
```

**Or in Application > Service Workers:**
- Click "Unregister" for all workers
- Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

---

## Success Criteria

✅ Banner appears when update detected
✅ Console shows all expected messages
✅ Click "Update now" triggers reload
✅ After reload, banner is GONE
✅ Version number updated in UI
✅ Only one service worker active (new version)
✅ Old caches deleted, new caches created
✅ No errors in console

---

## Report Results

After testing, report:

1. **Which step failed?** (1-5)
2. **What did you see in console?** (copy/paste logs)
3. **What did you see in Service Workers panel?** (screenshot helpful)
4. **Did banner disappear?** YES / NO

This will help identify exactly where the flow is breaking.
