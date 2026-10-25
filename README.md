# Tower of Hanoi, learning to solve itself

Train a Q-learning agent on 5-disc Tower of Hanoi, then replay every episode in the browser: the
board, the explore-or-exploit decision, the whole Q-table and the learning curves on one screen,
paced to be watched and recorded.

```mermaid
flowchart LR
    A[make train] -->|every step, 70 MB| B[telemetry]
    B -->|make replay-data| C[replay.json, 2.7 MB]
    C -->|make dashboard| D[browser dashboard]
```

![The dashboard mid-run: a disc lifting off one rod, with the pie, charts and Q-table](docs/img/dashboard.png)

The board animates (a disc lifts over its rod, travels across and lands on the other stack), and
the charts and Q-table follow the clock. Fitting everything on one screen, bars and a scatter chart
are next; see [PLAN.md](PLAN.md).

## Quick start

Needs Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                # install
make train             # about 30 s: trains, then writes records/replay.json
make dashboard         # prints a local URL; open it in a browser (plays about 11 minutes at 1x)
```

Seed 7 reaches its first optimal 31-move solution at episode 655.

## Usage

Controls: space plays or pauses, the arrow keys step (with shift, jump an episode), the speed buttons
run 1x to 64x, and the slider scrubs. `?t=120&paused=1` on the URL opens at 120 seconds, paused.

Replay the run you just trained, or point the dashboard at another replay file:

```bash
uv run python -m src.dashboard records/replay.json
```

Train with other settings from Python:

```python
from train import train

train("records/small.json", num_discs=4, max_steps=100, max_episodes=500, seed=1)
```

Then convert it with `uv run python -m src.replay records/small.json records/replay.json`.

Play the game yourself in the terminal with `uv run python -m src.core.game`; moves are saved to
`records/`.

## Project layout

- `src/core`, `src/envs`, `src/agents`: the game, a Gymnasium environment and the Q-learning agent.
- `src/replay`: converts training telemetry into a compact replay and a watchable timeline.
- `src/dashboard`: the [indah](https://github.com/leejianrong/indah) app and its browser modules.
- `docs/adr`: architecture decisions. `PLAN.md`: where the project is going.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run `make check` before pushing.

## License

No licence file yet, so all rights are reserved until one is added.
