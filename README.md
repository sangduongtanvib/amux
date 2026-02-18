# cmux — Claude Code Multiplexer

Manage multiple Claude Code sessions from your terminal or phone. cmux wraps tmux to let you run, monitor, and control headless Claude Code instances from a single dashboard — locally or over the network as a PWA.

## Install

```bash
git clone <repo> && cd cmux
./install.sh
```

Requires `tmux` and `python3`. Installs `cmux` (and alias `cc`) to `/usr/local/bin`.

## Quick Start

```bash
# Register a session
cmux register myproject --dir ~/Dev/myproject --yolo

# Start it headless
cmux start myproject

# Open the terminal dashboard
cmux

# Or serve the web dashboard
cmux serve
```

## CLI Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `cmux` | | Interactive terminal dashboard |
| `cmux register <name> --dir <path>` | `reg` | Register a new session |
| `cmux start <name>` | | Start a session headless |
| `cmux stop <name>` | `kill` | Stop a running session |
| `cmux attach <name>` | `a` | Attach to a session's tmux |
| `cmux peek <name> [lines]` | `p` | View session output without attaching |
| `cmux send <name> <text>` | | Send text/command to a session |
| `cmux exec <name> [flags] -- <prompt>` | `run` | Register, start, and send a prompt in one shot |
| `cmux ls` | `list` | List all sessions |
| `cmux info <name>` | | Show session details |
| `cmux rm <name>` | `del` | Remove a session |
| `cmux start-all` | | Start all registered sessions |
| `cmux stop-all` | | Stop all running sessions |
| `cmux defaults` | `config` | Manage default flags |
| `cmux serve` | `web` | Start the web dashboard |

Session names support prefix matching — `cmux attach my` resolves to `myproject` if unambiguous.

## Claude Code Flags

Pass any Claude Code flag when registering:

```bash
cmux register api --dir ~/Dev/api --yolo --model sonnet
cmux register fast --dir ~/Dev/fast --model haiku --dangerously-skip-permissions
```

## Web Dashboard (PWA)

`cmux serve` starts an HTTPS server (default port 8822) that serves a full-featured dashboard:

```bash
cmux serve           # serves on :8822
cmux serve 9000      # custom port
```

### Features

- **Session cards** — view all sessions with live status (working / needs input / idle), preview lines, model badge, and tags
- **Expand cards** — single tap to expand, see token stats, send commands, quick-action chips
- **Peek mode** — double-tap card header or click preview lines to open full scrollback output with auto-refresh
- **Send commands** — input with `/` slash-command autocomplete, or use quick chips (`/compact`, `/status`, `/cost`, Ctrl-C, etc.)
- **Search & filter** — search sessions by name/dir/desc/tags, filter by tag
- **Session management** — create, start, stop, rename, delete, duplicate, clone & continue
- **Model switching** — change model from the menu, automatically sends `/model` to running sessions
- **YOLO mode** — toggle `--dangerously-skip-permissions` per session
- **Pin sessions** — pin important sessions to the top
- **Descriptions & tags** — organize sessions with metadata
- **File preview** — clickable file paths in peek output open syntax-highlighted previews
- **Peek search** — find text within peek output with match highlighting and count
- **Peek command bar** — send commands directly from peek mode with slash autocomplete
- **Connect tmux sessions** — adopt existing tmux sessions not created by cmux

### Board (Kanban)

A built-in kanban board for task tracking across sessions:

- **Columns** — To Do, In Progress, Done with drag-and-drop between columns
- **Session linking** — associate board items with sessions; click session badges to filter
- **Tags** — add tags to items, click tag chips to filter the board
- **Search** — full-text search across board item titles and descriptions
- **Issue keys** — auto-generated keys based on session name (e.g., VAN-1, CMUX-3)
- **Clear done** — bulk-clear completed items
- **REST API** — `GET/POST/PATCH/DELETE /api/board` for external integrations

```bash
# Add an item via curl
curl -sk -X POST -H 'Content-Type: application/json' \
  -d '{"title":"Fix auth bug","status":"todo","session":"myproject"}' \
  https://localhost:8822/api/board

# List all items
curl -sk https://localhost:8822/api/board
```

Board data is stored in `~/.cmux/board.json`.

### Real-Time Updates (SSE)

The dashboard uses Server-Sent Events for push-based updates instead of polling:

- **`GET /api/events`** — SSE stream that pushes session and board changes every 2s
- **Shared server cache** — multiple browser tabs share cached subprocess results (2s TTL) to avoid redundant work
- **Heartbeat** — server sends heartbeats every 15s to keep connections alive
- **Auto-fallback** — if SSE fails 3 times, the client falls back to 5s polling
- **Reconnection** — SSE automatically reconnects when coming back online

```bash
# Test the SSE stream directly
curl -sk -N https://localhost:8822/api/events
# Outputs: data: {"type":"sessions","payload":[...]}\n\n
```

### Offline / PWA

Install as a PWA on iOS or Android for app-like access. The dashboard is designed for offline-first use:

