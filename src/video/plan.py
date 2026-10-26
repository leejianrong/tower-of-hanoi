"""Pure planning for the video export (ADR-0009): which times to draw and how to run ffmpeg.

No browser and no ffmpeg here, so all of it is testable. Video time ``i / fps`` maps to timeline
time ``start + i * speed / fps``; ``speed`` is the playback multiplier (64 turns a 14 hour
timeline into a 13 minute video).
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPlan:
    start: float  # timeline seconds of the first frame
    end: float  # timeline seconds the video stops at (exclusive)
    fps: int = 60
    speed: float = 1.0

    def __post_init__(self) -> None:
        if self.fps < 1 or self.speed <= 0 or self.end <= self.start or self.start < 0:
            raise ValueError(f"Invalid export plan: {self!r}")

    @property
    def frame_count(self) -> int:
        return max(1, round((self.end - self.start) / self.speed * self.fps))

    def time_of(self, frame: int) -> float:
        return self.start + frame * self.speed / self.fps


def split_frames(count: int, workers: int) -> list[range]:
    """Cut ``count`` frames into at most ``workers`` consecutive runs of near-equal length."""
    if count < 1 or workers < 1:
        raise ValueError("count and workers must be positive")
    workers = min(workers, count)
    base, extra = divmod(count, workers)
    runs, first = [], 0
    for worker in range(workers):
        size = base + (1 if worker < extra else 0)
        runs.append(range(first, first + size))
        first += size
    return runs


def segment_args(fps: int, out: Path, crf: int = 16) -> list[str]:
    """ffmpeg reads PNG frames from stdin and writes one H.264 segment."""
    return [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-r", str(fps), str(out),
    ]  # fmt: skip


def concat_args(listing: Path, out: Path) -> list[str]:
    """Join segments with identical encoding parameters without re-encoding them."""
    return [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", "-movflags", "+faststart", str(out),
    ]  # fmt: skip


def concat_listing(segments: list[Path]) -> str:
    return "".join(f"file '{segment.resolve()}'\n" for segment in segments)
