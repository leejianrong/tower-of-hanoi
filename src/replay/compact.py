"""Compact, columnar replay of a training run (ADR-0008).

Training telemetry (``src/agents/telemetry.py``) is a log for humans: every step carries full
state tuples and Q rows, and every episode carries a Q-table snapshot, so a 655-episode run is
70 MB. The dashboard needs far less, because Q-learning is deterministic: the Q-table at any
step is the zero table plus every ``(state, action) -> q_after`` update up to that step.
"""

import json
from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.replay.encoding import ACTION_MAP, apply_action, encode_state, legal_mask, num_states

REPLAY_SCHEMA_VERSION = 1

_STEP_COLUMNS = ("state", "action", "disc", "explore", "reward", "next_state", "q_after", "draw")
_EPISODE_COLUMNS = ("epsilon", "reward", "solved", "optimal")


@dataclass(frozen=True)
class Move:
    disc: int
    source: int
    target: int


@dataclass
class ReplayData:
    """A run as parallel arrays. ``episode_start`` has one extra entry: the total step count."""

    config: dict[str, Any]
    episode_start: list[int]
    episode_epsilon: list[float]
    episode_reward: list[float]
    episode_solved: list[int]
    episode_optimal: list[int]
    step_state: list[int]
    step_action: list[int]
    step_disc: list[int]
    step_explore: list[int]
    step_reward: list[float]
    step_next_state: list[int]
    step_q_after: list[float]
    step_draw: list[float]
    _legal: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        episodes = len(self.episode_start) - 1
        if episodes < 0 or any(
            len(getattr(self, f"episode_{name}")) != episodes
            for name in ("epsilon", "reward", "solved", "optimal")
        ):
            raise ValueError("Episode columns must all have one entry per episode.")
        steps = self.episode_start[-1]
        if any(len(getattr(self, f"step_{name}")) != steps for name in _STEP_COLUMNS):
            raise ValueError("Step columns must all have episode_start[-1] entries.")
        if any(b < a for a, b in zip(self.episode_start, self.episode_start[1:])):
            raise ValueError("episode_start must be non-decreasing.")

    @property
    def num_discs(self) -> int:
        return int(self.config["num_discs"])

    @property
    def episode_count(self) -> int:
        return len(self.episode_start) - 1

    @property
    def step_count(self) -> int:
        return self.episode_start[-1]

    def episode_range(self, episode: int) -> range:
        return range(self.episode_start[episode], self.episode_start[episode + 1])

    def episode_of_step(self, step: int) -> int:
        if not 0 <= step < self.step_count:
            raise IndexError(f"Step {step} out of range 0..{self.step_count - 1}")
        return bisect_right(self.episode_start, step) - 1

    def move(self, step: int) -> Move:
        source, target = ACTION_MAP[self.step_action[step]]
        return Move(disc=self.step_disc[step], source=source, target=target)

    def legal_table(self) -> list[int]:
        """Legal-action bitmask for every state id (the heatmap's masked cells)."""
        if not self._legal:
            self._legal = [legal_mask(s, self.num_discs) for s in range(num_states(self.num_discs))]
        return self._legal

    # -- serialization -----------------------------------------------------------------------

    def to_json(self) -> dict[str, Any]:
        return {
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "config": self.config,
            "episodes": {
                "start": self.episode_start,
                "epsilon": self.episode_epsilon,
                "reward": self.episode_reward,
                "solved": self.episode_solved,
                "optimal": self.episode_optimal,
            },
            "steps": {
                "state": self.step_state,
                "action": self.step_action,
                "disc": self.step_disc,
                "explore": self.step_explore,
                "reward": self.step_reward,
                "next_state": self.step_next_state,
                "q_after": self.step_q_after,
                "draw": self.step_draw,
            },
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ReplayData":
        if data.get("replay_schema_version") != REPLAY_SCHEMA_VERSION:
            raise ValueError(f"Expected replay_schema_version={REPLAY_SCHEMA_VERSION}.")
        episodes, steps = data["episodes"], data["steps"]
        missing = [c for c in _STEP_COLUMNS if c not in steps]
        missing += [c for c in ("start", *_EPISODE_COLUMNS) if c not in episodes]
        if missing:
            raise ValueError(
                f"Replay is missing columns {missing}; it was made by an older version. "
                "Run `make replay-data` to rebuild it."
            )
        return cls(
            config=data["config"],
            episode_start=list(episodes["start"]),
            episode_epsilon=list(episodes["epsilon"]),
            episode_reward=list(episodes["reward"]),
            episode_solved=list(episodes["solved"]),
            episode_optimal=list(episodes["optimal"]),
            step_state=list(steps["state"]),
            step_action=list(steps["action"]),
            step_disc=list(steps["disc"]),
            step_explore=list(steps["explore"]),
            step_reward=list(steps["reward"]),
            step_next_state=list(steps["next_state"]),
            step_q_after=list(steps["q_after"]),
            step_draw=list(steps["draw"]),
        )

    def save(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_json(), separators=(",", ":")))
        return output

    @classmethod
    def load(cls, path: str | Path) -> "ReplayData":
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"Replay file not found: {source}. Run `make replay-data`.")
        return cls.from_json(json.loads(source.read_text()))


