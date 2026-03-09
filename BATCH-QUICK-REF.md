# AMUX Batch Operations - Quick Reference

## Send to Multiple Sessions

```json
{
  "tool": "amux_batch_send_messages",
  "arguments": {
    "messages": [
      {"session": "worker1", "text": "..."},
      {"session": "worker2", "text": "..."},
      {"session": "worker3", "text": "..."}
    ]
  }
}
```

**Returns:** `{ok, total, success, errors, results, message}`

---

## Mixed Operations

```json
{
  "tool": "amux_batch_operations",
  "arguments": {
    "operations": [
      {"type": "start", "session": "worker1"},
      {"type": "send", "session": "worker1", "text": "..."},
      {"type": "create_task", "title": "...", "session": "worker1"},
      {"type": "claim_task", "task_id": "PROJ-1", "session": "worker1"},
      {"type": "update_task", "task_id": "PROJ-1", "status": "doing"}
    ]
  }
}
```

**Operation types:** `start`, `stop`, `send`, `create_task`, `claim_task`, `update_task`

---

## Common Patterns

### Broadcast same message
```python
workers = ["w1", "w2", "w3"]
msg = "Check board for tasks"

amux_batch_send_messages({
    "messages": [{"session": w, "text": msg} for w in workers]
})
```

### Assign tasks
```python
operations = []
for worker, task in assignments:
    operations.append({"type": "claim_task", "task_id": task, "session": worker})
    operations.append({"type": "send", "session": worker, "text": f"Work on {task}"})

amux_batch_operations({"operations": operations})
```

### Restart workers
```python
operations = []
for w in workers:
    operations.append({"type": "stop", "session": w})
    operations.append({"type": "start", "session": w})

amux_batch_operations({"operations": operations})
```

---

## Performance

| Scenario | Old | New | Speedup |
|----------|-----|-----|---------|
| Send to 5 workers | 5 calls | 1 call | 5× |
| Assign 5 tasks | 10 calls | 1 call | 10× |
| Full orchestration | 11 calls | 2 calls | 5.5× |

---

## Error Handling

```python
result = amux_batch_send_messages({"messages": [...]})

if result["errors"] > 0:
    for r in result["results"]:
        if not r["success"]:
            print(f"Failed: {r['session']} - {r['error']}")
```

---

## Full Documentation

- **[BATCH-OPERATIONS.md](BATCH-OPERATIONS.md)** - Complete guide
- **[demo-batch-operations.py](demo-batch-operations.py)** - Demo script
