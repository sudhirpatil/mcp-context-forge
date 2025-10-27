#!/bin/bash
# Example script demonstrating OpenAPI tools import

set -e

echo "=================================================="
echo "OpenAPI Tools Import - Complete Example"
echo "=================================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
JWT_SECRET="${JWT_SECRET:-my-test-key}"

echo "📝 Step 1: Generate authentication token..."
TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
  --username admin@example.com \
  --exp 60 \
  --secret "$JWT_SECRET" 2>/dev/null | head -1)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to generate token"
    echo "💡 Make sure: pip install -e ."
    exit 1
fi

echo "✅ Token generated: ${TOKEN:0:50}..."
echo ""

# Example 1: Import Petstore API from URL
echo "=================================================="
echo "Example 1: Import Petstore API from URL"
echo "=================================================="
echo ""

curl -X POST "$BASE_URL/tools/openapi" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore3.swagger.io/api/v3/openapi.yaml",
    "namespace": "petstore",
    "visibility": "public"
  }' | jq '.'

echo ""
echo "=================================================="
echo "Example 2: List Created Tools"
echo "=================================================="
echo ""

curl -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/tools" | jq '.[] | select(.name | startswith("petstore_")) | {name, url, method: .request_type}'

echo ""
echo "=================================================="
echo "Example 3: Call an Imported Tool"
echo "=================================================="
echo ""

echo "Calling petstore_getPetById with petId=10..."
curl -X POST "$BASE_URL/mcp" \
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
  }' | jq '.'

echo ""
echo "=================================================="
echo "Example 4: Import from Direct YAML Content"
echo "=================================================="
echo ""

read -r -d '' OPENAPI_CONTENT << 'EOF' || true
openapi: 3.0.0
info:
  title: Example API
  version: 1.0.0
servers:
  - url: https://api.example.com
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
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
  /users/{userId}:
    get:
      operationId: getUserById
      summary: Get user by ID
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
EOF

# Note: In practice, you'd escape this properly for JSON
# This is just an example showing the structure

echo "Would import custom API with content (see script for YAML structure)"
echo ""

echo "=================================================="
echo "✅ Complete! Examples finished."
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Check imported tools: curl -H \"Authorization: Bearer \$TOKEN\" $BASE_URL/tools"
echo "  2. Update API keys if needed"
echo "  3. Test tools via MCP protocol"
echo "  4. Integrate with your MCP clients (Claude, VS Code, etc.)"

