# -*- coding: utf-8 -*-
"""Location: ./mcpgateway/utils/openapi_parser.py
Copyright 2025
SPDX-License-Identifier: Apache-2.0
Authors: Mihai Criveti

OpenAPI Specification Parser for MCP Gateway.

This module provides utilities for parsing OpenAPI specifications and converting
them into MCP Gateway tool definitions.
"""

# Standard
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

# Third-Party
import httpx
import yaml

# First-Party
from mcpgateway.schemas import ToolCreate

logger = logging.getLogger(__name__)


async def parse_openapi_spec(url: Optional[str] = None, content: Optional[str] = None) -> dict:
    """Parse OpenAPI specification from URL or direct content.

    Args:
        url: URL to fetch OpenAPI YAML specification from
        content: Direct YAML content as string

    Returns:
        Parsed OpenAPI specification as dictionary

    Raises:
        ValueError: If neither url nor content provided, or if parsing fails
        httpx.HTTPError: If URL fetch fails

    Examples:
        >>> import asyncio
        >>> # Parse from content
        >>> yaml_content = '''
        ... openapi: 3.0.0
        ... info:
        ...   title: Test API
        ...   version: 1.0.0
        ... paths: {}
        ... '''
        >>> spec = asyncio.run(parse_openapi_spec(content=yaml_content))
        >>> spec['info']['title']
        'Test API'
    """
    if not url and not content:
        raise ValueError("Either 'url' or 'content' must be provided")

    if url and content:
        raise ValueError("Provide either 'url' or 'content', not both")

    try:
        if url:
            logger.info(f"Fetching OpenAPI spec from URL: {url}")
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                spec_content = response.text
        else:
            spec_content = content

        # Parse YAML
        spec = yaml.safe_load(spec_content)

        # Validate it's a valid OpenAPI spec
        if not isinstance(spec, dict):
            raise ValueError("Invalid OpenAPI spec: root must be an object")

        if "openapi" not in spec and "swagger" not in spec:
            raise ValueError("Invalid OpenAPI spec: missing 'openapi' or 'swagger' version field")

        logger.info(f"Successfully parsed OpenAPI spec: {spec.get('info', {}).get('title', 'Unknown')}")
        return spec

    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML: {str(e)}")
    except httpx.HTTPError as e:
        raise ValueError(f"Failed to fetch OpenAPI spec from URL: {str(e)}")


def extract_base_url(spec: dict) -> str:
    """Extract base URL from OpenAPI specification.

    Uses the first server URL from the servers array.

    Args:
        spec: Parsed OpenAPI specification

    Returns:
        Base URL for API endpoints

    Raises:
        ValueError: If no servers defined

    Examples:
        >>> spec = {
        ...     'servers': [
        ...         {'url': 'https://api.example.com/v1'},
        ...         {'url': 'http://localhost:8080'}
        ...     ]
        ... }
        >>> extract_base_url(spec)
        'https://api.example.com/v1'

        >>> spec_no_servers = {'paths': {}}
        >>> try:
        ...     extract_base_url(spec_no_servers)
        ... except ValueError as e:
        ...     'No servers defined' in str(e)
        True
    """
    servers = spec.get("servers", [])

    if not servers:
        raise ValueError("No servers defined in OpenAPI spec. Cannot determine base URL.")

    base_url = servers[0].get("url", "")

    if not base_url:
        raise ValueError("First server in OpenAPI spec has no URL")

    logger.info(f"Using base URL: {base_url}")
    return base_url.rstrip("/")


