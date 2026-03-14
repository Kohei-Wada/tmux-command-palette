"""tmux-command-palette: interactive command palette for tmux."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import libtmux
from rich.console import Console

from tmux_command_palette.command import Command, CommandCategory
from tmux_command_palette.fuzzy_select import fuzzy_select
from tmux_command_palette.palette import (
    get_commands,
    get_description,
    get_entity,
    get_signature,
    list_entities,
    parse_optional_args,
    parse_required_args,
    parse_targets,
)
from tmux_command_palette.plugin import load_plugins


class CommandPalette:
    """Orchestrates the tmux command palette workflow."""

    def __init__(self, server: libtmux.Server) -> None:
        self._server = server

    def run(self) -> None:
        """Run the full palette flow: select, configure, execute."""
        selected = self._select_command()
        if not selected:
            return

        if selected.category == CommandCategory.PLUGIN:
            self._execute_plugin(selected)
            return

        sig = get_signature(self._server, selected.name)

        args = self._select_targets(selected.name, sig)
        if args is None:
            return

        positional = self._prompt_positional_args(selected.name, sig)
        if positional is None:
            return
        args.extend(positional)

        self._execute(selected.name, args)

    def _select_command(self) -> Command | None:
        builtin = get_commands(self._server)
        plugins = load_plugins(self._get_plugin_dir())
        commands = builtin + plugins
        return fuzzy_select(commands, prompt="tmux>", preview_fn=self._preview)

    def _get_plugin_dir(self) -> Path | None:
        try:
            result = self._server.cmd(
                "show-option", "-gqv", "@command-palette-plugin-dir"
            )
            stdout = result.stdout or []
            value = "\n".join(stdout).strip()
            if value:
                return Path(value).expanduser()
        except libtmux.exc.LibTmuxException:
            pass
        return None

    def _preview(self, cmd: Command) -> str:
        if cmd.category == CommandCategory.PLUGIN:
            return f"{cmd.name}\n\n{cmd.description}" if cmd.description else cmd.name

        sig = get_signature(self._server, cmd.name)
        desc = get_description(cmd.name)
        return f"{sig}\n\n{desc}" if desc else sig

    def _select_targets(self, cmd: str, sig: str) -> list[str] | None:
        targets = parse_targets(sig)
        args: list[str] = []

        for flag, type_name in targets:
            entity = get_entity(type_name)
            entities = list_entities(self._server, entity)
            if not entities:
                continue

            choice = fuzzy_select(entities, prompt=f"{cmd} {type_name}>")
            if choice is None:
                return None
            target_id = choice.split()[0]
            args.extend([f"-{flag}", target_id])

        return args

    def _prompt_positional_args(self, cmd: str, sig: str) -> list[str] | None:
        required = parse_required_args(sig, cmd)
        optional = parse_optional_args(sig)

        if required:
            try:
                user_input = input(f"{cmd} {' '.join(required)}: ")
            except (EOFError, KeyboardInterrupt):
                return None
            if not user_input:
                return None
            return [user_input]

        if optional:
            try:
                user_input = input(f"{cmd} {' '.join(optional)} (optional): ")
            except (EOFError, KeyboardInterrupt):
                return None
            if user_input:
                return [user_input]

        return []

    def _execute(self, cmd: str, args: list[str]) -> None:
        try:
            result = self._server.cmd(cmd, *args)
            stdout = result.stdout or []
            stderr = result.stderr or []
            output = "\n".join(stdout).strip() or "\n".join(stderr).strip()
        except libtmux.exc.LibTmuxException as e:
            output = str(e)

        if output:
            console = Console()
            with console.pager(styles=True):
                console.print(output)

    def _execute_plugin(self, cmd: Command) -> None:
        if not cmd.plugin_dir:
            return
        run_sh = cmd.plugin_dir / "run.sh"
        if not run_sh.exists():
            return

        env = {
            **os.environ,
            "TMUX_COMMAND_PALETTE_SOCKET": self._server.socket_path or "",
        }
        result = subprocess.run(
            ["sh", str(run_sh)],
            capture_output=True,
            text=True,
            env=env,
        )
        output = result.stdout.strip() or result.stderr.strip()
        if output:
            console = Console()
            with console.pager(styles=True):
                console.print(output)


def main() -> None:
    import sys

    from tmux_command_palette._version import __version__

    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(__version__)
        return

    server = libtmux.Server()
    CommandPalette(server).run()


if __name__ == "__main__":
    main()
