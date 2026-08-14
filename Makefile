.DEFAULT_GOAL := help

REPLAY_PID_FILE ?= /tmp/tower_of_hanoi_replay.pid
REPLAY_LOG_FILE ?= /tmp/tower_of_hanoi_replay.log

.PHONY: help sync lint test compile check train replay replay-stop replay-log dashboard-frame dashboard-animation-frame install-hooks

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make sync          Install dependencies with uv' \
		'  make lint          Run ruff' \
		'  make test          Run pytest' \
		'  make compile       Compile Python files' \
		'  make check         Run lint, test, and compile' \
		'  make train         Train the Q-learning agent and write telemetry' \
		'  make replay        Start the Pygame telemetry dashboard' \
		'  make replay-stop   Gracefully close the replay window' \
		'  make replay-log    Show replay startup/runtime logs' \
		'  make dashboard-frame Render one dashboard frame to /tmp' \
		'  make dashboard-animation-frame Render one animation frame to /tmp' \
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
	@if test -r "$(REPLAY_PID_FILE)" && kill -0 "$$(cat "$(REPLAY_PID_FILE)")" 2>/dev/null; then \
		echo "Replay is already running (PID $$(cat "$(REPLAY_PID_FILE)"))."; exit 1; \
	fi
	@rm -f "$(REPLAY_PID_FILE)"
	@REPLAY_PID_FILE="$(REPLAY_PID_FILE)" uv run python -m src.gui.dashboard_app >"$(REPLAY_LOG_FILE)" 2>&1 & echo $$! >"$(REPLAY_PID_FILE)"; \
	 echo "Replay started. Run 'make replay-stop' to close it gracefully."; \
	 echo "Logs: $(REPLAY_LOG_FILE)"

replay-stop:
	@if ! test -r "$(REPLAY_PID_FILE)"; then echo "Replay is not running."; exit 0; fi
	@pid=$$(cat "$(REPLAY_PID_FILE)"); \
	if ! kill -0 "$$pid" 2>/dev/null; then rm -f "$(REPLAY_PID_FILE)"; echo "Removed stale replay PID file."; exit 0; fi; \
	kill -TERM "$$pid"; \
	for attempt in 1 2 3 4 5 6 7 8 9 10; do \
		if ! kill -0 "$$pid" 2>/dev/null; then rm -f "$(REPLAY_PID_FILE)"; echo "Replay stopped gracefully."; exit 0; fi; \
		sleep 0.1; \
	done; \
	echo "Replay did not stop within one second; inspect $(REPLAY_LOG_FILE)."; exit 1

replay-log:
	@if test -f "$(REPLAY_LOG_FILE)"; then tail -n 40 "$(REPLAY_LOG_FILE)"; else echo "No replay log found."; fi

dashboard-frame:
	SDL_VIDEODRIVER=dummy uv run python -c 'from src.gui.dashboard import render_dashboard_frame; render_dashboard_frame("records/qlearningagent_training.json", "/tmp/tower_dashboard_frame.png"); print("/tmp/tower_dashboard_frame.png")'

dashboard-animation-frame:
	SDL_VIDEODRIVER=dummy uv run python -c 'from src.gui.dashboard import render_dashboard_animation_frame; render_dashboard_animation_frame("records/qlearningagent_training.json", "/tmp/tower_dashboard_animation_frame.png", animation_frame=1); print("/tmp/tower_dashboard_animation_frame.png")'

install-hooks:
	cp scripts/hooks/pre-push .git/hooks/pre-push
	chmod +x .git/hooks/pre-push
