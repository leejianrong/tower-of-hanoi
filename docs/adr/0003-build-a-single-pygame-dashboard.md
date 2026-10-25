# ADR-0003: Build a single Pygame dashboard

- Status: Superseded by ADR-0006
- Date: 2026-08-09
- Deciders: Jian, Codex

## Context

The current project already uses Pygame for Tower of Hanoi replay. The rendered view has substantial unused space and can be expanded into an explainer dashboard without adding a web frontend.

## Decision

The milestone will use one Pygame dashboard: tower board, Q-table heatmap, epsilon decision gauge, reward animations, episode summary, and learning curve in one synchronized view.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Web UI | Better layout tools, but adds a second app stack before the RL data contract is stable. |
| Multiple windows | Makes video export and user comprehension worse. |
| CLI plus static charts | Does not deliver the animated learning story. |

## Consequences

One renderer can support interactive replay and video export. Pygame charting and layout need careful custom drawing, but the scope remains local and deterministic.
