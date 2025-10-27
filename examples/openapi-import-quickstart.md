# OpenAPI Import - Quick Start Guide

## What is it?

The `/tools/openapi` endpoint automatically converts entire OpenAPI specifications into MCP tools, saving you from manually registering each REST API endpoint.

## Basic Usage

```bash
# Generate token
export TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com --exp 60 --secret my-test-key 2>/dev/null | head -1)

# Import from URL
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore",
    "visibility": "public"
  }'
```

## What Gets Created?

For this OpenAPI path:
```yaml
paths:
  /pet/{petId}:
    get:
      operationId: getPetById
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
```

You get this MCP tool:
- **Name**: `petstore_getPetById` (with namespace) or `getPetById` (without)
- **URL**: `https://petstore3.swagger.io/api/v3/pet/{petId}`
- **Method**: `GET`
- **Input Schema**: Validates `petId` as required integer
- **Integration Type**: `REST`

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `url` | conditional* | - | URL to OpenAPI YAML file |
| `content` | conditional* | - | Direct YAML content string |
| `namespace` | optional | - | Prefix for all tool names (recommended!) |
| `visibility` | optional | `public` | `private`, `team`, or `public` |
| `team_id` | optional | user's personal team | Team to assign tools to |

*Either `url` or `content` required, not both

## Tool Naming Rules

| OpenAPI | Generated Tool Name |
|---------|-------------------|
| `operationId: getUsers` | `getUsers` |
| `GET /users` (no operationId) | `get_users` |
| `GET /pet/{petId}` | `get_pet_petId` |
| `POST /store/order` | `post_store_order` |
| With namespace `api` → | `api_getUsers` |

## Response Format

```json
{
  "success": true,
  "message": "Successfully imported 18 tools",
  "created_count": 18,
  "failed_count": 0,
  "tools": [
    {"name": "petstore_getPetById", "url": "...", "method": "GET"}
  ],
  "errors": []
}
```

## Error Handling

### Tool Name Conflict

If ANY tool name conflicts, the ENTIRE import fails:

```json
{
  "detail": "Tool name conflict: Tool 'getPetById' already exists. No tools were registered. Operation rolled back."
}
```

**Solution**: 
- Use a different namespace
- Delete conflicting tools first
- Import a different OpenAPI spec

### Invalid Specification

```json
{
  "detail": "No servers defined in OpenAPI spec. Cannot determine base URL."
}
```

**Solution**: Ensure your OpenAPI spec includes a `servers` array

## After Import

### 1. List Your Tools

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/tools | jq '.[] | select(.name | startswith("petstore_"))'
```

### 2. Update API Keys (if needed)

```bash
# Get tool ID
TOOL_ID=$(curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tools | \
  jq -r '.[] | select(.name=="petstore_getPetById") | .id')

# Update API key
curl -X PUT "http://localhost:8000/tools/$TOOL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "headers": {
      "X-API-KEY": "your-actual-api-key"
    }
  }'
```

### 3. Call a Tool

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

## Common Use Cases

### Import Public APIs

```bash
# GitHub API
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.github.com/openapi.yaml",
    "namespace": "github"
  }'

# Stripe API (if they provide OpenAPI spec)
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://stripe.com/docs/api/openapi.yaml",
    "namespace": "stripe"
  }'
```

### Import Internal APIs

```bash
# Your company's internal API
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://internal-api.company.com/openapi.yaml",
    "namespace": "internal",
    "visibility": "team"
  }'
```

## Troubleshooting

### Gateway Not Running

```
❌ Cannot connect to http://localhost:8000
```

**Fix**: Start the gateway
```bash
make dev  # Development mode
# or
make serve  # Production mode
```

### Import Hangs

Check if the OpenAPI spec URL is accessible:
```bash
curl -I https://petstore3.swagger.io/api/v3/openapi.yaml
```

### Tools Not Appearing

Verify visibility settings and team assignment:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/tools?visibility=public"
```

## Advanced: Programmatic Import

```python
import httpx
import asyncio

async def import_and_use_api(spec_url: str, namespace: str):
    """Import OpenAPI spec and call a tool."""
    token = "your-jwt-token"
    
    async with httpx.AsyncClient() as client:
        # Import
        response = await client.post(
            "http://localhost:8000/tools/openapi",
            headers={"Authorization": f"Bearer {token}"},
            json={"url": spec_url, "namespace": namespace}
        )
        result = response.json()
        
        # Use first tool
        if result['tools']:
            first_tool = result['tools'][0]
            print(f"Calling {first_tool['name']}...")
            
            # Call via MCP
            call_response = await client.post(
                "http://localhost:8000/mcp",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": first_tool['name'],
                        "arguments": {}
                    }
                }
            )
            print(call_response.json())

asyncio.run(import_and_use_api(
    "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "petstore"
))
```

## See Also

- [Full OpenAPI Import Documentation](../docs/using/openapi-import.md)
- [Tool Management API](../docs/manage/api-usage.md#tool-management)
- [Authentication Guide](../docs/manage/securing.md)

