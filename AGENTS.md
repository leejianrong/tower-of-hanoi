# Agent brief

Trust the code and tests over any document, and fix the document. Plan: `PLAN.md`. Decisions:
`docs/adr/` (0001 to 0002 and 0005 to 0009 are current; 0003 and 0004 are superseded).

## What

Tower of Hanoi game logic, a Gymnasium env, a tabular Q-learning agent, and a browser dashboard
that replays a training run, built on the `indah` Python UI framework (no Node, no Pygame).

- `src/core`, `src/envs`, `src/agents`: game, env, agent, training telemetry.
- `src/replay`: telemetry to compact replay, Q-table rebuild, pacing schedule. No UI imports.
- `src/dashboard`: `Player` (what Python shows at a time `t`), the indah app, and `static/`:
  `hanoi-stage.js` (board, pie, transport, the browser clock) and `replay-core.js` (pure lookup and
  animation maths, tested under Node).
- `src/video`: video export. `plan.py` is pure; `capture.py` drives headless Chromium and ffmpeg.

## How

- `make sync`, `make check` (lint, pytest, Node tests in `tests/js`, compile), `make train` (also writes `records/replay.json`),
  `make dashboard`.
- Run tests with `uv run python -m pytest`, never `.venv/bin/pytest`.
- `src/replay` and `Player` must not import indah or a browser API: that is what keeps them testable.
- All pacing and timing decisions live in Python (`src/replay/schedule.py`); the browser only
  follows the schedule (ADR-0007). `tests/dashboard/test_js_contract.py` fails if Python and
  `replay-core.js` disagree.
- Video export needs `uv sync --group video`, `uv run playwright install chromium` and ffmpeg;
  `make video`. Browser tests in `tests/video` skip without them. Anything in the page that moves
  on real time (CSS transitions, `requestAnimationFrame` deltas) must be off in `?record=1` mode.
- Indah reads a module once at startup: restart `make dashboard` after editing `static/*.js`.
- Check UI changes with a screenshot from headless Chromium; the tests do not draw anything.
- The state-id encoding in `src/replay/encoding.py` is a contract with the browser (ADR-0008). Change
  it only with the ADR and the JavaScript together.
- Do not install packages outside `pyproject.toml` (the dev group has what tests need); the tests
  call the ASGI app directly instead of using starlette's test client for that reason.
- Do not commit `records/*.json`, except the one fixture already tracked.
- Branch per slice, PR into `main`; `scripts/hooks/pre-push` runs `make check`. Merge with
  `gh pr merge --squash` once CI is green. Commits must use the GitHub noreply email: the private
  one is rejected on push.
- Update README, PLAN and the ADRs in the PR that changes what they describe; the README
  screenshot is `docs/img/dashboard.png`, retake it when the layout changes.
