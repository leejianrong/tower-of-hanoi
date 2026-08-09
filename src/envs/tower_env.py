import gymnasium as gym
from gymnasium import spaces
import numpy as np

from src.core.tower import Tower
from collections import namedtuple


MoveEvent = namedtuple(
    "MoveEvent",
    ["disc_id", "source_rod_idx", "target_rod_idx"]
)


class TowerEnv(gym.Env):
    def __init__(self, num_discs=5, max_steps=150):
        super(TowerEnv, self).__init__()
        self.tower = Tower(num_discs=num_discs)
        self.num_discs = num_discs
        self.max_steps = max_steps
        self.current_step = 0
        self.pad_element = -1

        # Action space: 6 possible moves in a 3-rod game
        self.action_space = spaces.Discrete(6)
        self.action_map = {
            0: (0, 1),
            1: (0, 2),
            2: (1, 0),
            3: (1, 2),
            4: (2, 0),
            5: (2, 1)
        }
        # Observation space: the state of the rods
        # For Q-learning, use the raw state tuples as dictionary key
        # Apply mask so only legal actions are shown
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(
                low=0, high=num_discs, shape=(3, num_discs,), dtype=int
            ),
            "action_mask": spaces.Box(
                low=0, high=1, shape=(6,), dtype=np.int8
            )
        })

    def _get_action_mask(self):
        """
        Converts tower.get_valid_moves() into a binary mask for the 6 actions.
        """
        mask = np.zeros(6, dtype=np.int8)
        valid_moves = self.tower.get_valid_moves()

        for i, move_coords in self.action_map.items():
            if move_coords in valid_moves:
                mask[i] = 1
        return mask

    @property
    def current_observation(self):
        # game state is a ragged nested tuple where
        # inner tuples do not have the same number of elements
        # apply padding so all rows are equal in length
        # padded_state = [
        #     t + (self.pad_element,) * (self.num_discs - len(t))
        #     for t in self.tower.current_state
        # ]
        return {
            "observation": self.tower.current_state,
            "action_mask": self._get_action_mask()
        }

    def set_current_move_event(self, disc_id: int, source: int, target: int):
        """
        Sets value of class attribute to a named tuple that
        trackis the moving disc ID and source and target rod indices.
        This information is needed for visualizing the game history.
        """
        self.current_move_event = MoveEvent(
            disc_id=disc_id,
            source_rod_idx=source,
            target_rod_idx=target
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.tower.reset()
        self.current_step = 0
        self.current_move_event = None
        return self.current_observation, {}

    def step(self, action):
        self.current_step += 1
        source, target = self.action_map[action]

        # Check validity (safety check; mask should prevent this)
        if not self.tower.is_valid_move(source, target):
            return self.current_observation, -10, False, False, {"error": "Invalid move taken"}

        disc_id = self.tower.move(source, target)
        self.set_current_move_event(disc_id, source, target)
        terminated = self.tower.is_solved
        truncated = self.current_step >= self.max_steps

        if terminated:
            reward = 100
        elif truncated:
            reward = -10
        else:
            reward = -1

        return self.current_observation, reward, terminated, truncated, {}
