# ADR-0009: Export video by stepping the clock and capturing every frame

- Status: Accepted
- Date: 2026-10-27
- Deciders: Jian, Claude
- Builds on: ADR-0007

## Context

The video must look the same on every export. A real-time screen recording captures a frame
whenever the machine gets to it, so a busy CPU drops or repeats frames and the length drifts.
ADR-0007 already made every visible value a function of one clock; the exporter only has to drive
that clock by hand.

## Decision

1. `?record=1` puts the stage in recorder mode: the clock never advances by itself, the transport
   controls are hidden and CSS transitions are off (they run on real time). The page exposes
   `window.hanoiRecorder.seek(t)`.
2. `seek(t)` draws the board and pie for exactly `t`, reports `t` to Python through the normal
   `tick` event, and resolves only when Python has set the `applied_t` prop to that same `t` and the
   page has painted twice. Python sets `applied_t` last, after the charts and the Q-table.
3. `src/video` plans the frames (`plan.py`, pure), then each worker drives its own headless Chromium
   page through its run of frames, screenshots, and pipes the PNG into its own ffmpeg process
   (`capture.py`). The segments are joined with ffmpeg's concat demuxer without re-encoding.
4. Video time `i / fps` maps to timeline time `start + i * speed / fps`, so `--speed` turns a long
   timeline into a short video.
5. Playwright is an optional dependency group (`video`), imported lazily; `make check` and CI run
   without it and skip the browser tests.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Record the screen in real time (Playwright `recordVideo`, a screen recorder) | Not repeatable, drops frames under load |
| Chrome BeginFrame control or virtual time | Experimental, and fragile under WSL |
| Save every frame as a PNG, then encode | 47,000 frames would take gigabytes; piping avoids the disk |
| Wait a fixed delay after each seek | Either too slow everywhere or wrong when the machine is busy; the acknowledgement is exact |

## Consequences

- Export is slow but exact: about 6 frames a second with two workers on the development machine,
  so a minute of 60 fps video takes about ten minutes. More workers help until the CPU is full.
- `tests/video/test_capture.py` proves the acknowledgement: it delays Python by 250 ms and checks
  that the frame taken right after `seek` equals the frame taken once the page is idle. Without the
  wait that test fails.
- Pacing is unchanged and still lives in Python; the exporter only samples the timeline.
- The hidden transport leaves empty space in the stage card; the layout pass for the video can use it.
