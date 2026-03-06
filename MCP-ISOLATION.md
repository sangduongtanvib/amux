# MCP Config Isolation

## Vấn đề

Trước đây, tất cả sessions (Claude Code CLI, Cursor CLI) đều dùng chung **global MCP config**:
- Claude Code → `~/.claude/claude_desktop_config.json` (share với Claude Desktop app)
- Cursor → `~/.cursor/cli-config.json`

**Hạn chế:**
- ❌ Không thể customize MCP servers khác nhau cho từng session
- ❌ Sessions can't have isolated MCP environments
- ❌ Changes to global config affect ALL sessions
- ❌ No centralized management via Amux dashboard

## Giải pháp

Amux giờ đây **automatically isolates MCP config per session**:

### 1. Centralized MCP Database

MCP servers được lưu trong SQLite database (`~/.amux/amux.db`):
```sql
CREATE TABLE mcp_configs (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,  -- stdio | http
    command     TEXT,
    args        TEXT,
    url         TEXT,
    headers     TEXT,
    env_vars    TEXT,
    enabled     INTEGER NOT NULL DEFAULT 1,
    ...
);
```

### 2. Session-Specific Links

Mỗi session có thể link đến bất kỳ MCP servers nào:
```sql
CREATE TABLE session_mcp_links (
    session     TEXT NOT NULL,
    mcp_id      TEXT NOT NULL,
    position    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (session, mcp_id)
);
```

### 3. Auto-Generated `mcp.json`

Khi session start, Amux:
1. ✅ Query linked MCP servers từ database
2. ✅ Generate `mcp.json` trong work directory
3. ✅ Auto-inject `--mcp-config <work-dir>/mcp.json --strict-mcp-config`
4. ✅ Claude Code CLI uses ONLY session-specific MCP config

**Code:**
```python
# In start_session()
_generate_session_mcp_json(name, work_dir)

# Auto-inject --mcp-config flag
mcp_file = Path(work_dir) / "mcp.json"
if tool_name == "claude_code" and mcp_file.exists():
    mcp_flag = f"--mcp-config {shlex.quote(str(mcp_file))} --strict-mcp-config"
    flags = f"{flags} {mcp_flag}".strip()
```

## Workflow

### Import MCP Servers (One-time)

**Via Dashboard:**
1. Navigate to **Settings → MCP Servers**
2. Click **Import from JSON**
3. Paste `mcp.json` content
4. Click Save

**Via API:**
```bash
curl -X POST https://localhost:8822/api/mcp/import \
  -H "Content-Type: application/json" \
  -d @mcp.json
```

### Link MCP to Session

**Via Dashboard:**
1. Open session card
2. Click **⚙️ Settings → MCP Config**
3. Select MCPs to enable
4. Click Save

**Via API:**
```bash
curl -X POST https://localhost:8822/api/sessions/my-session/mcp \
  -H "Content-Type: application/json" \
  -d '{"mcp_ids": ["amux-orchestrator", "claude-in-chrome"]}'
```

### Verify Isolation

Start session and check generated config:
```bash
# Session generates mcp.json on start
cat ~/my-project/mcp.json

# Inside Claude Code CLI
mcp list
# Should show ONLY session-specific MCPs
```

## Benefits

✅ **Per-session customization** — different projects use different MCP servers  
✅ **No global config pollution** — sessions don't affect each other  
✅ **Centralized management** — manage all MCPs from Amux dashboard  
✅ **Version control friendly** — `mcp.json` generated per session, not committed  
✅ **Developer isolation** — team members can have different local MCP setups  

## Example Use Cases

### 1. Backend vs Frontend Sessions
```
backend-session:
  - database-mcp (DB queries)
  - docker-mcp (container management)
  
frontend-session:
  - figma-mcp (design assets)
  - browser-mcp (testing)
```

### 2. Development vs Production
```
dev-session:
  - local-db-mcp
  - debug-tools-mcp
  
staging-session:
  - staging-db-mcp
  - monitoring-mcp
```

### 3. Client-Specific Projects
```
clientA-session:
  - clientA-api-mcp
  - clientA-auth-mcp
  
clientB-session:
  - clientB-api-mcp
  - clientB-crm-mcp
```

## Future: Cursor CLI Support

Cursor CLI currently doesn't have `--mcp-config` flag yet. Tracking:
- [ ] Investigate Cursor CLI MCP config mechanism
- [ ] Add similar isolation for Cursor sessions
- [ ] Unified MCP management for all AI tools

## Related Files

- [`amux-server.py`](amux-server.py) — MCP generation & injection logic
- [`mcp.json`](mcp.json) — Template/example MCP config
- [`test-mcp-isolation.py`](test-mcp-isolation.py) — Test script
- [`CLAUDE.md`](CLAUDE.md) — Project conventions

## CLI Reference

```bash
# List all MCP configs
curl https://localhost:8822/api/mcp

# Get session's linked MCPs
curl https://localhost:8822/api/sessions/my-session

# Export all MCPs to JSON
curl https://localhost:8822/api/mcp/export > mcp-backup.json

# Import MCPs
curl -X POST https://localhost:8822/api/mcp/import -d @mcp-backup.json
```
