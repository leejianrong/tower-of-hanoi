# ADR-0007: Playback is a pure function of a clock; the clock ends up in the browser

- Status: Accepted (server-side clock now, client-side clock in slice 3)
- Date: 2026-10-25
- Deciders: Jian, Claude
- Supersedes: ADR-0004

## Context

Indah updates a page by sending patches from Python over SSE. That suits a stat or a chart that
changes a few times a second. It does not suit a disc that lifts, travels and lands at 60 frames
a second, and every patch also pays proxy padding on hosted setups. A video export needs frames
that do not depend on network timing.

## Decision

1. Every visible value is a function of one number, the clock `t` in seconds. `Player.frame()`
   is that function (`src/dashboard/player.py`) and imports nothing from indah or a browser.
2. All pacing decisions live in Python (`src/replay/schedule.py`): which episodes play slowly,
   which flash by, how long each step is on screen. The result is a timeline of step start times
   and durations.
3. Slice 2 runs the clock on the server at 10 Hz and pushes frames as patches. This proves the
   layout and the function-of-time design.
4. Slice 3 moves the clock into the browser: the page downloads the compact replay and the
   timeline once and renders every frame locally. The browser only interpolates between
   positions the timeline gives it.
5. The browser clock has a manual mode where time advances only when told to. A video export
   steps it frame by frame and captures each frame, so exported video does not depend on timing.

## Consequences

- Smooth animation and scrubbing, no per-frame network traffic, and deterministic export.
- Frame logic that is shared across Python and JavaScript must be kept small: the state-id decode
  (ADR-0008) and interpolation. Timing stays in Python only.
- Until slice 3, the dashboard updates at 10 Hz and does not animate disc motion.
