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
  "tool": "claude_code",  // or "cursor"
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
