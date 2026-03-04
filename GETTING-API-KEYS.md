# Hướng Dẫn Lấy API Keys và Authentication

## � Auto-Detect (Khuyến Nghị)

**Cách nhanh nhất:** AMUX có thể tự động tìm credentials đã có sẵn trên máy!

### Cách sử dụng:

1. Mở AMUX dashboard → tab **Credentials**
2. Click nút **🔍 Auto-Detect** (góc trên bên phải)
3. AMUX sẽ quét và tìm:
   - **Cursor**: OAuth token từ `~/.cursor/cli-config.json`
   - **Claude Code**: API key từ env var `ANTHROPIC_API_KEY`
   - **Gemini**: API key từ env var `GOOGLE_API_KEY` hoặc `GEMINI_API_KEY`
   - **Aider**: API key từ env var `OPENAI_API_KEY`
4. Chọn credentials muốn import → Click **Import Selected**

### Khi nào cần Manual Setup:

- Chưa cài AI tool nào
- Muốn dùng account khác
- Config files không có token (chưa login)
- Cần setup multi-account với load balancing

---

## �📋 Tổng Quan

AMUX hỗ trợ nhiều phương thức authentication cho các AI tools khác nhau:

| Tool | Auth Types | Difficulty |
|------|-----------|-----------|
| Claude Code | API Key, Session Token | ⭐ Easy |
| Cursor | OAuth Token, Session | ⭐⭐ Medium |
| Gemini | API Key | ⭐ Easy |
| Aider | API Keys (OpenAI/Anthropic) | ⭐ Easy |

---

## 🔑 Claude Code / Anthropic

### Option 1: API Key (Recommended)

