# OpenAPI Tools Import

## Overview

The MCP Gateway provides a powerful `/tools/openapi` endpoint that automatically converts OpenAPI specifications into MCP tools. This feature allows you to quickly register entire REST APIs as a collection of callable MCP tools without manually defining each endpoint.

## Quick Start

### Import from URL

```bash
# Set authentication
export TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com \
  --exp 10080 \
  --secret my-test-key 2>/dev/null | head -1)

# Import Petstore API
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore",
    "visibility": "public"
  }'
```

### Import from Direct Content

```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "openapi: 3.0.0\ninfo:\n  title: My API\n  version: 1.0.0\nservers:\n  - url: https://api.example.com\npaths:\n  /users:\n    get:\n      operationId: getUsers\n      summary: List users",
    "visibility": "public"
  }'
```

## Request Schema

### OpenAPIImportRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | conditional | URL to fetch OpenAPI YAML specification |
| `content` | string | conditional | Direct YAML content |
| `namespace` | string | optional | Prefix for all tool names |
| `team_id` | string | optional | Team ID to assign tools to |
| `visibility` | string | optional | Tool visibility: `private`, `team`, `public` (default: `public`) |

**Note**: Either `url` or `content` must be provided, but not both.

## Response Schema

### OpenAPIImportResponse

```json
{
  "success": true,
  "message": "Successfully imported 18 tools from OpenAPI specification",
  "created_count": 18,
  "failed_count": 0,
  "tools": [
    {
      "name": "petstore_getPetById",
      "url": "https://petstore3.swagger.io/api/v3/pet/123",
      "method": "GET"
    }
  ],
  "errors": []
}
```

## How It Works

### 1. Tool Name Generation

**With operationId:**
```yaml
paths:
  /pet/{petId}:
    get:
      operationId: getPetById  # ← Used as tool name
```
→ Tool name: `getPetById` (or `petstore_getPetById` with namespace)

**Without operationId:**
```yaml
paths:
  /store/inventory:
    get:
      summary: Get inventory
```
→ Tool name: `get_store_inventory` (generated from method + path)

### 2. Base URL Extraction

The importer uses the first server URL from the OpenAPI spec:

```yaml
servers:
  - url: https://petstore3.swagger.io/api/v3  # ← This is used
  - url: http://localhost:8080                 # ← Ignored
```

All endpoints will be prefixed with this base URL.

### 3. Parameter Mapping

**Path Parameters:**
```yaml
paths:
  /pet/{petId}:
    get:
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
```
→ Input schema: `{"properties": {"petId": {"type": "integer"}}, "required": ["petId"]}`

**Query Parameters:**
```yaml
parameters:
  - name: status
    in: query
    required: false
    schema:
      type: string
      enum: [available, pending, sold]
```
→ Input schema includes `status` as optional property with enum values

**Request Body (POST/PUT):**
```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name:
            type: string
          status:
            type: string
```
→ Properties are added directly to input schema

### 4. Authentication Extraction

The importer automatically detects and configures authentication from OpenAPI security schemes:

**API Key:**
```yaml
components:
  securitySchemes:
    api_key:
      type: apiKey
      name: X-API-KEY
      in: header
```
→ Creates header: `{"X-API-KEY": "PLACEHOLDER_API_KEY"}`  
*Note: Update the actual key value after import*

**Bearer Token:**
```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```
→ Auth type configured as `bearer`

**Basic Auth:**
```yaml
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
```
→ Auth type configured as `basic`

## Examples

### Example 1: Import Petstore API

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

**Created Tools:**
- `petstore_getPetById` - Get pet by ID
- `petstore_addPet` - Add a new pet
- `petstore_updatePet` - Update an existing pet
- `petstore_deletePet` - Delete a pet
- `petstore_findPetsByStatus` - Find pets by status
- `petstore_getInventory` - Get store inventory
- ... and more

### Example 2: Import Custom API with Authentication

```bash
# Your OpenAPI spec with API key auth
OPENAPI_SPEC='
openapi: 3.0.0
info:
  title: My Custom API
  version: 1.0.0
servers:
  - url: https://api.myservice.com
components:
  securitySchemes:
    apiKey:
      type: apiKey
      name: X-API-KEY
      in: header
paths:
  /users:
    get:
      operationId: listUsers
      summary: List all users
      security:
        - apiKey: []
'

curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"$OPENAPI_SPEC\",
    \"namespace\": \"myapi\",
    \"visibility\": \"team\"
  }"
```

### Example 3: Update API Key After Import

After importing, update the placeholder API key:

```bash
# Get the tool ID
TOOL_ID=$(curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/tools | jq -r '.[] | select(.name=="petstore_getPetById") | .id')

# Update with real API key
curl -X PUT http://localhost:8000/tools/$TOOL_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "headers": {
      "X-API-KEY": "your-real-api-key-here"
    }
  }'
```

## Error Handling

### Conflict Detection

If any tool name conflicts with an existing tool, the **entire operation fails** and no tools are created:

```json
{
  "detail": "Tool name conflict: Tool 'getPetById' already exists. No tools were registered. Operation rolled back."
}
```

**Status Code:** 409 Conflict

### Validation Errors

```json
{
  "detail": "No servers defined in OpenAPI spec. Cannot determine base URL."
}
```

**Status Code:** 422 Unprocessable Entity

### Network Errors

```json
{
  "detail": "Failed to fetch OpenAPI spec from URL: Connection timeout"
}
```

**Status Code:** 422 Unprocessable Entity

## Testing Imported Tools

After import, test a tool using the standard MCP protocol:

```bash
# List all tools to verify import
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/tools | jq '.[] | select(.name | startswith("petstore_"))'

# Call a tool
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "petstore_getPetById",
      "arguments": {
        "petId": 10
      }
    }
  }'
```

## Supported OpenAPI Versions

- OpenAPI 3.0.x
- Swagger 2.0 (limited support)

## Limitations

1. **HTTP Methods Only**: Supports GET, POST, PUT, DELETE, PATCH
2. **JSON Content**: Only `application/json` content types are processed
3. **First Server Only**: Uses only the first server URL from the servers array
4. **First Security Scheme**: Uses only the first security scheme if multiple defined
5. **Fail-Fast**: Any naming conflict or error causes entire import to fail and rollback

## Best Practices

1. **Use Namespaces**: Always provide a `namespace` to avoid tool name conflicts
   ```json
   {"url": "...", "namespace": "myapi"}
   ```

2. **Review Before Import**: Check the OpenAPI spec to understand what tools will be created

3. **Update Credentials**: Immediately update placeholder authentication values after import

4. **Test Incrementally**: Import a subset first (you may need to create a filtered OpenAPI spec)

5. **Monitor Conflicts**: If import fails due to conflicts, either:
   - Delete conflicting tools
   - Use a different namespace
   - Rename tools in the OpenAPI spec

## Programmatic Usage

```python
import httpx

async def import_openapi_tools(token: str, spec_url: str):
    """Import tools from OpenAPI specification."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/tools/openapi",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "url": spec_url,
                "namespace": "myapi",
                "visibility": "public"
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await import_openapi_tools(token, "https://api.example.com/openapi.yaml")
print(f"Imported {result['created_count']} tools")
```

## Related Documentation

- [Tool Management](../manage/api-usage.md#tool-management)
- [Bulk Import](../manage/bulk-import.md)
- [API Authentication](../manage/securing.md)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)

