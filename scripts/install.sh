#!/usr/bin/env bash
# Idempotent installer for tmux-command-palette binary.
# Called by TPM on plugin install or sourced manually.

set -euo pipefail

REPO="Kohei-Wada/tmux-command-palette"
PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$PLUGIN_DIR/bin"

notify() {
    if command -v tmux &>/dev/null; then
        tmux display-message "tmux-command-palette: $1"
    else
        echo "tmux-command-palette: $1" >&2
    fi
}

# Skip if already on PATH (e.g. installed via uv/pip)
if command -v tmux-command-palette &>/dev/null; then
    exit 0
fi

# Detect OS and architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)  OS="linux" ;;
    darwin) OS="darwin" ;;
    *)
        notify "Unsupported OS: $OS"
        exit 1
        ;;
esac

case "$ARCH" in
    x86_64|amd64)  ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64"
        [ "$OS" = "linux" ] && ARCH="aarch64"
        ;;
    *)
        notify "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

ARTIFACT="tmux-command-palette-${OS}-${ARCH}"

# Fetch latest release tag
get_latest_version() {
    local url="https://api.github.com/repos/${REPO}/releases/latest"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url" | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"//;s/".*//'
    elif command -v wget &>/dev/null; then
        wget -qO- "$url" | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"//;s/".*//'
    else
        notify "Neither curl nor wget found"
        exit 1
    fi
}

LATEST_VERSION="$(get_latest_version)"
if [ -z "$LATEST_VERSION" ]; then
    notify "Failed to fetch latest release version"
    exit 1
fi

# Check if existing binary is already up to date
if [ -x "$BIN_DIR/tmux-command-palette" ]; then
    INSTALLED_VERSION="$("$BIN_DIR/tmux-command-palette" --version 2>/dev/null || echo "")"
    # Strip leading 'v' from tag for comparison
    if [ "$INSTALLED_VERSION" = "${LATEST_VERSION#v}" ]; then
        exit 0
    fi
fi

# Download binary
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${LATEST_VERSION}/${ARTIFACT}"
mkdir -p "$BIN_DIR"

notify "Downloading ${ARTIFACT} ${LATEST_VERSION}..."

if command -v curl &>/dev/null; then
    curl -fsSL -o "$BIN_DIR/tmux-command-palette" "$DOWNLOAD_URL"
elif command -v wget &>/dev/null; then
    wget -qO "$BIN_DIR/tmux-command-palette" "$DOWNLOAD_URL"
fi

chmod +x "$BIN_DIR/tmux-command-palette"
notify "Installed ${LATEST_VERSION} successfully"
