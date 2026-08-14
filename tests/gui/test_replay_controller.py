from src.gui.replay_controller import TrainingReplayController
from src.gui.training_artifact import TrainingArtifact


def make_artifact() -> TrainingArtifact:
    def step(step_index, episode_number):
        return {
            "step_index": step_index,
            "state": [[0], [], []],
            "next_state": [[], [], [0]],
            "action": 1,
            "decision_mode": "explore",
            "epsilon": 1.0,
            "source_rod_idx": 0,
            "target_rod_idx": 2,
            "disc_id": 0,
            "reward": 100,
            "q_values_before": [0, 0, 0, 0, 0, 0],
            "q_values_after": [0, 50, 0, 0, 0, 0],
        }

    return TrainingArtifact({
        "schema_version": 1,
        "config": {"num_discs": 1},
        "summary": {},
        "episodes": [
            {
                "episode_number": 1,
                "total_reward": 100,
                "step_count": 2,
                "steps": [step(0, 1), step(1, 1)],
                "q_table": [{"state": [[0], [], []], "values": [0, 50, 0, 0, 0, 0]}],
            },
            {
                "episode_number": 2,
                "total_reward": 100,
                "step_count": 1,
                "steps": [step(0, 2)],
                "q_table": [{"state": [[0], [], []], "values": [0, 50, 0, 0, 0, 0]}],
            },
        ],
    })


def test_replay_controller_advances_by_elapsed_time():
    controller = TrainingReplayController(make_artifact(), steps_per_second=2)

    controller.update(0.49)
    assert controller.progress == (1, 3)

    controller.update(0.01)
    assert controller.progress == (2, 3)


def test_replay_controller_steps_and_clamps():
    controller = TrainingReplayController(make_artifact())

    controller.previous_step()
    assert controller.progress == (1, 3)

    controller.next_step()
    controller.next_step()
    controller.next_step()
    assert controller.progress == (3, 3)
    assert controller.at_end


def test_replay_controller_can_pause_and_change_speed():
    controller = TrainingReplayController(make_artifact(), steps_per_second=4)

    controller.toggle_playing()
    controller.update(1)
    assert controller.progress == (1, 3)

    controller.speed_up()
    assert controller.steps_per_second == 8
    controller.slow_down()
    assert controller.steps_per_second == 4


def test_replay_controller_waits_for_disc_animation_before_advancing():
    controller = TrainingReplayController(make_artifact(), steps_per_second=2)

    controller.update(0.5, animation_complete=False)
    assert controller.progress == (1, 3)
    assert controller.animation_progress == 1.0

    controller.update(0, animation_complete=True)
    assert controller.progress == (2, 3)
    assert controller.animation_progress == 0.0
