# Contributing

## Setup

```bash
make sync            # uv sync --dev
make install-hooks   # runs `make check` before every push
```

Python 3.11+, [uv](https://docs.astral.sh/uv/). The dashboard depends on `indah`, which ships its
own pre-built frontend. Node 20+ is needed only to run the browser-maths tests in `make check`.

## Checks

`make check` runs ruff, pytest, the Node tests for the browser maths (`tests/js`) and a compile
check. Tests are deterministic and need no display or
network; the integration fixture trains a small 3-disc agent in about a second. Use
`uv run python -m pytest`, not the `.venv/bin/pytest` script, whose shebang goes stale when the
repo moves.

Changed a sound in `src/audio/synth.py`? Run `uv run python -m src.audio` and commit the WAVs; a test
fails if they are stale.

Video export (`make video`) also needs ffmpeg and the optional group: `uv sync --group video`, then
`uv run playwright install chromium`. Without them the browser tests in `tests/video` are skipped.

## Workflow

Branch per slice, PR into `main`. Generated files under `records/` are local artifacts and stay out
of git unless a small fixture is explicitly wanted. Update the README, `AGENTS.md` and the ADRs in
the same PR as the change they describe. Architecture decisions go in `docs/adr/`; the plan is in
`PLAN.md`.
