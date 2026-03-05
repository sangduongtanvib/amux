# 🚀 Hướng Dẫn Setup và Sử Dụng AMUX

**AMUX** (AI Multiplexer) - Hệ thống quản lý và điều phối nhiều AI coding sessions song song.

---

## 📦 Cài Đặt

### Yêu Cầu Hệ Thống

- **macOS** (hoặc Linux)
- **Python 3.8+**
- **tmux** (quản lý terminal sessions)
- **Claude Code CLI** hoặc **Cursor Agent**
- **Git**

### Bước 1: Clone Repository

```bash
git clone https://github.com/your-repo/amux.git
cd amux
```

### Bước 2: Chạy Script Cài Đặt

```bash
./install.sh
```

Script này sẽ:
- Cài đặt tmux (nếu chưa có)
- Tạo thư mục cấu hình `~/.amux/`
- Setup SSL certificates cho HTTPS
- Cài đặt dependencies Python

### Bước 3: Khởi Động Server

```bash
python3 amux-server.py
```

Server sẽ chạy tại: **https://localhost:8822**

---

## 🔐 Cấu Hình Tài Khoản AI Tools

### Claude Code CLI

#### Bước 1: Cài Đặt Claude Code CLI

```bash
# Cài đặt Claude Desktop (bao gồm CLI)
# Download từ: https://claude.ai/download
```

#### Bước 2: Xác Thực

```bash
# Chạy lệnh này để login
claude login

# Kiểm tra trạng thái
claude --version
```

#### Bước 3: Lưu API Key (Nếu Cần)

```bash
# Sử dụng credential manager của AMUX
python3 credential-manager.py add

# Chọn service: anthropic
# Nhập ANTHROPIC_API_KEY
```

#### Bước 4: Test Claude Code

```bash
# Tạo session test
claude --model sonnet "Hello, can you help me?"
```

### Cursor Agent

#### Bước 1: Cài Đặt Cursor

```bash
# Download và cài đặt Cursor
# https://cursor.sh/

# Cursor CLI sẽ tự động được install
```

#### Bước 2: Xác Thực Cursor

```bash
# Mở Cursor app và đăng nhập
# Settings -> Account -> Sign In
```

#### Bước 3: Kiểm Tra CLI

```bash
# Test Cursor agent CLI
agent --help

# Nếu không có command 'agent', tạo alias:
alias agent="/Applications/Cursor.app/Contents/Resources/app/bin/cursor-agent"
```

#### Bước 4: Cấu Hình API Keys Cho Cursor

Cursor có thể sử dụng:
- **OpenAI API Key** (cho GPT models)
- **Anthropic API Key** (cho Claude models)

```bash
# Add vào credential manager
python3 credential-manager.py add

# Service: openai hoặc anthropic
# Nhập key tương ứng
```

---

## 🎯 Các Chức Năng Chính

### 1. 📊 Dashboard Overview

**Truy cập:** https://localhost:8822

**Chức năng:**
- Xem tất cả sessions đang chạy
- Monitor real-time status của từng session
- Kanban board tổng quan
- System metrics (token usage, cost)
- Recent activity feed

### 2. 🤖 Session Management

#### Tạo Session Mới

**Qua Web UI:**
1. Click nút **"+ New Session"**
2. Điền thông tin:
   - **Name:** Tên session (vd: `backend-api`)
   - **Directory:** Đường dẫn project (vd: `/Users/you/projects/myapp`)
   - **Tool:** Chọn `claude_code` hoặc `cursor`
   - **Model:** Chọn model (sonnet/opus cho Claude, gpt-4 cho Cursor)
   - **Description:** Mô tả ngắn gọn
3. Click **"Create"**

**Qua API:**
```bash
curl -X POST https://localhost:8822/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backend-api",
    "dir": "/Users/you/projects/myapp",
    "tool": "claude_code",
    "desc": "Backend API development",
    "flags": "--model sonnet"
  }'
```

#### Start Session

**Web UI:** Click nút **"Start"** trên session card

**API:**
```bash
curl -X POST https://localhost:8822/api/sessions/backend-api/start
```

#### Gửi Message Đến Session

**Web UI:** 
1. Click vào session
2. Gõ message vào textarea
3. Click **"Send"** hoặc Ctrl+Enter

**API:**
```bash
curl -X POST https://localhost:8822/api/sessions/backend-api/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a REST API endpoint for user authentication"}'
```

