# AMUX Credential Management

**Hệ thống quản lý credentials tập trung cho các AI tools (Claude Code, Cursor, Gemini, Aider)**

---

## 🎯 Vấn đề được giải quyết

Khi chạy nhiều session AMUX song song, mỗi AI tool cần authenticate. Vấn đề:
- **Cursor CLI**: Cần login và share authInfo across sessions
- **Claude Code**: Cần ANTHROPIC_API_KEY hoặc session authentication  
- **Gemini**: Cần GOOGLE_API_KEY
- **Aider**: Cần OPENAI_API_KEY hoặc ANTHROPIC_API_KEY

**Giải pháp:** Credential Manager tập trung lưu trữ và tự động inject credentials vào mọi session.

---

## 🔐 Features

### 1. **Encrypted Storage**
- Credentials được mã hóa với Fernet (AES)
- Key được derive từ machine-specific ID
- File permissions: 0600 (owner read/write only)
- Location: `~/.amux/credentials/credentials.enc`

### 2. **Auto-Detection**
- Tự động detect credentials hiện có từ:
  - Config files (`~/.cursor/cli-config.json`, `~/.claude/`)
  - Environment variables (`ANTHROPIC_API_KEY`, etc.)
  - OAuth tokens

### 3. **Auto-Injection**
- Credentials tự động được inject vào sessions khi start
- Via tmux environment variables (`-e` flag)
- Tool-specific env var mapping

### 4. **Multi-Tool Support**
- ✅ **Claude Code**: `anthropic_api_key`, `session_token`
- ✅ **Cursor**: `oauth`, `session` (from config file)
- ✅ **Gemini**: `google_api_key`
- ✅ **Aider**: `openai_api_key`, `anthropic_api_key`

---

## 📋 Usage

### **1. Check current status**

```bash
python3 credential-manager.py status
```

**Output:**
```
======================================================================
🔐 AMUX Credential Manager Status
======================================================================

📦 Claude Code (claude_code)
----------------------------------------------------------------------
   ⚠️  No credentials stored
   🔍 Detected: session
   💡 Supported: anthropic_api_key, session_token

📦 Cursor (cursor)
----------------------------------------------------------------------
   ⚠️  No credentials stored
   🔍 Detected: config_file
      Email: thao.tranngoc3@vib.com.vn
      Team: VIB ADC BTS
      Config: /Users/sang.duongtan/.cursor/cli-config.json
   💡 Supported: oauth, session
```

---

### **2. Detect existing credentials**

```bash
python3 credential-manager.py detect
```

Finds credentials from:
- `~/.cursor/cli-config.json` → Cursor OAuth
- `~/.claude/` → Claude session
- Environment variables

---

### **3. Store API key**

```bash
# Claude Code
python3 credential-manager.py set claude_code anthropic_api_key sk-ant-xxx

# Gemini
python3 credential-manager.py set gemini google_api_key AIzaxxxx

# Aider (OpenAI)
python3 credential-manager.py set aider openai_api_key sk-xxx

# Aider (Anthropic)
python3 credential-manager.py set aider anthropic_api_key sk-ant-xxx
```

---

### **4. Import from environment**

```bash
# If you have ANTHROPIC_API_KEY in your shell:
export ANTHROPIC_API_KEY=sk-ant-xxxxx
python3 credential-manager.py import claude_code

# Or GOOGLE_API_KEY:
export GOOGLE_API_KEY=AIzaxxxx
python3 credential-manager.py import gemini
```

---

### **5. View stored credentials**

```bash
python3 credential-manager.py get claude_code anthropic_api_key
```

---

### **6. Delete credential**

```bash
python3 credential-manager.py delete claude_code anthropic_api_key
```

---

## 🔄 How Credentials Flow Into Sessions

### **Automatic Injection Flow:**

