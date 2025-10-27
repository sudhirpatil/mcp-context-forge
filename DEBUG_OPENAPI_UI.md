# Debugging OpenAPI Import UI

## Quick Debugging Steps

The OpenAPI import form should now have detailed console logging. Here's how to check what's happening:

### Step 1: Open Browser Console

1. Go to http://localhost:4444/admin#tools
2. Open browser DevTools:
   - **Chrome/Edge**: Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - **Firefox**: Press `F12` or `Cmd+Option+K` (Mac) / `Ctrl+Shift+K` (Windows)
   - **Safari**: Enable Dev Menu first, then `Cmd+Option+C`
3. Click on "Console" tab

### Step 2: Check for Initialization Messages

When the page loads, you should see:
```
Registering OpenAPI import form handler
```

If you see:
```
OpenAPI import form not found in DOM
```

**Then**: The form isn't rendering. Check if you're on the Tools tab (#tools).

### Step 3: Test the Import

1. Fill in the form:
   - URL: `https://petstore3.swagger.io/api/v3/openapi.yaml`
   - Namespace: `petstore`
   - Keep "Public" selected

2. Click "Import Tools from OpenAPI"

3. Watch the console for these messages:
   ```
   OpenAPI import form submitted
   Importing OpenAPI spec with payload: {url: "...", namespace: "petstore", visibility: "public"}
   Calling API: /tools/openapi
   API response status: 200
   API response data: {success: true, created_count: 18, ...}
   Import successful! {...}
   Redirecting to: /admin#tools
   ```

### Step 4: Check for Errors

#### Common Issues & Solutions

**Issue 1: Form Not Found**
```
Console: "OpenAPI import form not found in DOM"
```
**Solution**: 
- Refresh the page (Cmd+R / Ctrl+R)
- Make sure you're on the Tools tab
- Check that uvicorn auto-reload picked up the changes

**Issue 2: 401 Unauthorized**
```
Console: "API response status: 401"
```
**Solution**:
- You're not logged in
- Go to http://localhost:4444/admin and login
- Username: admin, Password: changeme

**Issue 3: 403 Forbidden**
```
Console: "API response status: 403"
```
**Solution**:
- User doesn't have `tools.create` permission
- Login as admin user

**Issue 4: 422 Validation Error**
```
Console: "API response status: 422"
Console: "Either 'url' or 'content' must be provided"
```
**Solution**:
- Fill in either URL or YAML content
- Make sure the field is not empty

**Issue 5: 409 Conflict**
```
Console: "Tool name conflict: Tool 'getPetById' already exists"
```
**Solution**:
- Tools with those names already exist
- Use a different namespace (e.g., "petstore2")
- Or delete existing tools first

**Issue 6: CORS Error**
```
Console: "Access to fetch... has been blocked by CORS policy"
```
**Solution**:
- This shouldn't happen for same-origin requests
- Check CORS settings in gateway config

### Step 5: Network Tab Inspection

If the console doesn't help, check the Network tab:

1. Open DevTools → Network tab
2. Submit the form
3. Look for request to `/tools/openapi`
4. Click on it to see:
   - **Request**: Check the payload
   - **Response**: Check the server response
   - **Headers**: Verify cookies are sent

### Step 6: Force Reload

If changes aren't appearing:

1. **Hard Refresh**:
   - **Mac**: `Cmd+Shift+R`
   - **Windows**: `Ctrl+F5`

2. **Clear Cache**:
   - Chrome: DevTools → Network → Check "Disable cache"
   - Then reload

3. **Restart Gateway**:
   ```bash
   # Kill the process
   pkill -f "uvicorn mcpgateway.main:app"
   
   # Restart
   cd /Users/sudhirpatil/code/mcp-context-forge
   source ~/.venv/mcpgateway/bin/activate
   MCPGATEWAY_UI_ENABLED=true MCPGATEWAY_ADMIN_API_ENABLED=true AUTH_REQUIRED=false \
     uvicorn mcpgateway.main:app --host 0.0.0.0 --port 4444 --reload
   ```

### Expected Console Output (Success)

```
Registering OpenAPI import form handler
OpenAPI import form submitted
Importing OpenAPI spec with payload: {url: "https://petstore3.swagger.io/api/v3/openapi.yaml", namespace: "petstore", visibility: "public"}
Calling API: /tools/openapi
API response status: 200
API response data: {success: true, message: "Successfully imported 18 tools...", created_count: 18, failed_count: 0, tools: [...], errors: []}
Import successful! {success: true, created_count: 18, ...}
Redirecting to: /admin#tools
```

### Manual API Test

If the UI still doesn't work, test the API directly:

```bash
# In terminal
export TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com --exp 60 --secret my-test-key 2>/dev/null | head -1)

curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore_test",
    "visibility": "public"
  }' | jq '.'
```

If this works but the UI doesn't, it's a frontend issue (JavaScript or cookies).
If this also fails, it's a backend issue (check gateway logs).

### Check Gateway Logs

Look at the terminal where uvicorn is running for error messages when you submit the form.

Expected log entries:
```
INFO:mcpgateway.main:User admin@example.com importing tools from OpenAPI spec
INFO:mcpgateway.utils.openapi_parser:Fetching OpenAPI spec from URL: https://petstore3.swagger.io/api/v3/openapi.yaml
INFO:mcpgateway.utils.openapi_parser:Successfully parsed OpenAPI spec: Swagger Petstore
INFO:mcpgateway.main:Parsed 18 tools from OpenAPI spec
INFO:mcpgateway.services.tool_service:Registered tool: petstore_getPetById
...
```

### Still Not Working?

1. **Check browser console** for JavaScript errors
2. **Check network tab** for the actual request/response
3. **Check gateway logs** for server-side errors
4. **Try manual curl** to verify endpoint works
5. **Hard refresh** browser (Cmd+Shift+R)

## Quick Fixes

### Fix 1: Hard Refresh Browser

```
Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)
```

### Fix 2: Verify Form is Visible

Make sure you can see the purple section titled "🚀 Import Tools from OpenAPI Specification" on the page.

### Fix 3: Check Console for Registration

Should see: "Registering OpenAPI import form handler"

If not, the JavaScript hasn't loaded or setupFormHandlers() hasn't run.

---

After applying these debugging steps, the issue should be identified and the import should work!

