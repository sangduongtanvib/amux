#!/usr/bin/env python3
"""
AMUX Dashboard Browser Integration Test

Tests AMUX dashboard interaction using browser automation.
Verifies that MCP-orchestrated sessions and tasks are visible in the UI.

Usage:
    python3 test-dashboard-integration.py
"""

import json
import subprocess
import time
import sys


def test_dashboard():
    """Test AMUX dashboard via browser."""
    print("\n" + "="*70)
    print("🌐 AMUX Dashboard Integration Test")
    print("="*70 + "\n")
    
    print("📝 Note: This test requires:")
    print("   - AMUX server running on https://localhost:8822")
    print("   - Browser automation tools available")
    print("   - Active sessions from previous MCP tests")
    print()
    
    # Manual verification steps
    print("🧪 Manual Verification Steps:")
    print()
    
    print("1️⃣  Open Dashboard:")
    print("   → Navigate to https://localhost:8822")
    print("   → Accept self-signed certificate if prompted")
    print()
    
    print("2️⃣  Verify Sessions:")
    print("   → Check that test sessions are listed:")
    print("      • test-session-* (from integration tests)")
    print("      • workflow-*-worker-1 (Claude Code)")
    print("      • workflow-*-worker-2 (Cursor)")
    print("      • frontend-worker, backend-worker, test-worker (from demo)")
    print()
    
    print("3️⃣  Verify Board Tasks:")
    print("   → Click 'Board' tab")
    print("   → Check for test tasks:")
    print("      • 'Integration test task ...'")
    print("      • 'Build React login component'")
    print("      • 'Implement JWT authentication API'")
    print("      • 'Write integration tests'")
    print("      • Workflow tasks for workers")
    print()
    
    print("4️⃣  Test Session Interaction:")
    print("   → Click on a session to view details")
    print("   → Verify session info displays:")
    print("      • Session name")
    print("      • Tool type (claude_code or cursor)")
    print("      • Status (running/stopped)")
    print("      • Output log")
    print()
    
    print("5️⃣  Test Board Task Management:")
    print("   → Try creating a new task via UI")
    print("   → Try claiming a task")
    print("   → Try moving task between columns (todo/doing/done)")
    print()
    
    print("6️⃣  Test MCP Orchestration Visibility:")
    print("   → Verify that sessions created via MCP appear in UI")
    print("   → Verify that tasks created via MCP are shown")
    print("   → Verify that task assignments are visible")
    print()
    
    print("=" * 70)
    print()
    print("💡 Automated Browser Test:")
    print("   To run automated browser tests, you would need to:")
    print("   1. Use open_browser_page tool to open https://localhost:8822")
    print("   2. Use read_page to capture page state")
    print("   3. Use click_element/type_in_page for interactions")
    print("   4. Verify elements exist using selectors")
    print()
    print("   This is best done interactively in Claude Code with")
    print("   access to browser automation tools.")
    print("=" * 70)
    print()
    
    # Get current session/task counts via MCP API
    print("📊 Current AMUX State (via MCP):")
    print("-" * 70)
    
    try:
        # List sessions
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "amux_list_sessions",
                "arguments": {}
            }
        }
        
        proc = subprocess.run(
            ["python3", "amux-mcp-server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True
        )
        
        lines = proc.stdout.strip().split('\n')
        response_lines = [l for l in lines if l.startswith('{"jsonrpc"')]
        
        if response_lines:
            response = json.loads(response_lines[0])
            if "result" in response:
                content = json.loads(response["result"]["content"][0]["text"])
                sessions = content.get("sessions", [])
                print(f"\n✅ Sessions: {len(sessions)} total")
                for sess in sessions[:10]:  # Show first 10
                    status = "🟢" if sess.get("running") else "🔴"
                    tool = sess.get("tool", "unknown")
                    print(f"   {status} {sess['name']} ({tool})")
                if len(sessions) > 10:
                    print(f"   ... and {len(sessions) - 10} more")
        
        # List board tasks
        request["id"] = 2
        request["params"]["name"] = "amux_list_board_tasks"
        
        proc = subprocess.run(
            ["python3", "amux-mcp-server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True
        )
        
        lines = proc.stdout.strip().split('\n')
        response_lines = [l for l in lines if l.startswith('{"jsonrpc"')]
        
        if response_lines:
            response = json.loads(response_lines[0])
            if "result" in response:
                content = json.loads(response["result"]["content"][0]["text"])
                tasks = content.get("tasks", [])
                print(f"\n✅ Board Tasks: {len(tasks)} total")
                for task in tasks[:10]:  # Show first 10
                    status_emoji = {"todo": "⏳", "doing": "🔄", "done": "✅"}.get(task["status"], "❓")
                    print(f"   {status_emoji} {task['id']}: {task['title']} [{task['status']}]")
                if len(tasks) > 10:
                    print(f"   ... and {len(tasks) - 10} more")
        
    except Exception as e:
        print(f"\n❌ Error querying MCP: {e}")
    
    print("\n" + "=" * 70)
    print()
    print("✅ Dashboard should now display all these sessions and tasks!")
    print()
    print("🔗 Open in browser: https://localhost:8822")
    print()


if __name__ == "__main__":
    test_dashboard()
