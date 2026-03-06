#!/usr/bin/env python3
"""Manual test: Verify MCP config isolation per session."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

AMUX_HOME = Path.home() / ".amux"
DB_PATH = AMUX_HOME / "amux.db"

print("=" * 70)
print("🧪 Manual Test: MCP Config Isolation")
print("=" * 70)

# Step 1: Check database has MCP configs
print("\n1️⃣  Checking MCP configs in database...")
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

mcp_configs = cursor.execute(
    "SELECT id, name, type FROM mcp_configs WHERE deleted IS NULL AND enabled = 1"
).fetchall()

if not mcp_configs:
    print("❌ No MCP configs found. Please import mcp.json via dashboard first.")
    sys.exit(1)

print(f"✅ Found {len(mcp_configs)} MCP configs:")
for cfg in mcp_configs:
    print(f"   - {cfg['name']} ({cfg['type']})")

# Step 2: Create a test session programmatically
print("\n2️⃣  Creating test session in database...")
test_session = "mcp-test-session"
test_dir = "/tmp/amux-mcp-test"

# Create test directory
Path(test_dir).mkdir(parents=True, exist_ok=True)
(Path(test_dir) / "test.txt").write_text("Test project for MCP isolation\n")

# Create session config file
session_file = AMUX_HOME / "sessions" / f"{test_session}.env"
session_file.parent.mkdir(parents=True, exist_ok=True)
session_file.write_text(f"""CC_DIR={test_dir}
CC_TOOL=claude_code
CC_FLAGS=
""")

print(f"✅ Created session: {test_session}")
print(f"   Work dir: {test_dir}")

# Step 3: Link MCP servers to session
print("\n3️⃣  Linking MCP servers to session...")
mcp_ids = [cfg['id'] for cfg in mcp_configs[:3]]  # Link first 3 MCPs

# Delete existing links
cursor.execute("DELETE FROM session_mcp_links WHERE session = ?", (test_session,))

# Add new links
import time
now = int(time.time())
for idx, mcp_id in enumerate(mcp_ids):
    cursor.execute(
        "INSERT INTO session_mcp_links (session, mcp_id, position, created) VALUES (?, ?, ?, ?)",
        (test_session, mcp_id, idx, now)
    )

conn.commit()
print(f"✅ Linked {len(mcp_ids)} MCP servers")

# Step 4: Check what MCP servers are linked
linked = cursor.execute(
    """SELECT m.name FROM session_mcp_links sml
       JOIN mcp_configs m ON m.id = sml.mcp_id
       WHERE sml.session = ?
       ORDER BY sml.position""",
    (test_session,)
).fetchall()

print(f"   Linked MCPs: {', '.join([r['name'] for r in linked])}")

conn.close()

# Step 5: Instructions for manual verification
print("\n" + "=" * 70)
print("📋 MANUAL TEST STEPS:")
print("=" * 70)
print(f"""
1. Start the test session:
   \033[1mamux start {test_session}\033[0m
   (or via dashboard at https://localhost:8822)

2. Attach to the session:
   \033[1mamux attach {test_session}\033[0m
   
3. In the Claude Code CLI, run:
   \033[1mmcp list\033[0m
   
4. Verify that ONLY these MCP servers appear:
   {', '.join([r['name'] for r in linked])}
   
5. Check mcp.json was generated:
   \033[1mcat {test_dir}/mcp.json\033[0m

6. Expected: Session uses isolated MCP config, NOT global ~/.claude/

7. To cleanup:
   \033[1mamux stop {test_session}\033[0m
   \033[1mrm -rf {test_dir}\033[0m
   \033[1mrm {session_file}\033[0m
""")

print("=" * 70)
print("🚀 Test setup complete. Follow manual steps above to verify.")
print("=" * 70)
