# How to Release a New Version

## Quick Steps

1. **Update the version number** in `webapp/routes.py`:
   ```python
   APP_VERSION = "1.6.38"  # Change this
   ```

2. **Restart the server**:
   ```bash
   # If using systemd:
   systemctl restart shovo

   # If running manually:
   # Stop the current process (Ctrl+C) and restart
   ```

3. **Done!** Users will see the update notification automatically.

## What Happens Next?

- **Existing users** (already have the app open):
  - Within 1 hour, they'll see a gold banner: "New version available!"
  - They click "Update now" and get the latest version
  - Or they can dismiss it and update later

- **New visitors**:
  - Automatically get the latest version
  - No notification needed

## Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **1.7.0** - New feature (increment MINOR)
- **1.6.38** - Bug fix (increment PATCH)
- **2.0.0** - Breaking change (increment MAJOR)

## Examples

### Bug Fix Release
```python
APP_VERSION = "1.6.37"  # Current
APP_VERSION = "1.6.38"  # After bug fix
```

### New Feature Release
```python
APP_VERSION = "1.6.38"  # Current
APP_VERSION = "1.7.0"   # After adding feature
```

### Major Update
```python
APP_VERSION = "1.7.5"   # Current
APP_VERSION = "2.0.0"   # Major redesign
```

## Testing the Update Flow

1. Open the app in a browser (incognito mode recommended)
2. Note the version in the header (e.g., "v1.6.37")
3. Update `APP_VERSION` in `routes.py`
4. Restart the server
5. In the browser:
   - Open DevTools → Application → Service Workers
   - Click "Update" button next to the service worker
   - Or wait up to 1 hour for automatic check
6. You should see the update notification banner appear
7. Click "Update now"
8. Page reloads with new version

## Troubleshooting

### "Update notification doesn't appear"
- Hard refresh the page (Ctrl+Shift+R / Cmd+Shift+R)
- Check DevTools → Console for errors
- Verify service worker is registered (DevTools → Application)

### "Still seeing old version after update"
- Unregister service worker in DevTools → Application → Service Workers
- Clear all site data
- Hard refresh

### "Need to force immediate update for all users"
This implementation already handles it! When you change the version:
- The HTML loads fresh (never cached)
- The service worker URL changes (`sw.js?v=1.6.38`)
- Browser downloads new service worker
- Update notification appears

## Best Practices

1. **Test locally first**: Change version, test the update flow
2. **Increment version for every deployment**: Even small changes
3. **Keep a changelog**: Document what changed in each version
4. **Monitor users**: Check how many are on old versions
5. **Don't skip versions**: Go 1.6.37 → 1.6.38, not 1.6.37 → 1.6.40

## Files You Should Never Edit Manually

These files are auto-generated from the version number:
- ❌ Don't edit `/static/sw.js` (it's generated from `templates/sw.js.j2`)
- ❌ Don't change version strings in HTML (they use `{{ app_version }}`)
- ✅ **Only edit** `APP_VERSION` in `routes.py`

## Emergency: Revert to Previous Version

If you need to roll back:

1. Change `APP_VERSION` back to previous number:
   ```python
   APP_VERSION = "1.6.37"  # Revert from 1.6.38
   ```

2. Restart server

3. Users will see update notification and get the old version

Note: Rolling back doesn't undo database changes, only frontend code.

## Advanced: Skip Update Notification

If you want to deploy a change without notifying users (e.g., backend-only update):

**Don't increment the version number.** However, this is not recommended because:
- Users might see cached old content
- Defeats the purpose of cache busting
- Can cause inconsistencies

Better approach: Always increment version for any deployment.