def build_replay(telemetry: dict[str, Any]) -> ReplayData:
    """Convert a training telemetry document (schema v1) to a compact replay."""
    if telemetry.get("schema_version") != 1:
        raise ValueError("Expected training telemetry schema_version=1.")
    source_config = telemetry["config"]
    num_discs = int(source_config["num_discs"])
    config = {
        "num_discs": num_discs,
        "max_steps": source_config["max_steps"],
        "optimal_steps": source_config["optimal_steps"],
        "alpha": source_config["alpha"],
        "gamma": source_config["gamma"],
        "epsilon_decay": source_config["epsilon_decay"],
        "min_epsilon": source_config["min_epsilon"],
        "seed": source_config.get("seed"),
        "num_actions": len(ACTION_MAP),
        "action_map": [list(pair) for pair in ACTION_MAP],
    }
    columns: dict[str, list] = {name: [] for name in _STEP_COLUMNS}
    episode_start = [0]
    episodes: dict[str, list] = {name: [] for name in _EPISODE_COLUMNS}

    for episode in telemetry["episodes"]:
        for step in episode["steps"]:
            action = int(step["action"])
            state_id = encode_state(step["state"], num_discs)
            columns["state"].append(state_id)
            columns["action"].append(action)
            columns["disc"].append(apply_action(state_id, action, num_discs)[1])
            columns["explore"].append(1 if step["decision_mode"] == "explore" else 0)
            columns["reward"].append(float(step["reward"]))
            columns["next_state"].append(encode_state(step["next_state"], num_discs))
            columns["q_after"].append(round(float(step["q_values_after"][action]), 6))
            columns["draw"].append(round(float(step["random_draw"]), 4))
        episode_start.append(len(columns["state"]))
        episodes["epsilon"].append(float(episode["epsilon_start"]))
        episodes["reward"].append(float(episode["total_reward"]))
        episodes["solved"].append(1 if episode["solved"] else 0)
        episodes["optimal"].append(1 if episode["optimal"] else 0)

    return ReplayData(
        config=config,
        episode_start=episode_start,
        episode_epsilon=episodes["epsilon"],
        episode_reward=episodes["reward"],
        episode_solved=episodes["solved"],
        episode_optimal=episodes["optimal"],
        step_state=columns["state"],
        step_action=columns["action"],
        step_disc=columns["disc"],
        step_explore=columns["explore"],
        step_reward=columns["reward"],
        step_next_state=columns["next_state"],
        step_q_after=columns["q_after"],
        step_draw=columns["draw"],
    )


def load_telemetry(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Training telemetry not found: {source}. Run `make train`.")
    return json.loads(source.read_text())
