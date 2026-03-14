"""Tests for palette.py."""

from tmux_command_palette.palette import (
    get_description,
    get_entity,
    parse_optional_args,
    parse_required_args,
    parse_targets,
)


class TestParseTargets:
    def test_extracts_target_pane(self):
        targets = parse_targets("clock-mode [-t target-pane]")
        assert ("t", "target-pane") in targets

    def test_extracts_target_session(self):
        targets = parse_targets(
            "attach-session [-dErx] [-c working-directory]"
            " [-f flags] [-t target-session]"
        )
        assert ("t", "target-session") in targets

    def test_extracts_multiple_targets(self):
        targets = parse_targets(
            "break-pane [-abdP] [-F format]"
            " [-n window-name] [-s src-pane] [-t dst-window]"
        )
        assert ("s", "src-pane") in targets
        assert ("t", "dst-window") in targets

    def test_excludes_uppercase_flags(self):
        targets = parse_targets("break-pane [-abdP] [-F format] [-s src-pane]")
        flags = [flag for flag, _ in targets]
        assert "F" not in flags

    def test_no_targets_returns_empty(self):
        targets = parse_targets("list-commands [command]")
        assert targets == []

    def test_multiple_flag_groups_ignored(self):
        """Grouped flags like [-abdP] should not produce targets."""
        targets = parse_targets("some-cmd [-abdP]")
        assert targets == []


class TestGetEntity:
    def test_target_session(self):
        assert get_entity("target-session") == "session"

    def test_target_window(self):
        assert get_entity("target-window") == "window"

    def test_target_pane(self):
        assert get_entity("target-pane") == "pane"

    def test_src_pane(self):
        assert get_entity("src-pane") == "pane"

    def test_dst_window(self):
        assert get_entity("dst-window") == "window"

    def test_target_client(self):
        assert get_entity("target-client") == "client"


class TestParseRequiredArgs:
    def test_extracts_required_arg(self):
        sig = "send-keys [-lMRX] [-t target-pane] key"
        assert parse_required_args(sig, "send-keys") == ["key"]

    def test_excludes_command_name(self):
        args = parse_required_args("list-commands [command]", "list-commands")
        assert "list-commands" not in args

    def test_no_required_args(self):
        assert parse_required_args("clock-mode [-t target-pane]", "clock-mode") == []

    def test_multiple_required_args(self):
        sig = "bind-key [-nr] [-T key-table] key command"
        assert parse_required_args(sig, "bind-key") == ["key", "command"]


class TestParseOptionalArgs:
    def test_extracts_optional_arg(self):
        assert parse_optional_args("list-commands [command]") == ["command"]

    def test_no_optional_args(self):
        assert parse_optional_args("clock-mode [-t target-pane]") == []

    def test_multiple_optional_args(self):
        sig = "some-cmd [foo] [bar]"
        assert parse_optional_args(sig) == ["foo", "bar"]


class TestGetDescription:
    def test_known_command(self):
        desc = get_description("new-session")
        assert "session" in desc.lower()

    def test_unknown_command_returns_empty(self):
        assert get_description("nonexistent-command") == ""
