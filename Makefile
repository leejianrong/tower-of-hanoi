.DEFAULT_GOAL := help

.PHONY: help sync lint test compile check train replay-data dashboard video install-hooks

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make sync          Install dependencies with uv' \
		'  make lint          Run ruff' \
		'  make test          Run pytest and the Node tests for the browser core' \
		'  make compile       Compile Python files' \
		'  make check         Run lint, test, and compile' \
		'  make train         Train the Q-learning agent and write telemetry' \
		'  make replay-data   Convert training telemetry to the compact replay' \
		'  make dashboard     Serve the browser dashboard (needs records/replay.json)' \
		'  make video         Export the dashboard to records/hanoi.mp4 (ARGS="--end 60 --speed 4")' \
		'  make install-hooks Install the local pre-push hook'

sync:
	uv sync --dev

lint:
	uv run ruff check .

test:
	uv run python -m pytest
	node --test "tests/js/*.test.mjs"

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

video:
	uv run --group video python -m src.video $(ARGS)

install-hooks:
	cp scripts/hooks/pre-push .git/hooks/pre-push
	chmod +x .git/hooks/pre-push
