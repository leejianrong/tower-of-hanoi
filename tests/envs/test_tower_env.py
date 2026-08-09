import numpy as np

from src.envs.tower_env import TowerEnv


def test_reset_returns_initial_observation_and_action_mask():
    env = TowerEnv(num_discs=3)

    obs, info = env.reset()

    assert info == {}
    assert obs["observation"] == ((2, 1, 0), (), ())
    np.testing.assert_array_equal(obs["action_mask"], np.array([1, 1, 0, 0, 0, 0], dtype=np.int8))


def test_step_valid_action_records_move_event_and_penalizes_step():
    env = TowerEnv(num_discs=3)
    env.reset()

    obs, reward, terminated, truncated, info = env.step(1)

    assert obs["observation"] == ((2, 1), (), (0,))
    assert reward == -1
    assert not terminated
    assert not truncated
    assert info == {}
    assert env.current_move_event.disc_id == 0
    assert env.current_move_event.source_rod_idx == 0
    assert env.current_move_event.target_rod_idx == 2


def test_step_invalid_action_returns_error_without_changing_state():
    env = TowerEnv(num_discs=3)
    env.reset()

    obs, reward, terminated, truncated, info = env.step(2)

    assert obs["observation"] == ((2, 1, 0), (), ())
    assert reward == -10
    assert not terminated
    assert not truncated
    assert info == {"error": "Invalid move taken"}


def test_step_truncates_at_max_steps():
    env = TowerEnv(num_discs=3, max_steps=1)
    env.reset()

    _, reward, terminated, truncated, _ = env.step(1)

    assert reward == -10
    assert not terminated
    assert truncated
