# Cache Busting and Update Notification Implementation

## Overview
This implementation ensures users always see the latest version of the app after updates, with automatic update notifications and proper cache management.

## Implementation Summary

### 1. Centralized Version Management ✓
- **Single source of truth**: `APP_VERSION` in `routes.py` (currently v1.6.37)
- Version injected into all templates via Jinja2
- Version available in JavaScript via `window.APP_VERSION`
- API endpoint `/api/version` provides version info

### 2. Dynamic Service Worker ✓
- **File**: `webapp/templates/sw.js.j2` (Jinja2 template)
- **Route**: `/static/sw.js` serves dynamically generated service worker
- **Cache names** include version: `shovo-v{{ app_version }}`
- Service worker is **never cached** (Cache-Control: no-cache, no-store, must-revalidate)
- Old service worker file backed up to `webapp/static/sw.js.old`

### 3. Static File Cache Busting ✓
All static files include version query strings:
- `/static/style.css?v=1.6.37`
- `/static/js/main.js?v=1.6.37`
- `/static/app.js?v=1.6.37`
- `/manifest.json?v=1.6.37`
- `/static/sw.js?v=1.6.37` (registration URL)

### 4. Update Notification UI ✓
- **Banner**: Fixed position notification at top of page
- **Design**: Gold gradient background matching app theme
- **Actions**: "Update now" button and dismiss (×) button
- **Animation**: Slides down from top when shown
- **Styling**: Responsive mobile/desktop layout

### 5. Service Worker Update Detection ✓
Enhanced service worker registration in `index.html`:
- **Periodic checks**: Update check every hour (3600000ms)
- **Event listeners**: Detects `updatefound` and service worker state changes
- **Version check**: Compares SW version with current app version
- **Automatic notification**: Shows banner when update detected

### 6. Cache-Control Headers ✓
Configured in `webapp/app.py` via `@application.after_request`:

| Resource Type | Cache-Control | Duration |
|---------------|---------------|----------|
| Static files (`/static/*`) | `max-age=31536000, public` | 1 year |
| Service Worker (`/static/sw.js`) | `no-cache, no-store, must-revalidate` | Never |
| API endpoints (`/api/*`) | `no-cache, no-store, must-revalidate` | Never |
| HTML pages (`/r/*`, `/`) | `no-cache, must-revalidate` | Never |

## Update Flow

### When APP_VERSION Changes (e.g., 1.6.37 → 1.6.38)

1. **Developer updates** `APP_VERSION` in `routes.py`
2. **Server restart** applies new version
3. **User visits app**:
   - HTML loads with no-cache (always fresh)
   - Browser checks `/static/sw.js?v=1.6.38`
   - Query string changed, so browser downloads new service worker
4. **Service worker update detected**:
   - Old SW: `shovo-v1.6.37`
   - New SW: `shovo-v1.6.38` (installing)
5. **Update notification appears**:
   - Banner slides down from top
   - Shows "New version available!"
6. **User clicks "Update now"**:
   - Sends `SKIP_WAITING` message to new service worker
   - Page reloads
7. **New service worker activates**:
   - Deletes old caches (`shovo-v1.6.37`, `shovo-static-v1.6.37`, `shovo-api-v1.6.37`)
   - Creates new caches (`shovo-v1.6.38`, `shovo-static-v1.6.38`, `shovo-api-v1.6.38`)
8. **Static files load with new version**:
   - `/static/style.css?v=1.6.38` (cache miss, downloads fresh)
   - `/static/js/main.js?v=1.6.38` (cache miss, downloads fresh)
   - All assets up to date

## Files Modified

### New Files
1. `webapp/templates/sw.js.j2` - Dynamic service worker template

### Modified Files
1. `webapp/routes.py`:
   - Added `/static/sw.js` route (serves templated service worker)
   - Added `/api/version` endpoint

2. `webapp/app.py`:
   - Added `@application.after_request` handler for cache control headers

3. `webapp/templates/index.html`:
   - Added version query strings to all static file URLs
   - Added `window.APP_VERSION` global variable
   - Added update notification banner HTML
   - Enhanced service worker registration with update detection
   - Added `showUpdateNotification()`, `hideUpdateNotification()`, `reloadApp()` functions

4. `webapp/static/style.css`:
   - Added `.update-notification` banner styles
   - Added responsive mobile styles
   - Added slide-down animation

### Backed Up Files
1. `webapp/static/sw.js.old` - Original service worker (backup)

## Testing

### Manual Testing Steps

1. **Verify version strings in HTML**:
   ```bash
   curl http://localhost:5000/r/test | grep "v=1.6.37"
   ```
   Should see version strings in CSS, JS, manifest, and SW URLs.

