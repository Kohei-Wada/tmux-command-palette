#!/usr/bin/env bash
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install binary if not available (first run only)
if ! command -v tmux-command-palette &>/dev/null \
   && [ ! -x "$CURRENT_DIR/bin/tmux-command-palette" ]; then
    "$CURRENT_DIR/scripts/install.sh"
fi

# Prefer PATH binary, fall back to plugin-local binary
if command -v tmux-command-palette &>/dev/null; then
    PALETTE_BIN="tmux-command-palette"
else
    PALETTE_BIN="$CURRENT_DIR/bin/tmux-command-palette"
fi

tmux set-option -gq @command-palette-plugin-dir "$HOME/.config/tmux-command-palette/plugins"
tmux bind-key : display-popup -E -w 100% -h 40% -y 0 "$PALETTE_BIN"
