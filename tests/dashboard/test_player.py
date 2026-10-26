import numpy as np
import pytest

from src.dashboard.player import UPDATE_PHASE, Player
from src.replay.encoding import decode_state
from src.replay.qtable import QReplayer
from src.replay.schedule import build_schedule


@pytest.fixture()
def player(replay):
    return Player(replay, build_schedule(replay))


def test_frame_at_time_zero_is_the_first_step_of_the_first_episode(player, replay):
    frame = player.frame()
    assert (frame.step, frame.episode_number, frame.step_in_episode) == (0, 1, 1)
    assert frame.rods == ((2, 1, 0), (), ())
    assert frame.applied == 0 and not frame.done
    assert frame.episode_count == replay.episode_count


def test_frame_is_a_pure_function_of_the_clock(player):
    player.seek(5.0)
    first = player.frame()
    player.seek(100.0)
    player.seek(5.0)
    assert player.frame() == first


def test_frame_reports_the_move_and_decision_of_its_step(player, replay):
    player.seek(player.schedule.step_t0[7] + 1e-6)
    frame = player.frame()
    move = replay.move(7)
    assert (frame.disc, frame.source, frame.target) == (move.disc, move.source, move.target)
    assert frame.explore == bool(replay.step_explore[7])
    assert frame.rods == decode_state(replay.step_state[7], replay.num_discs)


def test_the_q_update_lands_late_in_the_step(player):
    t0, dur = player.schedule.step_t0[3], player.schedule.step_dur[3]
    player.seek(t0 + dur * (UPDATE_PHASE - 0.1))
    assert player.frame().applied == 3
    player.seek(t0 + dur * (UPDATE_PHASE + 0.05))
    assert player.frame().applied == 4


def test_episode_return_accumulates_within_an_episode_only(player, replay):
    second = replay.episode_start[1]
    player.seek(player.schedule.step_t0[second] + 1e-6)
    assert player.frame().episode_return == replay.step_reward[second]


def test_seek_clamps_to_the_run(player):
    player.seek(-5)
    assert player.t == 0.0
    player.seek(1e9)
    assert player.t == player.schedule.total_s
    assert player.frame().done


def test_seek_episode_jumps_to_that_episodes_first_step(player, replay):
    player.seek_episode(10)
    assert player.frame().step == replay.episode_start[10]
    player.seek_episode(10_000)
    assert player.frame().episode == replay.episode_count - 1


def test_heatmap_masks_illegal_moves_and_matches_the_replayed_table(player, replay):
    applied = replay.step_count
    columns = player.heatmap_columns(applied)
    table = QReplayer(replay).seek(applied)
    legal = replay.legal_table()
    assert len(columns) == len(table)
    for state, column in enumerate(columns):
        for action, value in enumerate(column):
            if legal[state] >> action & 1:
                assert value == pytest.approx(table[state, action])
            else:
                assert value is None


def test_chart_series_cover_exactly_the_requested_range(player, replay):
    assert len(player.reward_by_episode(5)) == 5
    assert player.steps_by_episode(3) == [
        [e + 1, replay.episode_start[e + 1] - replay.episode_start[e]] for e in range(3)
    ]
    first = replay.episode_start[2]
    series = player.return_in_episode(2, first + 3)
    assert [x for x, _ in series] == [1, 2, 3, 4]
    assert series[-1][1] == pytest.approx(sum(replay.step_reward[first : first + 4]))
    deltas = player.q_change_in_episode(2, first + 3)
    assert len(deltas) == 4 and all(v >= 0 for _, v in deltas)


def test_epsilon_series_has_one_point_per_episode(player, replay):
    series = player.epsilon_by_episode()
    assert len(series) == replay.episode_count
    assert series[0] == [1, replay.episode_epsilon[0]]
    assert np.all(np.diff([v for _, v in series]) <= 1e-12)


def test_reward_points_split_solved_from_failed_and_average(player, replay):
    rows = player.reward_points(40)
    assert len(rows) == 40
    for e, (episode, solved, failed, average) in enumerate(rows):
        assert episode == e + 1
        assert (solved is None) != (failed is None)  # exactly one of the two dots
        assert (solved is not None) == bool(replay.episode_solved[e])
    window = replay.episode_reward[15:40]
    assert rows[39][3] == pytest.approx(sum(window) / 25, abs=1e-3)
    assert rows[0][3] == replay.episode_reward[0]


def test_step_points_count_the_steps_of_each_episode(player, replay):
    rows = player.step_points(10)
    for e, (episode, solved, failed) in enumerate(rows):
        steps = len(replay.episode_range(e))
        assert solved == (steps if replay.episode_solved[e] else None)
        assert failed == (None if replay.episode_solved[e] else steps)


def test_return_vs_best_ghosts_the_best_solved_episode_so_far(player, replay):
    first_solved = next(e for e in range(replay.episode_count) if replay.episode_solved[e])
    assert all(r[2] is None for r in player.return_vs_best(first_solved, replay.episode_start[first_solved]))
    later = first_solved + 1
    rows = player.return_vs_best(later, replay.episode_start[later] + 2)
    assert [r[1] is not None for r in rows[:3]] == [True, True, True]
    assert rows[0][2] == player._cumulative[replay.episode_start[first_solved]]
    assert len(rows) >= len(replay.episode_range(first_solved))


def test_q_change_bars_split_by_decision_mode(player, replay):
    first = replay.episode_start[3]
    rows = player.q_change_bars(3, first + 5)
    for i, (step, explored, exploited) in enumerate(rows):
        assert step == i + 1
        assert (explored is None) != (exploited is None)
        assert (explored is not None) == bool(replay.step_explore[first + i])
