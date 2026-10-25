# ADR-0007: Playback is a pure function of a clock; the clock ends up in the browser

- Status: Accepted. Built in slice 3 (the browser clock); see Slice 3 below.
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

## Slice 3, as built

- `hanoi-stage` (`src/dashboard/static/hanoi-stage.js`) is one indah bridge module holding the
  board, the explore/exploit pie and the transport controls (play, step, episode jump, speed,
  scrubber). It downloads `/hanoi/replay.json` once and runs the clock with `requestAnimationFrame`.
- Python follows. The module reports the playhead in a `tick` event (every 200 ms, every 50 ms at
  16x and 64x so the charts keep up); `Player.seek` moves to that time and the charts, Q-table and
  progress readouts update from it. The charts stay indah components for now, so they trail the
  board by up to one tick.
- The pure part, `replay-core.js`, decodes state ids, finds the step for a time and computes every
  disc's position. It is served by the app, tested under Node (`tests/js`) and checked against the
  Python rules (`tests/dashboard/test_js_contract.py`). That test found real drift: the schedule
  sent to the browser was rounded and Python's was not, so times are now kept to four decimals
  on both sides.
- A move is three phases of one step: the disc lifts clear above its rod, travels over, then
  descends onto the top of the target stack (`PHASE` in `replay-core.js`). There is no arrow.
- `?t=<seconds>&paused=1` opens at a time, paused. The manual-advance clock for export is slice 5.
