#!/usr/bin/env bash
# amux cloud VM bootstrap — runs as root via GCP startup script
# Also works standalone: sudo bash setup.sh
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
STORAGE_DEV="/dev/disk/by-id/google-amux-storage"
STORAGE_MOUNT="/mnt/storage"
AMUX_USER="amux"

log() { echo "[amux-setup] $(date '+%H:%M:%S') $*"; }

# ── System packages ──
log "Updating packages..."
apt-get update -qq
apt-get install -y -qq \
  tmux git curl wget unzip jq htop \
  python3 python3-pip python3-venv \
  build-essential ca-certificates gnupg lsb-release

# ── Node.js 22 LTS ──
if ! command -v node &>/dev/null; then
  log "Installing Node.js 22..."
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y -qq nodejs
fi

# ── Tailscale ──
if ! command -v tailscale &>/dev/null; then
  log "Installing Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh
fi
log "Connecting to Tailscale..."
tailscale up --authkey="${tailscale_auth_key}" --hostname=amux-cloud --ssh || true

# ── Mount storage disk ──
if [ -b "$STORAGE_DEV" ] && ! mountpoint -q "$STORAGE_MOUNT"; then
  log "Setting up storage disk..."
  mkdir -p "$STORAGE_MOUNT"
  # Format only if no filesystem exists
  if ! blkid "$STORAGE_DEV" &>/dev/null; then
    mkfs.ext4 -q -L amux-storage "$STORAGE_DEV"
  fi
  # Ensure fstab entry
  if ! grep -q amux-storage /etc/fstab; then
    echo "LABEL=amux-storage $STORAGE_MOUNT ext4 defaults,nofail 0 2" >> /etc/fstab
  fi
  mount -a
  log "Storage mounted at $STORAGE_MOUNT"
fi

# ── Create amux user ──
if ! id "$AMUX_USER" &>/dev/null; then
  log "Creating user $AMUX_USER..."
  useradd -m -s /bin/bash "$AMUX_USER"
  usermod -aG sudo "$AMUX_USER"
  echo "$AMUX_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/amux
fi
# Give user access to storage
chown -R "$AMUX_USER:$AMUX_USER" "$STORAGE_MOUNT" 2>/dev/null || true

# ── code-server ──
if ! command -v code-server &>/dev/null; then
  log "Installing code-server..."
  curl -fsSL https://code-server.dev/install.sh | sh
fi
mkdir -p /home/$AMUX_USER/.config/code-server
cat > /home/$AMUX_USER/.config/code-server/config.yaml <<'CSCFG'
bind-addr: 0.0.0.0:8080
auth: none
cert: false
CSCFG
chown -R "$AMUX_USER:$AMUX_USER" /home/$AMUX_USER/.config

# code-server systemd service
cat > /etc/systemd/system/code-server.service <<CSSVC
[Unit]
Description=code-server
After=network.target

[Service]
Type=simple
User=$AMUX_USER
ExecStart=/usr/bin/code-server --config /home/$AMUX_USER/.config/code-server/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
CSSVC
systemctl daemon-reload
systemctl enable --now code-server

# ── Claude Code CLI ──
log "Installing Claude Code..."
npm install -g @anthropic-ai/claude-code || true

# ── amux itself ──
AMUX_DIR="/home/$AMUX_USER/amux"
if [ ! -d "$AMUX_DIR" ]; then
  log "Cloning amux..."
  sudo -u "$AMUX_USER" git clone https://github.com/your-username/amux.git "$AMUX_DIR" 2>/dev/null || {
    # If repo isn't public yet, create the directory structure
    sudo -u "$AMUX_USER" mkdir -p "$AMUX_DIR"
    log "amux repo not available — directory created, copy files manually"
  }
fi

# Symlink centralized MCP config into claude code's config location
CLAUDE_DIR="/home/$AMUX_USER/.claude"
sudo -u "$AMUX_USER" mkdir -p "$CLAUDE_DIR"
if [ -f "$AMUX_DIR/mcp.json" ]; then
  ln -sf "$AMUX_DIR/mcp.json" "$CLAUDE_DIR/mcp.json"
  log "Linked mcp.json into Claude config"
fi

# ── amux server as systemd service ──
cat > /etc/systemd/system/amux.service <<CMXSVC
[Unit]
Description=amux server
After=network.target

[Service]
Type=simple
User=$AMUX_USER
WorkingDirectory=$AMUX_DIR
ExecStart=/usr/bin/python3 $AMUX_DIR/amux-server.py --port 8822
Restart=always
RestartSec=5
Environment=HOME=/home/$AMUX_USER

[Install]
WantedBy=multi-user.target
CMXSVC
systemctl daemon-reload
systemctl enable amux

# ── Shell config ──
BASHRC="/home/$AMUX_USER/.bashrc"
if ! grep -q "amux-cloud" "$BASHRC" 2>/dev/null; then
  cat >> "$BASHRC" <<'SHELL'

# ── amux cloud env ──
export PATH="$HOME/amux:$PATH"
export AMUX_STORAGE="/mnt/storage"
alias ll='ls -alF'
alias cls='clear'

# Auto-start tmux on SSH login
if [ -n "$SSH_CONNECTION" ] && [ -z "$TMUX" ]; then
  tmux new-session -A -s main
fi
SHELL
  chown "$AMUX_USER:$AMUX_USER" "$BASHRC"
fi

# ── tmux config ──
TMUX_CONF="/home/$AMUX_USER/.tmux.conf"
if [ ! -f "$TMUX_CONF" ]; then
  cat > "$TMUX_CONF" <<'TMUX'
set -g mouse on
set -g history-limit 50000
set -g default-terminal "screen-256color"
set -g status-style "bg=colour235,fg=colour248"
set -g status-left "#[fg=colour39,bold] amux-cloud #[default]"
set -g status-right "#[fg=colour245]%H:%M "
set -g base-index 1
setw -g pane-base-index 1
TMUX
  chown "$AMUX_USER:$AMUX_USER" "$TMUX_CONF"
fi

log "Setup complete."
log "  Tailscale:   ssh amux@amux-cloud"
log "  code-server: http://amux-cloud:8080"
log "  amux:        https://amux-cloud:8822"
log "  Storage:     $STORAGE_MOUNT ($(df -h $STORAGE_MOUNT 2>/dev/null | awk 'NR==2{print $2}' || echo 'not mounted'))"
