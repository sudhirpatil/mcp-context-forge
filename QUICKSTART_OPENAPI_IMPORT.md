# 🚀 Quick Start: OpenAPI Tools Import

## What You Got

A new API endpoint that automatically converts OpenAPI specifications into MCP tools!

**Endpoint**: `POST /tools/openapi`

---

## ⚡ 30-Second Start

```bash
# 1. Start gateway
make dev

# 2. In another terminal - generate token
export TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com --exp 60 --secret my-test-key 2>/dev/null | head -1)

# 3. Import Petstore API (18 tools in one command!)
curl -X POST http://localhost:4444/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore"
  }' | jq '.'

# 4. List created tools
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tools | \
  jq '.[] | select(.name | startswith("petstore_")) | .name'

# 5. Call a tool
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "petstore_getPetById",
      "arguments": {"petId": 10}
    }
  }' | jq '.'
```

---

## 📖 What This Does

**Before**: Manually register each REST API endpoint (hours of work)
```bash
curl -X POST /tools -d '{"name": "get_pet", ...}'  # Repeat 50 times
```

**After**: One command for entire API (seconds)
```bash
curl -X POST /tools/openapi -d '{"url": "https://api.com/openapi.yaml"}'
```

---

## 🎯 Key Features

✅ **Import from URL** - Fetch OpenAPI spec from any public URL  
✅ **Import from Content** - Paste YAML directly  
✅ **Auto-naming** - Uses operationId or generates smart names  
✅ **Auth Detection** - Extracts API keys, bearer tokens, basic auth  
✅ **Namespace Support** - Prefix tools to avoid conflicts  
✅ **Fail-Safe** - Rolls back entire import on any error  

---

## 📝 Request Format

```json
{
  "url": "https://api.example.com/openapi.yaml",  // OR
  "content": "openapi: 3.0.0\n...",               // provide YAML directly
  "namespace": "myapi",                            // optional prefix
  "visibility": "public"                           // public|team|private
}
```

---

## 📤 Response Format

```json
{
  "success": true,
  "message": "Successfully imported 18 tools",
  "created_count": 18,
  "failed_count": 0,
  "tools": [
    {"name": "petstore_getPetById", "url": "...", "method": "GET"},
    ...
  ],
  "errors": []
}
```

---

## 🧪 Testing

### Run Unit Tests (26 tests)
```bash
pytest tests/unit/mcpgateway/utils/test_openapi_parser.py -v
```

### Run Complete Example
```bash
python examples/openapi_import_complete_example.py
```

---

## 📚 Full Documentation

- **Feature Guide**: `docs/docs/using/openapi-import.md`
- **Quick Reference**: `examples/openapi-import-quickstart.md`
- **Examples**: `examples/README_OPENAPI_IMPORT.md`
- **Technical Details**: `OPENAPI_IMPORT_FEATURE.md`

---

## 🎓 Common Use Cases

### Import Public APIs
```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://api.github.com/openapi.yaml", "namespace": "github"}'
```

### Import Private/Team APIs
```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://internal-api.company.com/openapi.yaml", 
       "namespace": "internal", "visibility": "team"}'
```

### Update API Keys After Import
```bash
TOOL_ID=$(curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tools | \
  jq -r '.[] | select(.name=="myapi_getData") | .id')

curl -X PUT "http://localhost:8000/tools/$TOOL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"headers": {"X-API-KEY": "real-key-here"}}'
```

---

## ⚠️ Important Notes

1. **Conflict = Fail**: If ANY tool name exists, ENTIRE import fails (rollback)
2. **Use Namespaces**: Always provide namespace to avoid conflicts
3. **Auth Placeholders**: Update API keys/tokens after import
4. **Base URL**: First server URL from spec is used

---

## ✅ What Was Tested

- ✅ Import from URL (Petstore API)
- ✅ Import from direct YAML content
- ✅ Tool name generation (operationId and auto-generated)
- ✅ Path parameter extraction
- ✅ Query parameter extraction
- ✅ Request body schemas (POST/PUT)
- ✅ Security scheme extraction
- ✅ Namespace prefixing
- ✅ Conflict detection and rollback
- ✅ Multi-tenancy support

---

## 🎉 You're Ready!

Start using the feature right now. Import your first API:

```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore",
    "visibility": "public"
  }'
```

**Enjoy! 🎊**

