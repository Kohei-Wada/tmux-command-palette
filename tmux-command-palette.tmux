#!/usr/bin/env bash
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve binary: PATH > plugin-local binary > install from release > uv run fallback
if command -v tmux-command-palette &>/dev/null; then
    PALETTE_BIN="tmux-command-palette"
elif [ -x "$CURRENT_DIR/bin/tmux-command-palette" ]; then
    PALETTE_BIN="$CURRENT_DIR/bin/tmux-command-palette"
elif "$CURRENT_DIR/scripts/install.sh" 2>/dev/null && [ -x "$CURRENT_DIR/bin/tmux-command-palette" ]; then
    PALETTE_BIN="$CURRENT_DIR/bin/tmux-command-palette"
elif command -v uv &>/dev/null; then
    PALETTE_BIN="uv --directory $CURRENT_DIR run tmux-command-palette"
else
    tmux display-message "tmux-command-palette: no binary found and uv not available"
    return 2>/dev/null || exit 1
fi

tmux set-option -gq @command-palette-plugin-dir "$HOME/.config/tmux-command-palette/plugins"
tmux bind-key : display-popup -E -w 100% -h 40% -y 0 "$PALETTE_BIN"
