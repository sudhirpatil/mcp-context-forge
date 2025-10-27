# OpenAPI Import - Error Messages Guide

## 📋 Comprehensive Error Reference

The `/tools/openapi` endpoint now provides detailed error messages for every failure scenario. Here's what each error means and how to fix it.

---

## 🔴 **HTTP 422 - Validation Errors**

### Error: "Either 'url' or 'content' must be provided"

**Cause**: Empty request body or missing both url and content fields

**Example**:
```json
{}
```

**Fix**:
```json
{
  "url": "https://petstore3.swagger.io/api/v3/openapi.yaml"
}
```

---

### Error: "Provide either 'url' or 'content', not both"

**Cause**: Both url and content provided in request

**Example**:
```json
{
  "url": "https://api.com/openapi.yaml",
  "content": "openapi: 3.0.0..."
}
```

**Fix**: Choose one or the other
```json
{
  "url": "https://api.com/openapi.yaml"
}
```

---

### Error: "Timeout fetching OpenAPI spec from {url}. The server took too long to respond (>30s)"

**Cause**: Remote server is slow or unresponsive

**Fix**: 
- Try downloading the spec and using content mode instead
- Check if the URL is correct
- Verify the server is online

---

### Error: "HTTP error fetching OpenAPI spec from {url}: 404 Not Found"

**Cause**: URL doesn't exist or is incorrect

**Common HTTP codes**:
- 404: Not found - check URL
- 403: Forbidden - authentication required
- 500: Server error - remote server issue

**Fix**:
- Verify the URL in your browser
- Check if authentication headers needed
- Try a different URL or download and use content mode

---

### Error: "Connection error fetching OpenAPI spec from {url}. Cannot connect to the server"

**Cause**: Network connectivity issue or invalid hostname

**Fix**:
- Check your internet connection
- Verify the URL is correctly formatted
- Check if behind proxy/firewall
- Try downloading spec and using content mode

---

### Error: "Failed to parse YAML at line X, column Y: {problem}"

**Cause**: Invalid YAML syntax in the OpenAPI spec

**Example**:
```
Failed to parse YAML at line 12, column 5: expected <block end>, but found '-'
```

**Fix**:
- Check YAML syntax at the specified line
- Validate YAML online: https://www.yamllint.com/
- Ensure proper indentation (spaces, not tabs)

---

### Error: "Invalid OpenAPI spec: root must be an object/dictionary, not a string or list"

**Cause**: YAML parsed but result is not an object

**Example bad YAML**:
```yaml
- item1
- item2
```

**Fix**: OpenAPI spec must start with object:
```yaml
openapi: 3.0.0
info:
  title: My API
```

---

### Error: "Invalid OpenAPI spec: missing 'openapi' or 'swagger' version field"

**Cause**: File is not an OpenAPI/Swagger specification

**Fix**: Ensure your spec has:
```yaml
openapi: 3.0.0  # For OpenAPI 3.x
# or
swagger: "2.0"  # For Swagger 2.0
```

---

### Error: "No servers defined in OpenAPI spec. Cannot determine base URL"

**Cause**: OpenAPI spec missing servers array

**Fix**: Add servers to your spec:
```yaml
servers:
  - url: https://api.example.com
```

---

### Error: "First server in OpenAPI spec has no URL"

**Cause**: Server object exists but has no URL

**Bad**:
```yaml
servers:
  - description: My server
```

**Fix**:
```yaml
servers:
  - url: https://api.example.com
    description: My server
```

---

### Error: "No valid endpoints found in OpenAPI specification"

**Cause**: 
- Empty paths object
- All operations use unsupported HTTP methods
- Spec has no endpoints defined

**Fix**:
- Add paths to your spec
- Ensure using supported methods: GET, POST, PUT, DELETE, PATCH
- Check spec is complete

---

### Error: "Failed to convert OpenAPI spec to tools: {reason}"

**Cause**: Error during tool creation from OpenAPI paths