def extract_security_config(spec: dict) -> Dict[str, Any]:
    """Extract authentication configuration from OpenAPI security schemes.

    Maps OpenAPI security schemes to gateway authentication format.

    Args:
        spec: Parsed OpenAPI specification

    Returns:
        Dictionary with auth_type and auth_headers/auth_value

    Examples:
        >>> spec = {
        ...     'components': {
        ...         'securitySchemes': {
        ...             'api_key': {
        ...                 'type': 'apiKey',
        ...                 'name': 'X-API-KEY',
        ...                 'in': 'header'
        ...             }
        ...         }
        ...     }
        ... }
        >>> config = extract_security_config(spec)
        >>> config['auth_type']
        'apiKey'
        >>> config['header_name']
        'X-API-KEY'
    """
    security_schemes = spec.get("components", {}).get("securitySchemes", {})

    if not security_schemes:
        logger.info("No security schemes found in OpenAPI spec")
        return {"auth_type": None}

    # Use the first security scheme
    scheme_name, scheme = next(iter(security_schemes.items()))
    scheme_type = scheme.get("type", "").lower()

    logger.info(f"Found security scheme: {scheme_name} (type: {scheme_type})")

    if scheme_type == "apikey":
        return {
            "auth_type": "apiKey",
            "header_name": scheme.get("name", "X-API-KEY"),
            "in": scheme.get("in", "header"),
        }
    elif scheme_type == "http":
        http_scheme = scheme.get("scheme", "").lower()
        if http_scheme == "bearer":
            return {"auth_type": "bearer", "bearer_format": scheme.get("bearerFormat", "JWT")}
        elif http_scheme == "basic":
            return {"auth_type": "basic"}
    elif scheme_type == "oauth2":
        return {"auth_type": "oauth2", "flows": scheme.get("flows", {})}

    return {"auth_type": None}


def generate_tool_name(method: str, path: str, namespace: Optional[str] = None) -> str:
    """Generate tool name from HTTP method and path.

    Converts path parameters and special characters to underscores.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., /pet/{petId})
        namespace: Optional prefix for tool name

    Returns:
        Generated tool name

    Examples:
        >>> generate_tool_name("GET", "/pet/{petId}")
        'get_pet_petId'

        >>> generate_tool_name("POST", "/user")
        'post_user'

        >>> generate_tool_name("GET", "/store/inventory")
        'get_store_inventory'

        >>> generate_tool_name("DELETE", "/pet/{petId}", namespace="petstore")
        'petstore_delete_pet_petId'

        >>> generate_tool_name("GET", "/api/v1/users/{user-id}/posts")
        'get_api_v1_users_user_id_posts'
    """
    # Remove leading slash and replace special characters
    clean_path = path.lstrip("/")

    # Replace path separators and special characters with underscores
    clean_path = re.sub(r"[/\-\.]", "_", clean_path)

    # Remove curly braces but keep parameter names
    clean_path = re.sub(r"[{}]", "", clean_path)

    # Remove multiple consecutive underscores
    clean_path = re.sub(r"_+", "_", clean_path)

    # Remove trailing underscore
    clean_path = clean_path.rstrip("_")

    # Build tool name
    tool_name = f"{method.lower()}_{clean_path}" if clean_path else method.lower()

    # Add namespace prefix if provided
    if namespace:
        tool_name = f"{namespace}_{tool_name}"

    return tool_name


def path_to_input_schema(path: str, parameters: Optional[List[Dict[str, Any]]] = None, request_body: Optional[Dict[str, Any]] = None, method: str = "GET") -> Dict[str, Any]:
    """Convert OpenAPI path parameters and request body to JSON Schema.

    Args:
        path: API path with parameter placeholders
        parameters: OpenAPI parameters array
        request_body: OpenAPI requestBody object
        method: HTTP method

    Returns:
        JSON Schema for tool input validation

    Examples:
        >>> # Path parameters
        >>> params = [
        ...     {'name': 'petId', 'in': 'path', 'required': True,
        ...      'schema': {'type': 'integer'}, 'description': 'Pet ID'}
        ... ]
        >>> schema = path_to_input_schema('/pet/{petId}', parameters=params)
        >>> schema['properties']['petId']['type']
        'integer'
        >>> 'petId' in schema['required']
        True

        >>> # Query parameters
        >>> params = [
        ...     {'name': 'status', 'in': 'query', 'required': False,
        ...      'schema': {'type': 'string', 'enum': ['available', 'sold']}}
        ... ]
        >>> schema = path_to_input_schema('/pet/findByStatus', parameters=params)
        >>> schema['properties']['status']['enum']
        ['available', 'sold']
    """
    schema = {"type": "object", "properties": {}, "required": []}

    # Extract path parameters from the path itself
    path_params = re.findall(r"\{(\w+)\}", path)

    # Process parameters array
    if parameters:
        for param in parameters:
            param_name = param.get("name")
            param_in = param.get("in", "query")
            param_schema = param.get("schema", {})
            param_required = param.get("required", False)
            param_description = param.get("description", "")

            # Only include path and query parameters
            if param_in in ["path", "query"]:
                schema["properties"][param_name] = {
                    "type": param_schema.get("type", "string"),
                    "description": param_description,
                }

                # Add enum if present
                if "enum" in param_schema:
                    schema["properties"][param_name]["enum"] = param_schema["enum"]

                # Add default if present
                if "default" in param_schema:
                    schema["properties"][param_name]["default"] = param_schema["default"]

                # Mark as required
                if param_required or param_in == "path":
                    schema["required"].append(param_name)

    # Add path parameters not in parameters array
    for path_param in path_params:
        if path_param not in schema["properties"]:
            schema["properties"][path_param] = {"type": "string", "description": f"Path parameter: {path_param}"}
            if path_param not in schema["required"]:
                schema["required"].append(path_param)

    # Process request body for POST, PUT, PATCH
    if request_body and method.upper() in ["POST", "PUT", "PATCH"]:
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})

        if json_content and "schema" in json_content:
            body_schema = json_content["schema"]

            # If body schema has properties, add them directly
            if "properties" in body_schema:
                for prop_name, prop_schema in body_schema["properties"].items():
                    schema["properties"][prop_name] = prop_schema

                # Add required fields from body
                if "required" in body_schema:
                    schema["required"].extend(body_schema["required"])
            else:
                # Entire body as a single property
                schema["properties"]["body"] = body_schema
                if request_body.get("required", False):
                    schema["required"].append("body")

    return schema