#### Stop Session

**Web UI:** Click **"Stop"**

**API:**
```bash
curl -X POST https://localhost:8822/api/sessions/backend-api/stop
```

### 3. 📋 Kanban Board

**Truy cập:** Dashboard > Board tab

**Chức năng:**

#### Tạo Task Mới

```bash
curl -X POST https://localhost:8822/api/board \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user login API",
    "desc": "Create POST /api/auth/login endpoint with JWT",
    "status": "todo",
    "session": "backend-api"
  }'
```

#### Di Chuyển Task

Drag & drop trên UI hoặc:

```bash
curl -X PATCH https://localhost:8822/api/board/{task-id} \
  -H "Content-Type: application/json" \
  -d '{"status": "doing"}'
```

#### Link Task Với Session

```bash
curl -X PATCH https://localhost:8822/api/board/{task-id} \
  -H "Content-Type: application/json" \
  -d '{"session": "backend-api"}'
```

### 4. 🔄 Auto-Recovery

AMUX tự động xử lý các tình huống:

#### Auto-Approve Prompts

Khi Claude/Cursor hỏi "Press Y to approve":
```bash
# Enable auto-approve cho session
curl -X PATCH https://localhost:8822/api/sessions/backend-api/config \
  -H "Content-Type: application/json" \
  -d '{"auto_approve": true}'
```

#### Context Compaction

Khi context window đầy, tự động gọi `/compact`:
```bash
# Enable auto-compact
curl -X PATCH https://localhost:8822/api/sessions/backend-api/config \
  -H "Content-Type: application/json" \
  -d '{"auto_compact": true}'
```

#### Auto-Restart

Tự động restart session khi bị crash:
```bash
# Enable auto-restart
curl -X PATCH https://localhost:8822/api/sessions/backend-api/config \
  -H "Content-Type: application/json" \
  -d '{"auto_restart": true, "max_restarts": 3}'
```

### 5. 🌐 Browser Automation

**Chức năng:** Điều khiển trình duyệt với Claude vision + Playwright

#### Start Browser Agent

**Web UI:** Click **"Browser"** tab > **"Start Agent"**

**API:**
```bash
curl -X POST https://localhost:8822/api/browser/agent \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Go to gmail.com and check for unread emails from support@company.com",
    "start_url": "https://gmail.com",
    "max_steps": 20
  }'
```

#### Monitor Agent Status

```bash
curl https://localhost:8822/api/browser/agent/status
```

#### Download Recording

Sau khi agent hoàn thành:
```bash
# List recordings
curl https://localhost:8822/api/browser/recordings

# Download specific video
curl https://localhost:8822/api/browser/recordings/{recording-id} -o output.mp4
```

### 6. 🔌 MCP Server Configuration

**MCP (Model Context Protocol)** - Tích hợp thêm tools cho AI agents.

#### Xem Danh Sách MCP Servers

```bash
curl https://localhost:8822/api/mcp-configs
```

#### Thêm MCP Server Mới

**Edit file:** `~/.amux/mcp.json` hoặc project root `mcp.json`

```json
{
  "mcpServers": {
    "your-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "your-mcp-server"],
      "env": {
        "API_KEY": "${YOUR_API_KEY}"
      }
    }
  }
}
```

#### Link MCP Server Cho Session

```bash
curl -X POST https://localhost:8822/api/sessions/backend-api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_ids": ["your-server", "another-server"]
  }'
```

### 7. 📊 Reports & Token Usage

#### Xem Token Usage

**Web UI:** Dashboard > Reports tab

**API:**
```bash
# Token usage summary
curl https://localhost:8822/api/token-usage

# Chi tiết theo ngày
curl https://localhost:8822/api/token-usage?groupBy=day&days=7
```

#### Tạo Custom Report

```bash
curl -X POST https://localhost:8822/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Infrastructure Cost",
    "type": "infra-spend",
    "config": {
      "period": "week",
      "include_sessions": ["backend-api", "frontend-ui"]
    }
  }'
```

### 8. 📧 Email & Calendar Sync (macOS Only)

**Chức năng:** Tự động detect events từ email và sync vào Calendar.app

#### Enable Email Sync

