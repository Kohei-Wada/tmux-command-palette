# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A tmux command palette tool written in Python. Early-stage project.

## Development Setup

- Python 3.13+ (managed via `.python-version`)
- Uses `uv` as the package manager (pyproject.toml, no lock file yet)

## Commands

- **Run (dev)**: `uv run tmux-command-palette [pane_id]`
- **Test**: `uv run pytest tests/ -v`
- **Install**: `uv tool install .`
- **Add dependency**: `uv add <package>`
