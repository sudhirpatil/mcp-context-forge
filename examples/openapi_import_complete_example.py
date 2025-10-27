#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete example of using the OpenAPI import feature.

This script demonstrates:
1. Importing tools from OpenAPI spec URL
2. Listing created tools
3. Calling imported tools via MCP protocol
4. Cleaning up tools

Usage:
    python examples/openapi_import_complete_example.py
"""

import asyncio
import json
import subprocess
import sys

import httpx


async def generate_token(secret_key: str = "my-test-key") -> str:
    """Generate JWT authentication token."""
    try:
        result = subprocess.run(
            ["python3", "-m", "mcpgateway.utils.create_jwt_token", "--username", "admin@example.com", "--exp", "60", "--secret", secret_key],
            capture_output=True,
            text=True,
            check=True,
        )
        token = result.stdout.strip().split("\n")[0]
        return token
    except Exception as e:
        print(f"❌ Failed to generate token: {e}")
        sys.exit(1)


async def import_openapi_tools(base_url: str, token: str, spec_url: str, namespace: str = None) -> dict:
    """Import tools from OpenAPI specification."""
    print(f"📥 Importing tools from: {spec_url}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/tools/openapi",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"url": spec_url, "namespace": namespace, "visibility": "public"},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully imported {result['created_count']} tools")
            return result
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"   Error: {response.text}")
            raise Exception(f"Import failed: {response.text}")


async def list_tools(base_url: str, token: str, filter_prefix: str = None) -> list:
    """List all tools, optionally filtered by name prefix."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/tools", headers={"Authorization": f"Bearer {token}"})

        if response.status_code == 200:
            tools = response.json()
            if filter_prefix:
                tools = [t for t in tools if t.get("name", "").startswith(filter_prefix)]
            return tools
        else:
            print(f"❌ Failed to list tools: {response.status_code}")
            return []


async def call_tool(base_url: str, token: str, tool_name: str, arguments: dict) -> dict:
    """Call a tool via MCP protocol."""
    print(f"\n🔧 Calling tool: {tool_name}")
    print(f"   Arguments: {json.dumps(arguments, indent=2)}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/mcp",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}},
        )

        result = response.json()

        if "result" in result:
            print(f"✅ Tool executed successfully")
            return result["result"]
        elif "error" in result:
            print(f"❌ Tool execution failed: {result['error']}")
            return result["error"]
        else:
            return result


async def delete_tool(base_url: str, token: str, tool_id: str):
    """Delete a tool by ID."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{base_url}/tools/{tool_id}", headers={"Authorization": f"Bearer {token}"})
        return response.status_code == 200


async def main():
    """Run the complete example workflow."""
    base_url = "http://localhost:8000"

    print("=" * 70)
    print("OpenAPI Tools Import - Complete Example")
    print("=" * 70)
    print()
    print("⚠️  Prerequisites:")
    print("   1. Gateway must be running: make dev")
    print("   2. Database must be initialized")
    print()
    print("=" * 70)
    print()

    # Step 1: Generate token
    print("📝 Step 1: Generate authentication token...")
    token = await generate_token()
    print(f"✅ Token generated: {token[:50]}...")
    print()

    # Step 2: Import Petstore API
    print("=" * 70)
    print("📝 Step 2: Import Petstore API")
    print("=" * 70)
    print()

    try:
        result = await import_openapi_tools(base_url, token, "https://petstore3.swagger.io/api/v3/openapi.yaml", namespace="petstore")

        print(f"\n📋 Imported Tools (showing first 10):")
        for tool in result["tools"][:10]:
            print(f"   • {tool['name']} ({tool['method']}) → {tool['url']}")

        if len(result["tools"]) > 10:
            print(f"   ... and {len(result['tools']) - 10} more")

    except Exception as e:
        print(f"❌ Failed to import: {e}")
        if "Connection" in str(e):
            print("\n💡 Make sure the gateway is running:")
            print("   cd /path/to/mcp-context-forge")
            print("   make dev")
        sys.exit(1)

    print()

    # Step 3: List created tools
    print("=" * 70)
    print("📝 Step 3: List Petstore Tools")
    print("=" * 70)
    print()

    tools = await list_tools(base_url, token, filter_prefix="petstore_")
    print(f"Found {len(tools)} Petstore tools:")
    for tool in tools[:5]:
        print(f"   • {tool['name']}: {tool.get('description', 'No description')}")

    print()

    # Step 4: Call a tool
    print("=" * 70)
    print("📝 Step 4: Test Tool Invocation")
    print("=" * 70)

    # Test getPetById (petId=10 should exist in Petstore demo)
    try:
        result = await call_tool(base_url, token, "petstore_getPetById", {"petId": 10})

        if result:
            print(f"\n📄 Response:")
            # Pretty print the result
            if isinstance(result, dict) and "content" in result:
                for content in result.get("content", []):
                    if content.get("type") == "text":
                        text = content.get("text", "")
                        try:
                            parsed = json.loads(text)
                            print(json.dumps(parsed, indent=2)[:500])
                        except:
                            print(text[:500])
    except Exception as e:
        print(f"⚠️  Tool call failed (this is expected if Petstore API is down): {e}")

    print()

    # Step 5: Summary
    print("=" * 70)
    print("✅ Example Complete!")
    print("=" * 70)
    print()
    print("What we accomplished:")
    print(f"  ✓ Imported {len(tools)} tools from Petstore OpenAPI spec")
    print(f"  ✓ All tools registered with namespace 'petstore_'")
    print(f"  ✓ Tools are now available via MCP protocol")
    print()
    print("Next steps:")
    print("  • Use tools in Claude Desktop, VS Code, or any MCP client")
    print("  • Update API keys if authentication required")
    print("  • Import other OpenAPI specs for your custom APIs")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)

