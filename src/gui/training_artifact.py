import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DashboardStep:
    episode_number: int
    episode_count: int
    step_number: int
    step_count: int
    total_reward: float
    epsilon: float
    decision_mode: str
    action: int
    source_rod_idx: int
    target_rod_idx: int
    disc_id: int
    reward: float
    state: tuple[tuple[int, ...], ...]
    next_state: tuple[tuple[int, ...], ...]
    q_values_before: tuple[float, ...]
    q_values_after: tuple[float, ...]
    q_table: tuple[tuple[tuple[tuple[int, ...], ...], tuple[float, ...]], ...]


def state_from_json(state: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(rod) for rod in state)


class TrainingArtifact:
    def __init__(self, data: dict[str, Any]) -> None:
        if data.get("schema_version") != 1:
            raise ValueError("Expected training telemetry schema_version=1.")
        self.data = data

    @classmethod
    def load(cls, path: str | Path) -> "TrainingArtifact":
        artifact_path = Path(path)
        if not artifact_path.exists():
            raise FileNotFoundError(f"Training telemetry artifact not found: {artifact_path}")
        with artifact_path.open() as file:
            return cls(json.load(file))

    @property
    def episode_count(self) -> int:
        return len(self.data["episodes"])

    @property
    def step_count(self) -> int:
        return sum(len(episode["steps"]) for episode in self.data["episodes"])

    def iter_steps(self):
        for episode_index, episode in enumerate(self.data["episodes"]):
            for step_index, _ in enumerate(episode["steps"]):
                yield episode_index, step_index, self.get_step(episode_index, step_index)

    def get_step(self, episode_index: int = -1, step_index: int = 0) -> DashboardStep:
        episode = self.data["episodes"][episode_index]
        steps = episode["steps"]
        if not steps:
            raise ValueError(f"Episode {episode['episode_number']} has no steps.")

        step = steps[step_index]
        q_table = tuple(
            (state_from_json(row["state"]), tuple(float(value) for value in row["values"]))
            for row in episode["q_table"]
        )
        return DashboardStep(
            episode_number=int(episode["episode_number"]),
            episode_count=self.episode_count,
            step_number=int(step["step_index"]) + 1,
            step_count=int(episode["step_count"]),
            total_reward=float(episode["total_reward"]),
            epsilon=float(step["epsilon"]),
            decision_mode=step["decision_mode"],
            action=int(step["action"]),
            source_rod_idx=int(step["source_rod_idx"]),
            target_rod_idx=int(step["target_rod_idx"]),
            disc_id=int(step["disc_id"]),
            reward=float(step["reward"]),
            state=state_from_json(step["state"]),
            next_state=state_from_json(step["next_state"]),
            q_values_before=tuple(float(value) for value in step["q_values_before"]),
            q_values_after=tuple(float(value) for value in step["q_values_after"]),
            q_table=q_table,
        )


def load_default_artifact(records_dir: str | Path = "records") -> TrainingArtifact:
    return TrainingArtifact.load(Path(records_dir) / "qlearningagent_training.json")
