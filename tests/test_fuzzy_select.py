"""Tests for FuzzySelector."""

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from tmux_command_palette.command import Command, CommandCategory
from tmux_command_palette.fuzzy_select import FuzzySelector


class TestFuzzySelector:
    def test_empty_items_returns_none(self):
        result = FuzzySelector([], prompt=">").run()
        assert result is None

    def test_filtering(self):
        selector = FuzzySelector(["attach-session", "bind-key", "break-pane"])
        selector._buffer.text = "att"
        selector._update_filtered()
        assert selector._filtered[0] == "attach-session"

    def test_filtering_empty_query_returns_all(self):
        items = ["attach-session", "bind-key", "break-pane"]
        selector = FuzzySelector(items)
        selector._buffer.text = ""
        selector._update_filtered()
        assert selector._filtered == items

    def test_filtering_no_match(self):
        selector = FuzzySelector(["attach-session", "bind-key"])
        selector._buffer.text = "zzzzz"
        selector._update_filtered()
        assert selector._filtered == []

    def test_selection_bounds(self):
        selector = FuzzySelector(["a", "b", "c"])
        assert selector._selected == 0
        # Can't go above 0
        selector._selected = 0
        selector._build_key_bindings()  # ensure bindings exist

    def test_enter_selects_current(self):
        items = ["attach-session", "bind-key", "break-pane"]
        selector = FuzzySelector(items)
        with create_pipe_input() as pipe_input:
            pipe_input.send_text("\r")
            app = selector._create_app(input=pipe_input, output=DummyOutput())
            app.run()
        assert selector._result == "attach-session"

    def test_escape_returns_none(self):
        items = ["attach-session", "bind-key"]
        selector = FuzzySelector(items)
        with create_pipe_input() as pipe_input:
            pipe_input.send_text("\x1b")
            app = selector._create_app(input=pipe_input, output=DummyOutput())
            app.run()
        assert selector._result is None

    def test_preview_fragments(self):
        selector = FuzzySelector(
            ["cmd-a", "cmd-b"],
            preview_fn=lambda cmd: f"sig: {cmd}\n\ndesc of {cmd}",
        )
        fragments = selector._get_preview_fragments()
        assert any("sig: cmd-a" in text for _, text in fragments)

    def test_preview_fn_none(self):
        selector = FuzzySelector(["cmd-a"])
        fragments = selector._get_preview_fragments()
        assert fragments == [("", "")]


class TestFuzzySelectorWithCommand:
    def _make_cmd(self, name, category=CommandCategory.BUILTIN):
        return Command(name=name, category=category, description=f"desc of {name}")

    def test_filtering_commands(self):
        cmds = [
            self._make_cmd("attach-session"),
            self._make_cmd("bind-key"),
            self._make_cmd("hello", CommandCategory.PLUGIN),
        ]
        selector = FuzzySelector(cmds)
        selector._buffer.text = "hello"
        selector._update_filtered()
        assert selector._filtered[0].name == "hello"

    def test_display_shows_category_prefix(self):
        cmds = [
            self._make_cmd("bind-key"),
            self._make_cmd("hello", CommandCategory.PLUGIN),
        ]
        selector = FuzzySelector(cmds)
        fragments = selector._get_list_fragments()
        texts = [text for _, text in fragments]
        assert any("[builtin] bind-key" in t for t in texts)

    def test_enter_selects_command(self):
        cmds = [self._make_cmd("attach-session")]
        selector = FuzzySelector(cmds)
        with create_pipe_input() as pipe_input:
            pipe_input.send_text("\r")
            app = selector._create_app(input=pipe_input, output=DummyOutput())
            app.run()
        assert isinstance(selector._result, Command)
        assert selector._result.name == "attach-session"

    def test_preview_with_command(self):
        cmds = [self._make_cmd("bind-key")]
        selector = FuzzySelector(
            cmds,
            preview_fn=lambda cmd: f"{cmd.name}\n\n{cmd.description}",
        )
        fragments = selector._get_preview_fragments()
        assert any("bind-key" in text for _, text in fragments)