```
1. User creates session: POST /api/sessions
   └─> name: "api-worker"
   └─> tool: "claude_code"

2. AMUX loads credentials:
   └─> CredentialManager.get_env_vars("claude_code")
   └─> Returns: {"ANTHROPIC_API_KEY": "sk-ant-xxx"}

3. AMUX starts tmux session with env vars:
   └─> tmux new-session -d -s api-worker \
       -e ANTHROPIC_API_KEY=sk-ant-xxx \
       -e AMUX_SESSION=api-worker \
       claude

4. Claude Code starts with auth:
   └─> ANTHROPIC_API_KEY available in environment
   └─> Authenticates successfully
   └─> No login prompt needed ✅
```

---

## 🧪 Testing

### **Test 1: Verify detection**

```bash
$ python3 credential-manager.py detect

{
  "cursor": {
    "found": true,
    "auth_method": "config_file",
    "email": "thao.tranngoc3@vib.com.vn",
    "team": "VIB ADC BTS"
  },
  "claude_code": {
    "found": true,
    "auth_method": "session"
  }
}
```

✅ **Cursor đã login** → Config file tồn tại  
✅ **Claude Code initialized** → Session active

---

### **Test 2: Store and retrieve**

```bash
# Store
$ python3 credential-manager.py set test_tool test_key test_value
✅ Credential 'test_key' saved for test_tool

# Retrieve
$ python3 credential-manager.py get test_tool test_key
test_tool.test_key = test_value

# Delete
$ python3 credential-manager.py delete test_tool test_key
✅ Credential 'test_key' deleted for test_tool
```

---

### **Test 3: Session injection (integrated)**

```bash
# Create session with credential injection
$ curl -X POST https://localhost:8822/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "test-creds", "dir": "~/", "tool": "claude_code"}'

# Start session → credentials injected
$ curl -X POST https://localhost:8822/api/sessions/test-creds/start

# Check server logs:
[credential] Injected 1 env vars for claude_code  ← ✅ Success!
```

---

## 🔧 Tool-Specific Notes

### **Cursor**

- **Auth method:** OAuth via config file
- **Config location:** `~/.cursor/cli-config.json`
- **Detection:** Automatic (checks `authInfo` object)
- **Session sharing:** Config file in `~/` accessible to all sessions ✅
- **No API key needed** if already logged in via Cursor app

**Setup:**
```bash
# Login once (in Cursor app or CLI):
cursor --login

# Verify:
python3 credential-manager.py status
# Should show "Detected: config_file" with your email
```

---

### **Claude Code**

- **Auth method:** Session token OR API key
- **Detection:** Checks `~/.claude/` directory
- **Env var:** `ANTHROPIC_API_KEY` (if using API key)
- **Session sharing:** Directory in `~/` accessible to all sessions ✅

**Setup (Option 1 - Session auth, recommended):**
```bash
# Run Claude Code once to initialize:
claude

# It will authenticate and save session
# No additional config needed
```

**Setup (Option 2 - API key):**
```bash
# Store API key:
python3 credential-manager.py set claude_code anthropic_api_key sk-ant-xxx

# Now all sessions will use this key
```

---

### **Gemini CLI**

- **Auth method:** API key
- **Env var:** `GOOGLE_API_KEY` or `GEMINI_API_KEY`

**Setup:**
```bash
# Get API key from https://makersuite.google.com/app/apikey
# Store it:
python3 credential-manager.py set gemini google_api_key AIzaxxxx

# Or import from environment:
export GOOGLE_API_KEY=AIzaxxxx
python3 credential-manager.py import gemini
```

---

### **Aider**

- **Auth method:** API keys (OpenAI or Anthropic)
- **Env vars:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Config:** Can also use `~/.aider.conf.yml`

**Setup:**
```bash
# For OpenAI:
python3 credential-manager.py set aider openai_api_key sk-xxx

# For Anthropic:
python3 credential-manager.py set aider anthropic_api_key sk-ant-xxx

# Aider will use whichever is available
```

---

## 🔒 Security

### **Encryption:**
- **Algorithm:** Fernet (AES-128 in CBC mode)
- **Key derivation:** PBKDF2-HMAC-SHA256 with 100k iterations
- **Salt:** Fixed salt + machine ID for key derivation
- **File permissions:** 0600 (owner only)

