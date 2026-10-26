import pytest

from src.audio.cues import STEP_CUES, CueSettings, build_cues
from src.audio.synth import MAX_DISCS, build_sounds
from src.replay.schedule import Pacing, build_schedule, record_episodes


def _names(cues, indices=None):
    indices = range(len(cues)) if indices is None else indices
    return [cues.names[cues.sound[i]] for i in indices]


def test_cues_are_sorted_and_every_name_has_a_sound(replay):
    cues = build_cues(replay, build_schedule(replay))
    assert cues.t == sorted(cues.t)
    assert set(cues.names) <= set(build_sounds())
    assert len(cues.t) == len(cues.sound)


def test_each_step_gets_a_decision_a_lift_a_landing_and_an_update(replay):
    schedule = build_schedule(replay)
    cues = build_cues(replay, schedule)
    step = replay.step_count // 2
    t0, dur = schedule.step_t0[step], schedule.step_dur[step]
    inside = cues.between(t0 - 1e-6, t0 + dur - 1e-3)
    names = _names(cues, inside)
    assert names.count("lift") == 1
    assert [n for n in names if n in ("explore", "exploit")] == [
        "explore" if replay.step_explore[step] else "exploit"
    ]
    assert f"land_{replay.step_disc[step]}" in names
    assert any(n.startswith("update_") for n in names)
    lift_t = cues.t[inside[names.index("lift")]]
    land_t = cues.t[inside[next(i for i, n in enumerate(names) if n.startswith("land_"))]]
    assert t0 < lift_t < land_t < t0 + dur


def test_every_step_lands_a_disc_that_exists(replay):
    cues = build_cues(replay, build_schedule(replay))
    lands = [n for n in cues.names if n.startswith("land_")]
    assert all(int(n.split("_")[1]) < min(replay.num_discs, MAX_DISCS) for n in lands)


def test_episode_endings_use_record_solved_and_final(replay):
    cues = build_cues(replay, build_schedule(replay))
    endings = [n for n in _names(cues) if n in ("record", "solved", "fail", "final")]
    last = replay.episode_count - 1
    records = record_episodes(replay)
    final = {last} if replay.episode_optimal[last] else set()
    solved = {e for e in range(replay.episode_count) if replay.episode_solved[e]}
    assert endings.count("final") == len(final)
    assert endings.count("record") == len(records - final)
    assert endings.count("solved") == len(solved - records - final)
    if final:
        assert endings[-1] == "final"


def test_the_ending_sound_plays_after_the_last_step_of_the_episode(replay):
    schedule = build_schedule(replay)
    cues = build_cues(replay, schedule)
    ending = [i for i, n in enumerate(_names(cues)) if n in ("record", "solved", "fail", "final")][0]
    last_end = max(
        schedule.step_t0[s] + schedule.step_dur[s]
        for s in range(replay.step_count)
        if schedule.step_t0[s] + schedule.step_dur[s] <= cues.t[ending] + 1e-6
    )
    assert cues.t[ending] == pytest.approx(last_end, abs=1e-3)


def test_short_steps_get_no_per_step_sounds_and_quick_failures_stay_silent(replay):
    flashing = build_cues(replay, build_schedule(replay, Pacing(constant_step_s=None)))
    first_episode_steps = replay.episode_range(0)
    schedule = build_schedule(replay, Pacing(constant_step_s=None))
    slow_until = schedule.step_t0[first_episode_steps[min(23, len(first_episode_steps) - 1)]] + 0.7
    late = [n for i, n in enumerate(_names(flashing)) if flashing.t[i] > slow_until + 5]
    steps_sounds = [n for n in late if n in STEP_CUES]
    # after the slow intro, only slowed episodes (records, the final solve) have per-step sounds
    assert len(steps_sounds) < len(late)
    quiet = build_cues(replay, schedule, CueSettings(min_fail_episode_s=1e9))
    assert "fail" not in quiet.names


def test_updates_can_be_muted(replay):
    cues = build_cues(replay, build_schedule(replay), CueSettings(mute_updates=True))
    assert not any(n.startswith("update_") for n in cues.names)


def test_between_returns_the_cues_passed_as_the_clock_moves(replay):
    cues = build_cues(replay, build_schedule(replay))
    t = cues.t
    assert list(cues.between(-1, t[0] - 1e-9)) == []
    assert list(cues.between(-1, t[0])) == [0]
    assert list(cues.between(t[3], t[3])) == []
    assert list(cues.between(t[3] - 1e-9, t[3])) == [3]
    assert len(cues.between(-1, t[-1] + 1)) == len(t)
