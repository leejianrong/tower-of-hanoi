import numpy as np
import pytest

from src.envs.tower_env import TowerEnv
from src.replay.compact import ReplayData
from src.replay.encoding import (
    ACTION_MAP,
    apply_action,
    decode_state,
    encode_state,
    legal_actions,
    num_states,
)
from src.replay.qtable import QReplayer
from src.replay.schedule import Pacing, build_schedule


def test_state_ids_round_trip_and_start_at_zero():
    assert encode_state(((4, 3, 2, 1, 0), (), ()), 5) == 0
    assert num_states(5) == 243
    for state_id in range(num_states(5)):
        assert encode_state(decode_state(state_id, 5), 5) == state_id


def test_decode_orders_each_rod_biggest_disc_first():
    # disc 0 on rod 2, disc 1 on rod 0, disc 2 on rod 1
    state_id = 2 * 3**0 + 0 * 3**1 + 1 * 3**2
    assert decode_state(state_id, 3) == ((1,), (2,), (0,))


def test_legal_actions_match_the_environment_along_a_random_walk():
    env = TowerEnv(num_discs=4, max_steps=10_000)
    obs, _ = env.reset()
    rng = np.random.default_rng(0)
    for _ in range(500):
        state_id = encode_state(obs["observation"], 4)
        expected = tuple(int(a) for a in np.flatnonzero(obs["action_mask"]))
        assert legal_actions(state_id, 4) == expected
        obs, *_ = env.step(int(rng.choice(expected)))
        if env.tower.is_solved:
            obs, _ = env.reset()


def _neighbours(state):
    out = []
    for source, target in ACTION_MAP:
        if not state[source]:
            continue
        disc = state[source][-1]
        if state[target] and state[target][-1] < disc:
            continue
        new = [list(rod) for rod in state]
        new[source].pop()
        new[target].append(disc)
        out.append(tuple(tuple(r) for r in new))
    return out


def test_legal_actions_agree_with_neighbour_search():
    for state_id in range(num_states(3)):
        state = decode_state(state_id, 3)
        by_rules = {encode_state(n, 3) for n in _neighbours(state)}
        by_actions = {apply_action(state_id, a, 3)[0] for a in legal_actions(state_id, 3)}
        assert by_rules == by_actions


def test_apply_action_rejects_an_illegal_move():
    with pytest.raises(ValueError, match="not legal"):
        apply_action(0, 2, 3)  # rod 1 is empty at the start


def test_replay_matches_telemetry_step_for_step(telemetry, replay):
    assert replay.episode_count == len(telemetry["episodes"])
    assert replay.step_count == sum(len(e["steps"]) for e in telemetry["episodes"])
    index = 0
    for e, episode in enumerate(telemetry["episodes"]):
        assert replay.episode_epsilon[e] == pytest.approx(episode["epsilon_start"])
        assert bool(replay.episode_optimal[e]) == episode["optimal"]
        for step in episode["steps"]:
            assert decode_state(replay.step_state[index], 3) == tuple(
                tuple(r) for r in step["state"]
            )
            assert decode_state(replay.step_next_state[index], 3) == tuple(
                tuple(r) for r in step["next_state"]
            )
            assert replay.step_action[index] == step["action"]
            assert replay.step_explore[index] == (step["decision_mode"] == "explore")
            move = replay.move(index)
            assert (move.disc, move.source, move.target) == (
                step["disc_id"],
                step["source_rod_idx"],
                step["target_rod_idx"],
            )
            index += 1


def test_replayed_q_table_equals_the_trained_q_table(telemetry, replay):
    final_rows = telemetry["episodes"][-1]["q_table"]
    table = QReplayer(replay).seek(replay.step_count)
    for row in final_rows:
        state_id = encode_state(row["state"], 3)
        np.testing.assert_allclose(table[state_id], row["values"], atol=1e-5)
    visited = {encode_state(row["state"], 3) for row in final_rows}
    for state_id in set(range(num_states(3))) - visited:
        assert not table[state_id].any()


def test_q_replayer_seeks_backward_to_the_same_table(replay):
    forward = QReplayer(replay, checkpoint_every=7)
    middle = replay.step_count // 2
    expected = forward.seek(middle).copy()
    forward.seek(replay.step_count)
    np.testing.assert_array_equal(forward.seek(middle), expected)
    np.testing.assert_array_equal(forward.seek(0), np.zeros_like(expected))


def test_q_replayer_rejects_out_of_range(replay):
    with pytest.raises(IndexError):
        QReplayer(replay).seek(replay.step_count + 1)


def test_replay_round_trips_through_json(tmp_path, replay):
    path = replay.save(tmp_path / "replay.json")
    loaded = ReplayData.load(path)
    assert loaded.to_json() == replay.to_json()


def test_replay_rejects_unknown_schema_and_missing_file(tmp_path):
    with pytest.raises(ValueError, match="replay_schema_version"):
        ReplayData.from_json({"replay_schema_version": 99})
    with pytest.raises(FileNotFoundError, match="make replay-data"):
        ReplayData.load(tmp_path / "missing.json")


def test_episode_of_step_agrees_with_episode_ranges(replay):
    for episode in (0, replay.episode_count // 2, replay.episode_count - 1):
        for step in replay.episode_range(episode):
            assert replay.episode_of_step(step) == episode


def test_schedule_is_ordered_and_covers_every_step(replay):
    schedule = build_schedule(replay)
    assert len(schedule.step_t0) == replay.step_count
    assert all(b > a for a, b in zip(schedule.step_t0, schedule.step_t0[1:]))
    assert schedule.total_s > schedule.step_t0[-1]


def test_schedule_locates_every_step_start_and_end_of_run(replay):
    schedule = build_schedule(replay)
    for step in (0, 5, replay.step_count // 2, replay.step_count - 1):
        position = schedule.locate(schedule.step_t0[step] + 1e-6)
        assert position.step == step
        assert position.episode == replay.episode_of_step(step)
        assert position.phase < 0.5 and not position.done
    end = schedule.locate(schedule.total_s + 1)
    assert end.done and end.step == replay.step_count - 1 and end.phase == 1.0
    assert schedule.locate(-1).step == 0


def test_schedule_is_slow_at_the_start_and_for_the_final_optimal_episode(replay):
    pacing = Pacing()
    schedule = build_schedule(replay, pacing)
    assert schedule.step_dur[0] == pacing.intro_step_s
    if replay.episode_optimal[-1]:
        final = replay.episode_range(replay.episode_count - 1)
        assert all(schedule.step_dur[i] == pacing.final_step_s for i in final)


def test_q_deltas_sum_to_the_final_table(replay):
    from src.replay.qtable import q_deltas

    deltas = q_deltas(replay)
    assert len(deltas) == replay.step_count
    total = sum(deltas)
    final = QReplayer(replay).seek(replay.step_count)
    assert total == pytest.approx(float(final.sum()), abs=1e-3)
