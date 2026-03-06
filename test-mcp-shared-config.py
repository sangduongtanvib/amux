#!/usr/bin/env python3
"""Test script for shared MCP configuration feature in Amux."""

import json
import sqlite3
import subprocess
import sys
import time
import urllib.request
import urllib.error
import ssl
from pathlib import Path

# Configuration
AMUX_API = "https://localhost:8822"
AMUX_HOME = Path.home() / ".amux"
DB_PATH = AMUX_HOME / "amux.db"
TEST_SESSION_NAME = "test-mcp-session"
TEST_DIR = "/tmp/amux-mcp-test"

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


def check_server_running():
    """Check if Amux server is running."""
    print("🔍 Checking if Amux server is running...")
    result = api_call("/api/sessions")
    if result is not None:
        print("✅ Server is running")
        return True
    print("❌ Server is not running. Please start with: amux serve")
    return False


def check_mcp_in_database():
    """Check MCP configs in database."""
    print("\n📊 Checking MCP configs in database...")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    rows = cursor.execute(
        "SELECT name, type, enabled FROM mcp_configs WHERE deleted IS NULL"
    ).fetchall()
    
    if not rows:
        print("❌ No MCP configs found in database")
        return False
    
    print(f"✅ Found {len(rows)} MCP configs:")
    for row in rows:
        print(f"   - {row['name']} ({row['type']}) - {'enabled' if row['enabled'] else 'disabled'}")
    
    conn.close()
    return True


def create_test_session():
    """Create a test session."""
    print(f"\n🏗️  Creating test session: {TEST_SESSION_NAME}")
    
    # Create test directory
    test_path = Path(TEST_DIR)
    test_path.mkdir(parents=True, exist_ok=True)
    (test_path / "README.md").write_text("# MCP Test Project\n")
    
    # Create session using API
    result = api_call(
        "/api/sessions",
        method="POST",
        data={
            "name": TEST_SESSION_NAME,
            "dir": TEST_DIR,
            "tool": "claude_code",
            "desc": "Test MCP shared config"
        }
    )
    
    if not result or not result.get("ok"):
        print(f"❌ Failed to create session: {result}")
        return False
    
    print(f"✅ Session created: {TEST_SESSION_NAME}")
    return True


def link_mcp_to_session():
    """Link all MCP servers to test session."""
    print(f"\n🔗 Linking MCP servers to {TEST_SESSION_NAME}...")
    
    # Get all MCP IDs from database
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    rows = cursor.execute(
        "SELECT id FROM mcp_configs WHERE deleted IS NULL AND enabled = 1"
    ).fetchall()
    
    mcp_ids = [row['id'] for row in rows]
    conn.close()
    
    if not mcp_ids:
        print("❌ No enabled MCP configs to link")
        return False
    
    # Link via API
    result = api_call(
        f"/api/sessions/{TEST_SESSION_NAME}/mcp",
        method="POST",
        data={"mcp_ids": mcp_ids}
    )
    
    if result and result.get("ok"):
        print(f"✅ Linked {result.get('count', 0)} MCP servers")
        return True
    
    print("❌ Failed to link MCP servers")
    return False


def verify_mcp_json_generated():
    """Verify that mcp.json was generated in work directory."""
    print(f"\n🔍 Verifying mcp.json generation...")
    
    # Get session work directory
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check session_mcp_links
    links = cursor.execute(
        """SELECT m.name, m.type 
           FROM session_mcp_links sml
           JOIN mcp_configs m ON m.id = sml.mcp_id
           WHERE sml.session = ?
           ORDER BY sml.position""",
        (TEST_SESSION_NAME,)
    ).fetchall()
    
    if not links:
        print("❌ No MCP links found for session")
        conn.close()
        return False
    
    print(f"✅ Found {len(links)} MCP links in database:")
    for link in links:
        print(f"   - {link['name']} ({link['type']})")
    
    conn.close()
    
    # Check if mcp.json exists in work directory
    mcp_file = Path(TEST_DIR) / "mcp.json"
    
    if not mcp_file.exists():
        print(f"❌ mcp.json not found at: {mcp_file}")
        print("   Note: mcp.json is generated when session starts")
        return False
    
    # Read and validate mcp.json
    try:
        mcp_data = json.loads(mcp_file.read_text())
        servers = mcp_data.get("mcpServers", {})
        
        print(f"\n✅ mcp.json generated successfully at: {mcp_file}")
        print(f"   Contains {len(servers)} MCP servers:")
        for name, config in servers.items():
            print(f"   - {name} ({config.get('type', 'unknown')})")
        
        return True
    except Exception as e:
        print(f"❌ Failed to read mcp.json: {e}")
        return False


def start_test_session():
    """Start the test session to trigger mcp.json generation."""
    print(f"\n🚀 Starting test session to trigger mcp.json generation...")
    
    result = api_call(
        f"/api/sessions/{TEST_SESSION_NAME}/start",
        method="POST"
    )
    
    if not result or not result.get("ok"):
        print(f"❌ Failed to start session: {result}")
        return False
    
    print(f"✅ Session started")
    time.sleep(2)  # Wait for initialization
    return True


def cleanup():
    """Clean up test session."""
    print(f"\n🧹 Cleaning up test session...")
    
    # Stop session
    subprocess.run(
        ["amux", " via API
    api_call(f"/api/sessions/{TEST_SESSION_NAME}/stop", method="POST"# Delete from database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session_mcp_links WHERE session = ?", (TEST_SESSION_NAME,))
    conn.commit()
    conn.close()
    
    # Delete session file
    session_file = AMUX_HOME / "sessions" / f"{TEST_SESSION_NAME}.env"
    if session_file.exists():
        session_file.unlink()
    
    print("✅ Cleanup completed")


def main():
    """Run the test."""
    print("=" * 60)
    print("🧪 Testing Amux Shared MCP Configuration Feature")
    print("=" * 60)
    
    # Step 1: Check server
    if not check_server_running():
        sys.exit(1)
    
    # Step 2: Check MCP configs in DB
    if not check_mcp_in_database():
        print("\n💡 Importing MCP configs from mcp.json...")
        # Note: This would normally be done via dashboard import
        print("   Please import mcp.json via dashboard first")
        sys.exit(1)
    
    # Step 3: Create test session
    if not create_test_session():
        sys.exit(1)
    
    # Step 4: Link MCP servers
    if not link_mcp_to_session():
        cleanup()
        sys.exit(1)
    
    # Step 5: Start session to generate mcp.json
    if not start_test_session():
        cleanup()
        sys.exit(1)
    
    # Step 6: Verify mcp.json
    success = verify_mcp_json_generated()
    
    # Cleanup
    cleanup()
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: MCP shared config feature works!")
        print("\nKey features verified:")
        print("  1. MCP configs stored in central database")
        print("  2. MCP servers can be linked to sessions")
        print("  3. mcp.json auto-generated per session on start")
    else:
        print("❌ TEST FAILED")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
