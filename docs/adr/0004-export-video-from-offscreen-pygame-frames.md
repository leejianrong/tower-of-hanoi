# ADR-0004: Export video from offscreen Pygame frames

- Status: Superseded by ADR-0006 and ADR-0007 (frames now come from a browser)
- Date: 2026-08-09
- Deciders: Jian, Codex

## Context

The end goal is a YouTube-ready training visualization. Screen capture is easy manually but flaky for an agent, hard to reproduce, and awkward in CI/headless environments.

## Decision

The exporter will render deterministic frames through the same Pygame dashboard path, then encode the frames and audio with `ffmpeg`.

## Alternatives Considered

| Option | Why not |
|--------|---------|
| Live desktop screen recording | Fragile, display-dependent, and hard for agents to validate. |
| Separate video rendering library | Duplicates visual logic and risks drift from interactive replay. |
| Pygame-only video encoding | Pygame is not the right tool for final encoding/muxing. |

## Consequences

Preview and export share one renderer. The project gains an external runtime dependency on `ffmpeg` for video export, while normal training/tests can still run without exporting.
