# Plan: browser dashboard for the Q-learning replay

Status: slices 1 to 3 done, slice 4 next. Supersedes the Pygame plan in `docs/archive/`.

## Goal

A single-screen (1920 x 1080, no scrolling) dashboard that replays a Q-learning run on Tower of
Hanoi from the first random episode to the first optimal 31-move solve, ready to screen-record for
YouTube. It shows the board, the explore/exploit decision, the full Q-table, and charts across and
within episodes, in dark and light themes (palette "Graphite and Citrus").

A second goal: find what [indah](https://github.com/leejianrong/indah) is missing for dashboards
like this and upstream it. Where indah falls short we say so here rather than work around it quietly.

## Decisions

| Decision | Why | ADR |
|----------|-----|-----|
| Build on indah in the browser, remove Pygame | Pygame crashed WSL; the layout outgrew hand-drawn UI | 0006 |
| Every frame is a pure function of one clock; the clock moves to the browser | Smooth 60 fps motion, scrubbing, deterministic video export | 0007 |
| Derive a compact columnar replay (2.7 MB) from telemetry (70 MB) | The Q-table is reproducible from the updates | 0008 |
| Board and pie live in this repo as indah bridge modules first, upstream later | Prove them before widening indah | 0006 |

### Server clock vs client clock

*Server clock:* Python decides what is on screen at every moment and sends each change over the
network. Simple, and every viewer is in sync, but motion is limited to a few updates a second,
every update crosses the network, and the video would depend on timing.

*Client clock:* the browser gets the whole replay once, then runs its own clock and draws each
frame itself. Python still decides the pacing (the timeline), the browser only follows it. Motion
is smooth, scrubbing is instant, and an exporter can advance the clock by hand, one frame at a
time. Slice 2 uses the server clock on purpose, to prove the layout; slice 3 swaps it.

## Shape

```mermaid
flowchart LR
    T[train.py] -->|telemetry 70 MB| C[src/replay<br/>convert]
    C -->|replay.json 2.7 MB| P[Player<br/>frame = f of clock]
    S[Pacing schedule<br/>Python] --> P
    P -->|slice 2: patches at 10 Hz| I[indah page]
    P -.->|slice 3: replay + schedule, once| B[browser clock]
    B -.-> I
```

## Slices

| # | Slice | Status |
|---|-------|--------|
| 1 | Data layer: state ids, compact replay, Q-table rebuild, pacing schedule; Pygame removed | Done |
| 2 | Dashboard on today's indah with a server clock: layout, charts, heatmap, board and pie modules (no motion) | Done |
| 3 | Browser clock, board animation (lift, travel over, descend; no arrow), transport and scrubbing, pacing caps | Done |
| 4 | Indah features below, each as an indah ADR and card | Next |
| 5 | Deterministic clock, `?record` mode, frame capture and ffmpeg export | |
| 6 | Sound cues synced to the clock (ADR-0005), auto-pacing polish | |

## What indah lacks for this dashboard

Found while building slice 2; slice 4 upstreams the generic ones.

| Gap | Today | Needed |
|-----|-------|--------|
| G1 Fixed viewport | `Grid`/`Row`/`Column` flow and scroll | A `Frame` that fits one screen (1920 x 1080 scaled to the window), plus a record mode |
| G2 Chart kinds | Line, optional points | Bars, a playhead, shaded future region, dashed reference lines, a ghost series |
| G3 Heatmap | `magma`/`viridis`/`gray`; empty cells paint as the lowest colour | Masked cells, labels, current-cell highlight, custom diverging colours, cell aspect |
| G4 Pie | None | A pie with one lit slice |
| G5 Theming | Core roles plus `x-` extras, usable by modules only | Charts and canvases that read tokens, so the theme toggle recolours them |
| G6 Client clock | None | A browser-side playback clock with a manual mode for export |
| G7 Large data | Props go through patches | Fetch a static dataset once (typed arrays) |
| G8 Sound cues | `Audio` plays a file | Cues fired from clock events |

Seen in the screenshots of slice 3: a chart in `points` mode still draws its line, so the reward and
steps charts read as spikes (wants a scatter kind, G2); the heatmap paints unvisited zeros and
negatives with opposite ends of one colour scale and cannot tell an illegal move from a very
negative Q (G3); and the page is taller than one screen (G1).

## Pacing

`Pacing` in `src/replay/schedule.py` sets the length of the video. The first run took 19 minutes at
1x because 172 solved episodes played at 0.06 s a step. Now a solved episode is capped at 2 s, one
that beats the best so far is slowed (0.15 s a step, up to 8 s), a failed one flashes by in 0.3 s:
the 655-episode run plays in about 10.8 minutes. Tune it by editing the defaults; the controls scale
it from 1x to 64x.

## Risks

- The charts and the Q-table follow the browser clock through the server, so they trail the board by
  up to one tick (200 ms, 50 ms at 16x and above). Moving them client-side needs G2, G3 and G7.
- The Q update appears when the disc has landed (90% of the step, `UPDATE_PHASE`); change it freely.
- Headless Chromium works under WSL (screenshots in this repo's history were taken with it) but is
  heavy; export in slice 5 may still fall back to a Windows screen recorder.
