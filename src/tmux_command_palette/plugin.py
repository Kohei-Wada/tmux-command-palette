"""Plugin loader for tmux-command-palette."""

from __future__ import annotations

import tomllib
from pathlib import Path

from tmux_command_palette.command import Command, CommandCategory

DEFAULT_PLUGIN_DIR = Path.home() / ".config" / "tmux-command-palette" / "plugins"


def load_plugins(plugin_dir: Path | None = None) -> list[Command]:
    """Load plugins from the plugin directory.

    Each plugin is a subdirectory containing a plugin.toml and run.sh.
    """
    base = plugin_dir or DEFAULT_PLUGIN_DIR
    if not base.is_dir():
        return []

    commands: list[Command] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        toml_path = entry / "plugin.toml"
        if not toml_path.exists():
            continue
        with toml_path.open("rb") as f:
            data = tomllib.load(f)
        name = data.get("name", entry.name)
        description = data.get("description", "")
        commands.append(
            Command(
                name=name,
                category=CommandCategory.PLUGIN,
                description=description,
                plugin_dir=entry,
            )
        )
    return commands
