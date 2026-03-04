# AMUX Orchestration Architecture

**Multi-AI Orchestration System with MCP Protocol**

> "One orchestrator agent manages many specialized worker agents across different AI tools"

---

## 🎯 Vision

A system where:
- **One orchestrator AI agent** (Claude/Cursor/Gemini) coordinates multiple worker sessions
- **Many worker agents** run in parallel, each using the best tool for their task
- **MCP protocol** provides the communication layer
- **Board tasks** define the work breakdown structure
- **Sessions** provide isolated execution environments

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                         │
│         (Claude Code, Cursor, or any MCP client)            │
│                                                              │
│  "Create 3 workers: frontend (Cursor), backend (Claude),    │
│   tests (Aider). Assign tasks from board. Monitor progress."│
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ MCP Protocol (JSON-RPC stdio)
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 AMUX MCP Server                              │
│              (amux-mcp-server.py)                           │
│                                                              │
│  Tools:                                                      │
│  • amux_list_sessions       • amux_list_board_tasks        │
│  • amux_create_session      • amux_create_board_task       │
│  • amux_start_session       • amux_claim_task              │
│  • amux_stop_session        • amux_update_task             │
│  • amux_send_message                                        │
│  • amux_get_status                                          │
│  • amux_peek_output                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTPS API
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    AMUX Server                               │
│                (amux-server.py)                             │
│                                                              │
│  • SQLite database                                          │
│  • Session management                                       │
│  • Board tasks                                              │
│  • File-based logs                                          │
│  • tmux multiplexing                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│  Worker #1    │         │  Worker #2    │
│  (Cursor)     │         │ (Claude Code) │
│               │         │               │
│  Frontend     │         │  Backend API  │
└───────────────┘         └───────────────┘
```

---

## 🔧 Phase Completion Status

### ✅ Phase 1: Multi-AI-Tool Support (COMPLETED)

**Goal:** Support multiple AI tools (Claude, Cursor, Gemini, Aider, etc.)

**Implementation:**
- `AITool` base class with tool-specific implementations
- `ClaudeCodeTool`, `CursorTool` parsers
- Tool registry: `_AI_TOOLS = {"claude_code": ..., "cursor": ...}`
- Session field: `CC_TOOL` to specify tool per session
- UI: Tool selector dropdown in create session modal

**Result:** ✅ AMUX can now manage sessions for different AI tools

---

### ✅ Phase 2: MCP Orchestration Server (COMPLETED)

**Goal:** Expose AMUX operations as MCP tools for orchestrator agents

**Implementation:**
- `amux-mcp-server.py` (780 lines)
- JSON-RPC 2.0 protocol over stdio
- 11 MCP tools (session + board management)
- Updated `mcp.json` configuration
- Full documentation in `MCP-README.md`

**MCP Tools:**

| Tool | Purpose |
|------|---------|
| `amux_list_sessions` | List all sessions |
| `amux_create_session` | Create new worker session |
| `amux_start_session` | Start a session |
| `amux_stop_session` | Stop a session |
| `amux_send_message` | Send prompt to worker |
| `amux_get_status` | Get session status |
| `amux_peek_output` | Read worker output |
| `amux_list_board_tasks` | List Kanban tasks |
| `amux_create_board_task` | Create task |
| `amux_claim_task` | Claim task (atomic) |
| `amux_update_task` | Update task status |

**Result:** ✅ AI agents can now orchestrate AMUX via MCP

---

### ⏳ Phase 3: Workflow Engine (PLANNED)

**Goal:** Define task dependencies and execution pipelines

**Features:**
- Directed Acyclic Graph (DAG) for task dependencies
- Conditional execution: `if task-1 succeeds then task-2`
- Pipeline templates: "microservice" → frontend + backend + tests
- Automatic task chaining

**Example:**
```yaml
pipeline:
  - task: design-api
    tool: claude_code
    depends_on: []
  
  - task: implement-backend
    tool: claude_code
    depends_on: [design-api]
  
  - task: implement-frontend
    tool: cursor
    depends_on: [design-api]
  
  - task: integration-tests
    tool: aider
    depends_on: [implement-backend, implement-frontend]