def convert_openapi_to_tools(spec: dict, base_url: str, auth_config: Dict[str, Any], namespace: Optional[str] = None) -> List[ToolCreate]:
    """Convert OpenAPI specification to list of ToolCreate objects.

    Args:
        spec: Parsed OpenAPI specification
        base_url: Base URL for API endpoints
        auth_config: Authentication configuration
        namespace: Optional prefix for tool names

    Returns:
        List of ToolCreate objects ready for registration

    Raises:
        ValueError: If spec is invalid or missing required fields

    Examples:
        >>> spec = {
        ...     'paths': {
        ...         '/pet/{petId}': {
        ...             'get': {
        ...                 'operationId': 'getPetById',
        ...                 'summary': 'Get pet by ID',
        ...                 'parameters': [
        ...                     {'name': 'petId', 'in': 'path', 'required': True,
        ...                      'schema': {'type': 'integer'}}
        ...                 ]
        ...             }
        ...         }
        ...     }
        ... }
        >>> tools = convert_openapi_to_tools(spec, 'https://api.example.com', {})
        >>> len(tools)
        1
        >>> tools[0].name
        'get_pet_petId'
        >>> tools[0].integration_type
        'REST'
    """
    paths = spec.get("paths", {})

    if not paths:
        raise ValueError("No paths defined in OpenAPI specification")

    tools = []
    supported_methods = ["get", "post", "put", "delete", "patch"]

    # Prepare headers for auth
    headers = {}
    if auth_config.get("auth_type") == "apiKey":
        # Note: Actual value needs to be provided at runtime
        # We just define the header name here
        header_name = auth_config.get("header_name", "X-API-KEY")
        headers[header_name] = "PLACEHOLDER_API_KEY"

    for path, path_item in paths.items():
        for method in supported_methods:
            if method not in path_item:
                continue

            operation = path_item[method]

            # Generate tool name (use operationId if available, otherwise generate)
            if "operationId" in operation:
                tool_name = operation["operationId"]
                # Add namespace if provided
                if namespace:
                    tool_name = f"{namespace}_{tool_name}"
            else:
                tool_name = generate_tool_name(method.upper(), path, namespace)

            # Build full URL
            full_url = urljoin(base_url + "/", path.lstrip("/"))

            # Get description
            description = operation.get("summary") or operation.get("description") or f"{method.upper()} {path}"

            # Build input schema
            parameters = operation.get("parameters", [])
            request_body = operation.get("requestBody")
            input_schema = path_to_input_schema(path, parameters, request_body, method.upper())

            # Create ToolCreate object
            tool = ToolCreate(
                name=tool_name,
                displayName=operation.get("summary", tool_name),
                url=full_url,
                description=description,
                integration_type="REST",
                request_type=method.upper(),
                headers=headers if headers else None,
                input_schema=input_schema,
                tags=operation.get("tags", []),
            )

            tools.append(tool)
            logger.debug(f"Created tool definition: {tool_name} ({method.upper()} {path})")

    logger.info(f"Converted {len(tools)} endpoints to tool definitions")
    return tools
