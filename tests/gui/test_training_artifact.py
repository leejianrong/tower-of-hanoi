import json

import pytest

from src.gui.training_artifact import TrainingArtifact


def test_training_artifact_loads_dashboard_step(tmp_path):
    path = tmp_path / "training.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "config": {"num_discs": 1},
        "summary": {},
        "episodes": [{
            "episode_number": 1,
            "total_reward": 100,
            "step_count": 1,
            "solved": True,
            "optimal": True,
            "steps": [{
                "step_index": 0,
                "state": [[0], [], []],
                "next_state": [[], [], [0]],
                "action": 1,
                "decision_mode": "explore",
                "epsilon": 1.0,
                "source_rod_idx": 0,
                "target_rod_idx": 2,
                "disc_id": 0,
                "reward": 100,
                "terminated": True,
                "truncated": False,
                "q_values_before": [0, 0, 0, 0, 0, 0],
                "q_values_after": [0, 50, 0, 0, 0, 0],
            }],
            "q_table": [
                {"state": [[0], [], []], "values": [0, 50, 0, 0, 0, 0]},
            ],
        }],
    }))

    artifact = TrainingArtifact.load(path)
    step = artifact.get_step()

    assert step.episode_number == 1
    assert step.state == ((0,), (), ())
    assert step.terminated
    assert step.episode_solved
    assert step.episode_optimal
    assert step.q_table == ((((0,), (), ()), (0.0, 50.0, 0.0, 0.0, 0.0, 0.0)),)


def test_training_artifact_rejects_unknown_schema():
    with pytest.raises(ValueError, match="schema_version=1"):
        TrainingArtifact({"schema_version": 999})
