"""Core logic for tmux-command-palette.

Command parsing, entity listing, description lookup.
"""

from __future__ import annotations

import json
import re
import sys
from functools import cache
from pathlib import Path

import libtmux

from tmux_command_palette.command import Command, CommandCategory

# Matches [-flag type-name] but excludes uppercase flags like [-F format]
_TARGET_RE = re.compile(r"\[-([a-z])\s+([\w-]+)\]")


def get_commands(server: libtmux.Server) -> list[Command]:
    """Return sorted list of tmux commands as Command objects."""
    result = server.cmd("list-commands")
    stdout = result.stdout or []
    names = sorted({line.split()[0] for line in stdout if line})
    return [
        Command(
            name=name,
            category=CommandCategory.BUILTIN,
            description=get_description(name),
        )
        for name in names
    ]


def get_signature(server: libtmux.Server, cmd: str) -> str:
    """Return the full signature line for a tmux command."""
    result = server.cmd("list-commands", cmd)
    stdout = result.stdout or []
    return "\n".join(stdout).strip()


_REQUIRED_ARG_RE = re.compile(r"(?<=\s)(?<!\[)([a-z][-a-z]*)(?!\])(?=\s|$)")


def parse_required_args(sig: str, cmd: str) -> list[str]:
    """Extract required positional arguments from a tmux command signature."""
    return [m for m in _REQUIRED_ARG_RE.findall(sig) if m != cmd]


def parse_optional_args(sig: str) -> list[str]:
    """Extract optional positional arguments from a tmux command signature."""
    return re.findall(r"\[([a-z][-a-z]*)\]", sig)


def parse_targets(sig: str) -> list[tuple[str, str]]:
    """Extract (-flag, type-name) pairs from a tmux command signature.

    Only lowercase flags are included (uppercase like -F are excluded).
    """
    return _TARGET_RE.findall(sig)


def get_entity(type_name: str) -> str:
    """Extract entity from a type name.

    E.g. 'target-pane' -> 'pane', 'src-pane' -> 'pane'.
    """
    return type_name.rsplit("-", 1)[-1]


def list_entities(server: libtmux.Server, entity: str) -> list[str]:
    """List entities using libtmux's API.

    Returns formatted strings matching LIST_FORMAT for the given entity type.
    """
    if entity == "session":
        return [s.name for s in server.sessions if s.name]
    elif entity == "window":
        return [
            f"{w.session.name}:{w.window_index} {w.window_name}"
            for s in server.sessions
            for w in s.windows
        ]
    elif entity == "pane":
        return [
            f"{p.window.session.name}:{p.window.window_index}"
            f".{p.pane_index} {p.pane_current_command}"
            for s in server.sessions
            for w in s.windows
            for p in w.panes
        ]
    elif entity == "client":
        # libtmux doesn't have a direct client API; use server.cmd()
        fmt = "#{client_name}"
        result = server.cmd("list-clients", "-F", fmt)
        stdout = result.stdout or []
        return [line for line in stdout if line]
    else:
        return []


def _get_data_dir() -> Path:
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "tmux_command_palette" / "data"
    return Path(__file__).parent / "data"


@cache
def _load_descriptions() -> dict[str, str]:
    data_path = _get_data_dir() / "descriptions.json"
    return json.loads(data_path.read_text())


def get_description(cmd: str) -> str:
    """Get description for a tmux command from bundled data."""
    return _load_descriptions().get(cmd, "")
