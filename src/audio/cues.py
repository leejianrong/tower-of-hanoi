"""When each sound plays (ADR-0010): a list of ``(time, sound)`` derived from the timeline.

Pure and deterministic, like the schedule: the browser plays the list live and the video exporter
mixes it into the soundtrack, so what you hear in the browser is what the video contains. Which
sounds exist and what they sound like is ``src/audio/synth.py``; this file only decides when.
"""

from bisect import bisect_right
from dataclasses import dataclass
from typing import Any

from src.dashboard.player import UPDATE_PHASE
from src.replay.compact import ReplayData
from src.replay.qtable import q_deltas
from src.replay.schedule import Schedule, record_episodes

# Played once per step; skipped when steps are short or playback is fast.
STEP_CUES = frozenset({"lift", "explore", "exploit", "update_up", "update_down"})
LIFT_AT = 0.03  # fraction of a step at which the lift sound plays


@dataclass(frozen=True)
class CueSettings:
    min_step_s: float = 0.25  # steps shorter than this get no per-step sounds
    min_fail_episode_s: float = 1.0  # a failed episode shorter than this gets no sound
    mute_updates: bool = False  # the Q-update tick can be dropped to thin the track
    max_playback_speed: float = 4.0  # above this speed per-step sounds are dropped (live and video)


@dataclass(frozen=True)
class Cues:
    names: list[str]
    t: list[float]
    sound: list[int]  # index into ``names``

    def __len__(self) -> int:
        return len(self.t)

    def between(self, start: float, end: float) -> range:
        """Indices of the cues with ``start < t <= end`` (the cues passed as the clock moves)."""
        return range(bisect_right(self.t, start), bisect_right(self.t, end))

    def to_json(self) -> dict[str, Any]:
        return {"names": self.names, "t": self.t, "sound": self.sound}


def build_cues(
    replay: ReplayData, schedule: Schedule, settings: CueSettings | None = None
) -> Cues:
    settings = settings or CueSettings()
    records = record_episodes(replay)
    deltas = q_deltas(replay)
    names: list[str] = []
    events: list[tuple[float, int, str]] = []  # (time, order, name); order keeps ties stable

    def add(t: float, name: str) -> None:
        events.append((round(t, 4), len(events), name))

    last_episode = replay.episode_count - 1
    for episode in range(replay.episode_count):
        steps = replay.episode_range(episode)
        if not steps:
            continue
        first, last = steps[0], steps[-1]
        for step in steps:
            if schedule.step_dur[step] < settings.min_step_s:
                continue
            t0, dur = schedule.step_t0[step], schedule.step_dur[step]
            add(t0, "explore" if replay.step_explore[step] else "exploit")
            add(t0 + LIFT_AT * dur, "lift")
            add(t0 + 0.98 * dur, f"land_{replay.step_disc[step]}")
            if not settings.mute_updates:
                add(t0 + UPDATE_PHASE * dur, "update_up" if deltas[step] >= 0 else "update_down")
        end = schedule.step_t0[last] + schedule.step_dur[last]
        length = end - schedule.step_t0[first]
        if episode == last_episode and replay.episode_optimal[episode]:
            add(end, "final")
        elif episode in records:
            add(end, "record")
        elif replay.episode_solved[episode]:
            add(end, "solved")
        elif length >= settings.min_fail_episode_s:
            add(end, "fail")

    events.sort()
    for _, _, name in events:
        if name not in names:
            names.append(name)
    index = {name: i for i, name in enumerate(names)}
    return Cues(names, [t for t, _, _ in events], [index[n] for _, _, n in events])