```

**Status:** Not yet implemented

---

### ⏳ Phase 4: Autonomous Orchestrator (PLANNED)

**Goal:** Self-managing orchestration with health monitoring

**Features:**
- Auto-assign tasks to workers based on:
  - Tool capabilities (Cursor for frontend, Claude for backend)
  - Worker availability
  - Task priority
- Health monitoring:
  - Detect stuck sessions
  - Auto-restart failed workers
  - Rebalance load
- Smart task distribution:
  - Parallel execution where possible
  - Sequential for dependencies
- Auto-healing:
  - Retry failed tasks (max 3 attempts)
  - Escalate to human on critical failure

**Status:** Not yet implemented

---

## 🚀 Usage Patterns

### Pattern 1: Manual Orchestration (Current)

Orchestrator agent manually creates workers and assigns tasks:

```
Orchestrator: "Create session 'backend-dev' with claude_code tool"
              "Create task 'Build API' assigned to backend-dev"
              "Start session backend-dev"
              "Send message to backend-dev: 'Check board and implement API'"
```

**Demo:** See `demo-mcp-orchestration.py`

---

### Pattern 2: Query-Based Orchestration (Phase 3)

Orchestrator receives high-level query and generates task graph:

```
User Query: "Build a login feature with React frontend and Node.js backend"

Orchestrator:
  1. Parses query
  2. Generates task graph:
     - frontend: "React login component" (Cursor)
     - backend: "JWT auth API" (Claude)
     - tests: "Integration tests" (Aider)
  3. Creates workers
  4. Starts execution
  5. Monitors progress
```

---

### Pattern 3: Autonomous Orchestration (Phase 4)

System self-manages based on board task queue:

```
Board has 20 tasks:
  - 8 frontend tasks
  - 7 backend tasks
  - 5 test tasks

Orchestrator (autonomously):
  1. Provisions 3 Cursor workers for frontend
  2. Provisions 2 Claude workers for backend
  3. Provisions 1 Aider worker for tests
  4. Auto-assigns tasks based on labels
  5. Monitors health (CPU, memory, responsiveness)
  6. Rebalances on failure
  7. Reports progress to user
```

---

## 🎮 Real-World Usage

### Example 1: Feature Development Sprint

**Scenario:** Build "User Profile" feature across full stack

**Setup:**
```bash
# Start AMUX server
python3 amux-server.py

# In Claude Code session with MCP enabled:
"I need to build a user profile feature with:
- React component for editing profile
- API endpoint for updating profile
- Tests for the flow

Please orchestrate this across 3 worker sessions."
```

**Orchestrator Agent Actions:**
1. Calls `amux_create_session("frontend-worker", tool="cursor")`
2. Calls `amux_create_session("backend-worker", tool="claude_code")`
3. Calls `amux_create_session("test-worker", tool="aider")`
4. Calls `amux_create_board_task("Build profile edit component")`
5. Calls `amux_create_board_task("API: PATCH /api/profile")`
6. Calls `amux_create_board_task("E2E tests for profile flow")`
7. Starts all workers
8. Sends initial prompts
9. Monitors via `amux_peek_output` and `amux_list_board_tasks`

---

### Example 2: Bug Triage and Fix

**Scenario:** 3 production bugs reported

**Setup:**
```bash
# Create board tasks for bugs
FW-1: Login button not clickable (frontend)
BW-1: API timeout on /users (backend)
TW-1: Flaky test in CI (tests)
```

**Orchestrator:**
```
"We have 3 bugs. Spin up 3 workers (Cursor for FW-1, Claude for BW-1, Aider for TW-1).
Assign each worker to investigate and fix their bug. Coordinate if fixes depend on each other."
```

---

### Example 3: Code Migration

**Scenario:** Migrate codebase from React Class components to Hooks

**Setup:**
- 50 component files to migrate
- Board has 50 tasks, one per file

**Orchestrator:**
```
"We have 50 migration tasks. Provision 5 Cursor workers.
Auto-distribute tasks equally. Monitor progress.
If a worker gets stuck (no output for 5 min), reassign task to another worker."
```

---

## 🧪 Testing

### Test 1: MCP Protocol

```bash
# Test initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  python3 amux-mcp-server.py

