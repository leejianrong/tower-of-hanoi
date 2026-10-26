"""The browser plays the cue list as the clock passes it. Needs Chromium; skipped without it."""

import asyncio

import indah
import pytest

from src.audio.cues import build_cues
from src.dashboard.app import create_app
from src.replay.schedule import build_schedule
from src.video.capture import CHROMIUM_ARGS, VIEWPORT

pytest.importorskip("playwright.async_api")

# Count every sound the page starts, by buffer length, without needing speakers.
HOOK = """
window.__played = [];
const start = AudioBufferSourceNode.prototype.start;
AudioBufferSourceNode.prototype.start = function (...args) {
  window.__played.push(this.buffer.length);
  return start.apply(this, args);
};
"""


def _run(replay, scenario):
    from playwright.async_api import async_playwright

    async def go():
        handle = indah.launch(create_app(replay, kiosk=True), block=False)
        try:
            async with async_playwright() as playwright:
                try:
                    browser = await playwright.chromium.launch(
                        args=CHROMIUM_ARGS + ["--autoplay-policy=no-user-gesture-required"]
                    )
                except Exception as error:
                    pytest.skip(f"Chromium is unavailable: {error}")
                page = await browser.new_page(viewport=VIEWPORT)
                await page.add_init_script(HOOK)
                result = await scenario(page, handle.url)
                await browser.close()
                return result
        finally:
            handle.stop()

    return asyncio.run(go())


async def _open(page, url, t, query=""):
    await page.goto(f"{url}?t={t}{query}")
    await page.wait_for_selector("indah-x-hanoi-stage")
    await page.wait_for_timeout(1500)
    await page.mouse.click(5, 5)  # a gesture: browsers load audio only after one
    await page.wait_for_function("window.__played !== undefined")


def test_the_browser_plays_the_cues_the_clock_passes(replay):
    schedule = build_schedule(replay)
    t = schedule.step_t0[replay.step_count // 3]
    cues = build_cues(replay, schedule)

    async def scenario(page, url):
        await _open(page, url, t, "&paused=1")
        await page.keyboard.press("Space")
        before = len(await page.evaluate("window.__played"))
        await page.wait_for_timeout(3000)
        await page.keyboard.press("Space")
        return len(await page.evaluate("window.__played")) - before

    played = _run(replay, scenario)
    expected = len(cues.between(t, t + 3.0))
    assert expected > 0 and abs(played - expected) <= 4, (played, expected)


def test_nothing_plays_when_muted_paused_scrubbed_or_fast(replay):
    schedule = build_schedule(replay)
    t = schedule.step_t0[replay.step_count // 3]

    async def count(page):
        return len(await page.evaluate("window.__played"))

    async def scenario(page, url):
        await _open(page, url, t, "&paused=1")
        await page.wait_for_timeout(1500)
        paused = await count(page)
        await page.keyboard.press("KeyM")  # mute, then play
        await page.keyboard.press("Space")
        await page.wait_for_timeout(2500)
        muted = await count(page)
        await page.keyboard.press("KeyM")  # sound back on, jump around: seeks stay silent
        await page.keyboard.press("Space")  # pause
        await page.keyboard.press("ArrowRight")
        await page.keyboard.press("ArrowRight")
        await page.wait_for_timeout(500)
        stepped = await count(page)
        await page.click("button[aria-label='Speed 16 times']", force=True)
        return paused, muted, stepped

    paused, muted, stepped = _run(replay, scenario)
    assert paused == muted == stepped == 0
