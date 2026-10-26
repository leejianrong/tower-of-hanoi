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


# Times are kept to this many decimals everywhere, so the schedule Python uses and the JSON the
# browser reads hold identical numbers and both resolve a step boundary the same way.
PRECISION = 4


@dataclass(frozen=True)
class Pacing:
    # While set, every step lasts this long and the rules below are ignored. Set it to None to
    # get the storyboard pacing back (slow intro, capped solves, slow records, flashing fails).
    constant_step_s: float | None = 0.6
    intro_episodes: int = 3  # the first episodes play slowly so the rules are visible
    intro_step_s: float = 0.7
    intro_slow_steps: int = 24  # after this many steps an intro episode speeds up
    fast_episode_s: float = 0.3  # a failed episode flashes by in this long, however long it was
    solved_step_s: float = 0.06  # a solved episode plays at a readable pace...
    solved_cap_s: float = 2.0  # ...but never longer than this
    record_step_s: float = 0.15  # an episode that beats the best solve so far is slowed down
    record_cap_s: float = 8.0
    final_step_s: float = 0.6  # the first optimal solve is slow
    episode_gap_s: float = 0.06  # a short beat between episodes


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
            "step_t0": self.step_t0,
            "step_dur": self.step_dur,
            "episode_t0": self.episode_t0,
            "total_s": self.total_s,
        }


def _episode_durations(
    replay: ReplayData, episode: int, pacing: Pacing, is_record: bool
) -> list[float]:
    count = len(replay.episode_range(episode))
    if count == 0:
        return []
    if pacing.constant_step_s is not None:
        return [pacing.constant_step_s] * count
    final = episode == replay.episode_count - 1 and bool(replay.episode_optimal[episode])
    if final:
        return [pacing.final_step_s] * count
    if episode < pacing.intro_episodes:
        slow = min(count, pacing.intro_slow_steps)
        fast = (pacing.fast_episode_s / count) if count > slow else 0.0
        return [pacing.intro_step_s] * slow + [fast] * (count - slow)
    if is_record:
        return [min(pacing.record_step_s, pacing.record_cap_s / count)] * count
    if replay.episode_solved[episode]:
        return [min(pacing.solved_step_s, pacing.solved_cap_s / count)] * count
    return [pacing.fast_episode_s / count] * count


def build_schedule(replay: ReplayData, pacing: Pacing | None = None) -> Schedule:
    pacing = pacing or Pacing()
    step_t0: list[float] = []
    step_dur: list[float] = []
    episode_t0: list[float] = []
    clock = 0.0
    best = None  # fewest steps of any solved episode so far
    for episode in range(replay.episode_count):
        count = len(replay.episode_range(episode))
        solved = bool(replay.episode_solved[episode])
        is_record = solved and (best is None or count < best)
        if solved:
            best = count if best is None else min(best, count)
        durations = _episode_durations(replay, episode, pacing, is_record)
        episode_t0.append(clock)
        for duration in durations:
            duration = max(round(duration, PRECISION), 10**-PRECISION)
            step_t0.append(clock)
            step_dur.append(duration)
            clock = round(clock + duration, PRECISION)
        if durations:
            clock = round(clock + pacing.episode_gap_s, PRECISION)
    if not step_t0:
        raise ValueError("Cannot schedule a replay with no steps.")
    return Schedule(step_t0, step_dur, episode_t0, clock, replay)
