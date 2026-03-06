# Gemini CLI Integration Guide

**Google Gemini CLI support in AMUX** - Sử dụng Gemini 2.0 models thông qua AMUX sessions.

---

## ✅ Tính năng đã hỗ trợ

- ✅ **GeminiTool class** - AI tool integration với command building
- ✅ **Credential management** - Tự động inject `GOOGLE_API_KEY` hoặc `GEMINI_API_KEY`
- ✅ **Status detection** - Phát hiện trạng thái: idle, working, needs_input, error
- ✅ **Model selection** - Default: `gemini-2.0-flash-exp`
- ✅ **Auth type** - Auto-inject `--auth-type gemini-api-key`
- ✅ **YOLO mode** - Support `--yolo` flag

---

## 🚀 Cách sử dụng

### 1. Cài đặt Gemini CLI

```bash
npm install -g @google/generative-ai-cli
# hoặc
yarn global add @google/generative-ai-cli
```

Verify installation:
```bash
gemini --version
```

### 2. Thêm API Key

**Option A: Qua Credential Manager (Recommended)**
```bash
python3 credential-manager.py set gemini google_api_key AIzaxxxx...
```

**Option B: Qua Environment Variable**
```bash
export GOOGLE_API_KEY="AIzaxxxx..."
# hoặc
export GEMINI_API_KEY="AIzaxxxx..."
```

**Option C: Qua server.env**
```bash
# ~/.amux/server.env
GOOGLE_API_KEY=AIzaxxxx...
```

Verify credentials:
```bash
python3 credential-manager.py status
```

### 3. Tạo session với Gemini

**Via Dashboard:**
1. Mở https://localhost:8822
2. Click "+ New Session"
3. Điền:
   - Name: `gemini-test`
   - Directory: `/path/to/project`
   - Tool: `gemini`
   - Model (optional): `gemini-2.0-flash-thinking-exp`
   - YOLO (optional): ✅ (auto-approve)
4. Click "Create"

**Via API:**
```bash
curl -k -X POST https://localhost:8822/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gemini-test",
    "dir": "/Users/you/project",
    "tool": "gemini",
    "yolo": true,
    "model": "gemini-2.0-flash-exp"
  }'
```

### 4. Start session

**Via Dashboard:**
- Click "▶ Start" button trên session card

**Via API:**
```bash
curl -k -X POST https://localhost:8822/api/sessions/gemini-test/start
```

### 5. Gửi prompt

**Via Dashboard:**
- Click vào session card
- Nhập message: "Create a hello world Express.js server"
- Enter

**Via API:**
```bash
curl -k -X POST https://localhost:8822/api/sessions/gemini-test/send \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Create a hello world Express.js server"
  }'
```

### 6. Monitor output

**Via Dashboard:**
- Session card tự động update output real-time

**Via API:**
```bash
curl -k https://localhost:8822/api/sessions/gemini-test/peek?lines=100
```

---

## 🔧 Advanced Configuration

### Custom model

```bash
# In session creation
{
  "tool": "gemini",
  "model": "gemini-2.0-flash-thinking-exp"
}
```

### Custom flags

```bash
# Enable debug mode
{
  "tool": "gemini",
  "flags": "--debug --yolo"
}
```

### Sandbox mode

```bash
{
  "tool": "gemini",
  "flags": "--sandbox"
}
```

---

## 🧪 Testing

Chạy integration test:
```bash
python3 test-gemini-integration.py
```

Expected output:
```
✅ 'gemini' found in _AI_TOOLS registry
✅ Got Gemini tool: gemini
✅ Basic command: gemini --auth-type gemini-api-key --model gemini-2.0-flash-exp
✅ All Gemini CLI integration tests passed!
```

---

## 📋 Available Models

Gemini CLI hỗ trợ các models sau (thay đổi qua `--model` flag):

| Model | Description |
|-------|-------------|
| `gemini-2.0-flash-exp` | Fast, efficient (default) |
| `gemini-2.0-flash-thinking-exp` | Advanced reasoning |
| `gemini-1.5-pro` | Production-ready |
| `gemini-1.5-flash` | Fast, cost-effective |

---

## 🐛 Troubleshooting

### "Error: Missing API key"
```bash
# Check credentials
python3 credential-manager.py status

# Add API key
python3 credential-manager.py set gemini google_api_key AIzaxxxx
```

### "Command not found: gemini"
```bash
# Install Gemini CLI
npm install -g @google/generative-ai-cli

# Verify
which gemini
```

### Session không start được
```bash
# Check logs
curl -k https://localhost:8822/api/sessions/gemini-test/peek?lines=200

# Check if tool is registered
python3 test-gemini-integration.py
```

### Credential không được inject
```bash
# Check AMUX server logs (terminal chạy amux-server.py)
# Tìm dòng:
[credential] Injected X env vars for gemini
```

---

## 🔗 References

- **Gemini CLI**: https://www.npmjs.com/package/@google/generative-ai-cli
- **Gemini API Keys**: https://aistudio.google.com/app/apikey
- **AMUX Credentials**: [CREDENTIALS.md](CREDENTIALS.md)
- **Integration Test**: [test-gemini-integration.py](test-gemini-integration.py)

---

## 💡 Tips

### Multi-account support
Gemini CLI hiện chưa hỗ trợ session isolation như Cursor. Nếu cần dùng nhiều API keys:
```bash
# Set different keys per session via flags
{
  "tool": "gemini",
  "flags": "--auth-type gemini-api-key"
  # Key được inject từ credential manager
}
```

### Performance
- `gemini-2.0-flash-exp` nhanh nhất, phù hợp cho iteration-intensive tasks
- `gemini-2.0-flash-thinking-exp` chậm hơn nhưng reasoning tốt hơn

### Cost optimization
Gemini 2.0 Flash:
- Free tier: 15 RPM (requests per minute)
- Paid: $0.075 / 1M input tokens, $0.30 / 1M output tokens

---

## 📝 Changelog

- **2026-03-06**: Initial Gemini CLI integration
  - Added GeminiTool class
  - Credential manager support
  - Documentation and tests
