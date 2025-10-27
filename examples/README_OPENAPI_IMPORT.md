# OpenAPI Tools Import - Feature Guide

## 🎯 Overview

The OpenAPI Tools Import feature allows you to automatically register entire REST APIs as MCP tools by simply providing an OpenAPI specification. No need to manually define each endpoint!

## 🚀 Quick Start

### 1. Start the Gateway

```bash
make dev  # Development mode on port 8000
```

### 2. Generate Auth Token

```bash
export TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com \
  --exp 60 \
  --secret my-test-key 2>/dev/null | head -1)
```

### 3. Import Petstore API

```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore",
    "visibility": "public"
  }' | jq '.'
```

### 4. List Created Tools

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tools | \
  jq '.[] | select(.name | startswith("petstore_")) | {name, url, method: .request_type}'
```

### 5. Call a Tool

```bash
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

## 📚 What Gets Created?

For each endpoint in the OpenAPI spec, a REST tool is created:

| OpenAPI Path | HTTP Method | Tool Name | Input Parameters |
|--------------|-------------|-----------|------------------|
| `/pet/{petId}` | GET | `petstore_getPetById` | `petId` (integer, required) |
| `/pet` | POST | `petstore_addPet` | Pet object (from requestBody) |
| `/pet/{petId}` | PUT | `petstore_updatePet` | `petId` + Pet object |
| `/pet/{petId}` | DELETE | `petstore_deletePet` | `petId` (integer, required) |
| `/store/inventory` | GET | `petstore_getInventory` | (no parameters) |

## 🎨 Features

### ✅ Dual Input Support
- **From URL**: Fetch OpenAPI spec from remote URL
- **From Content**: Provide YAML content directly

### ✅ Smart Tool Naming
- Uses `operationId` from OpenAPI spec
- Falls back to `{method}_{path}` format
- Optional namespace prefix to avoid conflicts

### ✅ Authentication Auto-Detection
- Extracts from OpenAPI `securitySchemes`
- Supports: API Key, Bearer Token, Basic Auth, OAuth2
- Placeholder values for manual update after import

### ✅ Complete Parameter Mapping
- **Path parameters**: `/users/{userId}` → required field
- **Query parameters**: `?status=active` → optional field
- **Request body**: POST/PUT schemas → input properties

### ✅ Fail-Safe Operation
- If ANY tool name conflicts → entire import fails
- All or nothing - no partial imports
- Database rollback on errors

## 📖 Examples

### Import from URL with Namespace

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

### Import from Direct YAML Content

```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "openapi: 3.0.0\ninfo:\n  title: My API\n  version: 1.0.0\nservers:\n  - url: https://api.example.com\npaths:\n  /users:\n    get:\n      operationId: getUsers\n      summary: List users",
    "visibility": "team",
    "team_id": "your-team-id"
  }'
```

### Import with Team-Level Visibility

```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://internal-api.company.com/openapi.yaml",
    "namespace": "internal",
    "visibility": "team"
  }'
```

## 🔧 Updating API Keys After Import

The importer creates placeholder values for authentication. Update them after import:

```bash
# 1. Find your tool
TOOL_ID=$(curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tools | \
  jq -r '.[] | select(.name=="petstore_getPetById") | .id')

# 2. Update with real credentials
curl -X PUT "http://localhost:8000/tools/$TOOL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "headers": {
      "X-API-KEY": "your-actual-api-key-here"
    }
  }'
```

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/unit/mcpgateway/utils/test_openapi_parser.py -v
```

**Result**: 26 tests ✅

### Run Complete Example

```bash
python examples/openapi_import_complete_example.py
```

### Run Shell Examples

```bash
bash examples/openapi-import-example.sh
```

## 📝 API Reference

### Request Schema

```typescript
{
  url?: string;           // URL to OpenAPI YAML spec
  content?: string;       // Direct YAML content
  namespace?: string;     // Prefix for tool names
  team_id?: string;       // Team assignment
  visibility?: string;    // "private" | "team" | "public"
}
```

### Response Schema

```typescript
{
  success: boolean;
  message: string;
  created_count: number;
  failed_count: number;
  tools: Array<{
    name: string;
    url: string;
    method: string;
  }>;
  errors: Array<{
    tool: string;
    error: string;
  }>;
}
```

## ⚠️ Important Notes

1. **Conflict Behavior**: If ANY tool name exists, ENTIRE import fails and rolls back
2. **Authentication**: Placeholder values created - update with real credentials after import
3. **Base URL**: Uses first server URL from OpenAPI spec
4. **Supported Methods**: GET, POST, PUT, DELETE, PATCH only
5. **Content Type**: Only `application/json` request/response bodies processed

## 🎓 Best Practices

1. **Always Use Namespaces**
   ```json
   {"url": "...", "namespace": "myapi"}
   ```
   Prevents naming conflicts with other APIs

2. **Import to Team First**
   ```json
   {"url": "...", "visibility": "team"}
   ```
   Test privately before making public

3. **Review Spec First**
   - Check the OpenAPI spec to see what tools will be created
   - Estimate ~1 tool per HTTP method per path

4. **Update Credentials Immediately**
   - Import creates placeholders
   - Update with real API keys before use

5. **Handle Conflicts**
   - If import fails, use different namespace
   - Or delete conflicting tools first

## 🔗 Related Documentation

- [Full Documentation](../docs/docs/using/openapi-import.md)
- [API Usage Guide](../docs/docs/manage/api-usage.md)
- [Tool Management](../docs/docs/manage/api-usage.md#tool-management)

## 💡 Tips & Tricks

### Preview Tools Before Import

Download the spec and examine it:
```bash
curl https://petstore3.swagger.io/api/v3/openapi.yaml > spec.yaml
cat spec.yaml | grep operationId
```

### Import Subset

Edit the OpenAPI spec to include only needed endpoints before importing.

### Batch Operations

Import multiple APIs with different namespaces:
```bash
for api in petstore github stripe; do
  curl -X POST http://localhost:8000/tools/openapi \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"url\": \"https://${api}.com/openapi.yaml\", \"namespace\": \"${api}\"}"
done
```

## 🐛 Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Tool name conflict | Tool already exists | Use different namespace or delete existing |
| No servers defined | Invalid OpenAPI spec | Add servers array to spec |
| Connection timeout | Slow or unavailable URL | Use `content` parameter with local copy |
| Invalid YAML | Malformed spec | Validate spec first |

## 🎉 Success!

You've now learned how to:
- ✅ Import REST APIs from OpenAPI specifications
- ✅ Automatically create MCP tools for all endpoints
- ✅ Call imported tools via MCP protocol
- ✅ Manage authentication and team visibility

**Happy API importing!** 🚀

