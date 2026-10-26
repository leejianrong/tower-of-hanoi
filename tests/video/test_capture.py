"""End to end: needs Chromium (Playwright), the ``video`` group and ffmpeg; skipped otherwise."""

import asyncio
import shutil
import subprocess
import time

import indah
import pytest

from src.dashboard.app import create_app
from src.dashboard.player import Player
from src.replay.schedule import build_schedule
from src.video.capture import CHROMIUM_ARGS, VIEWPORT
from src.video.plan import ExportPlan

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")


def _launch():
    from playwright.async_api import async_playwright

    return async_playwright()


@pytest.mark.parametrize("server_delay", [0.0, 0.25])
def test_a_seeked_frame_is_already_settled(replay, monkeypatch, server_delay):
    """The frame taken as soon as ``seek`` resolves equals the one taken after the page is idle.

    The delay makes Python slow to follow the clock, as a loaded machine would; a recorder that did
    not wait for the acknowledgement would capture charts that are still on the previous time.
    """
    seek = Player.seek

    def slow_seek(self, t):
        time.sleep(server_delay)
        return seek(self, t)

    monkeypatch.setattr(Player, "seek", slow_seek)
    total = build_schedule(replay).total_s
    # Large jumps in both directions force the charts and the Q-table to redraw from far away.
    times = [total * 0.9, 0.0, total * 0.45, total * 0.46, total * 0.2]

    async def run():
        handle = indah.launch(create_app(replay, kiosk=True), block=False)
        try:
            async with _launch() as playwright:
                try:
                    browser = await playwright.chromium.launch(args=CHROMIUM_ARGS)
                except Exception as error:  # no browser binary installed
                    pytest.skip(f"Chromium is unavailable: {error}")
                page = await browser.new_page(viewport=VIEWPORT, color_scheme="dark")
                await page.goto(f"{handle.url}?record=1")
                await page.wait_for_function("window.hanoiRecorder !== undefined")
                pairs = []
                for t in times:
                    await page.evaluate("t => window.hanoiRecorder.seek(t)", t)
                    quick = await page.screenshot()
                    await page.wait_for_timeout(1000 + int(server_delay * 1000))
                    pairs.append((t, quick, await page.screenshot()))
                await browser.close()
                return pairs
        finally:
            handle.stop()

    for t, quick, settled in asyncio.run(run()):
        assert quick == settled, f"the frame at t={t:.2f}s was captured before the page settled"


def _probe(path, entries, *extra):
    return subprocess.run(
        ["ffprobe", "-v", "error", *extra, "-show_entries", entries, "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.split()  # fmt: skip


def test_export_writes_a_video_with_the_planned_frames_and_a_matching_soundtrack(replay, tmp_path):
    from src.video.capture import export_video

    plan = ExportPlan(start=1, end=2, fps=12, speed=1)
    out = asyncio.run(export_video(replay, tmp_path / "out.mp4", plan, workers=2, crf=30))
    size = _probe(out, "stream=width,height,nb_read_frames", "-select_streams", "v", "-count_frames")
    assert size == [f"{VIEWPORT['width']},{VIEWPORT['height']},{plan.frame_count}"]
    durations = dict(line.split(",") for line in _probe(out, "stream=codec_type,duration"))
    assert float(durations["video"]) == pytest.approx(1.0, abs=0.01)
    assert float(durations["audio"]) == pytest.approx(float(durations["video"]), abs=0.03)


def test_export_without_audio_has_no_audio_stream(replay, tmp_path):
    from src.video.capture import export_video

    plan = ExportPlan(start=1, end=1.5, fps=10, speed=1)
    out = asyncio.run(export_video(replay, tmp_path / "quiet.mp4", plan, workers=1, audio=False))
    assert _probe(out, "stream=codec_type") == ["video"]