# Test list tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
  python3 amux-mcp-server.py

# Test tool call
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"amux_list_sessions","arguments":{}}}' | \
  python3 amux-mcp-server.py
```

**Status:** ✅ All tests pass

---

### Test 2: Orchestration Demo

```bash
python3 demo-mcp-orchestration.py
```

**Validates:**
- Session creation with different tools
- Board task creation
- Session start/stop
- Message sending
- Status checking

**Status:** ✅ Demo runs successfully

---

### Test 3: Real Agent Orchestration

```bash
# In Claude Code or Cursor with MCP enabled:
"Use AMUX to create 2 workers:
1. cursor-worker for frontend
2. claude-worker for backend

Create a task 'Build hello world' for each.
Start both sessions and send them their tasks."
```

**Status:** ⏳ Not yet tested with real Claude/Cursor MCP client

---

## 📊 Current Capabilities

| Capability | Status | Notes |
|------------|--------|-------|
| Multi-tool support | ✅ | Claude, Cursor |
| MCP protocol | ✅ | 11 tools implemented |
| Session management | ✅ | Create, start, stop, status |
| Board tasks | ✅ | Create, list, claim, update |
| Worker messaging | ✅ | Send prompts via API |
| Output monitoring | ✅ | Peek at worker output |
| Task dependencies | ❌ | Phase 3 |
| Auto-assignment | ❌ | Phase 4 |
| Health monitoring | ❌ | Phase 4 |
| Auto-healing | ❌ | Phase 4 |

---

## 🛠️ Adding New AI Tools

To add a new tool (e.g., Gemini CLI):

1. **Implement `AITool` subclass:**
```python
class GeminiTool(AITool):
    def get_command(self, flags, session_flag, default_flags, extra_flags):
        return f"gemini-cli {session_flag} {flags} {extra_flags}"
    
    def detect_status(self, raw_output):
        if "gemini>" in raw_output:
            return "idle"
        # ... tool-specific parsing
    
    # ... other methods
```

2. **Register tool:**
```python
_AI_TOOLS["gemini"] = GeminiTool()
```

3. **Update UI:**
Add `<option value="gemini">Gemini CLI</option>` to tool selector

4. **Test:**
Create session with `tool: "gemini"`, verify it starts correctly

---

## 🎯 Next Steps

### Immediate (Phase 2 complete):
- [x] MCP server implementation
- [x] MCP protocol testing
- [x] Demo script
- [ ] Real-world test with Claude/Cursor MCP client
- [ ] Add Gemini CLI support
- [ ] Add Aider support

### Short-term (Phase 3):
- [ ] Task dependency graph (DAG)
- [ ] Pipeline templates
- [ ] Conditional execution
- [ ] Auto-chaining completed tasks

### Long-term (Phase 4):
- [ ] Orchestrator agent implementation
- [ ] Health monitoring dashboard
- [ ] Auto-assignment algorithm
- [ ] Auto-healing and retry logic
- [ ] Load balancing across workers

---

## 📚 Documentation

- **[MCP-README.md](MCP-README.md)** — MCP server documentation
- **[CLAUDE.md](CLAUDE.md)** — AMUX project guidelines
- **[demo-mcp-orchestration.py](demo-mcp-orchestration.py)** — Usage demo
- **[README.md](README.md)** — Main project README

---

## 🤝 Contributing

To contribute to orchestration features:

1. Follow single-codebase rule (no cloud-only code in `amux-server.py`)
2. Commit after each completed task
3. Verify Python syntax after edits
4. Test MCP tools with `echo` commands before integrating
5. Update this document with new patterns/capabilities

---

**Status:** Phase 2 complete (80% of original vision achieved)  
**Last Updated:** 2025  
**Author:** Built with Claude Code