**Fix**: Check your paths are properly formatted

---

### Error: "Validation error on tool #X ('{tool_name}'): {details}"

**Cause**: Generated tool failed Pydantic validation

**Common issues**:
- Invalid tool name characters
- URL too long
- Invalid schema format

**Fix**:
- Check the tool name follows naming conventions
- Simplify complex schemas
- Check endpoint URL format

---

## 🔴 **HTTP 409 - Conflict Errors**

### Error: "Tool name conflict on tool #X ('{tool_name}'): Tool already exists"

**Cause**: A tool with that name already exists in the database

**Full message**:
```
Tool name conflict on tool #3 ('getPetById'): Tool 'getPetById' already exists. 
Already imported 2 tools but rolled back entire operation. 
Suggestion: Use a different namespace or delete conflicting tools first.
```

**Fixes**:

**Option 1: Use a different namespace**
```json
{
  "url": "...",
  "namespace": "petstore_v2"
}
```

**Option 2: Delete conflicting tools first**
```bash
# List existing tools
curl -H "Authorization: Bearer $TOKEN" http://localhost:4444/tools | \
  jq '.[] | select(.name | startswith("getPetById"))'

# Delete by ID
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:4444/tools/{tool_id}
```

**Option 3: Use different visibility**
```json
{
  "url": "...",
  "visibility": "private"  // Private tools can have same names
}
```

---

### Error: "Database error on tool #X ('{tool_name}'): {details}"

**Cause**: Database integrity constraint violation

**Fix**: Check database state, may need to clean up orphaned records

---

## 🔴 **HTTP 400 - Bad Request**

### Error: "Failed to register tool #X ('{tool_name}'): {details}"

**Cause**: Generic error during tool registration

**Full message includes**:
- Tool number in sequence
- Tool name that failed
- Specific error reason
- "Check server logs for full details"

**Fix**: Check server logs for detailed traceback

---

## 🔴 **HTTP 500 - Server Errors**

### Error: "Unexpected error during OpenAPI import: {ErrorType}: {message}"

**Cause**: Unexpected exception in code

**Example**:
```
Unexpected error during OpenAPI import: AttributeError: 'NoneType' object has no attribute 'get'. 
Check server logs for full traceback.
```

**Fix**:
- Check server logs for full stack trace
- Verify your OpenAPI spec is well-formed
- Report as bug if issue persists

---

## 📊 **Error Message Format**

All errors now include:

1. **Error Type/Category**: What kind of error
2. **Specific Details**: Exact what went wrong
3. **Context**: Which tool (number and name) if applicable
4. **Actionable Guidance**: What to do to fix it
5. **Server Logs Reference**: When to check logs

### Example Detailed Error

**Request**:
```json
{
  "url": "https://invalid-url.com/spec.yaml",
  "namespace": "test"
}
```

**Response** (422):
```json
{
  "detail": "HTTP error fetching OpenAPI spec from https://invalid-url.com/spec.yaml: 404 Not Found. The URL may be incorrect or the server is having issues."
}
```

**What you learn**:
- ✅ URL fetch was attempted
- ✅ Got HTTP 404 (not found)
- ✅ URL is probably wrong
- ✅ Action: Check the URL

---

## 🛠️ **Debugging Workflow**

### Step 1: Check Error Message

Read the `detail` field carefully - it tells you exactly what went wrong.

### Step 2: Check Server Logs

When message says "Check server logs":

```bash
# Look at terminal where uvicorn is running
# Recent errors appear at the bottom
```

Look for:
```
ERROR:mcpgateway.main:Failed to parse OpenAPI spec: ...
ERROR:mcpgateway.utils.openapi_parser:Fetching OpenAPI spec from URL: ...
```

### Step 3: Test URL Manually

If URL fetch fails, test in browser or curl:

```bash
curl -I https://petstore3.swagger.io/api/v3/openapi.yaml
```

Should return `200 OK` and `Content-Type: application/yaml` or `text/yaml`

### Step 4: Validate YAML

