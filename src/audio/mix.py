"""Mix the cues into a soundtrack for the video (ADR-0010)."""

import numpy as np

from src.audio.cues import STEP_CUES, CueSettings, Cues
from src.audio.synth import SAMPLE_RATE

MASTER_GAIN = 0.8


def render_track(
    cues: Cues,
    sounds: dict[str, np.ndarray],
    *,
    start: float,
    end: float,
    speed: float = 1.0,
    settings: CueSettings | None = None,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Mono float samples for timeline ``[start, end)`` played at ``speed``.

    A cue at timeline time ``t`` lands at sample ``(t - start) / speed * sample_rate``: playback
    speed moves the sounds closer together but never changes their pitch. Above
    ``settings.max_playback_speed`` the per-step sounds are dropped, as they are in the browser.
    """
    settings = settings or CueSettings()
    length = round((end - start) / speed * sample_rate)
    track = np.zeros(length)
    drop_steps = speed > settings.max_playback_speed
    for index in cues.between(start - 1e-9, end - 1e-9):
        name = cues.names[cues.sound[index]]
        if drop_steps and name in STEP_CUES:
            continue
        at = round((cues.t[index] - start) / speed * sample_rate)
        clip = sounds[name][: length - at]
        track[at : at + len(clip)] += clip
    return np.clip(track * MASTER_GAIN, -1.0, 1.0)
