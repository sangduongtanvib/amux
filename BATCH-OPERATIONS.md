# AMUX Batch Operations

## Problem

When orchestrating multiple agents, you often need to send commands to many sessions. Traditional approach requires one MCP call per session:

```python
# Traditional: slow and verbose
amux_send_message({"name": "worker1", "text": "Task 1"})
amux_send_message({"name": "worker2", "text": "Task 2"})
amux_send_message({"name": "worker3", "text": "Task 3"})
# 3 MCP calls, ~1.5s
```

This creates orchestration bottlenecks and delays.

## Solution: Batch Tools

### 1. `amux_batch_send_messages` - Send to Multiple Sessions

Send messages to multiple sessions in **one MCP call**.

**Usage:**
```json
{
  "tool": "amux_batch_send_messages",
  "arguments": {
    "messages": [
      {"session": "worker1", "text": "Build the login form"},
      {"session": "worker2", "text": "Implement auth API"},
      {"session": "worker3", "text": "Write integration tests"}
    ]
  }
}
```

**Response:**
```json
{
  "ok": true,
  "total": 3,
  "success": 3,
  "errors": 0,
  "results": [
    {"session": "worker1", "success": true, "message": "Sent: Build the login form..."},
    {"session": "worker2", "success": true, "message": "Sent: Implement auth API..."},
    {"session": "worker3", "success": true, "message": "Sent: Write integration tests..."}
  ],
  "message": "Sent 3/3 messages"
}
```

