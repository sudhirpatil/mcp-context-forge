# Tailwind CSS Local Migration

## Summary

Migrated Tailwind CSS from external CDN to local static file to resolve 403 Forbidden errors with `https://cdn.tailwindcss.com`.

## Changes Made

### 1. Downloaded Tailwind CSS Locally
- **File**: `mcpgateway/static/tailwindcss-cdn.js` (255KB)
- **Source**: `https://unpkg.com/@tailwindcss/browser@4` (alternative CDN)
- **Reason**: Original `cdn.tailwindcss.com` was returning 403 Forbidden errors

### 2. Updated HTML Templates
- **`mcpgateway/templates/admin.html`** (Line 21)
  - Before: `<script src="https://cdn.tailwindcss.com"></script>`
  - After: `<script src="{{ root_path }}/static/tailwindcss-cdn.js"></script>`

- **`mcpgateway/templates/login.html`** (Line 7)
  - Before: `<script src="https://cdn.tailwindcss.com"></script>`
  - After: `<script src="{{ root_path }}/static/tailwindcss-cdn.js"></script>`

### 3. Updated Content Security Policy
- **`mcpgateway/middleware/security_headers.py`** (Line 290)
  - Removed `https://cdn.tailwindcss.com` from `script-src` directive
  - Now: `"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com"`

### 4. Updated Tests
- **`tests/security/test_standalone_middleware.py`**
  - Commented out assertion for `cdn.tailwindcss.com` (Line 117-118)

- **`tests/security/test_security_middleware_comprehensive.py`**
  - Removed `https://cdn.tailwindcss.com` from required domains list (Line 304)

### 5. Updated Documentation
- **`docs/docs/manage/ui-customization.md`** (Line 88)
  - Updated to reflect local Tailwind serving

- **`docs/docs/architecture/adr/014-security-headers-cors-middleware.md`** (Line 51)
  - Removed `https://cdn.tailwindcss.com` from example CSP

## Benefits

1. ✅ **No more 403 errors** - Tailwind CSS loads from local static files
2. ✅ **Faster page loads** - No external network dependency
3. ✅ **Better offline support** - UI works without internet connectivity
4. ✅ **Enhanced security** - Reduced external CDN dependencies
5. ✅ **Simplified CSP** - Fewer external domains to whitelist

## Testing

To verify the changes:

```bash
# Restart the gateway
cd /Users/sudhirpatil/code/mcp-context-forge
source ~/.venv/mcpgateway/bin/activate

# With HTTP
MCPGATEWAY_UI_ENABLED=true \
MCPGATEWAY_ADMIN_API_ENABLED=true \
AUTH_REQUIRED=false \
PLUGINS_ENABLED=true \
uvicorn mcpgateway.main:app --host 0.0.0.0 --port 4444 --reload

# Or with HTTPS
make certs
MCPGATEWAY_UI_ENABLED=true \
MCPGATEWAY_ADMIN_API_ENABLED=true \
AUTH_REQUIRED=false \
PLUGINS_ENABLED=true \
uvicorn mcpgateway.main:app \
  --host 0.0.0.0 \
  --port 4444 \
  --ssl-keyfile=certs/key.pem \
  --ssl-certfile=certs/cert.pem \
  --reload
```

Then:
1. Open browser: `http://localhost:4444/admin` (or `https://localhost:4444/admin`)
2. Check browser DevTools → Network tab
3. Verify `tailwindcss-cdn.js` loads with status `200` from `/static/`
4. Verify UI is properly styled (no missing CSS)
5. Check Console for no errors

## File Location

- **Local Tailwind File**: `/Users/sudhirpatil/code/mcp-context-forge/mcpgateway/static/tailwindcss-cdn.js`
- **Size**: 255KB
- **Version**: Tailwind Browser v4 (from unpkg CDN)

## Rollback

If needed, to rollback to CDN:

```bash
# Restore original script tags in templates
sed -i '' 's|{{ root_path }}/static/tailwindcss-cdn.js|https://cdn.tailwindcss.com|g' mcpgateway/templates/admin.html
sed -i '' 's|{{ root_path }}/static/tailwindcss-cdn.js|https://cdn.tailwindcss.com|g' mcpgateway/templates/login.html

# Restore CSP in middleware/security_headers.py
# Add back https://cdn.tailwindcss.com to script-src
```

## Notes

- The local file is served via FastAPI's static file mounting at `/static/`
- The file is version-locked and won't auto-update (unlike CDN)
- To update Tailwind in future, re-download from unpkg or jsdelivr
- The `tailwind.config` blocks in templates remain unchanged