- **Service worker** — caches the app shell for instant loads, cache-first strategy
- **3-layer persistence** — Service Worker Cache API, localStorage (full HTML), and IndexedDB
- **Offline queue** — commands sent while offline are queued and replayed on reconnect
- **Background Sync** — on Chrome/Edge, the service worker replays queued operations automatically when connectivity returns, even if the tab is closed
- **Draft sessions** — create sessions offline, auto-synced when back online
- **Cached peek** — peek output stored in IndexedDB for offline browsing
- **Sync banner** — live progress display when replaying queued operations on reconnect
- **Connection indicator** — green "Live" / red "Offline (N pending)" pill in the header

Background Sync is Chrome/Edge only. Safari and Firefox fall back to the existing sync banner on reconnect.

### Token Stats

Click the "cmux" logo to open the about modal with daily token usage:

- Total tokens across all Claude Code sessions
- Per-session breakdown with bar charts
- cmux-managed vs external session split
- Reset button to zero counters for the day

### HTTPS & Tailscale

The server auto-generates TLS certs for HTTPS, required for PWA/service worker on non-localhost. It tries in order:

1. **Tailscale** — real Let's Encrypt cert via `tailscale cert`, trusted everywhere with zero setup
2. **mkcert** — locally-trusted CA, no browser warnings on the same machine
3. **Self-signed** — fallback via openssl, requires trusting the cert manually

```bash
# With Tailscale (recommended for phone access)
cmux serve
# → https://your-machine.tailnet-name.ts.net:8822

# With mkcert
brew install mkcert && mkcert -install
cmux serve
# → https://localhost:8822

# Disable TLS
cmux serve --no-tls
```

For iOS PWA without Tailscale: install the mkcert root CA (`~/.local/share/mkcert/rootCA.pem`) via AirDrop, then trust it in Settings > General > About > Certificate Trust Settings.

## REST API

All dashboard features are backed by a REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | List all sessions with status, preview, tokens |
| `/api/sessions` | POST | Create a new session |
| `/api/sessions/<name>/start` | POST | Start a session |
| `/api/sessions/<name>/stop` | POST | Stop a session |
| `/api/sessions/<name>/send` | POST | Send text to a session |
| `/api/sessions/<name>/keys` | POST | Send raw tmux keys |
| `/api/sessions/<name>/peek` | GET | Get session output |
| `/api/sessions/<name>/info` | GET | Session details |
| `/api/sessions/<name>/stats` | GET | Token usage stats |
| `/api/sessions/<name>/config` | PATCH | Update config (rename, model, dir, tags, etc.) |
| `/api/sessions/<name>/delete` | POST | Delete a session |
| `/api/sessions/<name>/duplicate` | POST | Duplicate session config |
| `/api/sessions/<name>/clone` | POST | Clone and continue conversation |
| `/api/sessions/<name>/clear` | POST | Clear tmux scrollback |
| `/api/sessions/connect` | POST | Adopt an existing tmux session |
| `/api/tmux-sessions` | GET | List unregistered tmux sessions |
| `/api/board` | GET | List board items |
| `/api/board` | POST | Create a board item |
| `/api/board/<id>` | PATCH | Update a board item |
| `/api/board/<id>` | DELETE | Delete a board item |
| `/api/board/clear-done` | POST | Remove all done items |
| `/api/events` | GET | SSE stream (sessions + board) |
| `/api/stats/daily` | GET | Daily token stats |
| `/api/stats/reset` | POST | Reset token counters |
| `/api/file` | GET | Read file contents (for peek previews) |
| `/api/autocomplete/dir` | GET | Directory path autocomplete |

## Session Logs

cmux periodically snapshots all running sessions to `~/.cmux/logs/` (every 60s, up to 10MB per session). This means:

- Stopped sessions still show preview lines and peek output from saved logs
- Session output survives server restarts
- Peek mode for stopped sessions loads from the saved log

## File Layout

```
~/.cmux/
  sessions/            # session .env files (CC_DIR, CC_FLAGS, etc.)
  logs/                # session scrollback snapshots
  tls/                 # auto-generated TLS certs
  board.json           # kanban board data
  token_baseline.json  # token counter reset baseline
  defaults.env         # global default flags
```

## Configuration

### Global defaults

```bash
cmux defaults show           # view current defaults
cmux defaults edit           # open in $EDITOR
cmux defaults reset          # clear all defaults
```

Set default flags applied to all sessions:

```bash
# In ~/.cmux/defaults.env:
CC_DEFAULT_FLAGS="--dangerously-skip-permissions"
```

### Per-session config

Each session is a simple env file in `~/.cmux/sessions/<name>.env`:

```bash
CC_DIR="/Users/you/Dev/project"
CC_FLAGS="--model sonnet --dangerously-skip-permissions"
CC_DESC="Main backend work"
CC_TAGS="backend,api"
CC_PINNED="1"
```

## Architecture

Everything lives in a single file: `cmux-server.py`. The Python server uses `http.server.ThreadingHTTPServer` with inline HTML/CSS/JS for the dashboard. No build step, no dependencies beyond Python 3 and tmux.

- **Server** — Python `BaseHTTPRequestHandler` with routing, TLS, file watching (auto-restart on save)
- **Client** — vanilla JS SPA with SSE for real-time updates, service worker for offline/PWA
- **State** — session configs in `.env` files, board in `board.json`, tmux for process management
- **Offline** — IndexedDB + localStorage + SW Cache API triple-layer, Background Sync for queue replay