**Benefits:**
- 1 call instead of N calls
- Automatic error handling per session
- Clear success/failure reporting
- Continues on error (doesn't fail completely if one session fails)

---

### 2. `amux_batch_operations` - Mixed Operations

Execute **different operation types** in one call: start, stop, send, create_task, claim_task, update_task.

**Usage:**
```json
{
  "tool": "amux_batch_operations",
  "arguments": {
    "operations": [
      {"type": "start", "session": "worker1"},
      {"type": "start", "session": "worker2"},
      {"type": "create_task", "title": "Build UI", "session": "worker1"},
      {"type": "create_task", "title": "Build API", "session": "worker2"},
      {"type": "send", "session": "worker1", "text": "Check board and start"},
      {"type": "send", "session": "worker2", "text": "Check board and start"}
    ]
  }
}
```

**Supported operation types:**

| Type | Required Fields | Description |
|------|----------------|-------------|
| `start` | `session` | Start a session |
| `stop` | `session` | Stop a session |
| `send` | `session`, `text` | Send message to session |
| `create_task` | `title` | Create board task |
| `claim_task` | `task_id`, `session` | Claim task for session |
| `update_task` | `task_id` | Update task (+ status/desc/title) |

**Response:**
```json
{
  "ok": true,
  "total": 6,
  "success": 6,
  "errors": 0,
  "results": [
    {"type": "start", "session": "worker1", "success": true},
    {"type": "start", "session": "worker2", "success": true},
    {"type": "create_task", "success": true, "task_id": "PROJ-5"},
    {"type": "create_task", "success": true, "task_id": "PROJ-6"},
    {"type": "send", "session": "worker1", "success": true},
    {"type": "send", "session": "worker2", "success": true}
  ],
  "message": "Executed 6/6 operations"
}
```

**Benefits:**
- Most flexible batch tool
- Mix different operation types
- Sequential execution (operations run in order)
- Partial failure support (continues on error)

---

## Performance Comparison

### Scenario 1: Send to 5 workers

**Traditional:**
```python
# 5 individual calls
for worker in workers:
    amux_send_message({"name": worker, "text": "..."})
# 5 calls × 0.5s = 2.5s
```

**Batch:**
```python
amux_batch_send_messages({
    "messages": [{"session": w, "text": "..."} for w in workers]
})
# 1 call × 0.5s = 0.5s
# 5× faster! 🚀
```

### Scenario 2: Orchestration workflow

**Traditional:**
```python
# 11 calls total
sessions = amux_list_sessions()              # 1
for s in sessions:
    output = amux_peek_output({"name": s})   # 3
tasks = amux_list_board_tasks()              # 1
for task in tasks:
    amux_claim_task(task, session)           # 3
    amux_send_message(session, "...")        # 3
# Total: 11 calls, ~5.5s
```

**Batch:**
```python
# 2 calls total
view = amux_get_orchestrator_view()          # 1 - monitoring
amux_batch_operations({                      # 1 - actions
    "operations": [
        {"type": "claim_task", ...},
        {"type": "send", ...},
        ...
    ]
})
# Total: 2 calls, ~1s
# 5.5× faster! 🚀
```

---

## Common Patterns

### Pattern 1: Broadcast Message

Send same message to all workers:

```python
workers = ["worker1", "worker2", "worker3"]
message = "Please check the board for new tasks"

amux_batch_send_messages({
    "messages": [{"session": w, "text": message} for w in workers]
})
```

### Pattern 2: Task Assignment

Assign tasks and notify workers:

```python
assignments = [
    ("worker1", "PROJ-1", "Build login UI"),
    ("worker2", "PROJ-2", "Implement auth API"),
    ("worker3", "PROJ-3", "Write tests"),
]

operations = []
for worker, task_id, desc in assignments:
    operations.append({"type": "claim_task", "task_id": task_id, "session": worker})
    operations.append({"type": "send", "session": worker, "text": f"Work on {task_id}: {desc}"})

amux_batch_operations({"operations": operations})
```

### Pattern 3: Restart All Workers

```python
workers = ["worker1", "worker2", "worker3"]

operations = []
for w in workers:
    operations.append({"type": "stop", "session": w})
    operations.append({"type": "start", "session": w})

amux_batch_operations({"operations": operations})
```

### Pattern 4: Conditional Messages

Send different messages based on status:

```python
view = amux_get_orchestrator_view()

messages = []
for session in view["sessions"]:
    if session["status"] == "idle":
        messages.append({
            "session": session["name"],
            "text": "Check board for new tasks"
        })
    elif session["status"] == "needs_input":
        messages.append({
            "session": session["name"],
            "text": "y"  # Auto-approve
        })

if messages:
    amux_batch_send_messages({"messages": messages})
```

---

## Error Handling

Both batch tools continue execution on errors and report them:

```python
result = amux_batch_send_messages({
    "messages": [
        {"session": "worker1", "text": "Task 1"},
        {"session": "nonexistent", "text": "Task 2"},  # Will fail
        {"session": "worker3", "text": "Task 3"},
    ]
})

# Check results
if result["errors"] > 0:
    print(f"⚠️  {result['errors']} messages failed")
    for r in result["results"]:
        if not r.get("success"):
            print(f"   Failed: {r['session']} - {r.get('error')}")
```

---

## Best Practices

### ✅ DO:

- Use `batch_send_messages` when sending to multiple sessions
- Use `batch_operations` for complex workflows
- Combine with `get_orchestrator_view` for full efficiency
- Check `success` count in response
- Log failed operations for debugging

### ❌ DON'T:

- Don't batch operations that depend on each other's results (use sequential calls)
- Don't batch hundreds of operations in one call (API timeout risk)
- Don't ignore error handling
- Don't use batch for single operations (overhead not worth it)

---

## Migration Guide

### Before (Individual Calls)

```python
# Orchestration loop
while True:
    sessions = amux_list_sessions()
    
    for session in sessions["sessions"]:
        if session["status"] == "idle":
            tasks = amux_list_board_tasks({"status": "todo"})
            if tasks:
                task = tasks[0]
                amux_claim_task({"task_id": task["id"], "session": session["name"]})
                amux_send_message({
                    "name": session["name"],
                    "text": f"Work on {task['title']}"
                })
    
    sleep(10)
```

### After (Batch Calls)

```python
# Orchestration loop
while True:
    view = amux_get_orchestrator_view()
    
    # Build batch operations
    operations = []
    idle = [s for s in view["sessions"] if s["status"] == "idle"]
    todo = [t for t in view["tasks"] if t["status"] == "todo"]
    
    for session, task in zip(idle, todo):
        operations.append({
            "type": "claim_task",
            "task_id": task["id"],
            "session": session["name"]
        })
        operations.append({
            "type": "send",
            "session": session["name"],
            "text": f"Work on {task['title']}"
        })
    
    if operations:
        amux_batch_operations({"operations": operations})
    
    sleep(10)
```

**Improvement:** From ~11 calls per loop to 2 calls per loop (5.5× fewer)

---

## Demo

Run the demo to see comparisons:

```bash
python3 demo-batch-operations.py
```

Shows:
- Traditional vs batch approach
- Performance comparison table
- Real-world workflow examples

---

## Summary

| Tool | Use Case | Performance |
|------|----------|-------------|
| `amux_batch_send_messages` | Send to multiple sessions | N× faster (N = sessions) |
| `amux_batch_operations` | Mixed operations | Up to 10× faster |
| Combined with `get_orchestrator_view` | Full orchestration | 5-10× fewer calls overall |

**Total orchestration efficiency: Up to 10× improvement** 🚀
