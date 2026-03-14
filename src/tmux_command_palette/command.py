"""Command model for tmux-command-palette."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CommandCategory(Enum):
    BUILTIN = "builtin"
    PLUGIN = "plugin"


@dataclass(frozen=True)
class Command:
    name: str
    category: CommandCategory
    description: str = ""
    plugin_dir: Path | None = None

    @property
    def display_name(self) -> str:
        return f"[{self.category.value}] {self.name}"

    @property
    def filter_name(self) -> str:
        return self.name
