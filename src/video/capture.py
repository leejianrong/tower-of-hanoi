"""Capture the dashboard frame by frame in headless Chromium and encode it with ffmpeg (ADR-0009).

Each worker owns a browser page in ``?record=1`` mode. For every frame it asks the page to show an
exact time, waits until the page says the board and Python's charts have caught up, screenshots,
and pipes the PNG into its own ffmpeg process, so no frames pile up on disk.
"""

import asyncio
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import indah
from src.dashboard.app import create_app
from src.replay.compact import ReplayData
from src.replay.schedule import Pacing
from src.video.plan import (
    ExportPlan,
    concat_args,
    concat_listing,
    segment_args,
    split_frames,
)

if TYPE_CHECKING:
    from playwright.async_api import Browser

VIEWPORT = {"width": 1920, "height": 1080}
SEEK_TIMEOUT_MS = 20_000
CHROMIUM_ARGS = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]


class ExportError(RuntimeError):
    pass


async def _run(args: list[str], what: str) -> None:
    process = await asyncio.create_subprocess_exec(*args, stderr=asyncio.subprocess.PIPE)
    _, stderr = await process.communicate()
    if process.returncode:
        raise ExportError(f"{what} failed: {stderr.decode(errors='replace').strip()}")


async def capture_segment(
    browser: "Browser",
    url: str,
    plan: ExportPlan,
    frames: range,
    out: Path,
    *,
    crf: int,
    theme: str,
    on_frame: Callable[[], None],
) -> None:
    context = await browser.new_context(
        viewport=VIEWPORT, device_scale_factor=1, color_scheme=theme
    )
    errors: list[str] = []
    page = await context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    ffmpeg = await asyncio.create_subprocess_exec(
        *segment_args(plan.fps, out, crf),
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert ffmpeg.stdin is not None
    try:
        await page.goto(f"{url}?record=1")
        await page.wait_for_function("window.hanoiRecorder !== undefined", timeout=60_000)
        for frame in frames:
            await page.evaluate(
                "([t, ms]) => Promise.race([window.hanoiRecorder.seek(t),"
                " new Promise((_, no) => setTimeout(() => no(new Error('seek timed out')), ms))])",
                [plan.time_of(frame), SEEK_TIMEOUT_MS],
            )
            ffmpeg.stdin.write(await page.screenshot(type="png"))
            await ffmpeg.stdin.drain()
            on_frame()
    except BaseException:
        ffmpeg.kill()
        raise
    finally:
        await context.close()
    ffmpeg.stdin.close()
    _, stderr = await ffmpeg.communicate()
    if ffmpeg.returncode:
        raise ExportError(f"ffmpeg failed: {stderr.decode(errors='replace').strip()}")
    if errors:
        raise ExportError(f"The page reported errors: {errors[:3]}")


async def export_video(
    replay: ReplayData,
    out: Path,
    plan: ExportPlan,
    *,
    workers: int = 2,
    crf: int = 16,
    theme: str = "dark",
    pacing: Pacing | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Render ``plan`` to ``out`` (an .mp4). Raises ExportError on any failure."""
    if shutil.which("ffmpeg") is None:
        raise ExportError("ffmpeg is not installed or not on PATH.")
    try:
        from playwright.async_api import async_playwright
    except ImportError as error:
        raise ExportError("Playwright is missing: run `uv sync --group video`.") from error
    handle = indah.launch(create_app(replay, pacing, kiosk=True), block=False)
    total = plan.frame_count
    done = 0

    def on_frame() -> None:
        nonlocal done
        done += 1
        if progress:
            progress(done, total)

    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="hanoi-export-") as scratch:
            runs = split_frames(total, workers)
            segments = [Path(scratch) / f"segment-{i:03d}.mp4" for i in range(len(runs))]
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(args=CHROMIUM_ARGS)
                try:
                    await asyncio.gather(
                        *(
                            capture_segment(
                                browser, handle.url, plan, frames, segment,
                                crf=crf, theme=theme, on_frame=on_frame,
                            )
                            for frames, segment in zip(runs, segments)
                        )
                    )  # fmt: skip
                finally:
                    await browser.close()
            listing = Path(scratch) / "segments.txt"
            listing.write_text(concat_listing(segments))
            await _run(concat_args(listing, out), "ffmpeg concat")
    finally:
        handle.stop()
    return out
