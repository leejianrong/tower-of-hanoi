.DEFAULT_GOAL := help

.PHONY: help sync lint test compile check train replay dashboard-frame install-hooks

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make sync          Install dependencies with uv' \
		'  make lint          Run ruff' \
		'  make test          Run pytest' \
		'  make compile       Compile Python files' \
		'  make check         Run lint, test, and compile' \
		'  make train         Train the Q-learning agent and write telemetry' \
		'  make replay        Run the Pygame telemetry dashboard' \
		'  make dashboard-frame Render one dashboard frame to /tmp' \
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
	uv run python -m src.gui.dashboard_app

dashboard-frame:
	SDL_VIDEODRIVER=dummy uv run python -c 'from src.gui.dashboard import render_dashboard_frame; render_dashboard_frame("records/qlearningagent_training.json", "/tmp/tower_dashboard_frame.png"); print("/tmp/tower_dashboard_frame.png")'

install-hooks:
	cp scripts/hooks/pre-push .git/hooks/pre-push
	chmod +x .git/hooks/pre-push
