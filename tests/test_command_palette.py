"""Tests for CommandPalette."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from tmux_command_palette.command import Command, CommandCategory
from tmux_command_palette.main import CommandPalette


class TestCommandPalette:
    def _make_server(self, commands=None, signature=""):
        server = MagicMock()
        cmd_result = MagicMock()
        cmd_result.stdout = commands or []
        cmd_result.stderr = []
        server.cmd.return_value = cmd_result
        return server

    def _make_builtin(self, name):
        return Command(name=name, category=CommandCategory.BUILTIN)

    def _make_plugin(self, name, description="", plugin_dir=None):
        return Command(
            name=name,
            category=CommandCategory.PLUGIN,
            description=description,
            plugin_dir=plugin_dir,
        )

    def test_preview_builtin(self):
        server = self._make_server()
        palette = CommandPalette(server)
        cmd = self._make_builtin("list-keys")
        with (
            patch(
                "tmux_command_palette.main.get_signature",
                return_value="list-keys [-1aN]",
            ),
            patch(
                "tmux_command_palette.main.get_description",
                return_value="List key bindings.",
            ),
        ):
            result = palette._preview(cmd)
        assert "list-keys [-1aN]" in result
        assert "List key bindings." in result

    def test_preview_builtin_no_description(self):
        server = self._make_server()
        palette = CommandPalette(server)
        cmd = self._make_builtin("list-keys")
        with (
            patch(
                "tmux_command_palette.main.get_signature",
                return_value="list-keys [-1aN]",
            ),
            patch("tmux_command_palette.main.get_description", return_value=""),
        ):
            result = palette._preview(cmd)
        assert result == "list-keys [-1aN]"
        assert "\n" not in result

    def test_preview_plugin(self):
        server = self._make_server()
        palette = CommandPalette(server)
        cmd = self._make_plugin("hello", description="Say hello")
        result = palette._preview(cmd)
        assert "hello" in result
        assert "Say hello" in result

    def test_preview_plugin_no_description(self):
        server = self._make_server()
        palette = CommandPalette(server)
        cmd = self._make_plugin("hello")
        result = palette._preview(cmd)
        assert result == "hello"

    def test_select_targets_no_targets(self):
        server = self._make_server()
        palette = CommandPalette(server)
        with (
            patch(
                "tmux_command_palette.main.get_signature",
                return_value="list-keys [-1aN]",
            ),
            patch("tmux_command_palette.main.parse_targets", return_value=[]),
        ):
            args = palette._select_targets("list-keys")
        assert args == []

    def test_prompt_positional_required(self):
        server = self._make_server()
        palette = CommandPalette(server)
        with (
            patch(
                "tmux_command_palette.main.get_signature",
                return_value="send-keys key",
            ),
            patch("builtins.input", return_value="C-a"),
        ):
            result = palette._prompt_positional_args("send-keys")
        assert result == ["C-a"]

    def test_prompt_positional_optional_empty(self):
        server = self._make_server()
        palette = CommandPalette(server)
        with (
            patch(
                "tmux_command_palette.main.get_signature",
                return_value="list-commands [command]",
            ),
            patch("builtins.input", return_value=""),
        ):
            result = palette._prompt_positional_args("list-commands")
        assert result == []

    def test_prompt_positional_none_when_no_args(self):
        server = self._make_server()
        palette = CommandPalette(server)
        with patch(
            "tmux_command_palette.main.get_signature",
            return_value="list-keys [-1aN]",
        ):
            result = palette._prompt_positional_args("list-keys")
        assert result == []

    def test_execute_plugin(self, tmp_path):
        server = self._make_server()
        server.socket_path = "/tmp/tmux-test"
        palette = CommandPalette(server)

        run_sh = tmp_path / "run.sh"
        run_sh.write_text("#!/bin/sh\necho 'Hello from plugin!'\n")
        run_sh.chmod(0o755)

        cmd = self._make_plugin("hello", plugin_dir=tmp_path)
        with patch("tmux_command_palette.main.Console"):
            palette._execute_plugin(cmd)

    def test_execute_plugin_no_run_sh(self, tmp_path):
        server = self._make_server()
        palette = CommandPalette(server)
        cmd = self._make_plugin("hello", plugin_dir=tmp_path)
        # Should not raise
        palette._execute_plugin(cmd)

    def test_execute_plugin_no_plugin_dir(self):
        server = self._make_server()
        palette = CommandPalette(server)
        cmd = self._make_plugin("hello")
        # Should not raise
        palette._execute_plugin(cmd)

    def test_run_dispatches_plugin(self, tmp_path):
        server = self._make_server()
        server.socket_path = "/tmp/tmux-test"
        palette = CommandPalette(server)

        run_sh = tmp_path / "run.sh"
        run_sh.write_text("#!/bin/sh\necho ok\n")
        run_sh.chmod(0o755)

        plugin_cmd = self._make_plugin("hello", plugin_dir=tmp_path)
        with (
            patch.object(palette, "_select_command", return_value=plugin_cmd),
            patch.object(palette, "_execute_plugin") as mock_exec,
        ):
            palette.run()
        mock_exec.assert_called_once_with(plugin_cmd)

    def test_run_dispatches_builtin(self):
        server = self._make_server()
        palette = CommandPalette(server)
        builtin_cmd = self._make_builtin("list-keys")
        with (
            patch.object(palette, "_select_command", return_value=builtin_cmd),
            patch.object(palette, "_select_targets", return_value=[]),
            patch.object(palette, "_prompt_positional_args", return_value=[]),
            patch.object(palette, "_execute") as mock_exec,
        ):
            palette.run()
        mock_exec.assert_called_once_with("list-keys", [])

    def test_get_plugin_dir_from_tmux_option(self):
        server = self._make_server()
        cmd_result = MagicMock()
        cmd_result.stdout = ["/custom/plugins"]
        server.cmd.return_value = cmd_result
        palette = CommandPalette(server)
        result = palette._get_plugin_dir()
        assert result == Path("/custom/plugins")

    def test_get_plugin_dir_returns_none_when_unset(self):
        server = self._make_server()
        cmd_result = MagicMock()
        cmd_result.stdout = [""]
        server.cmd.return_value = cmd_result
        palette = CommandPalette(server)
        result = palette._get_plugin_dir()
        assert result is None