If YAML parsing fails, validate the content:

```bash
# Copy the YAML content
# Visit: https://www.yamllint.com/
# Paste and check for errors
```

### Step 5: Check OpenAPI Validity

Validate your OpenAPI spec:

```bash
# Visit: https://editor.swagger.io/
# Paste your spec
# Check for validation errors
```

---

## 📝 **Error Message Examples**

### Connection Timeout
```
Timeout fetching OpenAPI spec from https://slow-server.com/spec.yaml. 
The server took too long to respond (>30s). Error: ReadTimeout
```

### Invalid YAML
```
Failed to parse YAML at line 15, column 3: expected <block end>, but found '-'. 
Please check your YAML syntax.
```

### Missing Required Field
```
Invalid OpenAPI spec: No servers defined in OpenAPI spec. 
Make sure your spec has a 'servers' array with at least one URL.
```

### Tool Name Conflict
```
Tool name conflict on tool #5 ('updatePet'): Tool 'updatePet' already exists. 
Already imported 4 tools but rolled back entire operation. 
Suggestion: Use a different namespace or delete conflicting tools first.
```

### Network Error
```
Connection error fetching OpenAPI spec from https://api.example.com/openapi.yaml. 
Cannot connect to the server. Error: Name or service not known
```

---

## ✅ **Testing Error Messages**

You can test different error scenarios:

### Test 1: Invalid URL
```bash
curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://invalid-domain-12345.com/spec.yaml",
    "namespace": "test"
  }'
```

**Expected**: Connection error with detailed message

### Test 2: Invalid YAML
```bash
curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "invalid: yaml: syntax: error:",
    "namespace": "test"
  }'
```

**Expected**: YAML parsing error with line number

### Test 3: Missing Servers
```bash
curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "openapi: 3.0.0\ninfo:\n  title: Test\npaths: {}",
    "namespace": "test"
  }'
```

**Expected**: "No servers defined" error

### Test 4: Tool Conflict
```bash
# Import once
curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://petstore3.swagger.io/api/v3/openapi.yaml", "namespace": "pet"}'

# Import again with same namespace
curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://petstore3.swagger.io/api/v3/openapi.yaml", "namespace": "pet"}'
```

**Expected**: Conflict error with tool name and suggestion

---

## 🎯 **Error Message Improvements**

### Before
```
Failed to fetch
```

### After
```
HTTP error fetching OpenAPI spec from https://example.com/spec.yaml: 404 Not Found. 
The URL may be incorrect or the server is having issues.
```

---

### Before
```
Tool name conflict
```

### After
```
Tool name conflict on tool #3 ('getPetById'): Tool 'getPetById' already exists. 
Already imported 2 tools but rolled back entire operation. 
Suggestion: Use a different namespace or delete conflicting tools first.
```

---

### Before
```
Invalid spec
```

### After
```
Invalid OpenAPI spec: No servers defined in OpenAPI spec. 
Make sure your spec has a 'servers' array with at least one URL.
```

---

## 🚀 **Benefits of Enhanced Errors**

1. **Specific Problem Identification**: Know exactly what failed
2. **Context Information**: Which tool, line number, URL, etc.
3. **Actionable Guidance**: Clear instructions on how to fix
4. **Error Classification**: HTTP status codes indicate error type
5. **Debug Information**: Trace errors through logs
6. **User-Friendly**: Non-technical users can understand

---

## 💡 **Quick Troubleshooting**

| Error Type | Quick Fix |
|------------|-----------|
| Timeout | Use content mode instead of URL |
| 404 Not Found | Verify URL in browser first |
| Invalid YAML | Validate at yamllint.com |
| Tool conflict | Change namespace or delete tools |
| Connection error | Check internet, try content mode |
| Missing servers | Add servers array to spec |
| No endpoints | Check spec has paths object |

---

**All errors now provide detailed, actionable information!** 🎉

When you see an error in the UI, you'll know exactly what went wrong and how to fix it.

