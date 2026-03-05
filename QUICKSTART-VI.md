# ⚡ AMUX Quick Start Guide

## 🚀 Cài Đặt Nhanh (5 phút)

```bash
# 1. Clone repo
git clone https://github.com/your-repo/amux.git
cd amux

# 2. Cài đặt
./install.sh

# 3. Start server
python3 amux-server.py
```

✅ Mở: **https://localhost:8822**

---

## 🔐 Setup Claude Code

```bash
# Cài Claude Desktop (bao gồm CLI)
# Download: https://claude.ai/download

# Login
claude login

# Test
claude --model sonnet "hello"
```

---

## 🔐 Setup Cursor Agent

```bash
# Cài Cursor
# Download: https://cursor.sh/

# Đăng nhập trong app
# Settings > Account > Sign In

# Test CLI
agent --help

# Nếu không có, add alias:
echo 'export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 📝 Sử Dụng Cơ Bản

### 1️⃣ Tạo Session Mới

**Qua Web:**
1. Mở https://localhost:8822
2. Click **"+ New Session"**
3. Điền:
   - Name: `my-project`
   - Directory: `/path/to/project`
   - Tool: `claude_code` hoặc `cursor`
4. Click **"Create"**

**Qua API:**
```bash
curl -k -X POST https://localhost:8822/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "dir": "/Users/you/projects/myapp",
    "tool": "claude_code"
  }'
```

### 2️⃣ Start Session

**Web:** Click nút **"Start"**

**API:**
```bash
curl -k -X POST https://localhost:8822/api/sessions/my-project/start
```

### 3️⃣ Gửi Task

**Web:** Gõ message và click **"Send"**

**API:**
```bash
curl -k -X POST https://localhost:8822/api/sessions/my-project/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a FastAPI hello world endpoint"}'
```

### 4️⃣ Monitor Real-time

Dashboard tự động update mỗi 2 giây qua **Server-Sent Events (SSE)**.

---

## 🎯 Use Cases Phổ Biến

### Parallel Development

```bash
# Backend session
curl -k -X POST https://localhost:8822/api/sessions \
  -d '{"name":"backend", "tool":"claude_code", "dir":"/app/backend"}'

# Frontend session  
curl -k -X POST https://localhost:8822/api/sessions \
  -d '{"name":"frontend", "tool":"cursor", "dir":"/app/frontend"}'

# Start cả 2
curl -k -X POST https://localhost:8822/api/sessions/backend/start
curl -k -X POST https://localhost:8822/api/sessions/frontend/start
```

### Auto-Recovery (24/7 Coding)

```bash
# Enable auto-features
curl -k -X PATCH https://localhost:8822/api/sessions/my-project/config \
  -H "Content-Type: application/json" \
  -d '{
    "auto_approve": true,
    "auto_compact": true,
    "auto_restart": true
  }'
```

Session sẽ tự động:
- ✅ Approve prompts
- ✅ Compact context khi đầy
- ✅ Restart khi crash

### Browser Automation

```bash
curl -k -X POST https://localhost:8822/api/browser/agent \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Go to github.com and check my notifications",
    "start_url": "https://github.com"
  }'
```

---

## 📊 Kanban Board

**Tạo task:**
```bash
curl -k -X POST https://localhost:8822/api/board \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user auth",
    "desc": "JWT authentication with refresh tokens",
    "status": "todo",
    "session": "backend"
  }'
```

**Update status:**
```bash
curl -k -X PATCH https://localhost:8822/api/board/{task-id} \
  -H "Content-Type: application/json" \
  -d '{"status": "doing"}'
```

---

## 🔌 MCP Servers

**File:** `mcp.json`

```json
{
  "mcpServers": {
    "amux-orchestrator": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/amux-mcp-server.py"]
    },
    "claude-in-chrome": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic-ai/claude-code-mcp-server-chrome"]
    }
  }
}
```

Link MCP cho session:
```bash
curl -k -X POST https://localhost:8822/api/sessions/my-project/mcp \
  -H "Content-Type: application/json" \
  -d '{"mcp_ids": ["amux-orchestrator", "claude-in-chrome"]}'
```

---

## 📈 Token Usage

```bash
# View usage
curl -k https://localhost:8822/api/token-usage

# Response:
{
  "today": {"input": 50000, "output": 20000, "cost": 2.40},
  "total": {"input": 500000, "output": 200000, "cost": 24.00}
}
```

---

## 🛠️ Troubleshooting

### ❌ Port 8822 đã được dùng

```bash
# Kill process
lsof -i :8822
kill -9 <PID>

# Hoặc đổi port
export AMUX_PORT=8823
python3 amux-server.py
```

### ❌ Claude command not found

```bash
# Check installation
which claude

# Nếu không có, cài Claude Desktop
# https://claude.ai/download
```

### ❌ Session không start

```bash
# Check logs
tail -f ~/.amux/logs/server.log
tail -f ~/.amux/logs/{session-name}.log

# Test tmux
tmux ls

# Restart session
curl -k -X POST https://localhost:8822/api/sessions/{name}/stop
curl -k -X POST https://localhost:8822/api/sessions/{name}/start
```

### ❌ SSL Certificate Warning

Trình duyệt sẽ cảnh báo self-signed certificate. Click **"Advanced"** → **"Proceed"**.

Hoặc trust certificate:
```bash
# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.amux/cert.pem
```

---

## 📚 Advanced Features

### iCal Export (Google Calendar)

```bash
# Local feed
https://localhost:8822/api/calendar.ics

# Setup S3 public sync
echo 'AMUX_S3_BUCKET=your-bucket' >> ~/.amux/server.env
echo 'AMUX_S3_KEY=amux/calendar.ics' >> ~/.amux/server.env
touch amux-server.py  # restart server
```

### Email/Calendar Sync (macOS)

```bash
echo 'AMUX_EMAIL_SYNC_INTERVAL=900' >> ~/.amux/server.env
echo 'AMUX_CALENDAR_NAME=AMUX Events' >> ~/.amux/server.env
touch amux-server.py
```

### Credential Manager

```bash
# Add API keys
python3 credential-manager.py add

# Services: anthropic, openai, mixpeek, etc.

# Check status
python3 credential-manager.py status
```

---

## 🎓 Example Workflow

```bash
# 1. Create & start session
curl -k -X POST https://localhost:8822/api/sessions \
  -d '{"name":"api", "tool":"claude_code", "dir":"/app"}'
curl -k -X POST https://localhost:8822/api/sessions/api/start

# 2. Enable auto-recovery
curl -k -X PATCH https://localhost:8822/api/sessions/api/config \
  -d '{"auto_approve":true, "auto_compact":true}'

# 3. Create board task
curl -k -X POST https://localhost:8822/api/board \
  -d '{"title":"Build REST API", "session":"api", "status":"doing"}'

# 4. Send work
curl -k -X POST https://localhost:8822/api/sessions/api/send \
  -d '{"text":"Create FastAPI app with CRUD endpoints for users"}'

# 5. Monitor dashboard
open https://localhost:8822

# 6. Check logs
tail -f ~/.amux/logs/api.log
```

---

## 📖 Full Documentation

- **Chi tiết:** [SETUP-GUIDE-VI.md](SETUP-GUIDE-VI.md)
- **API Reference:** [API-REFERENCE.md](API-REFERENCE.md)
- **MCP Guide:** [MCP-README.md](MCP-README.md)

---

**🚀 Happy Coding!**
