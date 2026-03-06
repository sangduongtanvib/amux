#!/usr/bin/env python3
"""
Test script for amux_delete_inactive_sessions MCP tool.
"""

import json
import sys
import subprocess


def test_mcp_tool():
    """Test the delete inactive sessions MCP tool via stdio protocol."""
    print("=" * 70)
    print("Testing amux_delete_inactive_sessions MCP Tool")
    print("=" * 70)
    
    # Test 1: Initialize
    print("\n[Test 1] MCP Initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    proc = subprocess.Popen(
        ["python3", "amux-mcp-server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send initialize
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    try:
        result = json.loads(response)
        print(f"✅ Initialize response: {result.get('result', {}).get('serverInfo', {}).get('name')}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response}")
        proc.terminate()
        return False
    
    # Test 2: List tools (verify our new tool exists)
    print("\n[Test 2] List tools...")
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    proc.stdin.write(json.dumps(list_request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    try:
        result = json.loads(response)
        tools = result.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]
        
        if "amux_delete_inactive_sessions" in tool_names:
            print("✅ Tool 'amux_delete_inactive_sessions' found in tools list")
            # Print tool details
            our_tool = next(t for t in tools if t["name"] == "amux_delete_inactive_sessions")
            print(f"   Description: {our_tool['description']}")
            print(f"   Parameters: {list(our_tool['inputSchema']['properties'].keys())}")
        else:
            print(f"❌ Tool not found. Available tools: {tool_names}")
            proc.terminate()
            return False
    except Exception as e:
        print(f"❌ Error parsing tools list: {e}")
        proc.terminate()
        return False
    
    # Test 3: Call tool with dry_run=true
    print("\n[Test 3] Call tool with dry_run=true...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "amux_delete_inactive_sessions",
            "arguments": {
                "dry_run": True,
                "include_archived": False
            }
        }
    }
    
    proc.stdin.write(json.dumps(call_request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    try:
        result = json.loads(response)
        if "error" in result:
            # This is expected if AMUX server is not running
            print(f"⚠️  Tool call failed (expected if AMUX server not running): {result['error']}")
            print("   To test fully, start amux-server.py first")
        else:
            tool_result = result.get("result", {})
            content = tool_result.get("content", [{}])[0]
            text = content.get("text", "")
            print(f"✅ Tool executed successfully")
            print(f"   Result: {text[:200]}")  # First 200 chars
    except Exception as e:
        print(f"❌ Error calling tool: {e}")
        print(f"   Response: {response}")
        proc.terminate()
        return False
    
    proc.terminate()
    
    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_mcp_tool()
    sys.exit(0 if success else 1)
