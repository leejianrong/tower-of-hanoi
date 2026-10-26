import numpy as np
import pytest

from src.audio.cues import CueSettings, Cues
from src.audio.mix import MASTER_GAIN, render_track

SR = 1000
SOUNDS = {"tick": np.full(10, 0.5), "lift": np.full(10, 0.25), "big": np.full(5000, 0.9)}


def _cues(*pairs):
    names = sorted({n for _, n in pairs})
    return Cues(names, [t for t, _ in pairs], [names.index(n) for _, n in pairs])


def test_a_cue_lands_at_its_time_in_video_seconds():
    cues = _cues((10.0, "tick"), (10.5, "tick"))
    track = render_track(cues, SOUNDS, start=10, end=12, sample_rate=SR)
    assert len(track) == 2000
    assert track[0] == pytest.approx(0.5 * MASTER_GAIN) and track[9] == track[0] and track[10] == 0
    assert track[500] == pytest.approx(0.5 * MASTER_GAIN)


def test_speed_compresses_cue_positions_but_not_the_sounds():
    cues = _cues((0.0, "tick"), (8.0, "tick"))
    track = render_track(cues, SOUNDS, start=0, end=16, speed=4, sample_rate=SR)
    assert len(track) == 4000
    assert track[2000] == pytest.approx(0.5 * MASTER_GAIN) and track[2009] == track[2000]
    assert track[2010] == 0  # still 10 samples long


def test_cues_outside_the_span_are_left_out():
    cues = _cues((1.0, "tick"), (5.0, "tick"))
    track = render_track(cues, SOUNDS, start=2, end=4, sample_rate=SR)
    assert not track.any()


def test_a_sound_that_runs_past_the_end_is_cut_not_an_error():
    track = render_track(_cues((0.9, "big")), SOUNDS, start=0, end=1, sample_rate=SR)
    assert len(track) == 1000 and track[899] == 0 and track[999] > 0


def test_fast_playback_drops_per_step_sounds_but_keeps_the_rest():
    cues = _cues((1.0, "lift"), (2.0, "tick"))
    settings = CueSettings(max_playback_speed=4)
    slow = render_track(cues, SOUNDS, start=0, end=8, speed=2, settings=settings, sample_rate=SR)
    fast = render_track(cues, SOUNDS, start=0, end=16, speed=8, settings=settings, sample_rate=SR)
    assert slow[500] > 0
    assert fast[125] == 0  # lift is a step sound: dropped
    assert fast[250] > 0  # tick is not: kept


def test_overlapping_sounds_add_and_then_clip():
    loud = {"x": np.full(10, 0.9)}
    track = render_track(_cues((0.0, "x"), (0.0, "x"), (0.0, "x")), loud, start=0, end=1, sample_rate=SR)
    assert track.max() == 1.0