```bash
# Edit ~/.amux/server.env
echo 'AMUX_EMAIL_SYNC_INTERVAL=900' >> ~/.amux/server.env
echo 'AMUX_EMAIL_LOOKBACK_DAYS=60' >> ~/.amux/server.env
echo 'AMUX_CALENDAR_NAME=AMUX Events' >> ~/.amux/server.env

# Restart server
touch amux-server.py
```

#### Manual Sync

```bash
curl -X POST https://localhost:8822/api/email/sync
```

#### View Detected Events

```bash
curl https://localhost:8822/api/email/events
```

### 9. 🗓️ iCal Feed Export

**Export board items với due dates sang Google Calendar**

#### Enable S3 Upload (Optional)

```bash
# Edit ~/.amux/server.env
echo 'AMUX_S3_BUCKET=your-bucket-name' >> ~/.amux/server.env
echo 'AMUX_S3_KEY=amux/calendar.ics' >> ~/.amux/server.env
echo 'AMUX_S3_REGION=us-east-1' >> ~/.amux/server.env

# Restart server
touch amux-server.py
```

#### Subscribe to Calendar

**Local URL:** `https://localhost:8822/api/calendar.ics`

**Public S3 URL:** `https://your-bucket.s3.region.amazonaws.com/amux/calendar.ics`

**Add to Google Calendar:**
1. Google Calendar > Settings > Add calendar > From URL
2. Paste URL
3. Click "Add calendar"

### 10. 📁 File Upload & Management

#### Upload File

```bash
curl -X POST https://localhost:8822/api/fs/upload \
  -F "file=@/path/to/document.pdf" \
  -F "path=/uploads/"
```

**Allowed formats:** `.png, .jpg, .jpeg, .gif, .webp, .pdf, .txt, .md, .csv, .json, .log`

**Max size:** 20MB

#### List Directory

```bash
curl https://localhost:8822/api/fs/list/uploads
```

#### Read File

```bash
curl https://localhost:8822/api/fs/read/uploads/document.pdf
```

---

## 🔧 Configuration Files

### `~/.amux/server.env`

Persistent server configuration:

```bash
# S3 iCal sync
AMUX_S3_BUCKET=your-bucket
AMUX_S3_KEY=amux/calendar.ics
AMUX_S3_REGION=us-east-1

# Email sync
AMUX_EMAIL_SYNC_INTERVAL=900
AMUX_EMAIL_LOOKBACK_DAYS=60
AMUX_CALENDAR_NAME=AMUX Events

# Server
CC_HOME=/Users/you/.amux
```

### `mcp.json`

MCP servers configuration (chia sẻ giữa local và cloud):

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

### Session Config: `~/.amux/sessions/{name}/session.env`

```bash
TOOL=claude_code
DIR=/Users/you/projects/myapp
FLAGS=--model sonnet
AUTO_APPROVE=true
AUTO_COMPACT=true
AUTO_RESTART=false
```

---

## 🎓 Workflow Examples

### Example 1: Phát Triển Full-Stack App

```bash
# 1. Tạo 2 sessions
curl -X POST https://localhost:8822/api/sessions \
  -d '{"name": "backend", "tool": "claude_code", "dir": "/app/backend"}'

curl -X POST https://localhost:8822/api/sessions \
  -d '{"name": "frontend", "tool": "cursor", "dir": "/app/frontend"}'

# 2. Start cả 2
curl -X POST https://localhost:8822/api/sessions/backend/start
curl -X POST https://localhost:8822/api/sessions/frontend/start

# 3. Tạo tasks
curl -X POST https://localhost:8822/api/board \
  -d '{"title": "Create REST API", "session": "backend", "status": "doing"}'

curl -X POST https://localhost:8822/api/board \
  -d '{"title": "Build React UI", "session": "frontend", "status": "doing"}'

# 4. Gửi instructions
curl -X POST https://localhost:8822/api/sessions/backend/send \
  -d '{"text": "Create Express.js REST API with MongoDB"}'

curl -X POST https://localhost:8822/api/sessions/frontend/send \
  -d '{"text": "Create React dashboard with API integration"}'

# 5. Monitor progress qua Dashboard
open https://localhost:8822
```

### Example 2: Testing & Browser Automation

