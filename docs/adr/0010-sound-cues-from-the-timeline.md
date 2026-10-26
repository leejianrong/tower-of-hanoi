# ADR-0010: Sound cues are derived from the timeline and shared by the browser and the video

- Status: Accepted
- Date: 2026-10-27
- Deciders: Jian, Claude
- Builds on: ADR-0005, ADR-0007, ADR-0009

## Context

ADR-0005 chose generated, licence-clean sound effects. The sounds have to line up with the board
in two places: live in the browser, and in the exported video. Two separate implementations of
"which sound plays when" would drift, as the schedule would have if the browser had decided it.

## Decision

1. `src/audio/synth.py` renders every effect from code (NumPy) and writes WAVs to
   `src/dashboard/static/audio/`, committed. A test fails if the files differ from a fresh render.
2. `src/audio/cues.py` turns the replay and the schedule into one sorted list of `(time, sound)`:
   per step, an explore or exploit blip at the start, a lift just after, a landing pitched by disc
   size at the end and a Q-update tick (up or down with the sign of the change); per episode, a
   `solved`, `record` or `fail` sound at the end and a `final` fanfare for the first optimal solve.
   Steps shorter than 0.25 s get no per-step sounds, and a failed episode shorter than 1 s is silent,
   so flashing episodes under storyboard pacing do not turn into noise. `CueSettings` holds these knobs.
3. The browser fetches `/hanoi/cues.json` and the WAVs only after a click or key (autoplay rules),
   then plays the cues the clock passes each frame (`cuesBetween` in `replay-core.js`, checked
   against Python). Seeks, pauses and playback above 4x play nothing. `M` or the speaker button
   mutes; the choice is kept in `localStorage`.
4. The exporter mixes the same cues and WAVs into a mono track with `src/audio/mix.py`, sample
   accurate (`(t - start) / speed * 44100`), exactly as long as the video, and muxes it as AAC.
   `--no-audio` skips it. At speeds above 4x the per-step sounds are dropped there too.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Synthesise in the browser with WebAudio | A second implementation of every sound; the video would need it again |
| Record the browser's audio while exporting | Real-time again, which ADR-0009 avoids |
| Put the cue rules in JavaScript | Timing decisions live in Python (ADR-0007) |

## Consequences

- What you hear live is what the video contains, because both read the same cue list and samples.
- The cue list is 340,000 entries for the full run (about 4 MB as JSON); it is fetched lazily.
- With constant 0.6 s steps the full run has a sound on every step. The storyboard pass will decide
  which of them stay; `CueSettings` is where that goes.
- The live check hooks `AudioBufferSourceNode.start` in headless Chromium, so nothing proves how
  it sounds on a real speaker; listen to a short export before trusting a mix.
