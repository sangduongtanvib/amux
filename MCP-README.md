# AMUX MCP Server

Model Context Protocol server for AMUX orchestration. Allows AI agents to control and monitor AMUX sessions through MCP tools.

## Setup

### 1. Install in Claude Code / Cursor

Add to your `~/.claude/mcp.json` or project's `mcp.json`:

```json
{
  "mcpServers": {
    "amux-orchestrator": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/amux/amux-mcp-server.py"]
    }
  }
}
```

### 2. Ensure AMUX server is running

```bash
cd /path/to/amux
python3 amux-server.py
# Server runs on https://localhost:8822
```

### 3. Use in AI agent sessions

The MCP tools will be automatically available in your Claude Code or Cursor sessions.

## Available Tools

### Orchestrator Monitoring (Recommended)

#### `amux_get_orchestrator_view` ⭐ NEW
**Get comprehensive view of all sessions and tasks in ONE call.**

This is the primary tool for orchestrator agents. Instead of making multiple calls to list sessions, peek output, and list tasks, this single tool returns everything at once.

**Parameters:**
```json
{
  "sessions": ["worker1", "worker2"],  // Optional: specific sessions (empty = all)
  "include_output": true,              // Optional: include terminal output (default: true)
  "output_lines": 30,                  // Optional: lines per session (default: 30)
  "include_tasks": true,               // Optional: include board tasks (default: true)
  "task_status": "doing"               // Optional: filter tasks by status
}
```

**Returns:**
```json
{
  "summary": {
    "total_sessions": 3,
    "running_sessions": 2,
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
      "output": "... terminal output ..."
    }
  ],
  "tasks": [
    {
      "id": "PROJ-1",
      "title": "Build login UI",
      "status": "doing",
      "session": "frontend-dev"
    }
  ]
}
```

**Use cases:**
- Monitor all worker agents in one call
- Check which sessions need approval
- Get task progress without multiple API calls
- Efficient polling for orchestrator dashboards

**Performance:** 7× faster than traditional approach when monitoring 5+ sessions.

See [ORCHESTRATOR-VIEW.md](ORCHESTRATOR-VIEW.md) for detailed guide.

---

### Batch Operations (Recommended)

#### `amux_batch_send_messages` ⭐ NEW
**Send messages to multiple sessions in ONE call.**

Instead of calling `amux_send_message` multiple times, send all messages at once.

**Parameters:**
```json
{
  "messages": [
    {"session": "worker1", "text": "Build the login form"},
    {"session": "worker2", "text": "Implement auth API"},
    {"session": "worker3", "text": "Write tests"}
  ]
}
```

**Returns:**
```json
{
  "ok": true,
  "total": 3,
  "success": 3,
  "errors": 0,
  "results": [
    {"session": "worker1", "success": true, "message": "Sent: Build the login form..."},
    {"session": "worker2", "success": true, "message": "Sent: Implement auth API..."},
    {"session": "worker3", "success": true, "message": "Sent: Write tests..."}
  ],
  "message": "Sent 3/3 messages"
}
```

**Performance:** N× faster (where N = number of sessions)

---

#### `amux_batch_operations` ⭐ NEW
**Execute multiple operations (start, stop, send, create_task, claim_task, update_task) in ONE call.**

Most flexible batch tool - supports mixed operation types.

**Parameters:**
```json
{
  "operations": [
    {"type": "start", "session": "worker1"},
    {"type": "create_task", "title": "Build UI", "session": "worker1"},
    {"type": "send", "session": "worker1", "text": "Check board and start"}
  ]
}
```

**Supported operations:**
- `start` - Start a session
- `stop` - Stop a session
- `send` - Send message to session
- `create_task` - Create board task
- `claim_task` - Claim task for session
- `update_task` - Update task status/desc/title

**Performance:** Up to 10× faster than individual calls

See [BATCH-OPERATIONS.md](BATCH-OPERATIONS.md) for detailed guide.

---

### Session Management

#### `amux_list_sessions`
List all AMUX sessions with their status.
```
No parameters required
```

#### `amux_create_session`
Create a new AMUX session.
```json
{
  "name": "backend-api",
  "dir": "/path/to/project",
  "tool": "claude_code",  // "claude_code", "cursor", or "gemini"
  "desc": "Backend API development"
}
```

#### `amux_start_session`
Start a session.
```json
{
  "name": "backend-api"
}
```

#### `amux_stop_session`
Stop a session.
```json
{
  "name": "backend-api"
}
```

#### `amux_send_message`
Send a message/prompt to a session.
```json
{
  "name": "backend-api",
  "text": "Implement the login endpoint with JWT authentication"
}
```

#### `amux_get_status`
Get session status. Omit `name` for all sessions summary.
```json
{
  "name": "backend-api"  // Optional
}
```

#### `amux_peek_output`
View terminal output without attaching.
```json
{
  "name": "backend-api",
  "lines": 100  // Optional, default: 50
}
```

### Board/Task Management

