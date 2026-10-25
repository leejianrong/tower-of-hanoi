# ADR-0008: A compact, columnar replay format derived from telemetry

- Status: Accepted
- Date: 2026-10-25
- Deciders: Jian, Claude
- Amends: ADR-0001 (telemetry stays the full log; the dashboard reads a derived replay)

## Context

Telemetry (ADR-0001) is complete but large: 70 MB for 655 episodes, mostly because every episode
stores a Q-table snapshot and every step stores full state tuples. A browser should not download
that. Q-learning is deterministic, so the snapshots are redundant: the table at any step is zero
plus every `(state, action) -> q_after` update so far.

## Decision

`python -m src.replay` converts telemetry to `records/replay.json` (about 2.7 MB for the same
run), schema `replay_schema_version: 1`:

- `config`: discs, step limit, learning parameters, seed.
- `episodes`: parallel arrays `start` (one extra entry, the total step count), `epsilon`
  (at the start of the episode), `reward`, `solved`, `optimal`.
- `steps`: parallel arrays `state`, `action`, `explore`, `reward`, `next_state`, `q_after`
  (the updated Q of that state and action), `draw` (the exploration random draw).

A state id is the rod of each disc in base 3: disc `d` on rod `r` adds `r * 3**d`, so the start
state is 0 and a 5-disc game has 243 states. Within a rod the bigger disc is below, so the id fixes
the whole picture. Actions are `(0,1) (0,2) (1,0) (1,2) (2,0) (2,1)`, as in `TowerEnv`.

The Q-table at any step is rebuilt by replaying updates (`QReplayer`), with checkpoints so
scrubbing backwards is cheap. Legal moves are derived from the state id, never stored per step.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Send the telemetry as is | 70 MB, and the browser would parse state tuples it does not need. |
| Drop per-episode Q snapshots from telemetry | Would change the tested v1 schema; the replay conversion gets the same saving without that. |
| Binary format now | JSON at 2.7 MB is fine for local use; the columnar layout maps straight onto typed arrays later. |

## Consequences

- The dashboard needs `make train` then `make replay-data` (`make train` does both).
- The state-id rule is part of the contract with the browser (ADR-0007) and is tested against the
  environment's own action masks.
