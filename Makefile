install:
	uv tool install --force --reinstall .

test:
	uv run pytest tests/ -v
