# Tower of Hanoi (RL + Visualization)

A small Tower of Hanoi project with three pieces:
- A terminal game loop to play manually.
- A Gymnasium-compatible environment + Q-learning agent.
- A Pygame replay visualizer for recorded games.

## Requirements
- Python 3.11+
- Dependencies: `gymnasium`, `numpy`, `pygame`

## Setup

If you use `uv`:

```bash
uv sync
```

If you use `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run The Game (CLI)

Runs a simple terminal-based game loop and records your moves into `records/`.

```bash
python -m src.core.game
```

Notes:
- You will be prompted for `start` and `target` rod indices (0, 1, 2).
- The recording is saved as `records/record_YYYY_MM_DD_HH_MM_SS.json`.

## Run The Visualization (Pygame Replay)

Runs the telemetry dashboard for `records/qlearningagent_training.json`.

```bash
python -m src.gui.dashboard_app
```

Notes:
- Run `python train.py` first if `records/qlearningagent_training.json` does not exist.
- The legacy move-history renderer still exists in `src/gui/renderer.py`.
- To render one dashboard frame headlessly, run `make dashboard-frame`.
- To render a deterministic in-motion replay frame headlessly, run
  `make dashboard-animation-frame`.
- To start the interactive replay, run `make replay`; close it with
  `make replay-stop`, and inspect startup errors with `make replay-log`.

## Training (Q-learning)

Runs a Q-learning loop and writes a complete training telemetry file to `records/`.
The trainer records every episode and every explore/exploit decision with rewards,
then stops early when the agent first solves the 5-disc puzzle in the optimal 31 moves.

```bash
python train.py
```

Notes:
- Training uses `TowerEnv` from `src/envs/tower_env.py`.
- Telemetry is written as `records/qlearningagent_training.json`.
- The existing Pygame renderer still replays legacy move-history JSON files.

## Project Layout

- `src/core/` core Tower of Hanoi logic and CLI game loop
- `src/envs/` Gymnasium environment
- `src/agents/` Q-learning agent
- `src/gui/` Pygame visualization + replay
- `records/` saved game histories for replay
- `train.py` training entrypoint

## Tips

- If Pygame fails to open a window (e.g., on a headless machine), run locally with a display server or use a remote desktop.
- If you change the number of discs in training, update the GUI settings to match before replaying (see `src/gui/tower.py` and `src/gui/renderer.py`).
