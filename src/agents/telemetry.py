import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TrainingConfig:
    num_discs: int
    max_steps: int
    max_episodes: int
    optimal_steps: int
    alpha: float
    gamma: float
    epsilon: float
    epsilon_decay: float
    min_epsilon: float
    seed: int | None = None


def serialize_state(state) -> list[list[int]]:
    return [list(rod) for rod in state]


def serialize_q_values(q_values) -> list[float]:
    return [float(value) for value in q_values]


def serialize_action_mask(action_mask) -> list[int]:
    return [int(value) for value in action_mask]


def serialize_q_table(q_table: dict[tuple[tuple[int, ...], ...], np.ndarray]) -> list[dict[str, Any]]:
    return [
        {
            "state": serialize_state(state),
            "values": serialize_q_values(values),
        }
        for state, values in sorted(q_table.items(), key=lambda item: repr(item[0]))
    ]


class TrainingTelemetryRecorder:
    def __init__(self, config: TrainingConfig) -> None:
        self.data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "config": {
                "num_discs": config.num_discs,
                "max_steps": config.max_steps,
                "max_episodes": config.max_episodes,
                "optimal_steps": config.optimal_steps,
                "alpha": config.alpha,
                "gamma": config.gamma,
                "epsilon": config.epsilon,
                "epsilon_decay": config.epsilon_decay,
                "min_epsilon": config.min_epsilon,
                "seed": config.seed,
            },
            "episodes": [],
            "summary": {},
        }

    def record_episode(
        self,
        *,
        episode_index: int,
        epsilon_start: float,
        epsilon_end: float,
        total_reward: float,
        steps: list[dict[str, Any]],
        terminated: bool,
        truncated: bool,
        q_table: dict[tuple[tuple[int, ...], ...], np.ndarray],
    ) -> None:
        self.data["episodes"].append({
            "episode_index": episode_index,
            "episode_number": episode_index + 1,
            "epsilon_start": float(epsilon_start),
            "epsilon_end": float(epsilon_end),
            "total_reward": float(total_reward),
            "step_count": len(steps),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "solved": bool(terminated),
            "optimal": bool(terminated and len(steps) == self.data["config"]["optimal_steps"]),
            "steps": steps,
            "q_table": serialize_q_table(q_table),
        })

    def finalize(self) -> None:
        episodes = self.data["episodes"]
        first_optimal = next((episode for episode in episodes if episode["optimal"]), None)
        self.data["summary"] = {
            "episode_count": len(episodes),
            "solved": any(episode["solved"] for episode in episodes),
            "first_optimal_episode_number": (
                first_optimal["episode_number"] if first_optimal is not None else None
            ),
            "first_optimal_step_count": first_optimal["step_count"] if first_optimal is not None else None,
        }

    def save(self, path: str | Path) -> Path:
        self.finalize()
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as file:
            json.dump(self.data, file)
        return output_path


def build_step_event(
    *,
    step_index: int,
    obs,
    decision,
    source_rod_idx: int,
    target_rod_idx: int,
    disc_id: int,
    reward: float,
    next_obs,
    terminated: bool,
    truncated: bool,
    q_values_after,
) -> dict[str, Any]:
    return {
        "step_index": step_index,
        "state": serialize_state(obs["observation"]),
        "action_mask": serialize_action_mask(obs["action_mask"]),
        "action": int(decision.action),
        "decision_mode": decision.mode,
        "epsilon": float(decision.epsilon),
        "random_draw": float(decision.random_draw),
        "valid_actions": list(decision.valid_actions),
        "q_values_before": list(decision.q_values),
        "source_rod_idx": int(source_rod_idx),
        "target_rod_idx": int(target_rod_idx),
        "disc_id": int(disc_id),
        "reward": float(reward),
        "next_state": serialize_state(next_obs["observation"]),
        "next_action_mask": serialize_action_mask(next_obs["action_mask"]),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "q_values_after": serialize_q_values(q_values_after),
    }
