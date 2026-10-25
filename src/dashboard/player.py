"""The playback state of the dashboard, with no UI in it (ADR-0007).

A ``Player`` owns one number, the clock ``t`` in seconds. Everything on screen is a function of
``t``: ``frame()`` asks the schedule where the playhead is and looks the rest up in the replay.
Nothing here imports indah or a browser API, so the same rules can be tested in plain Python and
later ported to a client-side clock without changing what a frame means.
"""

from dataclasses import dataclass

import numpy as np

from src.replay.compact import ReplayData
from src.replay.encoding import decode_state
from src.replay.qtable import QReplayer, q_deltas
from src.replay.schedule import Schedule

# The step's Q update lands this far through its animation (the disc has settled).
UPDATE_PHASE = 0.75


@dataclass(frozen=True)
class Frame:
    step: int  # global step index
    episode: int  # zero-based
    episode_number: int
    episode_count: int
    step_in_episode: int  # one-based
    max_steps: int
    phase: float
    done: bool
    rods: tuple[tuple[int, ...], ...]  # state before the move, bottom to top per rod
    disc: int
    source: int
    target: int
    explore: bool
    draw: float
    epsilon: float
    step_reward: float
    episode_return: float  # cumulative reward in this episode, up to and including this step
    applied: int  # how many Q updates are visible


class Player:
    def __init__(self, replay: ReplayData, schedule: Schedule) -> None:
        self.replay = replay
        self.schedule = schedule
        self.t = 0.0
        self.playing = True
        self.speed = 1.0
        self._q = QReplayer(replay)
        self._dq = q_deltas(replay)
        self._cumulative = self._episode_cumulative()

    def _episode_cumulative(self) -> list[float]:
        out: list[float] = []
        for episode in range(self.replay.episode_count):
            total = 0.0
            for step in self.replay.episode_range(episode):
                total += self.replay.step_reward[step]
                out.append(total)
        return out

    # -- clock ---------------------------------------------------------------------------

    def advance(self, dt: float) -> None:
        if self.playing and self.t < self.schedule.total_s:
            self.t = min(self.t + dt * self.speed, self.schedule.total_s)

    def seek(self, t: float) -> None:
        self.t = min(max(t, 0.0), self.schedule.total_s)

    def seek_episode(self, episode: int) -> None:
        episode = min(max(episode, 0), self.replay.episode_count - 1)
        self.seek(self.schedule.episode_t0[episode])

    # -- what is on screen at t ----------------------------------------------------------

    def frame(self) -> Frame:
        position = self.schedule.locate(self.t)
        replay, step = self.replay, position.step
        move = replay.move(step)
        episode = position.episode
        first = replay.episode_start[episode]
        landed = position.phase >= UPDATE_PHASE
        return Frame(
            step=step,
            episode=episode,
            episode_number=episode + 1,
            episode_count=replay.episode_count,
            step_in_episode=step - first + 1,
            max_steps=int(replay.config["max_steps"]),
            phase=position.phase,
            done=position.done,
            rods=decode_state(replay.step_state[step], replay.num_discs),
            disc=move.disc,
            source=move.source,
            target=move.target,
            explore=bool(replay.step_explore[step]),
            draw=replay.step_draw[step],
            epsilon=replay.episode_epsilon[episode],
            step_reward=replay.step_reward[step],
            episode_return=self._cumulative[step],
            applied=step + 1 if landed else step,
        )

    def q_table(self, applied: int) -> np.ndarray:
        """The Q-table after ``applied`` updates. The returned array is live: copy to keep."""
        return self._q.seek(applied)

    def heatmap_columns(self, applied: int) -> list[list[float | None]]:
        """Q values as columns (one per state), with illegal moves as None (a masked cell)."""
        table = self._q.seek(applied)
        legal = self.replay.legal_table()
        return [
            [float(v) if legal[s] >> a & 1 else None for a, v in enumerate(row)]
            for s, row in enumerate(table)
        ]

    # -- series for the charts ---------------------------------------------------------------

    def reward_by_episode(self, upto: int) -> list[list[float]]:
        """``[[episode_number, total_reward], ...]`` for completed episodes before ``upto``."""
        return [[e + 1, self.replay.episode_reward[e]] for e in range(upto)]

    def steps_by_episode(self, upto: int) -> list[list[float]]:
        r = self.replay
        return [[e + 1, r.episode_start[e + 1] - r.episode_start[e]] for e in range(upto)]

    def epsilon_by_episode(self) -> list[list[float]]:
        return [[e + 1, v] for e, v in enumerate(self.replay.episode_epsilon)]

    def return_in_episode(self, episode: int, upto_step: int) -> list[list[float]]:
        """Cumulative reward by step for one episode, through global step ``upto_step``."""
        first = self.replay.episode_start[episode]
        return [[s - first + 1, self._cumulative[s]] for s in range(first, upto_step + 1)]

    def q_change_in_episode(self, episode: int, upto_step: int) -> list[list[float]]:
        first = self.replay.episode_start[episode]
        return [[s - first + 1, round(abs(self._dq[s]), 6)] for s in range(first, upto_step + 1)]
