"""Synthesise the sound effects (ADR-0005, ADR-0010): small arcade blips, written as WAV files.

Every sound is a pure function of the numbers in this file, so the committed WAVs can be checked
against a fresh render and the browser and the video exporter play exactly the same samples.
"""

import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44_100
AUDIO_DIR = Path(__file__).resolve().parents[1] / "dashboard" / "static" / "audio"
MAX_DISCS = 8  # land_0 .. land_7: one pitch per disc


def _t(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE


def _wave(kind: str, phase: np.ndarray) -> np.ndarray:
    if kind == "sine":
        return np.sin(phase)
    if kind == "square":
        return np.sign(np.sin(phase)) * 0.6
    if kind == "triangle":
        return 2 / np.pi * np.arcsin(np.sin(phase))
    raise ValueError(f"Unknown waveform {kind!r}")


def tone(
    freq: float, seconds: float, *, kind: str = "triangle", end_freq: float | None = None,
    gain: float = 0.5, attack: float = 0.004, decay: float = 5.0,
) -> np.ndarray:  # fmt: skip
    """One note: optional pitch slide from ``freq`` to ``end_freq``, fast attack, exponential decay."""
    t = _t(seconds)
    sweep = np.linspace(freq, end_freq if end_freq is not None else freq, len(t))
    phase = 2 * np.pi * np.cumsum(sweep) / SAMPLE_RATE
    envelope = np.minimum(t / attack, 1.0) * np.exp(-decay * t / seconds)
    return gain * envelope * _wave(kind, phase)


def sequence(notes: list[tuple[float, float]], gap: float, **options) -> np.ndarray:
    """Notes ``(freq, seconds)`` one after another, ``gap`` seconds apart."""
    out = np.zeros(int(SAMPLE_RATE * (gap * (len(notes) - 1) + max(s for _, s in notes))))
    for index, (freq, seconds) in enumerate(notes):
        start = int(SAMPLE_RATE * gap * index)
        note = tone(freq, seconds, **options)
        out[start : start + len(note)] += note
    return out


def _land(disc: int) -> np.ndarray:
    freq = 880 * 0.85**disc
    thump = tone(freq, 0.16, kind="triangle", end_freq=freq * 0.8, gain=0.55, decay=6.0)
    click = tone(freq * 2, 0.02, kind="square", gain=0.2, decay=8.0)
    thump[: len(click)] += click
    return thump


def build_sounds() -> dict[str, np.ndarray]:
    """Every effect by name, as float samples in [-1, 1]."""
    sounds = {
        "lift": tone(330, 0.12, end_freq=560, gain=0.3, decay=3.0),
        "explore": sequence([(988, 0.07), (1319, 0.09)], 0.06, kind="square", gain=0.22, decay=4.0),
        "exploit": sequence([(523, 0.16), (659, 0.16)], 0.02, kind="sine", gain=0.35, decay=4.0),
        "update_up": tone(1568, 0.07, end_freq=2093, kind="square", gain=0.14, decay=5.0),
        "update_down": tone(1175, 0.07, end_freq=880, kind="square", gain=0.14, decay=5.0),
        "fail": tone(330, 0.3, end_freq=196, kind="triangle", gain=0.3, decay=3.0),
        "solved": sequence([(523, 0.18), (659, 0.18), (784, 0.3)], 0.09, kind="square", gain=0.3),
        "record": sequence(
            [(523, 0.2), (659, 0.2), (784, 0.2), (1047, 0.2), (1319, 0.5)], 0.1,
            kind="square", gain=0.34, decay=3.0,
        ),  # fmt: skip
        "final": sequence(
            [(392, 0.3), (523, 0.3), (659, 0.3), (784, 0.3), (1047, 0.35), (784, 0.2), (1047, 1.1)],
            0.16, kind="square", gain=0.36, decay=2.5,
        ),  # fmt: skip
    }
    for disc in range(MAX_DISCS):
        sounds[f"land_{disc}"] = _land(disc)
    return sounds


def to_pcm16(samples: np.ndarray) -> bytes:
    return (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def write_wav(path: Path, samples: np.ndarray) -> None:
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(to_pcm16(samples))


def write_all(directory: Path = AUDIO_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, samples in build_sounds().items():
        paths.append(directory / f"{name}.wav")
        write_wav(paths[-1], samples)
    return paths


if __name__ == "__main__":
    for written in write_all():
        print(written)
