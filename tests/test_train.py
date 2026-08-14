import json

from train import train


def test_train_records_every_step_and_stops_on_first_optimal_solution(tmp_path):
    output_path = train(
        tmp_path / "training.json",
        num_discs=1,
        max_steps=5,
        max_episodes=10,
        seed=7,
        log_every=100,
    )

    data = json.loads(output_path.read_text())

    assert data["summary"]["solved"] is True
    assert data["summary"]["episode_count"] == data["summary"]["first_optimal_episode_number"]
    assert data["summary"]["first_optimal_step_count"] == 1
    assert data["episodes"][-1]["optimal"] is True
    assert data["episodes"][-1]["steps"][0]["decision_mode"] == "explore"
    assert data["episodes"][-1]["steps"][0]["reward"] == 100.0
