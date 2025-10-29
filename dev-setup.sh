
# Start McpGateway Service using uvx 
BASIC_AUTH_PASSWORD=pass \
MCPGATEWAY_UI_ENABLED=true \
MCPGATEWAY_ADMIN_API_ENABLED=true \
PLATFORM_ADMIN_EMAIL=admin@example.com \
PLATFORM_ADMIN_PASSWORD=changeme \
PLATFORM_ADMIN_FULL_NAME="Platform Administrator" \
uvx --from mcp-contextforge-gateway mcpgateway --host 0.0.0.0 --port 4444

# McpGateway from source code
cd /Users/sudhirpatil/code/mcp-context-forge && source ~/.venv/mcpgateway/bin/activate && MCPGATEWAY_UI_ENABLED=true MCPGATEWAY_ADMIN_API_ENABLED=true AUTH_REQUIRED=false uvicorn mcpgateway.main:app --host 0.0.0.0 --port 4444 --reload
cd /Users/sudhirpatil/code/mcp-context-forge && source ~/.venv/mcpgateway/bin/activate && MCPGATEWAY_UI_ENABLED=true MCPGATEWAY_ADMIN_API_ENABLED=true AUTH_REQUIRED=false PLUGINS_ENABLED=true uvicorn mcpgateway.main:app --host 0.0.0.0 --port 4444 --reload 2>&1 | tee -a gateway.log &


cd /Users/sudhirpatil/code/mcp-context-forge && make venv
cd /Users/sudhirpatil/code/mcp-context-forge && make install-dev
cd /Users/sudhirpatil/code/mcp-context-forge && source /Users/sudhirpatil/.venv/mcpgateway/bin/activate && python -m pip install --upgrade pip setuptools wheel
cp -rp /Users/sudhirpatil/.venv/mcpgateway .venv 
source .venv/mcpgateway/bin/activate && pip install -e ".[dev]" 

#Start McpGateway Service without uv
cd /Users/sudhirpatil/code/mcp-context-forge && source ~/.venv/mcpgateway/bin/activate && MCPGATEWAY_UI_ENABLED=true MCPGATEWAY_ADMIN_API_ENABLED=true AUTH_REQUIRED=false PLUGINS_ENABLED=true mcpgateway --host 0.0.0.0 --port 4444 --reload 2>&1 | tee -a gateway.log &

export MCPGATEWAY_BEARER_TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
    --username admin@example.com --exp 10080 --secret my-test-key)

# Or using the official mcp-server-git using uvx:
pip install uv # to install uvx, if not already installed
python3 -m mcpgateway.translate --stdio "uvx mcp-server-git" --expose-sse --port 9000


# Register Serper search as mcp tool
# Generate Authentication Token:
export TOKEN=$(python3 -m mcpgateway.utils.create_jwt_token \
     --username admin@example.com \
     --exp 10080 \
     --secret my-test-key 2>/dev/null | head -1)
# Verify token
echo "Token: ${TOKEN:0:50}..."

export BASE_URL="http://localhost:4444"

#Register Individual REST API Endpoints as Tools
# 1. Set your API key
export SERPER_API_KEY="777f393659d367fb6a6fd786b2e5cc6dff39578a"

# 2. Register the tool (corrected version)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"tool\": {
      \"name\": \"google_search\",
      \"description\": \"Search Google using Serper API\",
      \"url\": \"https://google.serper.dev/search\",
      \"integration_type\": \"REST\",
      \"request_type\": \"POST\",
      \"headers\": {
        \"X-API-KEY\": \"$SERPER_API_KEY\",
        \"Content-Type\": \"application/json\"
      },
      \"input_schema\": {
        \"type\": \"object\",
        \"properties\": {
          \"q\": {
            \"type\": \"string\",
            \"description\": \"Search query\"
          },
          \"num\": {
            \"type\": \"number\",
            \"description\": \"Number of results\",
            \"default\": 10
          }
        },
        \"required\": [\"q\"]
      }
    }
  }" \
  $BASE_URL/tools | jq '.'

# 3. If successful, you should see a response with the tool ID
# Then test it:
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "google_search",
      "arguments": {
        "q": "FastAPI Python",
        "num": 5
      }
    }
  }' \
  $BASE_URL/mcp | jq '.'