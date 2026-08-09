.PHONY: sync lint test compile check train replay install-hooks

sync:
	uv sync --dev

lint:
	uv run ruff check .

test:
	uv run python -m pytest

compile:
	uv run python -m compileall src train.py

check: lint test compile

train:
	uv run python train.py

replay:
	uv run python src/gui/renderer.py

install-hooks:
	cp scripts/hooks/pre-push .git/hooks/pre-push
	chmod +x .git/hooks/pre-push
