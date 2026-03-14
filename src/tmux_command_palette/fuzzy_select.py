"""Fuzzy selector UI using prompt_toolkit."""

from __future__ import annotations

from collections.abc import Callable
from shutil import get_terminal_size
from typing import TypeVar

from pfzy.score import fzy_scorer
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style

from tmux_command_palette.command import Command

T = TypeVar("T", str, Command)

STYLE = Style.from_dict(
    {
        "prompt": "bold ansigreen",
        "pointer": "bold ansimagenta",
        "selected": "bold",
        "preview.signature": "bold ansicyan",
        "preview.description": "ansibrightyellow",
        "separator": "ansibrightblack",
    }
)


def _display_text(item: str | Command) -> str:
    if isinstance(item, Command):
        return item.display_name
    return item


def _filter_text(item: str | Command) -> str:
    if isinstance(item, Command):
        return item.filter_name
    return item


class FuzzySelector:
    """Interactive fuzzy finder with optional preview pane."""

    def __init__(
        self,
        items: list[str] | list[Command],
        prompt: str = "> ",
        preview_fn: Callable[[str], str] | Callable[[Command], str] | None = None,
    ) -> None:
        self._items = items
        self._prompt = prompt
        self._preview_fn = preview_fn
        self._selected = 0
        self._filtered: list[str] | list[Command] = list(items)
        self._result: str | Command | None = None
        self._buffer = Buffer(on_text_changed=lambda _: self._update_filtered())
        self._kb = self._build_key_bindings()

    def run(self) -> str | Command | None:
        """Show the selector and return the chosen item, or None if cancelled."""
        if not self._items:
            return None

        app = self._create_app()
        app.run()
        return self._result

    def _create_app(self, **kwargs) -> Application[None]:
        """Create the prompt_toolkit Application.

        Extra kwargs are forwarded to Application (e.g. input, output for testing).
        """
        return Application(
            layout=Layout(self._build_layout(), focused_element=self._prompt_window),
            key_bindings=self._kb,
            style=STYLE,
            full_screen=True,
            **kwargs,
        )

    # -- Filtering --

    def _update_filtered(self) -> None:
        query = self._buffer.text.strip()
        if not query:
            self._filtered = list(self._items)
        else:
            scored = []
            for item in self._items:
                score, _ = fzy_scorer(query, _filter_text(item))
                if score > float("-inf"):
                    scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            self._filtered = [item for _, item in scored]
        self._selected = 0

    # -- Key bindings --

    def _build_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-n")
        @kb.add("down")
        def _move_down(event) -> None:
            if self._filtered and self._selected < len(self._filtered) - 1:
                self._selected += 1

        @kb.add("c-p")
        @kb.add("up")
        def _move_up(event) -> None:
            if self._selected > 0:
                self._selected -= 1

        @kb.add("enter")
        def _accept(event) -> None:
            if self._filtered:
                self._result = self._filtered[self._selected]
            event.app.exit()

        @kb.add("escape")
        @kb.add("c-c")
        def _cancel(event) -> None:
            self._result = None
            event.app.exit()

        return kb

    # -- Layout --

    def _build_layout(self) -> HSplit:
        self._prompt_window = Window(
            content=BufferControl(buffer=self._buffer),
            height=1,
            get_line_prefix=lambda lineno, wrap_count: [
                ("class:prompt", f" {self._prompt}")
            ],
        )

        list_window = Window(
            content=FormattedTextControl(self._get_list_fragments),
            wrap_lines=False,
        )

        if self._preview_fn:
            cols = get_terminal_size().columns
            list_width = cols * 2 // 5
            body = VSplit(
                [
                    Window(
                        content=FormattedTextControl(self._get_list_fragments),
                        wrap_lines=False,
                        width=Dimension(preferred=list_width, max=list_width),
                    ),
                    Window(width=1, char="│", style="class:separator"),
                    Window(
                        content=FormattedTextControl(self._get_preview_fragments),
                        wrap_lines=True,
                    ),
                ],
            )
        else:
            body = list_window

        return HSplit([self._prompt_window, body])

    # -- Rendering --

    def _get_visible_height(self) -> int:
        return max(get_terminal_size().lines - 1, 1)

    def _get_list_fragments(self) -> list[tuple[str, str]]:
        fragments: list[tuple[str, str]] = []
        filtered = self._filtered
        sel = self._selected
        visible = self._get_visible_height()

        if sel < visible // 2:
            start = 0
        elif sel >= len(filtered) - visible // 2:
            start = max(0, len(filtered) - visible)
        else:
            start = sel - visible // 2
        end = min(start + visible, len(filtered))

        for i in range(start, end):
            item = filtered[i]
            label = _display_text(item)
            if i == sel:
                fragments.append(("class:pointer", " > "))
                fragments.append(("class:selected", label))
            else:
                fragments.append(("", "   "))
                fragments.append(("", label))
            if i < end - 1:
                fragments.append(("", "\n"))
        return fragments

    def _get_preview_fragments(self) -> list[tuple[str, str]]:
        if not self._preview_fn or not self._filtered:
            return [("", "")]
        item = self._filtered[self._selected]
        text = self._preview_fn(item)
        lines = text.split("\n", 1)
        fragments: list[tuple[str, str]] = []
        fragments.append(("class:preview.signature", lines[0]))
        if len(lines) > 1:
            fragments.append(("class:preview.description", lines[1]))
        return fragments


def fuzzy_select(
    items: list[str] | list[Command],
    prompt: str = "> ",
    preview_fn: Callable[[str], str] | Callable[[Command], str] | None = None,
) -> str | Command | None:
    """Convenience wrapper around FuzzySelector."""
    return FuzzySelector(items, prompt, preview_fn).run()
