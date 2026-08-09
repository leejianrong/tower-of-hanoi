# ADR-0001: Use a complete training telemetry event log

- Status: Accepted
- Date: 2026-08-09
- Deciders: Jian, Codex

## Context

The existing project records only selected replay checkpoints every 200 episodes. That is enough to replay a final game but not enough to visualize learning. The target experience needs every episode, every explore/exploit decision, the resulting reward, and Q-table changes.

## Decision

Training will write a schema-versioned event log containing every episode and every step until the agent first solves the 5-disc puzzle in the optimal 31 moves, or until the configured maximum episode limit.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Keep 200-episode checkpoints | Too coarse to explain learning dynamics. |
| Live training dashboard only | Couples training speed and GUI timing too early. |
| Per-step video capture only | Not inspectable, not diffable, and cannot power alternate renderers. |

## Consequences

The renderer can be deterministic and repeatable. Tests can validate the artifact before the GUI exists. File size becomes a real concern, so the schema should avoid unnecessary duplication and include a version field from the start.
