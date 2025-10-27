# -*- coding: utf-8 -*-
"""Location: ./tests/unit/mcpgateway/utils/test_openapi_parser.py
Copyright 2025
SPDX-License-Identifier: Apache-2.0
Authors: Mihai Criveti

Unit tests for OpenAPI parser utility.
"""

import pytest

from mcpgateway.utils.openapi_parser import convert_openapi_to_tools, extract_base_url, extract_security_config, generate_tool_name, parse_openapi_spec, path_to_input_schema


class TestGenerateToolName:
    """Test tool name generation from HTTP method and path."""

    def test_simple_path(self):
        """Test simple path without parameters."""
        assert generate_tool_name("GET", "/users") == "get_users"
        assert generate_tool_name("POST", "/pets") == "post_pets"

    def test_path_with_parameter(self):
        """Test path with single parameter."""
        assert generate_tool_name("GET", "/pet/{petId}") == "get_pet_petId"
        assert generate_tool_name("DELETE", "/user/{userId}") == "delete_user_userId"

    def test_nested_path(self):
        """Test nested path."""
        assert generate_tool_name("GET", "/store/inventory") == "get_store_inventory"
        assert generate_tool_name("POST", "/api/v1/users") == "post_api_v1_users"

    def test_path_with_hyphens(self):
        """Test path with hyphens."""
        assert generate_tool_name("GET", "/user-profile/{user-id}") == "get_user_profile_user_id"

    def test_with_namespace(self):
        """Test tool name with namespace prefix."""
        assert generate_tool_name("GET", "/pet/{petId}", namespace="petstore") == "petstore_get_pet_petId"

    def test_root_path(self):
        """Test root path."""
        assert generate_tool_name("GET", "/") == "get"


class TestExtractBaseUrl:
    """Test base URL extraction from OpenAPI spec."""

    def test_single_server(self):
        """Test extraction from spec with single server."""
        spec = {"servers": [{"url": "https://api.example.com/v1"}]}
        assert extract_base_url(spec) == "https://api.example.com/v1"

    def test_multiple_servers(self):
        """Test that first server is used when multiple present."""
        spec = {"servers": [{"url": "https://api.example.com"}, {"url": "http://localhost:8080"}]}
        assert extract_base_url(spec) == "https://api.example.com"

    def test_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        spec = {"servers": [{"url": "https://api.example.com/"}]}
        assert extract_base_url(spec) == "https://api.example.com"

    def test_no_servers(self):
        """Test error when no servers defined."""
        spec = {"paths": {}}
        with pytest.raises(ValueError, match="No servers defined"):
            extract_base_url(spec)


