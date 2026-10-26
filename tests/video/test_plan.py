from pathlib import Path

import pytest

from src.video.plan import ExportPlan, concat_listing, segment_args, split_frames


def test_frame_times_follow_fps_and_speed():
    plan = ExportPlan(start=10, end=12, fps=30, speed=1)
    assert plan.frame_count == 60
    assert plan.time_of(0) == 10
    assert plan.time_of(30) == pytest.approx(11)
    fast = ExportPlan(start=0, end=64, fps=60, speed=64)
    assert fast.frame_count == 60
    assert fast.time_of(1) == pytest.approx(64 / 60)


def test_a_plan_always_has_a_frame_and_rejects_nonsense():
    assert ExportPlan(0, 0.001, fps=1).frame_count == 1
    for bad in ({"start": 5, "end": 5}, {"start": -1, "end": 5}, {"start": 0, "end": 5, "fps": 0},
                {"start": 0, "end": 5, "speed": 0}):  # fmt: skip
        with pytest.raises(ValueError):
            ExportPlan(**bad)


@pytest.mark.parametrize("count,workers", [(10, 3), (3, 8), (1, 1), (60, 4)])
def test_split_frames_covers_every_frame_once_in_order(count, workers):
    runs = split_frames(count, workers)
    assert [f for run in runs for f in run] == list(range(count))
    assert len(runs) == min(count, workers)
    assert max(len(r) for r in runs) - min(len(r) for r in runs) <= 1


def test_split_frames_rejects_empty_work():
    with pytest.raises(ValueError):
        split_frames(0, 2)


def test_ffmpeg_arguments_pipe_pngs_in_and_h264_out():
    args = segment_args(60, Path("a.mp4"), crf=18)
    assert args[0] == "ffmpeg" and args[-1] == "a.mp4"
    assert args[args.index("-framerate") + 1] == "60"
    assert args[args.index("-crf") + 1] == "18"
    assert "yuv420p" in args and "-" in args


def test_concat_listing_names_each_segment_absolutely(tmp_path):
    listing = concat_listing([tmp_path / "a.mp4", tmp_path / "b.mp4"])
    assert listing.splitlines() == [f"file '{tmp_path / 'a.mp4'}'", f"file '{tmp_path / 'b.mp4'}'"]
