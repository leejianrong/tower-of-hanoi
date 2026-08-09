# Agent Brief

Trust the code and tests over this document if they disagree.

## Project

Tower of Hanoi game logic, a Gymnasium environment, a Q-learning agent, and a Pygame replay visualizer.

## Commands

- Install dependencies: `make sync`
- Run all cheap checks: `make check`
- Lint: `make lint`
- Test: `make test`
- Compile check: `make compile`
- Train Q-learning agent: `make train`
- Run replay visualizer: `make replay`
- Install local pre-push hook: `make install-hooks`

Use `uv run python -m pytest`, not the direct `.venv/bin/pytest` script, because virtualenv script shebangs can go stale when this repo moves.

## Workflow

- Work branch-per-slice once the GitHub repo is initialized.
- Keep `main` protected and PR-only after the bootstrap commit is pushed.
- Generated training records are local artifacts. Do not commit new `records/qlearningagent_*.json` or timestamped `records/record_*.json` files unless explicitly requested as fixtures.
- Core tests should stay no-infra and deterministic.

## Test Focus

- `src/core/`: Tower, Rod, and Disc behavior.
- `src/envs/`: Gymnasium reset/step semantics, rewards, action masks, truncation.
- `src/agents/`: Q-table initialization, masked action selection, learning update.
- `src/gui/`: keep importable and compile-clean; visual behavior needs manual verification unless a headless GUI test is added.