1. Đăng nhập vào [Anthropic Console](https://console.anthropic.com/)
2. Click **API Keys** trong sidebar
3. Click **Create Key**
4. Đặt tên cho key (e.g., "amux-production")
5. Copy API key (bắt đầu bằng `sk-ant-api03-...`)
6. Lưu key vào AMUX:
   - Mở dashboard → tab **Credentials**
   - Click **+ Add Account**
   - Tool: **Claude Code**
   - Account ID: email hoặc tên (e.g., `work-account`)
   - API Key: paste key vừa copy
   - Click **Save**

**Cost:** $3-4/hour cho parallel agents với Sonnet 3.5

### Option 2: Session Token (Advanced)

Sử dụng session token từ browser Claude.ai:

1. Đăng nhập vào [claude.ai](https://claude.ai)
2. Mở DevTools (F12)
3. Tab **Application** → **Cookies** → `https://claude.ai`
4. Copy giá trị của cookie `sessionKey`
5. Trong AMUX dashboard:
   - Tool: **Claude Code**
   - Account ID: `session-account`
   - Session Token: paste cookie value
   - Click **Save**

**⚠️ Warning:** Session tokens expire sau 30 ngày

---

## 🖱️ Cursor

### Option 1: OAuth Token via Browser (Easiest) 🌟

AMUX hỗ trợ **browser-based OAuth login** giống Cursor CLI:

1. Mở AMUX dashboard → tab **Credentials**
2. Click **+ Add Account** → Tool: **Cursor**
3. Auth Type: **OAuth Token**
4. Click nút **🌐 Login via Browser**
5. Trong modal popup, click **Open Cursor Login**
6. Login vào Cursor trong browser
7. Sau khi login, chạy lệnh extract token:
   ```bash
   cat ~/.cursor/cli-config.json | grep -o '"token":"[^"]*"' | cut -d'"' -f4
   ```
8. Copy token và paste vào form → Click **Save**

### Option 2: Auto-Detection

AMUX tự động detect từ:
```bash
~/.cursor/cli-config.json
```

**Steps:**
1. Đảm bảo đã login vào Cursor IDE ít nhất 1 lần
2. AMUX dashboard → tab **Credentials**
3. Click **🔍 Auto-Detect**
4. Chọn Cursor OAuth token → Click **Import Selected**

### Option 3: Manual from CLI Config

**Manual Setup:**

1. Đăng nhập vào Cursor IDE
2. Click **Settings** → **Account**
3. Copy OAuth token từ settings
4. Hoặc lấy từ CLI config:
   ```bash
   cat ~/.cursor/cli-config.json
   ```
5. Trong AMUX dashboard:
   - Tool: **Cursor**
   - Account ID: email của bạn
   - OAuth Token: paste token
   - Click **Save**

### Option 2: Session Token

1. Đăng nhập vào [cursor.sh](https://cursor.sh)
2. Mở DevTools (F12)
3. Tab **Network** → refresh page
4. Tìm request có header `Authorization: Bearer ...`
5. Copy bearer token
6. Lưu vào AMUX như OAuth token

**⚠️ Note:** Cursor tokens thường có TTL 90 ngày

---

## 🌟 Google Gemini

### Lấy API Key

1. Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Get API Key**
3. Chọn hoặc tạo Google Cloud project
4. Click **Create API Key**
5. Copy key (bắt đầu bằng `AIza...`)
6. Lưu vào AMUX:
   - Tool: **Gemini**
   - Account ID: `gemini-main`
   - API Key: paste key
   - Click **Save**

**Free Tier:** 60 requests/minute, phù hợp cho testing

---

## 🛠️ Aider

### OpenAI API Key

1. Đăng nhập vào [OpenAI Platform](https://platform.openai.com/)
2. Click **API Keys** → **Create new secret key**
3. Đặt tên cho key
4. Copy key (bắt đầu bằng `sk-...`)
5. Lưu vào AMUX:
   - Tool: **Aider**
   - Account ID: `openai-account`
   - API Key (OpenAI): paste key
   - Click **Save**

### Anthropic API Key

Tương tự như Claude Code section ở trên.

**⚠️ Note:** Aider có thể dùng cả hai providers, config trong dashboard.

---

## 🔄 Load Balancing

**Tại sao cần nhiều accounts?**

- Tránh rate limits (mỗi account có quota riêng)
- Phân tải requests khi chạy nhiều agents
- Dự phòng khi một account bị throttle

**Ví dụ Setup:**

```
Claude Code (Load Balancing: Round Robin)
├── work-account (sk-ant-api03-xxx...)
├── personal-account (sk-ant-api03-yyy...)
└── backup-account (sk-ant-api03-zzz...)
```

Mỗi session sẽ tự động pick account theo strategy:
- **Round Robin:** Xoay vòng lần lượt
- **Least Used:** Chọn account ít dùng nhất
- **Random:** Random mỗi request

---

## 🔒 Security Best Practices

### API Key Safety

```bash
# Credentials được encrypt với Fernet (AES-128)
~/.amux/credentials/credentials.enc  # Encrypted storage
~/.amux/credentials/.key            # Machine-specific key
```

**Permissions:**
```bash
chmod 600 ~/.amux/credentials/*
```

### Multiple Accounts

```
DON'T: Share API keys giữa nhiều người
DO: Mỗi người có account riêng trong AMUX

DON'T: Commit keys vào git
DO: Dùng AMUX credential manager

DON'T: Để keys trong .env files
DO: Lưu trong AMUX dashboard (encrypted)
```

---

## 🧪 Testing Credentials

### Test Claude API Key

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-3-5-20241022",
    "max_tokens": 20,
    "messages": [{"role": "user", "content": "hi"}]
  }'
```

### Test OpenAI API Key

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 20
  }'
```

### Test Gemini API Key

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"hi"}]}]}'
```

---

## ❓ Troubleshooting

### "API key invalid"

- Kiểm tra key không có dấu space đầu/cuối
- Verify key chưa expired trong provider console
- Test key bằng curl commands ở trên

### "Rate limit exceeded"

- Enable **Load Balancing** trong AMUX
- Add thêm accounts để chia tải
- Check quota limits trong provider dashboard

### "Session token expired"

- Session tokens thường expire sau 30-90 ngày
- Re-login vào provider và lấy token mới
- Consider switching sang API keys (không expire)

### "No credentials found"

- Check server logs: `Warning: credential-manager not available`
- Verify file exists: `ls ~/.amux/credentials/credentials.enc`
- Re-add credentials trong dashboard

---

## 📞 Support

Nếu gặp vấn đề:

1. Check server logs: `python3 amux-server.py`
2. Test API endpoint: `curl -sk https://localhost:8822/api/credentials`
3. Verify file permissions: `ls -la ~/.amux/credentials/`
4. Open issue on GitHub với logs

---

## 🚀 Next Steps

After setting up credentials:

1. ✅ Test với 1 session trước: `amux start test-session`
2. ✅ Verify trong dashboard: session card hiển thị đúng tool
3. ✅ Enable load balancing nếu có nhiều accounts
4. ✅ Monitor usage trong **Credentials** tab

**Happy coding with AMUX!** 🎉
