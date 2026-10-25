"""Rebuild the Q-table at any step of a replay (ADR-0008).

``seek(n)`` leaves the table as it was after the first ``n`` updates. Going forward applies the
updates in between; going back restarts from the nearest checkpoint, so scrubbing is cheap.
"""

import numpy as np

from src.replay.compact import ReplayData
from src.replay.encoding import NUM_ACTIONS, num_states


class QReplayer:
    def __init__(self, replay: ReplayData, checkpoint_every: int = 512) -> None:
        if checkpoint_every < 1:
            raise ValueError("checkpoint_every must be positive")
        self.replay = replay
        self.checkpoint_every = checkpoint_every
        self.table = np.zeros((num_states(replay.num_discs), NUM_ACTIONS))
        self.position = 0
        self._checkpoints: dict[int, np.ndarray] = {0: self.table.copy()}

    def seek(self, position: int) -> np.ndarray:
        """Return the live table after ``position`` updates (0 = all zeros)."""
        if not 0 <= position <= self.replay.step_count:
            raise IndexError(f"Position {position} out of range 0..{self.replay.step_count}")
        if position < self.position:
            base = max(p for p in self._checkpoints if p <= position)
            self.table = self._checkpoints[base].copy()
            self.position = base
        state, action, q_after = (
            self.replay.step_state,
            self.replay.step_action,
            self.replay.step_q_after,
        )
        while self.position < position:
            index = self.position
            self.table[state[index], action[index]] = q_after[index]
            self.position += 1
            if self.position % self.checkpoint_every == 0:
                self._checkpoints.setdefault(self.position, self.table.copy())
        return self.table


def q_deltas(replay: ReplayData) -> list[float]:
    """Signed Q change caused by each step (``q_after - q_before``), in one forward pass."""
    table = np.zeros((num_states(replay.num_discs), NUM_ACTIONS))
    deltas = []
    for state, action, q_after in zip(replay.step_state, replay.step_action, replay.step_q_after):
        deltas.append(q_after - table[state, action])
        table[state, action] = q_after
    return deltas
