#!/usr/bin/env python3
"""Demo: Using amux_get_orchestrator_view for efficient monitoring.

This demonstrates how an orchestrator agent can monitor all workers
in a single MCP tool call instead of multiple API calls.
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
    
    # Parse the text content from MCP response
    content = response.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        return json.loads(content[0]["text"])
    
    return {}


def demo_traditional_approach():
    """Traditional approach: multiple tool calls."""
    print("\n" + "="*60)
    print("TRADITIONAL APPROACH (Multiple Tool Calls)")
    print("="*60 + "\n")
    
    # Call 1: List sessions
    print("📞 Call 1: amux_list_sessions")
    sessions_result = call_mcp_tool("amux_list_sessions", {})
    sessions = sessions_result.get("sessions", [])
    print(f"   Found {len(sessions)} sessions")
    
    # Call 2-N: Peek output for each session
    for session in sessions:
        name = session["name"]
        print(f"📞 Call {sessions.index(session) + 2}: amux_peek_output for '{name}'")
    
    # Call N+1: List board tasks
    print(f"📞 Call {len(sessions) + 2}: amux_list_board_tasks")
    
    print(f"\n⚠️  Total MCP calls: {len(sessions) + 2}")
    print(f"⏱️  Estimated time: ~{(len(sessions) + 2) * 0.5:.1f}s (if each call takes 500ms)")


def demo_orchestrator_view():
    """New approach: single tool call."""
    print("\n" + "="*60)
    print("NEW APPROACH (Single Tool Call)")
    print("="*60 + "\n")
    
    print("📞 Call 1: amux_get_orchestrator_view")
    result = call_mcp_tool("amux_get_orchestrator_view", {
        "include_output": True,
        "output_lines": 30,
        "include_tasks": True,
    })
    
    if not result:
        print("⚠️  No data returned (server might be down)")
        return
    
    # Display summary
    summary = result.get("summary", {})
    print("\n📊 Summary:")
    print(f"   Total sessions: {summary.get('total_sessions', 0)}")
    print(f"   Running: {summary.get('running_sessions', 0)}")
    print(f"   Needs attention: {summary.get('needs_attention', 0)}")
    print(f"   Working: {summary.get('working_sessions', 0)}")
    print(f"   Idle: {summary.get('idle_sessions', 0)}")
    print(f"   Total tasks: {summary.get('total_tasks', 0)}")
    print(f"   Todo: {summary.get('todo_tasks', 0)}")
    print(f"   Doing: {summary.get('doing_tasks', 0)}")
    print(f"   Done: {summary.get('done_tasks', 0)}")
    
    # Display sessions needing attention
    needs_attention = result.get("needs_attention", [])
    if needs_attention:
        print(f"\n⚠️  Sessions needing attention:")
        for name in needs_attention:
            print(f"   • {name}")
    
    # Display all sessions
    sessions = result.get("sessions", [])
    if sessions:
        print(f"\n📋 Sessions ({len(sessions)}):")
        for s in sessions:
            status_emoji = {
                "idle": "💤",
                "working": "⚙️",
                "needs_input": "❓",
                "error": "❌",
            }.get(s["status"], "•")
            print(f"   {status_emoji} {s['name']:<20} [{s['status']:<15}] {s['tool']}")
            if s.get("output") and len(s["output"]) > 0:
                preview = s["output"].split("\n")[-3:]  # Last 3 lines
                print(f"      Output: {preview[-1][:60]}..." if preview else "")
    
    # Display tasks
    tasks = result.get("tasks", [])
    if tasks:
        print(f"\n📌 Tasks ({len(tasks)}):")
        for t in tasks:
            session_label = f"[{t['session']}]" if t['session'] else "[unassigned]"
            print(f"   • {t['id']:<10} {t['title']:<40} [{t['status']:<10}] {session_label}")
    
    print(f"\n✅ Total MCP calls: 1")
    print(f"⏱️  Estimated time: ~0.5s")


def demo_filtered_view():
    """Demo: Monitor specific sessions only."""
    print("\n" + "="*60)
    print("FILTERED VIEW (Specific Sessions)")
    print("="*60 + "\n")
    
    # Monitor only frontend and backend workers
    print("📞 Monitoring specific workers: ['frontend-dev', 'backend-dev']")
    result = call_mcp_tool("amux_get_orchestrator_view", {
        "sessions": ["frontend-dev", "backend-dev"],
        "include_output": True,
        "output_lines": 20,
        "include_tasks": True,
        "task_status": "doing"  # Only tasks in progress
    })
    
    if not result:
        print("⚠️  Sessions not found or server down")
        return
    
    summary = result.get("summary", {})
    print(f"\n📊 Filtered Summary:")
    print(f"   Monitored sessions: {summary.get('total_sessions', 0)}")
    print(f"   Tasks in 'doing': {summary.get('doing_tasks', 0)}")
    
    print(f"\n✅ Single MCP call with filters")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AMUX Orchestrator View - Demo Comparison")
    print("="*60)
    
    # Show traditional approach (conceptual)
    demo_traditional_approach()
    
    # Show new approach (actual call)
    demo_orchestrator_view()
    
    # Show filtered view
    demo_filtered_view()
    
    print("\n" + "="*60)
    print("💡 Benefits of amux_get_orchestrator_view:")
    print("="*60)
    print("  • Reduces MCP calls from N+2 to 1 (where N = number of sessions)")
    print("  • Faster response time (no round-trip delays)")
    print("  • Consistent snapshot (all data from same moment)")
    print("  • Lower API overhead and network usage")
    print("  • Easier error handling (single call to wrap)")
    print("  • Built-in summary statistics")
    print("  • Automatic detection of sessions needing attention")
    print("")
