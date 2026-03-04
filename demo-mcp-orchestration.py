#!/usr/bin/env python3
"""
AMUX MCP Orchestration Demo

This script demonstrates how an orchestrator agent can use the AMUX MCP server
to manage multiple AI coding sessions in parallel.

Usage:
    python3 demo-mcp-orchestration.py
"""

import json
import subprocess
import time


def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call an AMUX MCP tool via the server."""
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    # Call the MCP server
    proc = subprocess.run(
        ["python3", "amux-mcp-server.py"],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    # Parse response
    lines = proc.stdout.strip().split('\n')
    response_line = [l for l in lines if l.startswith('{"jsonrpc"')]
    if response_line:
        response = json.loads(response_line[0])
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            return json.loads(content)
    
    return {"error": "Failed to parse response"}


def demo():
    """Demo orchestration workflow."""
    print("=" * 60)
    print("AMUX MCP Orchestration Demo")
    print("=" * 60)
    print()
    
    # Step 1: List existing sessions
    print("📋 Step 1: Listing existing sessions...")
    result = call_mcp_tool("amux_list_sessions", {})
    print(f"   Found {result['count']} sessions")
    print()
    
    # Step 2: Create worker sessions
    print("🔧 Step 2: Creating worker sessions...")
    workers = [
        {
            "name": "frontend-worker",
            "dir": "~/projects/demo",
            "tool": "cursor",
            "desc": "Frontend React development"
        },
        {
            "name": "backend-worker",
            "dir": "~/projects/demo",
            "tool": "claude_code",
            "desc": "Backend API development"
        },
        {
            "name": "test-worker",
            "dir": "~/projects/demo",
            "tool": "claude_code",
            "desc": "Test automation"
        }
    ]
    
    for worker in workers:
        try:
            result = call_mcp_tool("amux_create_session", worker)
            print(f"   ✅ Created: {worker['name']} ({worker['tool']})")
        except Exception as e:
            print(f"   ⚠️  Skipped {worker['name']}: {str(e)}")
    print()
    
    # Step 3: Create board tasks
    print("📝 Step 3: Creating board tasks...")
    tasks = [
        {
            "title": "Build React login component",
            "desc": "Create responsive login form with validation",
            "session": "frontend-worker",
            "status": "todo"
        },
        {
            "title": "Implement JWT authentication API",
            "desc": "POST /api/auth/login with token generation",
            "session": "backend-worker",
            "status": "todo"
        },
        {
            "title": "Write integration tests",
            "desc": "Test login flow end-to-end",
            "session": "test-worker",
            "status": "todo"
        }
    ]
    
    created_tasks = []
    for task in tasks:
        result = call_mcp_tool("amux_create_board_task", task)
        task_id = result.get("task_id", "")
        created_tasks.append(task_id)
        print(f"   ✅ {task_id}: {task['title']}")
    print()
    
    # Step 4: Start worker sessions
    print("🚀 Step 4: Starting worker sessions...")
    for worker in workers:
        try:
            result = call_mcp_tool("amux_start_session", {"name": worker["name"]})
            print(f"   ✅ Started: {worker['name']}")
        except Exception as e:
            print(f"   ⚠️  Failed to start {worker['name']}: {str(e)}")
    print()
    
    # Step 5: Send initial prompts
    print("💬 Step 5: Sending initial prompts to workers...")
    prompts = [
        {
            "name": "frontend-worker",
            "text": "Check the board for your assigned task (login component) and start working on it."
        },
        {
            "name": "backend-worker",
            "text": "Check the board for your assigned task (JWT auth API) and implement it."
        },
        {
            "name": "test-worker",
            "text": "Wait for the other workers to complete their tasks, then write integration tests."
        }
    ]
    
    for prompt in prompts:
        try:
            result = call_mcp_tool("amux_send_message", prompt)
            print(f"   ✅ Sent to {prompt['name']}")
        except Exception as e:
            print(f"   ⚠️  Failed {prompt['name']}: {str(e)}")
    print()
    
    # Step 6: Get status
    print("📊 Step 6: Checking worker status...")
    time.sleep(2)  # Give workers time to start
    
    for worker in workers:
        try:
            result = call_mcp_tool("amux_get_status", {"name": worker["name"]})
            status = result.get("status", "unknown")
            running = result.get("running", False)
            print(f"   {worker['name']}: {status} {'🟢' if running else '🔴'}")
        except Exception as e:
            print(f"   {worker['name']}: error")
    print()
    
    # Step 7: List board tasks
    print("📋 Step 7: Current board tasks...")
    result = call_mcp_tool("amux_list_board_tasks", {})
    for task in result.get("tasks", []):
        status_emoji = {"todo": "⏳", "doing": "🔄", "done": "✅"}.get(task["status"], "❓")
        print(f"   {status_emoji} {task['id']}: {task['title']} [{task['status']}]")
    print()
    
    print("=" * 60)
    print("Demo completed!")
    print()
    print("Next steps:")
    print("1. Open https://localhost:8822 to view the dashboard")
    print("2. Monitor worker progress in real-time")
    print("3. Workers will claim and update tasks as they complete")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
