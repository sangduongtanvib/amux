# AMUX Orchestrator View Tool

## Problem

When orchestrating multiple AI agent sessions, the orchestrator needs to:
- Check status of all sessions
- Read terminal output from each session
- Monitor board tasks
- Detect which sessions need approval

**Traditional approach requires N+2 MCP calls:**
```
1. amux_list_sessions (get all sessions)
2. amux_peek_output for session1
3. amux_peek_output for session2
...
N+1. amux_peek_output for sessionN
N+2. amux_list_board_tasks
```

This is slow, inefficient, and creates race conditions (data from different moments).

## Solution: `amux_get_orchestrator_view`

**Single MCP call** that returns:
- ✅ All sessions with full status
- ✅ Terminal output preview from each session
- ✅ All board tasks (with optional filtering)
- ✅ Summary statistics
- ✅ List of sessions needing attention

## Usage

### Basic Usage (Monitor Everything)

```json
{
  "tool": "amux_get_orchestrator_view",
  "arguments": {}
}
```

Returns:
```json
{
  "summary": {
    "total_sessions": 3,
    "running_sessions": 3,
    "needs_attention": 1,
    "idle_sessions": 1,
    "working_sessions": 1,
    "total_tasks": 5,
    "todo_tasks": 2,
    "doing_tasks": 2,
    "done_tasks": 1
  },
  "needs_attention": ["frontend-dev"],
  "sessions": [
    {
      "name": "frontend-dev",
      "status": "needs_input",
      "running": true,
      "tool": "cursor",
      "dir": "/path/to/project",
      "preview": "? Press Y to approve file changes",
      "output": "... (last 30 lines of terminal) ..."
    },
    {
      "name": "backend-dev",
      "status": "working",
      "running": true,
      "tool": "claude_code",
      "output": "Implementing API endpoint..."
    },
    ...
  ],
  "tasks": [
    {
      "id": "PROJ-1",
      "title": "Build login UI",
      "status": "doing",
      "session": "frontend-dev"
    },
    ...
  ]
}
```

### Monitor Specific Sessions

```json
{
  "tool": "amux_get_orchestrator_view",
  "arguments": {
    "sessions": ["frontend-dev", "backend-dev"],
    "output_lines": 50
  }
}
```

### Filter Tasks by Status

```json
{
  "tool": "amux_get_orchestrator_view",
  "arguments": {
    "include_tasks": true,
    "task_status": "doing"
  }
}
```

### Lightweight Mode (No Output)

```json
{
  "tool": "amux_get_orchestrator_view",
  "arguments": {
    "include_output": false,
    "output_lines": 0
  }
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sessions` | array | `[]` | List of session names to monitor. Empty = all sessions |
| `include_output` | boolean | `true` | Include terminal output from each session |
| `output_lines` | integer | `30` | Number of output lines per session |
| `include_tasks` | boolean | `true` | Include board tasks |
| `task_status` | string | `""` | Filter tasks by status (empty = all) |

## Orchestrator Workflow Example

```python
# 1. Get complete view in ONE call
view = call_tool("amux_get_orchestrator_view", {})

# 2. Check summary
if view["summary"]["needs_attention"] > 0:
    print(f"⚠️  {view['summary']['needs_attention']} sessions need approval")

# 3. Handle sessions needing attention
for session_name in view["needs_attention"]:
    session = next(s for s in view["sessions"] if s["name"] == session_name)
    print(f"Session {session_name}: {session['preview']}")
    
    # Decide action based on preview
    if "approve" in session["preview"].lower():
        # Send approval
        call_tool("amux_send_message", {
            "name": session_name,
            "text": "y"
        })

# 4. Check task progress
doing_tasks = [t for t in view["tasks"] if t["status"] == "doing"]
print(f"In progress: {len(doing_tasks)} tasks")

# 5. Assign new tasks to idle workers
idle_workers = [s["name"] for s in view["sessions"] if s["status"] == "idle"]
todo_tasks = [t for t in view["tasks"] if t["status"] == "todo"]

for worker, task in zip(idle_workers, todo_tasks):
    call_tool("amux_claim_task", {
        "task_id": task["id"],
        "session": worker
    })
    call_tool("amux_send_message", {
        "name": worker,
        "text": f"Work on task {task['id']}: {task['title']}"
    })
```

## Performance Comparison

### Scenario: Monitor 5 worker sessions + board tasks

**Traditional approach:**
- `amux_list_sessions`: 500ms
- `amux_peek_output` × 5: 500ms × 5 = 2500ms
- `amux_list_board_tasks`: 500ms
- **Total: ~3.5 seconds, 7 MCP calls**

**New approach:**
- `amux_get_orchestrator_view`: 500ms
- **Total: ~0.5 seconds, 1 MCP call**

**🚀 7× faster, 7× fewer calls**

## Benefits

1. **Speed**: Single round-trip instead of multiple
2. **Consistency**: All data from same snapshot
3. **Simplicity**: One call instead of complex logic
4. **Reliability**: Less chance of failure (fewer network calls)
5. **Attention Detection**: Automatic flagging of sessions needing approval
6. **Flexible Filtering**: Monitor specific workers or task states

## Migration Guide

### Before (Multiple Calls)

```python
# Get all sessions
sessions = call_tool("amux_list_sessions", {})

# Peek each session
for session in sessions["sessions"]:
    output = call_tool("amux_peek_output", {
        "name": session["name"],
        "lines": 30
    })
    session["output"] = output["output"]

# Get tasks
tasks = call_tool("amux_list_board_tasks", {})
```

### After (Single Call)

```python
# Get everything
view = call_tool("amux_get_orchestrator_view", {
    "output_lines": 30
})

sessions = view["sessions"]  # Already includes output
tasks = view["tasks"]
summary = view["summary"]
needs_attention = view["needs_attention"]
```

## Demo

Run the included demo:

```bash
python3 demo-orchestrator-view.py
```

This shows:
- Traditional approach (conceptual)
- New approach (actual call)
- Filtered monitoring

## Integration with Cursor/Claude

When using AMUX orchestrator in Cursor or Claude Code:

```
User: "Monitor all my worker agents"

Agent: [calls amux_get_orchestrator_view with no filters]

Agent: "Here's the status:
- 3 sessions running
- 1 session needs your approval (frontend-dev)
- 2 tasks in progress
- 1 task completed

Session 'frontend-dev' is waiting for approval to modify index.tsx.
Would you like me to approve it?"
```

## API Endpoint (Direct HTTP)

If you prefer direct HTTP instead of MCP:

```bash
# This would require adding a new endpoint to amux-server.py
curl https://localhost:8822/api/orchestrator-view \
  -H "Content-Type: application/json" \
  -d '{"sessions": ["worker1"], "output_lines": 20}'
```

(Note: This endpoint doesn't exist yet - the MCP tool is the current interface)

## Future Enhancements

Potential additions to this tool:

- [ ] Real-time streaming mode (SSE-based)
- [ ] Health metrics (CPU, memory, response time per session)
- [ ] Task dependency graph
- [ ] Auto-suggestions for next actions
- [ ] Performance history (last 10 status checks)
- [ ] Alert rules (notify if session stuck > 5 min)

## Related Tools

- `amux_list_sessions` - List sessions only (lightweight)
- `amux_get_status` - Detailed status for one session
- `amux_peek_output` - Get terminal output for one session
- `amux_list_board_tasks` - List tasks only

Use `amux_get_orchestrator_view` when you need **comprehensive monitoring**.
Use individual tools when you need **specific data** for one session/task.
