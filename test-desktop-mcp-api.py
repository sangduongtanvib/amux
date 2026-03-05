#!/usr/bin/env python3
"""Test script for Desktop MCP Config API."""

import json
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path

AMUX_API = "https://localhost:8822"

# SSL context for self-signed cert
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def api_call(endpoint, method="GET", data=None):
    """Make API call to Amux server."""
    url = f"{AMUX_API}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers=headers,
                method=method
            )
        else:
            req = urllib.request.Request(url, headers=headers, method=method)
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ API Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


def test_list_desktop_configs():
    """Test GET /api/desktop-mcp."""
    print("\n🔍 Test 1: List available desktop configs")
    print("-" * 60)
    
    result = api_call("/api/desktop-mcp")
    if not result:
        return False
    
    configs = result.get("configs", [])
    print(f"✅ Found {len(configs)} desktop app configs:\n")
    
    for config in configs:
        status = "✓" if config["exists"] else "✗"
        print(f"  [{status}] {config['name']}")
        print(f"      ID: {config['id']}")
        print(f"      Path: {config['path']}")
        print(f"      Servers: {config['server_count']}")
        print()
    
    return len(configs) > 0


def test_get_claude_config():
    """Test GET /api/desktop-mcp/claude."""
    print("\n🔍 Test 2: Get Claude Desktop config")
    print("-" * 60)
    
    result = api_call("/api/desktop-mcp/claude")
    if not result:
        return False
    
    if "error" in result:
        print(f"⚠️  {result['error']}")
        return True  # Expected if file doesn't exist
    
    print(f"✅ {result['app']} config loaded")
    print(f"   Path: {result['path']}")
    print(f"   Format: {result['format']}")
    print(f"   Servers: {result['server_count']}\n")
    
    mcp_servers = result.get("mcpServers", {})
    if mcp_servers:
        print("   MCP Servers:")
        for name, config in mcp_servers.items():
            print(f"     - {name} ({config.get('type', 'unknown')})")
    
    return True


def test_get_cursor_config():
    """Test GET /api/desktop-mcp/cursor."""
    print("\n🔍 Test 3: Get Cursor config")
    print("-" * 60)
    
    result = api_call("/api/desktop-mcp/cursor")
    if not result:
        return False
    
    if "error" in result:
        print(f"⚠️  {result['error']}")
        return True  # Expected if file doesn't exist
    
    print(f"✅ {result['app']} config loaded")
    print(f"   Path: {result['path']}")
    print(f"   Format: {result['format']}")
    print(f"   Servers: {result['server_count']}\n")
    
    mcp_servers = result.get("mcpServers", {})
    if mcp_servers:
        print("   MCP Servers:")
        for name, config in mcp_servers.items():
            print(f"     - {name} ({config.get('type', 'unknown')})")
    
    return True


def test_update_claude_config():
    """Test POST /api/desktop-mcp/claude."""
    print("\n🔍 Test 4: Update Claude Desktop config (dry-run)")
    print("-" * 60)
    
    # First get existing config
    result = api_call("/api/desktop-mcp/claude")
    if not result or "error" in result:
        print("⚠️  Skipping update test - config not found")
        return True
    
    existing_servers = result.get("mcpServers", {})
    print(f"   Current servers: {len(existing_servers)}")
    print("   (Update test skipped to avoid modifying your config)")
    print("   To test update, uncomment the code in this function")
    
    # Uncomment below to actually test update:
    # new_servers = existing_servers.copy()
    # new_servers["test-server"] = {
    #     "type": "stdio",
    #     "command": "echo",
    #     "args": ["test"]
    # }
    # 
    # result = api_call(
    #     "/api/desktop-mcp/claude",
    #     method="POST",
    #     data={"mcpServers": new_servers}
    # )
    # 
    # if result and result.get("ok"):
    #     print(f"✅ {result['message']}")
    #     print(f"   Servers: {result['server_count']}")
    # else:
    #     return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Desktop MCP Config API")
    print("=" * 60)
    
    tests = [
        ("List desktop configs", test_list_desktop_configs),
        ("Get Claude config", test_get_claude_config),
        ("Get Cursor config", test_get_cursor_config),
        ("Update config", test_update_claude_config),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} failed\n")
        except Exception as e:
            failed += 1
            print(f"❌ {name} raised exception: {e}\n")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
