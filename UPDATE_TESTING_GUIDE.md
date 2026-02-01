# Service Worker Update Testing Guide

## Quick Test Setup

### 1. Access the Test Page
Navigate to: `http://localhost:5000/test-update`

This page provides:
- Real-time service worker state monitoring
- Detailed event logging
- Manual update triggers
- Debug information

### 2. Simulate a Version Update

**Terminal 1 - Check current version:**
```bash
cd /home/massimo/repos/shovo/webapp
source .venv/bin/activate
python -c "from routes import APP_VERSION; print(f'Current version: {APP_VERSION}')"
```

**Terminal 2 - Run the app:**
```bash
cd /home/massimo/repos/shovo/webapp
source .venv/bin/activate
python app.py
```

**Browser:**
1. Open `http://localhost:5000/test-update`
2. Watch the event log - you should see:
   ```
   ✓ Service Worker API available
   ✓ Service Worker registered successfully
   ✓ Service Worker currently controlling this page
   ```

### 3. Test Update Flow

**Step 1: Change Version**
```bash
# Edit webapp/routes.py
# Change: APP_VERSION = "1.6.38"
# To:     APP_VERSION = "1.6.39"
```

**Step 2: Restart Server**
```bash
# In Terminal 2, stop (Ctrl+C) and restart:
python app.py
```

**Step 3: Trigger Update Check**
In the browser (keep test page open):
1. Click "🔄 Manual Update Check" button
2. Watch the logs, you should see:
   ```
   📡 Manually checking for update...
   🔔 UPDATE FOUND! New service worker installing...
   New worker initial state: installing
   🔄 New worker state changed: installed
   🎉 NEW VERSION READY! Update notification should appear.
   ✓ Update check complete
   ```

**Step 4: Verify on Main App**
1. Open a new tab: `http://localhost:5000/r/test`
2. You should see the gold update banner at the top
3. Click "Update now"
4. Page should reload
5. Banner should disappear
6. Check version tag - should show v1.6.39

## Expected Behavior

### First Visit (No Service Worker)
```
[Time] ✓ Service Worker API available
[Time] ✓ Service Worker registered successfully
[Time] ✓ Service Worker installed for first time
[Time] ✅ New service worker ACTIVATED
[Time] No service worker controlling this page yet
```

### Update Available
```
[Time] 📡 Checking for update...
[Time] 🔔 UPDATE FOUND! New service worker installing...
[Time] New worker state: installing
[Time] 🔄 New worker state changed: installed
[Time] 🎉 NEW VERSION READY!
```

### After Clicking "Update Now"
```
[Browser Console] User clicked update, activating new service worker...
[Browser Console] SKIP_WAITING received
[Service Worker] skipWaiting complete
[Service Worker] Clients claimed
[Browser] 🔄 CONTROLLER CHANGED
[Browser] Just updated, clearing flag
[Browser] Page reloads
[Browser] No update banner shown (just updated)
```

## Common Issues & Fixes

### Issue: Banner doesn't disappear after update

**Debug:**
1. Open DevTools → Console
2. Check for errors
3. Look for: "Just updated, clearing flag"
4. Check sessionStorage: `sessionStorage.getItem('shovo_just_updated')`

**Fix:**
- Clear sessionStorage manually: `sessionStorage.clear()`
- Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

### Issue: Update notification never appears

**Debug:**
1. Go to `/test-update` page
2. Click "Manual Update Check"
3. Watch the logs for:
   - "UPDATE FOUND"
   - "New worker state changed: installed"

**Fix:**
- Verify version actually changed in routes.py
- Verify server restarted
- Check DevTools → Application → Service Workers
- Try "Unregister SW" button and refresh

### Issue: Service worker not updating

**Debug:**
1. DevTools → Application → Service Workers
2. Check if "Update on reload" is enabled (disable it for normal testing)
3. Look for "waiting to activate" workers

**Fix:**
- Click "skipWaiting" in DevTools
- Or unregister and hard refresh
- Or click "Unregister SW" on test page

### Issue: Old cache not clearing

**Debug:**
1. DevTools → Application → Cache Storage
2. Look for old version caches (e.g., `shovo-v1.6.38`)

**Fix:**
- Should auto-delete when new SW activates
- Manual: Right-click cache → Delete
- Check activate event in SW logs

## Testing Checklist

