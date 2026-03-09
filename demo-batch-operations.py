#!/usr/bin/env python3
"""Demo: Batch operations for efficient orchestration.

Shows how to send multiple commands in ONE MCP call instead of multiple calls.
"""

import json
import subprocess
import sys

def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool via the amux-mcp-server."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    proc = subprocess.run(
        ["python3", "amux-mcp-server.py"],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    if proc.returncode != 0:
        print(f"Error: {proc.stderr}", file=sys.stderr)
        return {}
    
    response = json.loads(proc.stdout)
    if "error" in response:
        print(f"MCP Error: {response['error']}", file=sys.stderr)
        return {}
    
    content = response.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        return json.loads(content[0]["text"])
    
    return {}


def demo_traditional_send():
    """Traditional approach: multiple individual calls."""
    print("\n" + "="*60)
    print("TRADITIONAL APPROACH (Multiple send_message calls)")
    print("="*60 + "\n")
    
    messages = [
        {"session": "frontend-dev", "text": "Build the login form with React"},
        {"session": "backend-dev", "text": "Implement JWT authentication API"},
        {"session": "test-worker", "text": "Write integration tests for auth flow"},
    ]
    
    print(f"Sending {len(messages)} messages individually:")
    for i, msg in enumerate(messages, 1):
        print(f"  📞 Call {i}: amux_send_message(session='{msg['session']}')")
    
    print(f"\n⚠️  Total MCP calls: {len(messages)}")
    print(f"⏱️  Estimated time: ~{len(messages) * 0.5:.1f}s")


def demo_batch_send():
    """New approach: single batch call."""
    print("\n" + "="*60)
    print("NEW APPROACH (Single batch_send_messages call)")
    print("="*60 + "\n")
    
    messages = [
        {"session": "frontend-dev", "text": "Build the login form with React"},
        {"session": "backend-dev", "text": "Implement JWT authentication API"},
        {"session": "test-worker", "text": "Write integration tests for auth flow"},
    ]
    
    print(f"Sending {len(messages)} messages in ONE call:")
    print(f"  📞 Call 1: amux_batch_send_messages(messages=[...])")
    
    result = call_mcp_tool("amux_batch_send_messages", {"messages": messages})
    
    if result:
        print(f"\n✅ Result:")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Success: {result.get('success', 0)}")
        print(f"   Errors: {result.get('errors', 0)}")
        
        for r in result.get("results", []):
            status = "✅" if r.get("success") else "❌"
            session = r.get("session", "unknown")
            print(f"   {status} {session}")
    
    print(f"\n✅ Total MCP calls: 1")
    print(f"⏱️  Estimated time: ~0.5s")
    print(f"🚀 {len(messages)}× fewer calls!")


def demo_batch_operations():
    """Advanced: mixed operations in one call."""
    print("\n" + "="*60)
    print("ADVANCED: Mixed operations (batch_operations)")
    print("="*60 + "\n")
    
    operations = [
        # Start sessions
        {"type": "start", "session": "frontend-dev"},
        {"type": "start", "session": "backend-dev"},
        
        # Create tasks
        {"type": "create_task", "title": "Build login UI", "session": "frontend-dev"},
        {"type": "create_task", "title": "Build auth API", "session": "backend-dev"},
        
        # Send messages
        {"type": "send", "session": "frontend-dev", "text": "Check board and start work"},
        {"type": "send", "session": "backend-dev", "text": "Check board and start work"},
    ]
    
    print(f"Executing {len(operations)} operations in ONE call:")
    print("  Operations:")
    for op in operations:
        print(f"    • {op['type']} ({op.get('session', op.get('title', ''))})")
    
    result = call_mcp_tool("amux_batch_operations", {"operations": operations})
    
    if result:
        print(f"\n✅ Result:")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Success: {result.get('success', 0)}")
        print(f"   Errors: {result.get('errors', 0)}")
        print(f"   Message: {result.get('message', '')}")
    
    print(f"\n✅ Total MCP calls: 1 (vs {len(operations)} individual calls)")
    print(f"🚀 {len(operations)}× fewer calls!")


def demo_workflow_example():
    """Real-world workflow example."""
    print("\n" + "="*60)
    print("REAL-WORLD WORKFLOW")
    print("="*60 + "\n")
    
    print("Scenario: Orchestrator assigns tasks to 3 idle workers")
    print()
    
    # Step 1: Get view (already shown in other demo)
    print("Step 1: Get orchestrator view (1 call)")
    print("  view = amux_get_orchestrator_view()")
    print()
    
    # Step 2: Batch operations
    print("Step 2: Assign tasks and send instructions (1 call)")
    operations = [
        {"type": "claim_task", "task_id": "PROJ-1", "session": "worker1"},
        {"type": "claim_task", "task_id": "PROJ-2", "session": "worker2"},
        {"type": "claim_task", "task_id": "PROJ-3", "session": "worker3"},
        {"type": "send", "session": "worker1", "text": "Work on PROJ-1: Build login UI"},
        {"type": "send", "session": "worker2", "text": "Work on PROJ-2: API endpoint"},
        {"type": "send", "session": "worker3", "text": "Work on PROJ-3: Write tests"},
    ]
    
    print(f"  amux_batch_operations(operations=[...])  # {len(operations)} operations")
    print()
    
    print("Total orchestration overhead: 2 MCP calls")
    print()
    print("Traditional approach would need:")
    print("  • 1 call: list_sessions")
    print("  • 3 calls: peek_output")
    print("  • 1 call: list_board_tasks")
    print("  • 3 calls: claim_task")
    print("  • 3 calls: send_message")
    print("  Total: 11 calls")
    print()
    print("🚀 New approach: 2 calls (5.5× fewer!)")


def demo_comparison_table():
    """Show comparison table."""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60 + "\n")
    
    scenarios = [
        ("Send messages to 3 workers", 3, 1),
        ("Send messages to 5 workers", 5, 1),
        ("Send messages to 10 workers", 10, 1),
        ("Start 5 sessions + send messages", 10, 1),
        ("Assign 5 tasks + send 5 messages", 10, 1),
    ]
    
    print(f"{'Scenario':<40} {'Old':<10} {'New':<10} {'Speedup'}")
    print("-" * 60)
    
    for scenario, old_calls, new_calls in scenarios:
        speedup = f"{old_calls}×"
        print(f"{scenario:<40} {old_calls:<10} {new_calls:<10} {speedup}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AMUX Batch Operations - Demo")
    print("="*60)
    
    demo_traditional_send()
    demo_batch_send()
    demo_batch_operations()
    demo_workflow_example()
    demo_comparison_table()
    
    print("\n" + "="*60)
    print("💡 Key Takeaways:")
    print("="*60)
    print("  • Use amux_batch_send_messages for sending to multiple sessions")
    print("  • Use amux_batch_operations for mixed operation types")
    print("  • Combine with amux_get_orchestrator_view for full efficiency")
    print("  • Reduces orchestration overhead by 5-10×")
    print("")
