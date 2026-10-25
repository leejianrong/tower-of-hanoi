# Contributing

## Setup

```bash
make sync            # uv sync --dev
make install-hooks   # runs `make check` before every push
```

Python 3.11+, [uv](https://docs.astral.sh/uv/). The dashboard depends on `indah`, which ships its
own pre-built frontend: no Node is needed.

## Checks

`make check` runs ruff, pytest and a compile check. Tests are deterministic and need no display or
network; the integration fixture trains a small 3-disc agent in about a second. Use
`uv run python -m pytest`, not the `.venv/bin/pytest` script, whose shebang goes stale when the
repo moves.

## Workflow

Branch per slice, PR into `main`. Generated files under `records/` are local artifacts and stay out
of git unless a small fixture is explicitly wanted. Update the README, `AGENTS.md` and the ADRs in
the same PR as the change they describe. Architecture decisions go in `docs/adr/`; the plan is in
`PLAN.md`.
