# OpenAPI Tools Import Feature

## Summary

This feature adds automatic tool registration from OpenAPI specifications, allowing users to quickly convert entire REST APIs into MCP tools without manually defining each endpoint.

## What Was Implemented

### 1. New API Endpoint

**Endpoint**: `POST /tools/openapi`

Accepts OpenAPI YAML specifications (via URL or direct content) and automatically creates REST API tools for all defined endpoints.

### 2. Components Created

#### Files Created:
1. **`mcpgateway/utils/openapi_parser.py`** - Core parsing logic
   - Fetches and parses OpenAPI YAML
   - Extracts endpoints, parameters, and authentication
   - Converts to ToolCreate objects

2. **`mcpgateway/schemas.py`** - Request/response models
   - `OpenAPIImportRequest` - Input validation
   - `OpenAPIImportResponse` - Response format

3. **`mcpgateway/main.py`** - API endpoint
   - `import_tools_from_openapi()` - Main handler

4. **Tests**:
   - `tests/unit/mcpgateway/utils/test_openapi_parser.py` - 26 unit tests (all passing ✅)
   - `test_openapi_import.py` - Integration test script
   
5. **Documentation**:
   - `docs/docs/using/openapi-import.md` - Full feature documentation
   - `examples/openapi-import-quickstart.md` - Quick reference
   - `examples/openapi-import-example.sh` - Shell script examples
   - `examples/openapi_import_complete_example.py` - Python example

## Key Features

### ✅ Implemented Requirements

1. **Dual Input Support** - Accept OpenAPI spec via URL or direct YAML content
2. **Fail-Fast on Conflicts** - If any tool name exists, entire operation rolls back
3. **Security Extraction** - Automatically extracts auth from `securitySchemes`
4. **Base URL from Spec** - Uses first server URL from OpenAPI spec
5. **Smart Tool Naming** - Uses `operationId` or generates from method + path

### 📋 Feature Highlights

- **Automatic Schema Generation**: Converts OpenAPI parameters → JSON Schema
- **Path Parameter Support**: Handles `/pet/{petId}` style paths
- **Request Body Mapping**: Extracts POST/PUT body schemas
- **Multi-Method Support**: GET, POST, PUT, DELETE, PATCH
- **Namespace Support**: Optional prefix to avoid naming conflicts
- **Team Assignment**: Integrates with multi-tenancy
- **Metadata Tracking**: Records creation via "openapi_import"

## Usage Examples

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

**Result**: Creates ~18 tools (getPetById, addPet, updatePet, etc.)

### Example 2: Import from Direct Content

```bash
curl -X POST http://localhost:8000/tools/openapi \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "openapi: 3.0.0\ninfo:\n  title: My API\npaths:\n  /users:\n    get:\n      operationId: getUsers",
    "visibility": "public"
  }'
```

### Example 3: Call an Imported Tool

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
  }'
```

## Technical Details

### Tool Name Generation Algorithm

```python
def generate_tool_name(method: str, path: str, namespace: Optional[str] = None) -> str:
    # /pet/{petId} → pet_petId
    clean_path = path.lstrip("/").replace("/", "_").replace("{", "").replace("}", "")
    
    # GET + pet_petId → get_pet_petId
    tool_name = f"{method.lower()}_{clean_path}"
    
    # Add namespace: api + get_pet_petId → api_get_pet_petId
    if namespace:
        tool_name = f"{namespace}_{tool_name}"
    
    return tool_name
```

### Parameter Mapping

| OpenAPI | JSON Schema |
|---------|-------------|
| `path: petId (integer)` | `{"properties": {"petId": {"type": "integer"}}, "required": ["petId"]}` |
| `query: status (enum)` | `{"properties": {"status": {"type": "string", "enum": [...]}}}` |
| `requestBody: {name, age}` | `{"properties": {"name": {...}, "age": {...}}}` |

### Authentication Mapping

| OpenAPI Security | Gateway Auth |
|------------------|--------------|
| `apiKey` in header | Header with placeholder value |
| `http: bearer` | Bearer token auth type |
| `http: basic` | Basic auth type |
| `oauth2` | OAuth2 flow config |

## Testing

### Run Unit Tests

```bash
pytest tests/unit/mcpgateway/utils/test_openapi_parser.py -v
```

**Result**: 26 tests, all passing ✅

### Run Integration Test

```bash
python test_openapi_import.py
```

**Prerequisites**:
- Gateway running on http://localhost:8000
- JWT_SECRET_KEY set to "my-test-key"

### Manual Testing

```bash
# Start gateway
make dev

# In another terminal, run the complete example
python examples/openapi_import_complete_example.py
```

## Code Quality

- **Type Hints**: Full type annotations
- **Docstrings**: Comprehensive documentation with examples
- **Error Handling**: Proper exception handling and rollback
- **Logging**: Detailed logging at appropriate levels
- **Validation**: Pydantic schema validation
- **Security**: Input sanitization and URL validation

## Dependencies

No new dependencies required! Uses existing packages:
- `httpx` - For fetching remote OpenAPI specs
- `pyyaml` - For parsing YAML (already in pyproject.toml)
- `pydantic` - For schema validation

## Future Enhancements

Potential improvements:
1. **Conflict Strategy Options** - Skip/update/rename instead of fail
2. **Batch Import** - Import multiple OpenAPI specs at once
3. **Spec Preview** - Preview tools before importing
4. **Custom Auth Injection** - Override spec auth with custom values
5. **Selective Import** - Import only specific endpoints
6. **JSON Support** - Accept OpenAPI in JSON format
7. **Spec Validation** - More comprehensive OpenAPI validation

## Files Modified

1. `mcpgateway/main.py` - Added endpoint and imports
2. `mcpgateway/schemas.py` - Added request/response schemas

## Files Created

1. `mcpgateway/utils/openapi_parser.py` - Parser implementation
2. `tests/unit/mcpgateway/utils/test_openapi_parser.py` - Unit tests
3. `docs/docs/using/openapi-import.md` - Feature documentation
4. `examples/openapi-import-quickstart.md` - Quick reference
5. `examples/openapi-import-example.sh` - Shell examples
6. `examples/openapi_import_complete_example.py` - Python example
7. `test_openapi_import.py` - Integration test
8. `OPENAPI_IMPORT_FEATURE.md` - This file

## Compatibility

- **MCP Protocol**: Fully compatible
- **Existing Tools**: No breaking changes
- **Authentication**: Works with JWT, Basic, OAuth
- **Multi-tenancy**: Full support for teams and visibility
- **Federation**: Tools can be federated like any other tool

## Performance

- **Parsing**: O(n) where n = number of endpoints
- **Registration**: O(n) database operations
- **Rollback**: Full transaction rollback on failure
- **Timeout**: 60 second timeout for fetching remote specs

## Security Considerations

1. **URL Validation**: Only HTTPS URLs recommended for production
2. **YAML Parsing**: Safe YAML parser used (no code execution)
3. **Authentication**: Credentials encrypted in database
4. **RBAC**: Requires `tools.create` permission
5. **Team Scoping**: Tools assigned to user's team

## Conclusion

The OpenAPI import feature dramatically simplifies REST API integration with the MCP Gateway, reducing the time to register APIs from hours to seconds. It maintains full compatibility with the existing tool system while adding powerful bulk import capabilities.

