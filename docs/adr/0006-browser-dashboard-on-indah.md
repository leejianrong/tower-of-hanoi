# ADR-0006: Build the dashboard in the browser on indah, drop pygame

- Status: Accepted
- Date: 2026-10-25
- Deciders: Jian, Claude
- Supersedes: ADR-0003

## Context

ADR-0003 chose one Pygame window for the replay dashboard. Pygame repeatedly crashed the WSL
environment, so it could not be run or tested reliably. The target layout also grew past what
hand-drawn Pygame handles well: a 243 by 6 heatmap, five charts, a pie and a board on one
1920 by 1080 screen, in two colour themes. The end goal is still a screen recording for YouTube.

## Decision

The dashboard is a web page served by [indah](https://github.com/leejianrong/indah), a Python UI
framework with a pre-built frontend (no Node at install or runtime). Python builds the page from
indah components. Two pieces indah lacks, the board and the explore/exploit pie, are small ES
modules registered through indah's web-component bridge (indah ADR-0039). Pygame is removed.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Keep Pygame, fix the WSL crashes | The cause is outside this repo, and the layout work is the larger cost. |
| Svelte + Vite app | A second toolchain (Node) and a second language for all logic. Indah gives reactive charts and a heatmap already, and improving indah is a goal of this project. |
| Matplotlib or Pillow frames only | No interactive replay, and every chart would be redrawn by hand. |

## Consequences

- The app depends on `indah>=0.9.0`. Gaps in indah (chart kinds, heatmap highlights, a pie, a
  fixed-viewport frame, named palettes) are tracked in PLAN.md and upstreamed as indah ADRs.
- Rendering happens in the viewer's browser, so tests need no display. Visual checks are manual
  until a browser test is added.
- ADR-0004's offscreen-Pygame export is replaced by frame capture from the browser (ADR-0007).
