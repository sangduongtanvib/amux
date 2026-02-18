#!/usr/bin/env bash
# Install cmux to /usr/local/bin
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/local/bin"

echo "Installing cmux to $INSTALL_DIR..."

# Check dependencies
command -v tmux &>/dev/null || echo "Warning: tmux not found (required for sessions)"
command -v python3 &>/dev/null || echo "Warning: python3 not found (required for cmux serve)"

chmod +x "$SCRIPT_DIR/cmux"
chmod +x "$SCRIPT_DIR/cmux-server.py"

if [[ -w "$INSTALL_DIR" ]]; then
  ln -sf "$SCRIPT_DIR/cmux" "$INSTALL_DIR/cmux"
  ln -sf "$SCRIPT_DIR/cmux-server.py" "$INSTALL_DIR/cmux-server.py"
  # Compat alias: cc → cmux
  ln -sf "$SCRIPT_DIR/cmux" "$INSTALL_DIR/cc"
else
  sudo ln -sf "$SCRIPT_DIR/cmux" "$INSTALL_DIR/cmux"
  sudo ln -sf "$SCRIPT_DIR/cmux-server.py" "$INSTALL_DIR/cmux-server.py"
  sudo ln -sf "$SCRIPT_DIR/cmux" "$INSTALL_DIR/cc"
fi

# Verify
if command -v cmux &>/dev/null; then
  echo "Installed: $(cmux --version)"
  echo ""
  echo "Quick start:"
  echo "  cmux register myproject --dir ~/Dev/myproject --yolo"
  echo "  cmux start myproject"
  echo "  cmux                     # open terminal dashboard"
  echo "  cmux serve               # open web dashboard on :8822"
else
  echo "Warning: cmux not found in PATH after install"
  echo "You may need to add $INSTALL_DIR to your PATH"
fi
