import numpy as np
import pytest

from src.audio.synth import AUDIO_DIR, MAX_DISCS, SAMPLE_RATE, build_sounds, to_pcm16, write_all


def test_every_sound_is_audible_bounded_and_short():
    for name, samples in build_sounds().items():
        assert 0.05 < len(samples) / SAMPLE_RATE < 2.5, name
        assert 0.05 < np.abs(samples).max() <= 1.0, name
        assert np.isfinite(samples).all(), name


def test_sounds_are_deterministic():
    first, second = build_sounds(), build_sounds()
    assert first.keys() == second.keys()
    assert all(np.array_equal(first[name], second[name]) for name in first)


def test_committed_wav_files_match_the_synthesiser(tmp_path):
    """Edit synth.py and forget `python -m src.audio`, and this fails."""
    written = write_all(tmp_path)
    assert {p.name for p in written} == {p.name for p in AUDIO_DIR.glob("*.wav")}
    for path in written:
        assert path.read_bytes() == (AUDIO_DIR / path.name).read_bytes(), path.name


def _pitch(samples):
    spectrum = np.abs(np.fft.rfft(samples))
    return np.argmax(spectrum) * SAMPLE_RATE / len(samples)


def test_bigger_discs_land_lower():
    sounds = build_sounds()
    pitches = [_pitch(sounds[f"land_{d}"]) for d in range(MAX_DISCS)]
    assert pitches == sorted(pitches, reverse=True)
    assert pitches[0] > pitches[4] * 1.4


def test_pcm_conversion_clips_instead_of_wrapping():
    pcm = np.frombuffer(to_pcm16(np.array([2.0, -2.0, 0.0])), dtype="<i2")
    assert list(pcm) == [32767, -32767, 0]


def test_unknown_waveform_is_rejected():
    from src.audio.synth import tone

    with pytest.raises(ValueError):
        tone(440, 0.1, kind="noise")
