import numpy as np

from src.agents.q_agent import QLearningAgent


def test_get_q_values_initializes_state_with_zeroes():
    agent = QLearningAgent(action_size=6)
    state = ((2, 1, 0), (), ())

    q_values = agent.get_q_values(state)

    np.testing.assert_array_equal(q_values, np.zeros(6))


def test_choose_action_never_selects_masked_action_when_exploiting():
    agent = QLearningAgent(action_size=6, epsilon=0)
    obs = {
        "observation": ((2, 1, 0), (), ()),
        "action_mask": np.array([0, 1, 0, 0, 0, 0], dtype=np.int8),
    }
    agent.q_table[tuple(obs["observation"])] = np.array([100, 1, 100, 100, 100, 100])

    assert agent.choose_action(obs) == 1


def test_learn_updates_q_value_for_selected_action():
    agent = QLearningAgent(action_size=6, alpha=0.5, gamma=0.9)
    obs = {
        "observation": ((2, 1, 0), (), ()),
        "action_mask": np.array([1, 1, 0, 0, 0, 0], dtype=np.int8),
    }
    next_obs = {
        "observation": ((2, 1), (), (0,)),
        "action_mask": np.array([1, 0, 0, 1, 1, 0], dtype=np.int8),
    }

    agent.learn(obs, action=1, reward=-1, next_obs=next_obs, terminated=True, truncated=False)

    assert agent.get_q_values(tuple(obs["observation"]))[1] == -0.5
