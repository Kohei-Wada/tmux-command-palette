"""Tests for plugin loader."""

from tmux_command_palette.command import CommandCategory
from tmux_command_palette.plugin import load_plugins


class TestLoadPlugins:
    def test_empty_when_dir_missing(self, tmp_path):
        result = load_plugins(tmp_path / "nonexistent")
        assert result == []

    def test_loads_plugin_from_toml(self, tmp_path):
        plugin_dir = tmp_path / "hello"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.toml").write_text(
            'name = "hello"\ndescription = "Say hello"\n'
        )
        (plugin_dir / "run.sh").write_text("#!/bin/sh\necho hello\n")

        result = load_plugins(tmp_path)
        assert len(result) == 1
        assert result[0].name == "hello"
        assert result[0].description == "Say hello"
        assert result[0].category == CommandCategory.PLUGIN
        assert result[0].plugin_dir == plugin_dir

    def test_skips_dirs_without_toml(self, tmp_path):
        (tmp_path / "no-toml").mkdir()
        result = load_plugins(tmp_path)
        assert result == []

    def test_loads_multiple_plugins_sorted(self, tmp_path):
        for name in ["beta", "alpha"]:
            d = tmp_path / name
            d.mkdir()
            (d / "plugin.toml").write_text(f'name = "{name}"\n')
        result = load_plugins(tmp_path)
        assert [c.name for c in result] == ["alpha", "beta"]

    def test_defaults_name_to_dir_name(self, tmp_path):
        d = tmp_path / "my-plugin"
        d.mkdir()
        (d / "plugin.toml").write_text('description = "no name field"\n')
        result = load_plugins(tmp_path)
        assert result[0].name == "my-plugin"

    def test_skips_files_in_plugin_dir(self, tmp_path):
        (tmp_path / "not-a-dir.txt").write_text("ignored")
        result = load_plugins(tmp_path)
        assert result == []
