# MCP Performance Analysis & Optimization

## Vấn đề hiện tại

MCP server (`amux-mcp-server.py`) hiện đang gọi **HTTP API** cho mọi operation:

```python
# Mỗi tool call = 1 HTTP request
def tool_amux_list_sessions(args: Dict) -> Dict:
    sessions = amux_api_call("/api/sessions")  # HTTP GET
    ...

def tool_amux_get_status(args: Dict) -> Dict:
    sessions = amux_api_call("/api/sessions")  # HTTP GET
    ...
```

### Bottlenecks

1. **HTTP Overhead** (10-50ms mỗi request)
   - TCP handshake
   - HTTPS/SSL handshake
   - HTTP headers parsing
   - JSON serialization/deserialization
   - Timeout 30s per request

2. **Không tái sử dụng connections**
   - Mỗi request mở connection mới
   - Không có connection pooling
   - SSL handshake lặp lại mỗi lần

3. **Read operations không cần HTTP**
   - `list_sessions` - chỉ đọc filesystem + SQLite
   - `get_status` - chỉ đọc tmux state
   - `peek_output` - chỉ đọc log files
   - Không cần serialize qua network

4. **Dashboard polling overhead**
   - Dashboard poll `/api/sessions/*/peek` mỗi 2s cho 5 sessions
   - = 2.5 requests/giây liên tục
   - Thấy rõ trong terminal logs:
     ```
     2026-03-06 09:02:15 [127.0.0.1] GET /api/sessions/agent-content/peek 200 16ms
     2026-03-06 09:02:16 [127.0.0.1] GET /api/sessions/agent-ui/peek 200 18ms
     ...
     ```

## Giải pháp được đề xuất

### **Option 1: Direct Python Import (RECOMMENDED)**

Tách shared code và cho phép MCP server gọi trực tiếp, bỏ qua HTTP cho read operations.

#### Architecture

```
┌─────────────────────┐
│  amux-core.py       │  ← Shared utilities
│  - list_sessions()  │
│  - parse_env_file() │
│  - read_db()        │
└──────────┬──────────┘
           │ import
      ┌────┴────┬──────────────┐
      │         │              │
┌─────▼─────┐ ┌▼────────────┐ ┌▼───────────────┐
│ amux-     │ │ amux-       │ │ amux-          │
│ server.py │ │ mcp-        │ │ dashboard.html │
│           │ │ server.py   │ │                │
│ (HTTP     │ │ (direct for │ │ (HTTP for UI)  │
│  API)     │ │  reads)     │ │                │
└───────────┘ └─────────────┘ └────────────────┘
```

#### Implementation

```python
# amux-mcp-server.py
import os
from pathlib import Path

# Direct filesystem access
CC_HOME = Path(os.environ.get("CC_HOME", Path.home() / ".amux"))
CC_SESSIONS = CC_HOME / "sessions"
CC_LOGS = CC_HOME / "logs"

def parse_env_file(path: Path) -> dict:
    """Parse .env file into dict (copied from amux-server.py)."""
    cfg = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

def list_sessions_direct() -> list:
    """Direct filesystem read - no HTTP needed."""
    sessions = []
    if not CC_SESSIONS.is_dir():
        return sessions
    
    for env_file in sorted(CC_SESSIONS.glob("*.env")):
        name = env_file.stem
        cfg = parse_env_file(env_file)
        sessions.append({
            "name": name,
            "dir": cfg.get("CC_DIR", ""),
            "desc": cfg.get("CC_DESC", ""),
            "running": tmux_is_running(name),
            "tool": cfg.get("CC_TOOL", "claude_code"),
        })
    return sessions

def tool_amux_list_sessions(args: Dict) -> Dict:
    """List sessions using direct access."""
    sessions = list_sessions_direct()  # ← No HTTP!
    return {
        "sessions": sessions,
        "count": len(sessions),
        "message": f"Found {len(sessions)} sessions"
    }
```

#### Performance Impact

| Operation | Before (HTTP) | After (Direct) | Speedup |
|-----------|---------------|----------------|---------|
| list_sessions | 15-50ms | 1-5ms | **10x** |
| get_status | 15-50ms | 1-5ms | **10x** |
| peek_output | 15-50ms | 1-3ms | **15x** |
| create_session | 20-60ms | 20-60ms | Same (needs HTTP) |
| send_message | 20-60ms | 20-60ms | Same (needs HTTP) |

**Overall:** Read operations (80% of calls) become **10-15x faster**.

---

### **Option 2: Unix Domain Socket**

Replace HTTPS với Unix socket cho local IPC.

```python
# amux-server.py
import socket

# Add Unix socket listener
SOCKET_PATH = CC_HOME / "amux.sock"
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(str(SOCKET_PATH))
sock.listen(5)

# amux-mcp-server.py  
import socket

def amux_api_call_socket(endpoint: str, method: str = "GET", data: Optional[Dict] = None):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(str(SOCKET_PATH))
    # Send HTTP-like request
    ...
```

**Performance:** 2-3x faster than HTTP (5-15ms), but still has serialization overhead.