class TestExtractSecurityConfig:
    """Test security configuration extraction."""

    def test_api_key_security(self):
        """Test API key security scheme extraction."""
        spec = {"components": {"securitySchemes": {"api_key": {"type": "apiKey", "name": "X-API-KEY", "in": "header"}}}}
        config = extract_security_config(spec)
        assert config["auth_type"] == "apiKey"
        assert config["header_name"] == "X-API-KEY"
        assert config["in"] == "header"

    def test_bearer_token_security(self):
        """Test bearer token security scheme extraction."""
        spec = {"components": {"securitySchemes": {"bearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}}}
        config = extract_security_config(spec)
        assert config["auth_type"] == "bearer"
        assert config["bearer_format"] == "JWT"

    def test_basic_auth_security(self):
        """Test basic auth security scheme extraction."""
        spec = {"components": {"securitySchemes": {"basic": {"type": "http", "scheme": "basic"}}}}
        config = extract_security_config(spec)
        assert config["auth_type"] == "basic"

    def test_no_security(self):
        """Test when no security schemes defined."""
        spec = {"components": {}}
        config = extract_security_config(spec)
        assert config["auth_type"] is None


class TestPathToInputSchema:
    """Test conversion of OpenAPI parameters to JSON Schema."""

    def test_path_parameter(self):
        """Test path parameter extraction."""
        parameters = [{"name": "petId", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Pet ID to fetch"}]
        schema = path_to_input_schema("/pet/{petId}", parameters=parameters)

        assert "petId" in schema["properties"]
        assert schema["properties"]["petId"]["type"] == "integer"
        assert "petId" in schema["required"]

    def test_query_parameter(self):
        """Test query parameter extraction."""
        parameters = [{"name": "status", "in": "query", "required": False, "schema": {"type": "string", "enum": ["available", "sold"]}}]
        schema = path_to_input_schema("/pet/findByStatus", parameters=parameters)

        assert "status" in schema["properties"]
        assert schema["properties"]["status"]["enum"] == ["available", "sold"]
        assert "status" not in schema["required"]

    def test_request_body_post(self):
        """Test request body for POST method."""
        request_body = {
            "required": True,
            "content": {"application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}, "required": ["name"]}}},
        }
        schema = path_to_input_schema("/user", request_body=request_body, method="POST")

        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "name" in schema["required"]

    def test_multiple_parameters(self):
        """Test multiple parameters of different types."""
        parameters = [
            {"name": "userId", "in": "path", "required": True, "schema": {"type": "integer"}},
            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "default": 10}},
            {"name": "offset", "in": "query", "required": False, "schema": {"type": "integer", "default": 0}},
        ]
        schema = path_to_input_schema("/user/{userId}/posts", parameters=parameters)

        assert len(schema["properties"]) == 3
        assert schema["properties"]["limit"]["default"] == 10
        assert "userId" in schema["required"]
        assert "limit" not in schema["required"]


class TestConvertOpenapiToTools:
    """Test conversion of OpenAPI spec to ToolCreate objects."""

    def test_simple_get_endpoint(self):
        """Test conversion of simple GET endpoint."""
        spec = {
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "List all users",
                        "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
                    }
                }
            }
        }
        tools = convert_openapi_to_tools(spec, "https://api.example.com", {})

        assert len(tools) == 1
        assert tools[0].name == "getUsers"
        assert tools[0].request_type == "GET"
        assert tools[0].url == "https://api.example.com/users"
        assert tools[0].integration_type == "REST"

    def test_post_endpoint_with_body(self):
        """Test conversion of POST endpoint with request body."""
        spec = {
            "paths": {
                "/pets": {
                    "post": {
                        "operationId": "createPet",
                        "summary": "Create a new pet",
                        "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}}}},
                    }
                }
            }
        }
        tools = convert_openapi_to_tools(spec, "https://api.example.com", {})

        assert len(tools) == 1
        assert tools[0].name == "createPet"
        assert tools[0].request_type == "POST"
        assert "name" in tools[0].input_schema["properties"]

    def test_multiple_methods_same_path(self):
        """Test path with multiple HTTP methods."""
        spec = {"paths": {"/pet/{petId}": {"get": {"operationId": "getPet"}, "put": {"operationId": "updatePet"}, "delete": {"operationId": "deletePet"}}}}
        tools = convert_openapi_to_tools(spec, "https://api.example.com", {})

        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert "getPet" in tool_names
        assert "updatePet" in tool_names
        assert "deletePet" in tool_names

    def test_with_namespace(self):
        """Test tool creation with namespace prefix."""
        spec = {"paths": {"/users": {"get": {"operationId": "getUsers"}}}}
        tools = convert_openapi_to_tools(spec, "https://api.example.com", {}, namespace="myapi")

        assert len(tools) == 1
        assert tools[0].name == "myapi_getUsers"

    def test_no_operation_id(self):
        """Test generation when operationId is missing."""
        spec = {"paths": {"/pet/{petId}": {"get": {"summary": "Get pet by ID"}}}}
        tools = convert_openapi_to_tools(spec, "https://api.example.com", {})

        assert len(tools) == 1
        assert tools[0].name == "get_pet_petId"

    def test_with_api_key_auth(self):
        """Test tool creation with API key authentication."""
        spec = {"paths": {"/data": {"get": {"operationId": "getData"}}}}
        auth_config = {"auth_type": "apiKey", "header_name": "X-API-KEY", "in": "header"}
        tools = convert_openapi_to_tools(spec, "https://api.example.com", auth_config)

        assert len(tools) == 1
        assert tools[0].headers is not None
        assert "X-API-KEY" in tools[0].headers


@pytest.mark.asyncio
async def test_parse_openapi_spec_from_content():
    """Test parsing OpenAPI spec from direct content."""
    yaml_content = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
servers:
  - url: https://api.test.com
paths:
  /test:
    get:
      operationId: testGet
"""
    spec = await parse_openapi_spec(content=yaml_content)

    assert spec["info"]["title"] == "Test API"
    assert spec["servers"][0]["url"] == "https://api.test.com"
    assert "/test" in spec["paths"]


@pytest.mark.asyncio
async def test_parse_openapi_spec_validation():
    """Test validation errors in parse_openapi_spec."""
    # Test missing both url and content
    with pytest.raises(ValueError, match="must be provided"):
        await parse_openapi_spec()

    # Test both url and content provided
    with pytest.raises(ValueError, match="not both"):
        await parse_openapi_spec(url="http://example.com", content="test")

    # Test invalid YAML
    with pytest.raises(ValueError, match="Failed to parse YAML"):
        await parse_openapi_spec(content="invalid: yaml: content:")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