```bash
# 1. Tạo test session
curl -X POST https://localhost:8822/api/sessions \
  -d '{"name": "e2e-tests", "tool": "claude_code", "dir": "/app/tests"}'

curl -X POST https://localhost:8822/api/sessions/e2e-tests/start

# 2. Generate test code
curl -X POST https://localhost:8822/api/sessions/e2e-tests/send \
  -d '{"text": "Create Playwright tests for login flow"}'

# 3. Run browser agent to manually test
curl -X POST https://localhost:8822/api/browser/agent \
  -d '{
    "task": "Test login flow: go to app, click login, enter test credentials, verify dashboard loads",
    "start_url": "http://localhost:3000"
  }'

# 4. Download recording
curl https://localhost:8822/api/browser/recordings/latest -o test-recording.mp4
```

### Example 3: 24/7 Development với Auto-Recovery

```bash
# Setup session với full auto-recovery
curl -X POST https://localhost:8822/api/sessions \
  -d '{
    "name": "overnight-dev",
    "tool": "claude_code",
    "dir": "/app",
    "flags": "--model sonnet-4"
  }'

curl -X PATCH https://localhost:8822/api/sessions/overnight-dev/config \
  -d '{
    "auto_approve": true,
    "auto_compact": true,
    "auto_restart": true,
    "max_restarts": 5
  }'

curl -X POST https://localhost:8822/api/sessions/overnight-dev/start

# Gửi large task
curl -X POST https://localhost:8822/api/sessions/overnight-dev/send \
  -d '{"text": "Implement complete user management system: CRUD APIs, auth middleware, database migrations, unit tests, and API documentation"}'

# Session sẽ tự động:
# - Approve all prompts
# - Compact context khi cần
# - Restart nếu crash
# - Log mọi thứ vào ~/.amux/logs/overnight-dev.log
```

---

## 🐛 Troubleshooting

### Server Không Start

```bash
# Kiểm tra port đã được dùng chưa
lsof -i :8822

# Restart server
pkill -f amux-server.py
python3 amux-server.py
```

### Session Không Start

```bash
# Kiểm tra tmux
tmux ls

# Xem logs
tail -f ~/.amux/logs/{session-name}.log
tail -f ~/.amux/logs/server.log

# Test CLI trực tiếp
claude --help
agent --help
```

### Claude Code: API Key Issues

```bash
# Re-login
claude logout
claude login

# Hoặc set ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=sk-ant-...
python3 credential-manager.py add
```

### Cursor: Command Not Found

```bash
# Add Cursor CLI to PATH
echo 'export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Hoặc tạo alias
alias agent="/Applications/Cursor.app/Contents/Resources/app/bin/cursor-agent"
```

### Browser Automation Fails

```bash
# Install Playwright browsers
npx playwright install chromium

# Kiểm tra Playwright
npx playwright --version

# Check ffmpeg (for video conversion)
which ffmpeg
brew install ffmpeg  # if not found
```

---

## 📚 Advanced Topics

### Custom AI Tool Integration

Extend `AITool` class trong `amux-server.py`:

```python
class YourCustomTool(AITool):
    def __init__(self):
        super().__init__("your_tool")
    
    def get_command(self, flags, session_flag, default_flags, extra_flags):
        return f"your-cli-command {flags}"
    
    def detect_status(self, raw_output):
        # Parse terminal output
        if "Working..." in raw_output:
            return "working"
        return "idle"
    
    def get_home_dir(self):
        return Path.home() / ".your-tool"

# Register
_AI_TOOLS["your_tool"] = YourCustomTool()
```

### Cloud Deployment (GCP)

```bash
cd cloud/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project

terraform init
terraform apply

# Deploy
./deploy.sh
```

### Organization Mode

```bash
# Create organization
curl -X POST https://localhost:8822/api/org \
  -d '{"name": "My Team", "owner_email": "you@company.com"}'

# Invite members
curl -X POST https://localhost:8822/api/org/invite \
  -d '{"email": "teammate@company.com", "role": "developer"}'
```

---

## 🔗 Resources

- **Documentation:** [README.md](README.md)
- **API Reference:** [API-REFERENCE.md](API-REFERENCE.md)
- **MCP Guide:** [MCP-README.md](MCP-README.md)
- **Credentials:** [CREDENTIALS.md](CREDENTIALS.md)
- **Getting API Keys:** [GETTING-API-KEYS.md](GETTING-API-KEYS.md)

## 🆘 Support

- **Issues:** https://github.com/your-repo/amux/issues
- **Discussions:** https://github.com/your-repo/amux/discussions
- **Email:** support@amux.dev

---

**Happy Coding with AMUX! 🚀**