- [ ] Test page loads at `/test-update`
- [ ] Service worker registers successfully
- [ ] Version update detected when APP_VERSION changes
- [ ] "UPDATE FOUND" appears in logs
- [ ] Update notification banner appears on main app
- [ ] Clicking "Update now" reloads the page
- [ ] Banner disappears after reload
- [ ] New version shown in header
- [ ] Old caches deleted (check Cache Storage)
- [ ] New caches created with new version
- [ ] App works normally after update

## Automated Test

Run this script to verify the update flow programmatically:

```bash
cd /home/massimo/repos/shovo/webapp
source .venv/bin/activate
python << 'EOF'
from app import create_app
import time

app = create_app()

print("Testing update notification flow...")
print("=" * 60)

with app.test_client() as client:
    # Test 1: Version API
    response = client.get('/api/version')
    version = response.json['version']
    print(f"✓ Current version: {version}")

    # Test 2: Service worker serves with version
    response = client.get('/static/sw.js')
    if f"shovo-v{version}" in response.data.decode():
        print(f"✓ Service worker cache name: shovo-v{version}")
    else:
        print(f"✗ Service worker cache name mismatch")

    # Test 3: HTML has version strings
    response = client.get('/r/test')
    html = response.data.decode()
    if f"style.css?v={version}" in html:
        print(f"✓ Static files have version: ?v={version}")
    else:
        print(f"✗ Static files missing version string")

    # Test 4: Update notification present
    if "update-notification-banner" in html:
        print("✓ Update notification banner in HTML")
    else:
        print("✗ Update notification banner missing")

    # Test 5: Update JS functions present
    if "showUpdateNotification" in html and "reloadApp" in html:
        print("✓ Update functions present")
    else:
        print("✗ Update functions missing")

    # Test 6: Test page available
    response = client.get('/test-update')
    if response.status_code == 200:
        print("✓ Test page available at /test-update")
    else:
        print("✗ Test page not available")

print("=" * 60)
print("All checks complete!")
EOF
```

## Manual End-to-End Test

### Scenario: Deploy a new version

1. **Current state:** App is running with v1.6.38
2. **User has app open** in browser
3. **You deploy** v1.6.39 (change APP_VERSION, restart server)
4. **Within 1 hour** (or immediate with manual check):
   - Update detected
   - Gold banner appears: "New version available!"
5. **User clicks** "Update now"
6. **Expected result:**
   - Page reloads immediately
   - Banner disappears
   - App shows v1.6.39
   - All features work normally

### Test Both Paths

**Path A: User with app already open**
- Keep browser tab open
- Update version on server
- Wait or trigger manual check
- Verify banner appears
- Click update
- Verify banner disappears after reload

**Path B: New user after update**
- Close all browser tabs
- Update version on server
- Open app in new tab
- Verify no banner (already latest version)
- Verify version is correct

## Browser DevTools Tips

### Service Worker Panel
`DevTools → Application → Service Workers`

Useful controls:
- **Update** - Manually check for updates
- **Unregister** - Remove service worker
- **Bypass for network** - Disable SW for testing
- **Update on reload** - Auto-update (disable for normal testing)

### Cache Storage
`DevTools → Application → Cache Storage`

Should see:
- `shovo-v1.6.XX` - Main cache
- `shovo-static-v1.6.XX` - Static files cache
- `shovo-api-v1.6.XX` - API cache

Old version caches should disappear after update.

### Console Logs

Look for these key messages:
```
ServiceWorker registered
[SW] Installing service worker v1.6.XX
[SW] Activating service worker v1.6.XX
Update found! New service worker installing...
New service worker state: installed
Controller changed, reloading page...
Just updated, clearing flag
```

## Production Testing

Before deploying to production:

1. Test locally with multiple browsers
2. Test on mobile device
3. Test with slow network (DevTools → Network throttling)
4. Test offline mode (DevTools → Offline checkbox)
5. Verify no console errors
6. Verify update banner is dismissible
7. Verify update banner doesn't show on fresh visits

## Rollback Testing

Test reverting to an older version:

1. Current: v1.6.39
2. Deploy: v1.6.38 (rollback)
3. Expected: Users see update notification
4. Expected: After update, they have v1.6.38
5. Expected: Caches update to v1.6.38

## Success Criteria

✅ Update detection works within 1 hour (or immediately with manual check)
✅ Update notification appears when new version available
✅ Update notification is user-friendly and clear
✅ Clicking "Update now" reloads page successfully
✅ Banner disappears after update (doesn't show again)
✅ Version number updates in UI
✅ Old caches are deleted
✅ New caches are created
✅ App works normally after update
✅ No manual cache clearing needed
✅ Works on mobile devices
✅ Works offline (PWA functionality preserved)
