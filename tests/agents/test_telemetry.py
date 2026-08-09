import json

import numpy as np

from src.agents.q_agent import ActionDecision
from src.agents.telemetry import (
    SCHEMA_VERSION,
    TrainingConfig,
    TrainingTelemetryRecorder,
    build_step_event,
)


def test_training_telemetry_recorder_writes_schema_versioned_json(tmp_path):
    recorder = TrainingTelemetryRecorder(
        TrainingConfig(
            num_discs=3,
            max_steps=10,
            max_episodes=2,
            optimal_steps=7,
            alpha=0.1,
            gamma=0.99,
            epsilon=1.0,
            epsilon_decay=0.995,
            min_epsilon=0.01,
            seed=7,
        )
    )

    recorder.record_episode(
        episode_index=0,
        epsilon_start=1.0,
        epsilon_end=0.995,
        total_reward=-1,
        steps=[],
        terminated=False,
        truncated=True,
        q_table={((2, 1, 0), (), ()): np.array([0, 1, 0, 0, 0, 0])},
    )
    output_path = recorder.save(tmp_path / "training.json")

    data = json.loads(output_path.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["config"]["num_discs"] == 3
    assert data["summary"]["episode_count"] == 1
    assert data["episodes"][0]["q_table"] == [
        {"state": [[2, 1, 0], [], []], "values": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]}
    ]


def test_build_step_event_serializes_numpy_values():
    obs = {
        "observation": ((2, 1, 0), (), ()),
        "action_mask": np.array([1, 1, 0, 0, 0, 0], dtype=np.int8),
    }
    next_obs = {
        "observation": ((2, 1), (), (0,)),
        "action_mask": np.array([1, 0, 0, 1, 1, 0], dtype=np.int8),
    }
    decision = ActionDecision(
        action=1,
        mode="explore",
        epsilon=1.0,
        random_draw=0.5,
        valid_actions=(0, 1),
        q_values=(0, 0, 0, 0, 0, 0),
    )

    event = build_step_event(
        step_index=0,
        obs=obs,
        decision=decision,
        source_rod_idx=0,
        target_rod_idx=2,
        disc_id=0,
        reward=-1,
        next_obs=next_obs,
        terminated=False,
        truncated=False,
        q_values_after=np.array([0, -0.5, 0, 0, 0, 0]),
    )

    assert event["decision_mode"] == "explore"
    assert event["state"] == [[2, 1, 0], [], []]
    assert event["action_mask"] == [1, 1, 0, 0, 0, 0]
    assert event["q_values_after"] == [0.0, -0.5, 0.0, 0.0, 0.0, 0.0]
