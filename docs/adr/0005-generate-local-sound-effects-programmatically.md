# ADR-0005: Generate local sound effects programmatically

- Status: Accepted
- Date: 2026-08-09
- Deciders: Jian, Codex

## Context

The video should include fun sounds: beeps, boops, coin clinks, short arpeggios, decision cues, penalties, and celebration stingers. Because the result may be uploaded to YouTube, licensing must be clean and reproducible.

## Decision

The project will include a small Python sound generator that writes short WAV assets into `src/gui/assets/audio/`. It will use NumPy and stdlib WAV writing first, with `ffmpeg` only for optional conversion or final video muxing.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Download sound packs | Adds licensing and attribution risk. |
| Use an MCP sound-notification server | Existing examples mostly play IDE notification sounds; they do not generate project assets. |
| Use AI audio generation for all sounds | Heavy, less deterministic, harder to test, and unnecessary for arcade micro-SFX. |
| Require SoX/Csound/FluidSynth | Good tools, but not installed locally and not needed for the first simple generated assets. |

## Consequences

Codex or Claude Code can regenerate and tweak sounds from source parameters. The sounds may initially be more chiptune than realistic, but they are license-clean, deterministic, and easy to replace.
