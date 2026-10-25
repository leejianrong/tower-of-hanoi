# Agent brief

Trust the code and tests over any document, and fix the document. Plan: `PLAN.md`. Decisions:
`docs/adr/` (0001 to 0002 and 0005 to 0008 are current; 0003 and 0004 are superseded).

## What

Tower of Hanoi game logic, a Gymnasium env, a tabular Q-learning agent, and a browser dashboard
that replays a training run, built on the `indah` Python UI framework (no Node, no Pygame).

- `src/core`, `src/envs`, `src/agents`: game, env, agent, training telemetry.
- `src/replay`: telemetry to compact replay, Q-table rebuild, pacing schedule. No UI imports.
- `src/dashboard`: `Player` (frame = pure function of a clock), the indah app, two browser modules
  in `static/`.

## How

- `make sync`, `make check` (lint, test, compile), `make train` (also writes `records/replay.json`),
  `make dashboard`.
- Run tests with `uv run python -m pytest`, never `.venv/bin/pytest`.
- `src/replay` and `Player` must not import indah or a browser API: that is what keeps them testable.
- All pacing and timing decisions live in Python (`src/replay/schedule.py`); the browser only
  follows the schedule (ADR-0007).
- The state-id encoding in `src/replay/encoding.py` is a contract with the browser (ADR-0008). Change
  it only with the ADR and the JavaScript together.
- Do not install packages outside `pyproject.toml` (the dev group has what tests need); the tests
  call the ASGI app directly instead of using starlette's test client for that reason.
- Do not commit `records/*.json`, except the one fixture already tracked.
- Branch per slice, PR into `main`; `scripts/hooks/pre-push` runs `make check`.