**Pros:** Still decoupled, easier to debug.  
**Cons:** Needs server changes, not as fast as direct access.

---

### **Option 3: HTTP Connection Pooling**

Reuse connections with `http.client.HTTPSConnection`.

```python
from http.client import HTTPSConnection
import ssl

_connection_pool = {}

def amux_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None):
    conn = _connection_pool.get("localhost:8822")
    if not conn:
        conn = HTTPSConnection("localhost", 8822, context=ssl_context)
        _connection_pool["localhost:8822"] = conn
    
    conn.request(method, endpoint, body=json.dumps(data) if data else None)
    response = conn.getresponse()
    return json.loads(response.read())
```

**Performance:** 1.5-2x faster (save SSL handshake).

**Pros:** Easy to implement, no server changes.  
**Cons:** Still has HTTP overhead, connections can timeout.

---

### **Option 4: Direct SQLite + Filesystem (Minimal Change)**

Chỉ cần đọc trực tiếp cho read operations, không cần refactor server.

```python
import sqlite3
from pathlib import Path

def list_sessions_from_fs():
    """Read directly from ~/.amux/sessions/*.env files."""
    sessions = []
    sessions_dir = Path.home() / ".amux" / "sessions"
    
    for env_file in sessions_dir.glob("*.env"):
        cfg = parse_env_file(env_file)
        sessions.append({
            "name": env_file.stem,
            "dir": cfg.get("CC_DIR", ""),
            "tool": cfg.get("CC_TOOL", "claude_code"),
            "desc": cfg.get("CC_DESC", ""),
        })
    return sessions

def get_board_tasks_from_db():
    """Read directly from ~/.amux/amux.db."""
    db_path = Path.home() / ".amux" / "amux.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM issues WHERE deleted IS NULL").fetchall()
    return [dict(row) for row in rows]
```

**Pros:** 
- Fastest possible (microseconds)
- No server changes needed
- No HTTP overhead

**Cons:**
- Can't get real-time tmux state (need subprocess call)
- Duplicate code between server and MCP

---

## Recommendation

### **Hybrid Approach (Best of both worlds)**

1. **Read operations → Direct filesystem/SQLite access**
   - `list_sessions()` → read `~/.amux/sessions/*.env`
   - `list_board_tasks()` → read `~/.amux/amux.db`
   - `peek_output()` → read log files directly

2. **Write operations → HTTP API (unchanged)**
   - `create_session()` → POST /api/sessions
   - `start_session()` → POST /api/sessions/{name}/start
   - `send_message()` → POST /api/sessions/{name}/send
   - Server maintains state consistency

3. **Optional: Cache tmux state**
   - MCP server can call `tmux list-sessions` directly
   - Or read from server's cached state file
   - Update every 5-10s instead of every request

### Implementation Steps

1. **Extract shared utilities** (2 hours)
   ```bash
   # Create amux-core.py with:
   - parse_env_file()
   - list_sessions_from_fs()
   - read_session_log()
   - get_board_tasks()
   ```

2. **Update amux-mcp-server.py** (1 hour)
   - Import shared utilities
   - Replace HTTP calls for read operations
   - Keep HTTP for write operations

3. **Test & validate** (1 hour)
   - Ensure no data staleness
   - Verify write operations still work
   - Benchmark performance improvement

**Total effort:** 4 hours for 10-15x performance improvement on reads.

---

## Performance Comparison

| Scenario | Current (HTTP) | Option 1 (Direct) | Option 2 (Socket) | Option 3 (Pool) |
|----------|----------------|-------------------|-------------------|-----------------|
| **List 5 sessions** | 20-50ms | 2-5ms | 8-15ms | 12-30ms |
| **Get board (10 tasks)** | 15-40ms | 1-3ms | 6-12ms | 10-25ms |
| **Peek session log** | 15-45ms | 1-3ms | 7-14ms | 10-30ms |
| **Create session** | 30-80ms | 30-80ms | 15-40ms | 20-50ms |
| **Send message** | 30-100ms | 30-100ms | 15-50ms | 20-60ms |

## Dashboard Impact

Current polling pattern (5 sessions, every 2s):
```
Current:  2.5 req/s × 20ms = 50ms every 2s (blocked)
Direct:   2.5 req/s × 2ms  = 5ms every 2s  (10x faster)
Socket:   2.5 req/s × 8ms  = 20ms every 2s (2.5x faster)
```

**Result:** Dashboard becomes more responsive, agent orchestration faster.

---

## Conclusion

**Recommended:** Implement **Hybrid Approach** with direct filesystem/SQLite access for reads.

**Benefits:**
- ✅ 10-15x faster read operations  
- ✅ Reduced CPU/network overhead
- ✅ Better scalability (no HTTP limits)
- ✅ Maintains write safety through HTTP API
- ✅ Single-codebase rule preserved (same .py file)
- ✅ 4 hours implementation time

**Next steps:**
1. Agree on approach
2. Extract shared utilities to top of amux-server.py
3. Update MCP server to import and use direct access
4. Test and benchmark
5. Deploy

