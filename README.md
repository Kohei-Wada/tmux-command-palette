# tmux-command-palette

An interactive command palette for tmux. Fuzzy-search and execute any tmux command from a popup.

## Features

- Fuzzy search across all tmux commands
- Preview pane showing command signature and description
- Interactive target selection (session / window / pane / client)
- Plugin system for custom commands

## Installation

### TPM (recommended)

Add the following to `~/.tmux.conf`:

```tmux
set -g @plugin 'Kohei-Wada/tmux-command-palette'
```

Then press `prefix + I` to install. A pre-built binary will be downloaded automatically — no Python or uv required.

### Manual (from source)

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```sh
uv tool install .
```

Then add to `~/.tmux.conf`:

```tmux
run-shell /path/to/tmux-command-palette.tmux
```

By default, the palette is bound to the `:` key.

## Usage

Press `:` inside tmux to open the palette. Type to filter commands, then press Enter to execute.

| Key | Action |
|-----|--------|
| Type | Fuzzy filter |
| `Ctrl-n` / `Down` | Next item |
| `Ctrl-p` / `Up` | Previous item |
| `Enter` | Select and execute |
| `Escape` / `Ctrl-c` | Cancel |

## Plugins

Add custom commands to the palette using shell script plugins.

### Creating a plugin

Create a directory under `~/.config/tmux-command-palette/plugins/` with a `plugin.toml` and a `run.sh`:

```
~/.config/tmux-command-palette/plugins/
  hello/
    plugin.toml
    run.sh
```

**plugin.toml:**

```toml
name = "hello"
description = "Say hello"
```

**run.sh:**

```sh
#!/bin/sh
echo "Hello from plugin!"
```

Commands are displayed with a `[builtin]` or `[plugin]` prefix in the palette.

### Custom plugin directory

Override the default plugin directory in `~/.tmux.conf`:

```tmux
set -g @command-palette-plugin-dir "/path/to/plugins"
```

### Environment variables

The following environment variables are set when a plugin runs:

| Variable | Description |
|----------|-------------|
| `TMUX_COMMAND_PALETTE_SOCKET` | Path to the tmux socket |

## Development

```sh
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/ tests/
```

## License

MIT
