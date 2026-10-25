"""Turn a replay into a watchable timeline (ADR-0007).

Every step of the run stays in the data, but a literal playback of 655 episodes would be far
too long to watch. The schedule decides how long each step is on screen: the first episodes
play slowly so a viewer sees the rules, failed episodes flash by, solved ones play at a
readable pace, and the final optimal solve is slow. All timing decisions live here, in Python;
the browser only follows the timeline, so a video export and a live replay never disagree.
"""

from bisect import bisect_right
from dataclasses import dataclass
from typing import Any

from src.replay.compact import ReplayData


@dataclass(frozen=True)
class Pacing:
    intro_episodes: int = 3  # the first episodes play slowly so the rules are visible
    intro_step_s: float = 0.7
    intro_slow_steps: int = 24  # after this many steps an intro episode speeds up
    fast_episode_s: float = 0.45  # a failed episode flashes by in this long, however long it was
    solved_step_s: float = 0.06  # a solved episode plays at a readable pace
    final_step_s: float = 0.6  # the first optimal solve is slow
    episode_gap_s: float = 0.12  # a short beat between episodes


@dataclass(frozen=True)
class Position:
    """Where the playhead is: a global step index and how far through that step it is."""

    step: int
    episode: int
    phase: float  # 0.0 at the start of the step's animation, 1.0 once it has finished
    done: bool  # the playhead is past the end of the run


@dataclass(frozen=True)
class Schedule:
    step_t0: list[float]
    step_dur: list[float]
    episode_t0: list[float]
    total_s: float
    replay: ReplayData

    def locate(self, t: float) -> Position:
        """The position at time ``t`` seconds. Gaps between episodes read as a finished step."""
        last = len(self.step_t0) - 1
        if t >= self.total_s:
            step = last
            return Position(step, self.replay.episode_of_step(step), 1.0, True)
        step = max(0, bisect_right(self.step_t0, t) - 1)
        phase = (t - self.step_t0[step]) / self.step_dur[step]
        return Position(step, self.replay.episode_of_step(step), min(max(phase, 0.0), 1.0), False)

    def to_json(self) -> dict[str, Any]:
        return {
            "step_t0": [round(v, 4) for v in self.step_t0],
            "step_dur": [round(v, 4) for v in self.step_dur],
            "episode_t0": [round(v, 4) for v in self.episode_t0],
            "total_s": round(self.total_s, 4),
        }


def _episode_durations(replay: ReplayData, episode: int, pacing: Pacing) -> list[float]:
    count = len(replay.episode_range(episode))
    if count == 0:
        return []
    final = episode == replay.episode_count - 1 and bool(replay.episode_optimal[episode])
    if final:
        return [pacing.final_step_s] * count
    if episode < pacing.intro_episodes:
        slow = min(count, pacing.intro_slow_steps)
        fast = (pacing.fast_episode_s / count) if count > slow else 0.0
        return [pacing.intro_step_s] * slow + [fast] * (count - slow)
    if replay.episode_solved[episode]:
        return [pacing.solved_step_s] * count
    return [pacing.fast_episode_s / count] * count


def build_schedule(replay: ReplayData, pacing: Pacing | None = None) -> Schedule:
    pacing = pacing or Pacing()
    step_t0: list[float] = []
    step_dur: list[float] = []
    episode_t0: list[float] = []
    clock = 0.0
    for episode in range(replay.episode_count):
        durations = _episode_durations(replay, episode, pacing)
        episode_t0.append(clock)
        for duration in durations:
            step_t0.append(clock)
            step_dur.append(duration)
            clock += duration
        if durations:
            clock += pacing.episode_gap_s
    if not step_t0:
        raise ValueError("Cannot schedule a replay with no steps.")
    return Schedule(step_t0, step_dur, episode_t0, clock, replay)