#### `amux_list_board_tasks`
List Kanban board tasks with optional filters.
```json
{
  "status": "todo",       // Optional: filter by status
  "session": "backend-api" // Optional: filter by session
}
```

#### `amux_create_board_task`
Create a new task.
```json
{
  "title": "Implement user authentication",
  "desc": "Add JWT token-based auth with refresh tokens",
  "status": "todo",       // Optional, default: "todo"
  "session": "backend-api" // Optional: assign to session
}
```

#### `amux_claim_task`
Atomically claim a task for a session (prevents race conditions).
```json
{
  "task_id": "PROJ-5",
  "session": "backend-api"
}
```

#### `amux_update_task`
Update task status/description.
```json
{
  "task_id": "PROJ-5",
  "status": "done",
  "desc": "Completed: Authentication implemented with tests"
}
```

### Session Cleanup

#### `amux_delete_inactive_sessions`
Delete all inactive (stopped) sessions. Useful for cleanup after batch work or to free up resources.

**Parameters:**
- `dry_run` (boolean, optional): If true, only shows what would be deleted without actually deleting (default: false)
- `include_archived` (boolean, optional): If true, also delete archived sessions (default: false)
- `exclude_names` (array of strings, optional): List of session names to exclude from deletion

**Example - Dry run to see what would be deleted:**
```json
{
  "dry_run": true,
  "include_archived": false
}
```

**Example - Delete all inactive sessions except specific ones:**
```json
{
  "dry_run": false,
  "include_archived": false,
  "exclude_names": ["orchestrator", "monitoring"]
}
```

**Example - Delete everything including archived:**
```json
{
  "dry_run": false,
  "include_archived": true
}
```

**Response:**
```json
{
  "ok": true,
  "deleted": ["worker-1", "worker-2", "temp-session"],
  "deleted_count": 3,
  "errors": [],
  "error_count": 0,
  "message": "Deleted 3 inactive session(s)"
}
```

## Usage Examples

### Example 1: Orchestrator Agent Creating Workers

```python
# In your orchestrator agent session with MCP enabled:

# 1. Create worker sessions
amux_create_session({
  "name": "frontend-worker",
  "dir": "/project",
  "tool": "cursor",
  "desc": "Frontend development"
})

amux_create_session({
  "name": "backend-worker", 
  "dir": "/project",
  "tool": "claude_code",
  "desc": "Backend API"
})

# 2. Start them
amux_start_session({"name": "frontend-worker"})
amux_start_session({"name": "backend-worker"})

# 3. Create tasks
amux_create_board_task({
  "title": "Build login UI",
  "session": "frontend-worker",
  "status": "todo"
})

# 4. Send initial prompts
amux_send_message({
  "name": "frontend-worker",
  "text": "Check the board for your assigned task and start working"
})
```

### Example 2: Monitoring Workers

```python
# Get all sessions status
status = amux_get_status({})

# Check specific worker
worker_status = amux_get_status({"name": "backend-worker"})

# Peek at what it's doing
output = amux_peek_output({
  "name": "backend-worker",
  "lines": 100
})
```

### Example 3: Task Workflow

```python
# List available tasks
tasks = amux_list_board_tasks({"status": "todo"})

# Worker claims a task
amux_claim_task({
  "task_id": "PROJ-5",
  "session": "backend-worker"
})

# Update when done
amux_update_task({
  "task_id": "PROJ-5",
  "status": "done",
  "desc": "Implementation complete with tests"
})
```

## Architecture

```
┌─────────────────┐
│ Orchestrator    │ (Claude/Cursor with MCP)
│ Agent           │
└────────┬────────┘
         │ MCP Tools
         ↓
┌─────────────────┐
│ amux-mcp-server │ (Python stdio server)
│                 │
└────────┬────────┘
         │ HTTPS API
         ↓
┌─────────────────┐
│ amux-server.py  │ (Port 8822)
│                 │
└────────┬────────┘
         │ tmux control
         ↓
┌─────────────────┐
│ Worker Sessions │ (claude/agent processes)
│ - frontend      │
│ - backend       │
│ - testing       │
└─────────────────┘
```

## Debugging

The MCP server logs to stderr (visible in Claude Code's MCP server logs):

```
[AMUX-MCP] AMUX MCP Server starting...
[AMUX-MCP] Connecting to AMUX at https://localhost:8822
[AMUX-MCP] Handling request: initialize
[AMUX-MCP] Calling tool: amux_list_sessions with args: {}
```

## Testing Manually

You can test the MCP server directly via stdin/stdout:

```bash
cd /path/to/amux

# Test initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 amux-mcp-server.py

# Test list tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 amux-mcp-server.py

# Test calling a tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"amux_list_sessions","arguments":{}}}' | python3 amux-mcp-server.py
```

## Requirements

- Python 3.7+
- AMUX server running on https://localhost:8822
- No external dependencies (uses stdlib only)

## Security Note

The MCP server connects to `localhost:8822` with SSL verification disabled (for local development). For production, configure proper SSL certificates.
