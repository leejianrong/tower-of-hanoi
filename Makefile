.DEFAULT_GOAL := help

.PHONY: help sync lint test compile check train replay install-hooks

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make sync          Install dependencies with uv' \
		'  make lint          Run ruff' \
		'  make test          Run pytest' \
		'  make compile       Compile Python files' \
		'  make check         Run lint, test, and compile' \
		'  make train         Train the Q-learning agent' \
		'  make replay        Run the Pygame replay visualizer' \
		'  make install-hooks Install the local pre-push hook'

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
