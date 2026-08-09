# ADR-0002: Limit the MVP to tabular Q-learning

- Status: Accepted
- Date: 2026-08-09
- Deciders: Jian, Codex

## Context

The user's goal includes reinforcement learning examples such as Q-learning and deep Q-learning. The immediate visualization idea is a Q-table heatmap, which maps directly to tabular Q-learning but not to DQN.

## Decision

The first visualization milestone supports tabular Q-learning only. DQN is explicitly deferred until the training telemetry and replay dashboard are stable.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Include DQN now | It changes the data model, UI language, tests, and heatmap semantics. |
| Abstract all RL algorithms up front | Adds architecture before the first demo proves the visualization contract. |

## Consequences

The first build can focus on explainability and polish. Later DQN work will need a different visualization, likely value probes or policy summaries rather than a literal table.