2. **Verify service worker version**:
   ```bash
   curl http://localhost:5000/static/sw.js | grep "shovo-v"
   ```
   Should see `shovo-v1.6.37` in cache names.

3. **Verify cache headers**:
   ```bash
   curl -I http://localhost:5000/static/style.css
   # Should see: Cache-Control: max-age=31536000, public

   curl -I http://localhost:5000/static/sw.js
   # Should see: Cache-Control: no-cache, no-store, must-revalidate
   ```

4. **Test update flow**:
   - Open app in browser
   - Open DevTools → Application → Service Workers
   - Note current version (e.g., v1.6.37)
   - Update `APP_VERSION` to "1.6.38" in `routes.py`
   - Restart server
   - Refresh page or wait for periodic check (1 hour)
   - Update notification banner should appear
   - Click "Update now"
   - Page reloads with new version
   - DevTools shows new service worker with v1.6.38 caches

### Browser DevTools Testing

1. **Network Tab**:
   - Verify static files have `?v=1.6.37` query strings
   - Verify Cache-Control headers match specification
   - Verify 304 Not Modified responses for cached static files

2. **Application Tab → Service Workers**:
   - Verify service worker cache names include version
   - Test "Update on reload" to simulate updates
   - Verify old caches are deleted when new SW activates

3. **Application Tab → Cache Storage**:
   - Verify cache names: `shovo-v1.6.37`, `shovo-static-v1.6.37`, `shovo-api-v1.6.37`
   - After update, verify old caches deleted and new caches created

4. **Console**:
   - Verify `window.APP_VERSION` is set correctly
   - No errors during service worker registration or update

## Benefits

✅ **No manual cache clearing**: Users never need to clear browser cache
✅ **Automatic updates**: Users see notification when new version available
✅ **One-click update**: Simple "Update now" button
✅ **Offline support preserved**: PWA functionality works as before
✅ **Performance optimized**: Static files cached aggressively (1 year)
✅ **Always fresh**: API and HTML always fetch from server
✅ **Version consistency**: All components use same version number
✅ **User-friendly**: Non-intrusive notification banner, dismissible

## Maintenance

### To Release a New Version

1. Update `APP_VERSION` in `webapp/routes.py`:
   ```python
   APP_VERSION = "1.6.38"  # Increment version
   ```

2. Restart the Flask server:
   ```bash
   systemctl restart shovo  # or your deployment method
   ```

3. Users will see update notification on their next visit or within 1 hour (automatic check interval)

### Version Numbering

Currently using semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes

For every change that users should see (new features, bug fixes, UI changes), increment the version number.

## Troubleshooting

### Update notification doesn't appear
- Check browser console for service worker errors
- Verify `window.APP_VERSION` is set correctly
- Ensure service worker registration succeeded
- Check if service worker update was detected (DevTools → Application)

### Static files not updating
- Verify version query string in HTML source
- Check if browser is ignoring cache headers (DevTools → Network → Disable cache)
- Clear service worker and hard refresh (DevTools → Application → Service Workers → Unregister)

### Service worker not updating
- Verify `/static/sw.js` is not cached (check Cache-Control header)
- Ensure version query string changed (`?v=1.6.38` vs `?v=1.6.37`)
- Try "Skip waiting" in DevTools → Application → Service Workers

### Old caches not deleted
- Check service worker `activate` event is firing
- Verify cache name filter in `activate` event handler
- Manually delete old caches in DevTools → Application → Cache Storage

## Security Considerations

- Version number is public (visible in HTML/JS)
- No sensitive information in version string
- Cache headers prevent serving stale content for dynamic data
- Service worker follows same-origin policy
- Update notification doesn't execute arbitrary code

## Performance Impact

- **Minimal**: One additional route (`/static/sw.js`) for dynamic generation
- **Template rendering**: Negligible overhead for Jinja2 variable injection
- **Cache headers**: Applied via efficient after_request hook
- **Update checks**: Hourly check causes minimal network overhead
- **Static file caching**: Reduces server load with 1-year cache

## Future Enhancements

Potential improvements for future versions:

1. **Update notification customization**:
   - Show changelog/release notes in notification
   - Different notification styles for major/minor updates
   - Remember if user dismissed notification

2. **Background sync**:
   - Pre-download new version in background
   - Instant activation when user clicks update

3. **Analytics**:
   - Track update adoption rate
   - Monitor service worker update success/failure

4. **Configurable update frequency**:
   - Allow users to set update check interval
   - Option to disable automatic update checks

5. **Version comparison**:
   - Warn if user's version is very outdated
   - Show update importance (critical, recommended, optional)

## Conclusion

The cache busting and update notification system is fully implemented and tested. Users will now always see the latest version of the app with minimal friction, and the update process is user-friendly and automatic.
