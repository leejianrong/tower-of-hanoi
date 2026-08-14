from dataclasses import dataclass
import numpy as np
import random


@dataclass(frozen=True)
class ActionDecision:
    action: int
    mode: str
    epsilon: float
    random_draw: float
    valid_actions: tuple[int, ...]
    q_values: tuple[float, ...]


class QLearningAgent:
    def __init__(
        self,
        action_size=6,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        min_epsilon=0.01,
        rng=None,
    ):
        self.q_table = {}  # Sparse Q-table: {state_tuple: np.array([q1, q2, ...])}
        self.action_size = action_size
        self.alpha = alpha  # learning rate
        self.gamma = gamma  # discount factor
        self.epsilon = epsilon  # exploration rate
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.rng = rng or random.Random()

    def get_q_values(self, state):
        """Retrieve Q-values for a state, initializing if necessary."""
        if state not in self.q_table:
            # Initialize q-values as 0
            self.q_table[state] = np.zeros(self.action_size)
        return self.q_table[state]

    def choose_action(self, obs) -> int:
        """Epsilon-greedy selection with action-masking."""
        return self.select_action(obs).action

    def select_action(self, obs) -> ActionDecision:
        """Epsilon-greedy selection with action metadata for visualization."""
        state = tuple(obs["observation"])
        mask = obs["action_mask"]
        valid_indices = np.where(mask == 1)[0]
        valid_actions = tuple(int(idx) for idx in valid_indices)
        q_values = self.get_q_values(state)
        random_draw = self.rng.random()

        if random_draw < self.epsilon:
            # Exploration: randomly pick from valid actions only
            action = self.rng.choice(valid_actions)
            mode = "explore"
        else:
            # Exploitation: Pick best Q-value among valid actions
            # Set invalid actions to -inf so they are never chosen by argmax
            masked_q = np.where(mask == 1, q_values, -np.inf)
            action = int(np.argmax(masked_q))
            mode = "exploit"

        return ActionDecision(
            action=action,
            mode=mode,
            epsilon=self.epsilon,
            random_draw=random_draw,
            valid_actions=valid_actions,
            q_values=tuple(float(value) for value in q_values),
        )

    def get_masked_q_values(self, obs) -> np.ndarray:
        state = tuple(obs["observation"])
        mask = obs["action_mask"]
        # Exploitation: Pick best Q-value among valid actions
        q_values = self.get_q_values(state)
        # Set invalid actions to -inf so they are never chosen by argmax
        return np.where(mask == 1, q_values, -np.inf)

    def learn(self, obs, action, reward, next_obs, terminated, truncated):
        """Update Q-values using the Bellman Equation."""
        state = tuple(obs["observation"])
        next_state = tuple(next_obs["observation"])
        next_mask = next_obs["action_mask"]

        current_q = self.get_q_values(state)[action]

        if terminated:
            # If state is terminal (game won), there is no future reward
            target = reward
        else:
            # Even if truncated (timeout), the state itself isn't the 'end of game'
            # So we bootstrap the best possible future value from the next state
            next_q_values = self.get_q_values(next_state)
            masked_next_q = np.where(next_mask == 1, next_q_values, -np.inf)
            target = reward + self.gamma * np.max(masked_next_q)

        # Update Q-table
        self.q_table[state][action] += self.alpha * (target - current_q)

    def decay_epsilon(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
