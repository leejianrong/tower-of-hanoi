.DEFAULT_GOAL := help

.PHONY: help sync lint test compile check train replay-data dashboard install-hooks

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make sync          Install dependencies with uv' \
		'  make lint          Run ruff' \
		'  make test          Run pytest' \
		'  make compile       Compile Python files' \
		'  make check         Run lint, test, and compile' \
		'  make train         Train the Q-learning agent and write telemetry' \
		'  make replay-data   Convert training telemetry to the compact replay' \
		'  make dashboard     Serve the browser dashboard (needs records/replay.json)' \
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
	uv run python -m src.replay

replay-data:
	uv run python -m src.replay

dashboard:
	uv run python -m src.dashboard

install-hooks:
	cp scripts/hooks/pre-push .git/hooks/pre-push
	chmod +x .git/hooks/pre-push
