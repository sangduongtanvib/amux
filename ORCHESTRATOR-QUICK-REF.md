# AMUX Orchestrator Quick Reference

## Single Call to Monitor Everything

```json
{
  "tool": "amux_get_orchestrator_view",
  "arguments": {}
}
```

**Returns:** sessions + tasks + output + summary + needs_attention list

---

## Common Patterns

### Pattern 1: Check if any session needs approval

```python
view = amux_get_orchestrator_view()

if view["needs_attention"]:
    for session_name in view["needs_attention"]:
        print(f"⚠️  {session_name} needs approval")
```

### Pattern 2: Monitor specific workers

```python
view = amux_get_orchestrator_view({
    "sessions": ["frontend", "backend", "tests"]
})
```

### Pattern 3: Check task progress

```python
view = amux_get_orchestrator_view({"task_status": "doing"})

print(f"{len(view['tasks'])} tasks in progress")
for task in view["tasks"]:
    print(f"- {task['title']} ({task['session']})")
```

### Pattern 4: Find idle workers

```python
view = amux_get_orchestrator_view()

idle = [s["name"] for s in view["sessions"] if s["status"] == "idle"]
print(f"Available workers: {idle}")
```

### Pattern 5: Lightweight status check

```python
view = amux_get_orchestrator_view({
    "include_output": False,
    "include_tasks": False
})

print(f"{view['summary']['running_sessions']} / {view['summary']['total_sessions']} running")
```

---

## Response Structure

```
{
  summary: {
    total_sessions, running_sessions, needs_attention,
    idle_sessions, working_sessions,
    total_tasks, todo_tasks, doing_tasks, done_tasks
  },
  needs_attention: [session_names],
  sessions: [
    {name, status, running, tool, dir, preview, output}
  ],
  tasks: [
    {id, title, status, session, desc}
  ]
}
```

---

## Status Values

**Session status:**
- `idle` - Waiting for input
- `working` - Processing/thinking
- `needs_input` - Approval required
- `error` - Error occurred

**Task status:**
- `todo` - Not started
- `doing` - In progress
- `done` - Completed
- (custom statuses allowed)

---

## Performance Tips

✅ **DO:** Use `amux_get_orchestrator_view` for monitoring loops  
✅ **DO:** Filter by specific sessions if you only care about some  
✅ **DO:** Set `include_output: false` if you don't need terminal output  
❌ **DON'T:** Call individual tools (list_sessions, peek_output) in loop  
❌ **DON'T:** Poll more frequently than needed (10s interval is good)

---

## Error Handling

```python
try:
    view = amux_get_orchestrator_view()
    
    if not view.get("sessions"):
        print("No sessions found")
    
    if view.get("summary", {}).get("needs_attention", 0) > 0:
        handle_attention_needed(view)
        
except Exception as e:
    print(f"Failed to get orchestrator view: {e}")
    # Fallback to individual calls or retry
```

---

## Integration with Other Tools

```python
# Get full view
view = amux_get_orchestrator_view()

# Take actions based on view
for session in view["needs_attention"]:
    # Send approval
    amux_send_message({"name": session, "text": "y"})

# Assign tasks to idle workers
idle = [s["name"] for s in view["sessions"] if s["status"] == "idle"]
todo = [t for t in view["tasks"] if t["status"] == "todo"]

for worker, task in zip(idle, todo):
    amux_claim_task({"task_id": task["id"], "session": worker})
    amux_send_message({
        "name": worker,
        "text": f"Work on {task['title']}: {task['desc']}"
    })
```

---

## Full Documentation

- **[ORCHESTRATOR-VIEW.md](ORCHESTRATOR-VIEW.md)** - Complete guide
- **[MCP-README.md](MCP-README.md)** - All MCP tools
- **[demo-orchestrator-view.py](demo-orchestrator-view.py)** - Demo script
