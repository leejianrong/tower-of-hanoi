"""Export the dashboard as a video: ``python -m src.video [replay.json] [options]``.

Needs ffmpeg on PATH and the ``video`` dependency group (``uv sync --group video``) plus a
Playwright Chromium (``uv run playwright install chromium``).
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from src.core.game import RECORD_DIR
from src.replay.compact import ReplayData
from src.replay.schedule import build_schedule
from src.video.capture import ExportError, export_video
from src.video.plan import ExportPlan


def parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m src.video", description=__doc__)
    parser.add_argument("replay", nargs="?", type=Path, default=RECORD_DIR / "replay.json")
    parser.add_argument("--out", type=Path, default=RECORD_DIR / "hanoi.mp4")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--start", type=float, default=0.0, help="timeline seconds to start at")
    parser.add_argument("--end", type=float, help="timeline seconds to stop at (default: the end)")
    parser.add_argument("--speed", type=float, default=1.0, help="playback multiplier")
    parser.add_argument("--workers", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)))
    parser.add_argument("--crf", type=int, default=16, help="x264 quality, lower is better")
    parser.add_argument("--no-audio", action="store_true", help="skip the sound effects")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse(argv)
    replay = ReplayData.load(args.replay)
    total = build_schedule(replay).total_s
    plan = ExportPlan(args.start, min(args.end or total, total), args.fps, args.speed)

    def progress(done: int, count: int) -> None:
        if done % args.fps == 0 or done == count:
            print(f"\r{done}/{count} frames ({done / count:.0%})", end="", file=sys.stderr, flush=True)

    try:
        out = asyncio.run(
            export_video(
                replay, args.out, plan, workers=args.workers, crf=args.crf,
                theme=args.theme, audio=not args.no_audio, progress=progress,
            )
        )  # fmt: skip
    except ExportError as error:
        print(f"\nExport failed: {error}", file=sys.stderr)
        return 1
    print(f"\nWrote {out} ({plan.frame_count} frames, {plan.frame_count / plan.fps:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