### **Best Practices:**
1. ✅ **Never commit credentials to git**
2. ✅ **Use environment variables for temporary keys**
3. ✅ **Rotate API keys periodically**
4. ✅ **Store keys only on trusted machines**
5. ✅ **Use session auth when possible** (Cursor, Claude)

---

## 📁 Files

| File | Purpose |
|------|---------|
| `credential-manager.py` | Standalone CLI tool (448 lines) |
| `~/.amux/credentials/credentials.enc` | Encrypted credential storage |
| `~/.amux/credentials/.key` | Encryption key (machine-specific) |
| `~/.cursor/cli-config.json` | Cursor config (auto-detected) |
| `~/.claude/` | Claude Code config (auto-detected) |

---

## 🎓 Integration with AMUX

Credentials are automatically injected when `amux-server.py` starts sessions:

```python
# In amux-server.py start_session():
if _CRED_MANAGER:
    cred_env = _CRED_MANAGER.get_env_vars(tool_name)
    for env_key, env_val in cred_env.items():
        tmux_cmd.extend(["-e", f"{env_key}={env_val}"])
```

**What this means:**
- ✅ Once you store a credential, ALL sessions of that tool get it
- ✅ No need to configure each session individually
- ✅ Works for both local and cloud deployments
- ✅ Secure: credentials never logged or exposed

---

## 🚀 Quick Start Guide

### **For Cursor users:**

```bash
# 1. Verify Cursor is logged in:
cursor --version
python3 credential-manager.py status

# 2. You should see "Detected: config_file" with your email
# 3. Done! All AMUX sessions can now use Cursor
```

---

### **For Claude Code users:**

```bash
# Option A: Session auth (recommended)
# 1. Run Claude once to initialize:
claude
# 2. Verify:
python3 credential-manager.py status
# Should show "Detected: session"

# Option B: API key
# 1. Store your Anthropic API key:
python3 credential-manager.py set claude_code anthropic_api_key sk-ant-xxx
# 2. Done! All sessions will use this key
```

---

### **For multi-tool orchestration:**

```bash
# Setup all tools:
python3 credential-manager.py set claude_code anthropic_api_key sk-ant-xxx
python3 credential-manager.py set gemini google_api_key AIzaxxxx
python3 credential-manager.py set aider openai_api_key sk-xxx

# Verify:
python3 credential-manager.py status

# Create orchestrated session:
curl -X POST https://localhost:8822/api/sessions \
  -d '{"name": "backend", "tool": "claude_code", "dir": "~/project"}'

curl -X POST https://localhost:8822/api/sessions \
  -d '{"name": "frontend", "tool": "cursor", "dir": "~/project"}'

# All sessions auto-authenticated! ✅
```

---

## ❓ FAQ

**Q: Do I need to store credentials if I'm already logged in to Cursor?**  
A: No! Cursor uses config file auth. If you're logged in via the Cursor app, all AMUX sessions can access it automatically.

**Q: What if I don't have an API key for Claude?**  
A: Claude Code supports session auth (no API key). Just run `claude` once to initialize. It will authenticate via your Anthropic account.

**Q: Can I use different credentials for different sessions?**  
A: Not yet. Currently, all sessions of the same tool share one credential. This is planned for future versions.

**Q: Are credentials synced across machines?**  
A: No. Credentials are machine-specific (encrypted with machine ID). You need to set them up on each machine.

**Q: What happens if credentials are invalid?**  
A: The AI tool will fail to start and show an auth error in the session output. Check credentials with `python3 credential-manager.py status`.

---

## 🔜 Roadmap

- [ ] **UI for credential management** in dashboard
- [ ] **Per-session credential override** (different keys per session)
- [ ] **Credential sync** via encrypted cloud storage
- [ ] **Credential rotation** (automatic key refresh)
- [ ] **OAuth flow** for tools that support it
- [ ] **Credential health check** (test if keys are valid)
- [ ] **Usage tracking** (API quota monitoring)

---

**Status:** ✅ Production ready  
**Version:** 1.0  
**Last Updated:** March 4, 2026
